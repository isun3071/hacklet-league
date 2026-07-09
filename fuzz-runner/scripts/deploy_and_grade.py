#!/usr/bin/env python3
"""LLM-assisted deploy + grade for a hackathon repo (Devpost / GitHub).

Clone a repo, ask an LLM (via OpenRouter) HOW to deploy it — a Dockerfile, an optional DB sidecar, env,
and a migrate step — then execute that plan on a throwaway docker network, iterating on build/run/health
failures by feeding the error back to the LLM, and finally grade the running app with the fuzz-runner.
The LLM ONLY figures out the deploy; the fuzzer does the grading.

    export OPENROUTER_API_KEY=sk-or-...
    # optional: export OPENROUTER_MODEL=...   (default deepseek/deepseek-v4-flash — cheap; deploy-planning
    #   is a read-the-repo/write-a-Dockerfile task, not frontier work, and the retry loop covers misses)
    uv run python scripts/deploy_and_grade.py https://github.com/user/repo
    uv run python scripts/deploy_and_grade.py --browser --attempts 4 https://github.com/user/repo
    uv run python scripts/deploy_and_grade.py /path/to/local/repo         # skip the clone

Safety: builds + runs UNTRUSTED code in Docker. Run it on a sandbox/firewalled box (your RMM workstation
is ideal). It does NOT inject real secrets — an app needing an external API key may only partly boot; the
grader still probes whatever comes up.
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

import httpx

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from hacklet_runner import browser  # noqa: E402
from hacklet_runner.catalog import load_catalog  # noqa: E402
from hacklet_runner.deploy import RemoteDeployer  # noqa: E402
from hacklet_runner.pipeline import run  # noqa: E402

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
NET = "hl-deploy-net"
APP = "hl-deploy-app"
DB = "hl-db"
DB_CREDS = {"user": "hacklet", "password": "hacklet", "db": "hacklet"}


class DeployError(Exception):
    """A build/run/health failure whose message is fed back to the LLM for a revised plan."""


# ---- docker helpers -------------------------------------------------------------------------------

def _docker(*args, timeout=None, check=False):
    p = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise DeployError((p.stderr or p.stdout)[-3000:])
    return p


_STEP = re.compile(r"^#\d+ \[[^\]]*\d+/\d+\]\s+(.+)")   # BuildKit step header, e.g. "#5 [2/6] RUN npm ci"
_STEP_LEGACY = re.compile(r"^Step \d+/\d+ : (.+)")       # legacy builder
_META = re.compile(r"load metadata for (\S+)")


def _build_streamed(dockerfile, ctx, verbose=False, timeout=1200):
    """docker build. verbose -> stream every line (prefixed '│'). Otherwise print only the high-level
    steps: base-image pull, each RUN/COPY/WORKDIR instruction (so 'RUN npm install' / 'RUN pip install
    -r requirements.txt' are visible), and errors — with a heartbeat during long steps. Always captures
    the tail for the LLM error-feedback loop."""
    proc = subprocess.Popen(["docker", "build", "-f", str(dockerfile), "-t", APP, str(ctx)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines, start, dots = [], time.time(), 0
    for line in proc.stdout:
        lines.append(line)
        if verbose:
            sys.stderr.write("    │ " + line)
            sys.stderr.flush()
        else:
            step = _STEP.match(line) or _STEP_LEGACY.match(line)
            meta = _META.search(line)
            if step or meta or (line.startswith("#") and "ERROR" in line):
                if dots:
                    sys.stderr.write("\n"); dots = 0
                if step:
                    sys.stderr.write("    ▸ " + step.group(1).split("@sha256:")[0].strip()[:90] + "\n")
                elif meta:
                    sys.stderr.write("    ▸ pulling base image " + meta.group(1) + "\n")
                else:
                    sys.stderr.write("    ✗ " + line.strip()[:120] + "\n")
                sys.stderr.flush()
            elif line.strip():          # suppressed detail -> a heartbeat so long installs show life
                dots += 1
                if dots % 80 == 0:
                    sys.stderr.write("."); sys.stderr.flush()
        if time.time() - start > timeout:
            proc.kill()
            lines.append("\n(build exceeded %ds — killed)" % timeout)
            break
    if dots:
        sys.stderr.write("\n")
    proc.wait()
    return proc.returncode, "".join(lines)[-3000:]


def _teardown():
    _docker("rm", "-f", APP, DB)
    _docker("network", "rm", NET)
    _docker("rmi", "-f", APP)   # drop this repo's app image; base images stay cached (speeds later builds)


# ---- 1. clone + gather deploy context -------------------------------------------------------------

_CONTEXT_FILES = ("README.md", "README", "readme.md", "package.json", "requirements.txt", "Pipfile",
                  "pyproject.toml", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
                  "Procfile", ".env.example", ".env.sample", "go.mod", "Gemfile", "composer.json",
                  "next.config.js", "vite.config.js", "app.py", "main.py", "server.js", "index.js",
                  "manage.py", "wsgi.py", "asgi.py")


def clone(url_or_path: str) -> pathlib.Path:
    if pathlib.Path(url_or_path).exists():
        return pathlib.Path(url_or_path).resolve()
    dest = pathlib.Path(tempfile.mkdtemp(prefix="hl-deploy-")) / "repo"
    print(f"  cloning {url_or_path} ...")
    p = subprocess.run(["git", "clone", "--depth", "1", url_or_path, str(dest)],
                       capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        sys.exit(f"clone failed: {p.stderr.strip()[:300]}")
    return dest


def gather_context(repo: pathlib.Path) -> str:
    tree = subprocess.run(["bash", "-c",
                           f"cd {repo} && (git ls-files 2>/dev/null || find . -type f) "
                           "| grep -vE 'node_modules/|\\.git/|dist/|build/|venv/' | head -200"],
                          capture_output=True, text=True).stdout
    parts = [f"REPO FILE TREE (truncated):\n{tree}"]
    seen = set()
    for pat in _CONTEXT_FILES:
        for f in list(repo.rglob(pat))[:2]:
            if f.is_file() and f not in seen and "node_modules" not in f.parts and ".git" not in f.parts:
                seen.add(f)
                try:
                    body = f.read_text(encoding="utf-8", errors="replace")[:4000]
                except OSError:
                    continue
                parts.append(f"\n===== {f.relative_to(repo)} =====\n{body}")
    return "\n".join(parts)[:24000]


# ---- 2. ask the LLM for a deploy plan -------------------------------------------------------------

_SYSTEM = """You are a deployment engineer. Given a hackathon repo, output a JSON plan to build and run it
in Docker for black-box testing. Respond with ONLY a JSON object, no prose, no markdown fences.

Constraints and environment you are targeting:
- A shared docker network. If the app needs a database, request a sidecar; it will be reachable at
  hostname "hl-db" on the standard port. Credentials are user=hacklet password=hacklet db=hacklet.
- The app MUST bind 0.0.0.0 (not 127.0.0.1) and listen on the "port" you specify.
- Do NOT rely on real third-party secrets/API keys. If the app reads env vars, provide harmless
  defaults in app_env so it boots as far as possible; note in "notes" anything that won't work.
- Prefer generating a fresh, correct Dockerfile over a broken existing one. Pin dependency versions that
  are known to be mutually compatible (e.g. Flask 2.0.x needs Werkzeug 2.0.x). Install deps, copy the
  app code (many repos' Dockerfiles forget to COPY the code), set the workdir, expose the port.

JSON schema (all keys required unless marked optional):
{
  "stack": "short description, e.g. 'Flask + Postgres'",
  "dockerfile": "the FULL Dockerfile text to write at the build_context root",
  "files": { "relative/path": "full file contents to overwrite/create (repairs, e.g. a fixed requirements.txt)" },  // optional, may be {}
  "build_context": ".",                       // subdir (relative to repo root) holding the app
  "port": 8000,                                // the port the app listens on inside the container
  "app_env": { "KEY": "value" },               // env for the app container (DB url, harmless defaults)
  "db": { "type": "postgres|mysql|mongo|none", "image": "postgres:16-alpine", "env": {"POSTGRES_USER":"hacklet","POSTGRES_PASSWORD":"hacklet","POSTGRES_DB":"hacklet"} },
  "migrate": "optional shell command to run in the app image before serving (e.g. 'flask db upgrade'), or empty string",
  "health_path": "/",                          // a path that returns <500 when the app is up
  "notes": "anything the grader should know"
}
If a previous attempt failed, you will be given the error — fix the specific cause (missing COPY, wrong
port, dep conflict, missing build tool, wrong start command, DB not ready, etc.)."""


def plan_deploy(context: str, model: str, error: str = "", prev: dict = None) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set. export it and re-run.")
    user = f"REPO CONTEXT:\n{context}"
    if error:
        user += (f"\n\nThe PREVIOUS plan FAILED. Previous plan:\n{json.dumps(prev)[:3000]}"
                 f"\n\nError output:\n{error[:4000]}\n\nReturn a corrected JSON plan.")
    body = {"model": model, "temperature": 0.2,
            "messages": [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}]}
    try:
        r = httpx.post(OPENROUTER_URL, json=body, timeout=120,
                       headers={"Authorization": "Bearer " + key,
                                "HTTP-Referer": "https://hacklet.league", "X-Title": "hacklet-deploy"})
    except httpx.HTTPError as e:
        sys.exit(f"OpenRouter request failed: {e}")
    if r.status_code != 200:
        sys.exit(f"OpenRouter {r.status_code}: {r.text[:400]}")
    content = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", content, re.S)   # tolerate stray prose / code fences
    if not m:
        sys.exit(f"LLM did not return JSON:\n{content[:400]}")
    return json.loads(m.group(0))


# ---- 3. execute the plan --------------------------------------------------------------------------

_DB_READY = {
    "postgres": ["pg_isready", "-U", DB_CREDS["user"]],
    "mysql": ["mysqladmin", "ping", "-h", "127.0.0.1", "-u", "root", "-phacklet"],
    "mongo": ["mongosh", "--quiet", "--eval", "db.runCommand({ping:1})"],
}
_DB_DEFAULT_IMAGE = {"postgres": "postgres:16-alpine", "mysql": "mysql:8", "mongo": "mongo:7"}


def _start_db(db: dict):
    dbtype = db.get("type", "none")
    if dbtype in ("none", "", None):
        return
    image = db.get("image") or _DB_DEFAULT_IMAGE.get(dbtype, "postgres:16-alpine")
    env = db.get("env") or {}
    if dbtype == "mysql":
        env.setdefault("MYSQL_ROOT_PASSWORD", "hacklet")
        env.setdefault("MYSQL_DATABASE", DB_CREDS["db"])
    print(f"  starting {dbtype} sidecar ({image}) at host '{DB}' ...")
    args = ["run", "-d", "--name", DB, "--network", NET]
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]
    _docker(*args, image, check=True)
    ready = _DB_READY.get(dbtype)
    for _ in range(40):
        if ready and _docker("exec", DB, *ready).returncode == 0:
            print("  db ready"); return
        time.sleep(2)
    print("  (db readiness probe timed out — continuing anyway)")


def execute(plan: dict, repo: pathlib.Path, verbose: bool = False) -> str:
    _docker("rm", "-f", APP)
    _docker("network", "create", NET)  # idempotent-ish; ignore "already exists"
    _start_db(plan.get("db") or {"type": "none"})

    ctx = (repo / plan.get("build_context", ".")).resolve()
    for rel, content in (plan.get("files") or {}).items():
        target = (ctx / rel).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    dockerfile = ctx / "Dockerfile.hacklet"
    dockerfile.write_text(plan["dockerfile"])

    print("  docker build (streaming — base-image pull + npm/pip install is the slow part):")
    rc, tail = _build_streamed(dockerfile, ctx, verbose=verbose)
    if rc != 0:
        raise DeployError("BUILD FAILED:\n" + tail)

    app_env = plan.get("app_env") or {}
    env_args = []
    for k, v in app_env.items():
        env_args += ["-e", f"{k}={v}"]
    env_args += ["-e", f"PORT={plan['port']}"]

    migrate = (plan.get("migrate") or "").strip()
    if migrate:
        print(f"  migrate: {migrate}")
        m = _docker("run", "--rm", "--network", NET, *env_args, APP, "sh", "-c", migrate, timeout=300)
        if m.returncode != 0:
            print("  (migrate returned nonzero — continuing)\n" + (m.stderr or m.stdout)[-600:])

    print("  running app ...")
    _docker("run", "-d", "--name", APP, "--network", NET, *env_args, APP, check=True, timeout=120)
    time.sleep(3)
    ip = _docker("inspect", "-f",
                 '{{(index .NetworkSettings.Networks "%s").IPAddress}}' % NET, APP).stdout.strip()
    if not ip:
        raise DeployError("app container has no IP (it exited?):\n" + _docker("logs", "--tail", "40", APP).stderr)
    url = f"http://{ip}:{plan['port']}"
    health = plan.get("health_path", "/")
    for _ in range(20):
        p = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "4",
                            url + health], capture_output=True, text=True)
        code = p.stdout.strip()
        if code and code != "000" and int(code) < 500:
            print(f"  up at {url} (health {health} -> {code})")
            return url
        time.sleep(2)
    logs = _docker("logs", "--tail", "50", APP)
    raise DeployError(f"app did not become healthy at {url}{health}.\nLOGS:\n"
                      + (logs.stdout + logs.stderr)[-3000:])


# ---- 4. grade + main ------------------------------------------------------------------------------

def grade(url: str, use_browser: bool):
    render = browser.render_html if use_browser else None
    report = run(RemoteDeployer(url, health_timeout=20), load_catalog(str(_ROOT / "catalog")), render=render)
    return report


def main():
    ap = argparse.ArgumentParser(description="LLM-assisted deploy + fuzz-grade of a hackathon repo.")
    ap.add_argument("repo", help="a git URL or a local path")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id (default: %(default)s)")
    ap.add_argument("--attempts", type=int, default=3, help="max deploy attempts (LLM fixes errors between)")
    ap.add_argument("--browser", action="store_true", help="grade the browser surface too (a11y/CWV/DOM-XSS)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="stream the full docker build output (default: high-level steps only)")
    ap.add_argument("--keep", action="store_true", help="don't tear the containers down after grading")
    args = ap.parse_args()

    repo = clone(args.repo)
    context = gather_context(repo)
    plan, url, error = None, None, ""
    try:
        for attempt in range(1, args.attempts + 1):
            print(f"\n=== attempt {attempt}/{args.attempts}: planning deploy ({args.model}) ===")
            plan = plan_deploy(context, args.model, error=error, prev=plan)
            print(f"  stack: {plan.get('stack')}  port: {plan.get('port')}  db: {(plan.get('db') or {}).get('type')}")
            if plan.get("notes"):
                print(f"  notes: {plan['notes'][:200]}")
            try:
                url = execute(plan, repo, verbose=args.verbose)
                break
            except DeployError as e:
                error = str(e)
                print(f"  deploy failed:\n{error[-800:]}")
                _docker("rm", "-f", APP)
        if not url:
            print("\nGAVE UP — could not deploy after all attempts.")
            return
        print(f"\n=== grading {url} ===")
        report = grade(url, args.browser)
        slop = [o for o in report.outcomes if o.outcome == "slop_detected"]
        print(f"\n  SLOP SCORE: {report.slop_score}   axis: {report.axis_slop}")
        print(f"  {len(slop)} findings — security-relevant:")
        for pid in sorted({o.probe_id for o in slop if o.probe_id.startswith("sec-")}):
            o = next(o for o in slop if o.probe_id == pid)
            print(f"    {pid:18} {o.category:20} {o.penalty:>3}  {o.reason[:70]}")
    finally:
        if args.keep:
            print(f"\n(left running: docker rm -f {APP} {DB}; docker network rm {NET})")
        else:
            _teardown()
        if str(repo).startswith(tempfile.gettempdir()):
            shutil.rmtree(repo.parent, ignore_errors=True)


if __name__ == "__main__":
    main()

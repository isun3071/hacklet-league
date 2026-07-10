#!/usr/bin/env python3
"""Grab hackathon project GitHub repos from Devpost — the input list for scripts/deploy_and_grade.py.

Two modes, toggled by flag:
  --hackathon SLUG   scrape ONE hackathon (its Devpost subdomain, e.g. madhacks-fall-2025)
  --search QUERY     auto-pick hackathons from Devpost's open hackathons JSON API matching QUERY

    uv run python scripts/devpost_repos.py --hackathon madhacks-fall-2025 --limit 15
    uv run python scripts/devpost_repos.py --search flask --hackathons 5 --completed --limit 20
    # chain straight into deploy + grade:
    uv run python scripts/devpost_repos.py --search flask --completed \
      | while read repo; do uv run python scripts/deploy_and_grade.py "$repo"; done

Repos go to stdout (one per line — pipeable); progress goes to stderr. `--json` emits
{hackathon, project, repo} records instead.

How it works (verified 2026): Devpost's hackathons API (`/api/hackathons`) is open JSON. The GLOBAL
software gallery is AWS-WAF-blocked, but each hackathon's OWN submissions pages
(`<slug>.devpost.com/submissions/search?page=N`) are plain server-rendered HTML with no WAF — so this
needs only httpx + a browser UA (no key, no Playwright). A project's real repo lives in the page's
`app-links` block (embedded vendor scripts like newrelic sit outside it, so they're excluded).
"""
import argparse
import json
import re
import sys
import time

import httpx

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
_HACK_API = "https://devpost.com/api/hackathons"
_SUBS = "https://{slug}.devpost.com/submissions/search?page={page}"
_PROJ = re.compile(r"https://devpost\.com/software/[a-z0-9][a-z0-9-]*")
_SLUG = re.compile(r"https?://([a-z0-9][a-z0-9-]*)\.devpost\.com")
_GH = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_APP_LINKS = re.compile(r"app-links.*?</ul>", re.S)


def _get(client, url, **kw):
    try:
        return client.get(url, headers={"User-Agent": UA}, timeout=25, **kw)
    except httpx.HTTPError:
        return None


def hackathon_slugs(client, query, count, completed):
    """Subdomain slugs of hackathons matching `query` (newest first), optionally only ended ones."""
    slugs, page = [], 1
    while len(slugs) < count and page <= 25:
        r = _get(client, _HACK_API, params={"search": query, "page": page})
        if not r or r.status_code != 200:
            break
        hacks = r.json().get("hackathons", [])
        if not hacks:
            break
        for h in hacks:
            if completed and not h.get("winners_announced") and h.get("open_state") != "ended":
                continue
            m = _SLUG.match(h.get("url", ""))
            if m and m.group(1) not in slugs:
                slugs.append(m.group(1))
                if len(slugs) >= count:
                    break
        page += 1
    return slugs


_GALLERY_SPLIT = re.compile(r'(?=class="[^"]*gallery-item)')


def project_urls(client, slug, pages):
    """(project_url, winner) per submission, across the first `pages` gallery pages. `winner` is BEST-EFFORT
    from a 'winner' marker in the gallery entry — Devpost only badges winners post-judging and often on a
    separate view, so it's frequently False/None; override per app with deploy_and_grade --meta if you have
    the real result."""
    out, seen = [], set()
    for page in range(1, pages + 1):
        r = _get(client, _SUBS.format(slug=slug, page=page))
        if not r or r.status_code != 200:
            break
        page_hits = []
        for block in _GALLERY_SPLIT.split(r.text)[1:]:
            m = _PROJ.search(block)
            if not m or m.group(0) in seen:
                continue
            seen.add(m.group(0))
            page_hits.append((m.group(0), bool(re.search(r"\bwinner\b", block, re.I))))
        if not page_hits:
            break
        out.extend(page_hits)
        time.sleep(0.3)
    return out


def repo_for(client, project_url):
    """The project's declared GitHub repo (first github link in its app-links block), or None."""
    r = _get(client, project_url)
    if not r or r.status_code != 200:
        return None
    block = _APP_LINKS.search(r.text)
    repos = list(dict.fromkeys(_GH.findall(block.group(0) if block else r.text)))
    return repos[0].rstrip('.,);"\'') if repos else None


def main():
    ap = argparse.ArgumentParser(description="Grab hackathon project GitHub repos from Devpost.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--hackathon", metavar="SLUG", help="one hackathon subdomain slug")
    mode.add_argument("--search", metavar="QUERY", help="auto-pick hackathons matching QUERY via the API")
    ap.add_argument("--hackathons", type=int, default=5, help="(--search) how many hackathons (default 5)")
    ap.add_argument("--completed", action="store_true",
                    help="(--search) only ended / winners-announced hackathons (real submissions)")
    ap.add_argument("--pages", type=int, default=1, help="submissions pages per hackathon (default 1)")
    ap.add_argument("--limit", type=int, default=25, help="max repos to output (default 25)")
    ap.add_argument("--json", action="store_true",
                    help="emit {hackathon, project, repo, winner} JSON records (feeds a batch driver)")
    args = ap.parse_args()

    with httpx.Client(follow_redirects=True) as c:
        slugs = ([args.hackathon] if args.hackathon
                 else hackathon_slugs(c, args.search, args.hackathons, args.completed))
        if not slugs:
            sys.exit("no hackathons matched")
        sys.stderr.write(f"hackathons ({len(slugs)}): {', '.join(slugs)}\n")
        records, seen = [], set()
        for slug in slugs:
            if len(records) >= args.limit:
                break
            projects = project_urls(c, slug, args.pages)
            sys.stderr.write(f"  {slug}: {len(projects)} projects\n")
            for project_url, winner in projects:
                if len(records) >= args.limit:
                    break
                repo = repo_for(c, project_url)
                if repo and repo not in seen:
                    seen.add(repo)
                    records.append({"hackathon": slug, "project": project_url, "repo": repo,
                                    "winner": winner})   # best-effort: True=badge found; False=none seen
                    if not args.json:
                        print(repo, flush=True)
                time.sleep(0.2)
        if args.json:
            print(json.dumps(records, indent=2))
        sys.stderr.write(f"\n{len(records)} repos.\n")


if __name__ == "__main__":
    main()

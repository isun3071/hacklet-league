"""Deployers: get a submission to a reachable HTTP base URL, then tear it down.

The pipeline depends only on this interface, so the same fuzzing logic runs against a local
subprocess (dev/CI) or a sandboxed container (production). This is the ONLY stack-specific
seam in the runner.
"""
from __future__ import annotations

import abc
import os
import socket
import subprocess
import sys
import time

import httpx


class DeployHandle:
    def __init__(self, base_url: str):
        self.base_url = base_url


class Deployer(abc.ABC):
    @abc.abstractmethod
    def deploy(self) -> DeployHandle:
        """Bring the app up and return a handle once it answers HTTP (the health gate)."""

    @abc.abstractmethod
    def teardown(self) -> None:
        ...


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class SubprocessDeployer(Deployer):
    """Dev/CI deployer for TRUSTED reference apps only. Launches the app as a local subprocess
    on an injected $PORT and waits for the health gate.

    NEVER use this for untrusted submissions — a bare subprocess has no isolation. Production
    uses DockerDeployer, which runs untrusted code in the sandbox (no egress, quotas, ephemeral).
    """

    def __init__(self, app_script: str, health_timeout: float = 30.0):
        self.app_script = app_script
        self.health_timeout = health_timeout
        self.proc: subprocess.Popen | None = None

    def deploy(self) -> DeployHandle:
        port = _free_port()
        env = {**os.environ, "PORT": str(port)}
        self.proc = subprocess.Popen(
            [sys.executable, self.app_script],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + self.health_timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("reference app exited during startup")
            try:
                r = httpx.get(base + "/", timeout=1.0)
                if r.status_code < 500:
                    return DeployHandle(base)
            except httpx.HTTPError:
                pass
            time.sleep(0.15)
        raise TimeoutError("health gate failed: app did not respond in time (this would be a DNF)")

    def teardown(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class DockerDeployer(Deployer):
    """Production deployer (runner host). Builds the submission's Dockerfile and runs it in the
    sandbox: unprivileged, no network egress, fixed CPU/RAM/PID/disk quotas, wall-clock bound,
    injecting $PORT (+ optional $DATABASE_URL sidecar). Stubbed here; wired where Docker exists.
    """

    def __init__(self, artifact_dir: str):
        self.artifact_dir = artifact_dir

    def deploy(self) -> DeployHandle:
        raise NotImplementedError(
            "DockerDeployer runs on the runner host (Docker required); see FUZZ_RUNNER_SPEC"
        )

    def teardown(self) -> None:
        pass

"""Probe published orchestrator versions (GitHub Releases) for upgrade checks.

Local/offline-first: never fails hard. Opt out with ``ORCHESTRATOR_NO_REMOTE_VERSION=1``.

Env:
  ORCHESTRATOR_GITHUB_REPO   default ``ndestates/orchestrator-memory`` (public product).
                             Maintainers may override to the private factory.
  ORCHESTRATOR_GITHUB_API    default ``https://api.github.com``
  GITHUB_TOKEN / GH_TOKEN    optional for private repos
  ORCHESTRATOR_NO_REMOTE_VERSION  set to 1/true/yes to skip network
  ORCHESTRATOR_REMOTE_VERSION_TIMEOUT  seconds (default 3)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

# Public product face. Private factory is ndestates/orchestrator (override via env).
DEFAULT_GITHUB_REPO = "ndestates/orchestrator-memory"


@dataclass(frozen=True)
class RemoteVersion:
    version: str
    source: str
    tag: str | None = None


def remote_version_suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_NO_REMOTE_VERSION", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _timeout() -> float:
    raw = (os.environ.get("ORCHESTRATOR_REMOTE_VERSION_TIMEOUT") or "3").strip()
    try:
        return max(0.5, min(30.0, float(raw)))
    except ValueError:
        return 3.0


def _repo() -> str:
    return (os.environ.get("ORCHESTRATOR_GITHUB_REPO") or DEFAULT_GITHUB_REPO).strip()


def release_wheel_url(version: str, repo: str | None = None) -> str:
    """GitHub Release wheel URL for an exact product version (must match npm)."""
    ver = (version or "").strip().lstrip("v")
    target = (repo or _repo()).strip() or DEFAULT_GITHUB_REPO
    return (
        f"https://github.com/{target}/releases/download/v{ver}/"
        f"orchestrator-{ver}-py3-none-any.whl"
    )


def _api_base() -> str:
    return (os.environ.get("ORCHESTRATOR_GITHUB_API") or "https://api.github.com").rstrip("/")


def _token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "ORCHESTRATOR_GITHUB_TOKEN"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    return None


def fetch_latest_release_version() -> RemoteVersion | None:
    """Return latest non-draft GitHub release version, or None on any failure."""
    if remote_version_suppressed():
        return None
    url = f"{_api_base()}/repos/{_repo()}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "orchestrator-cli-remote-version",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name") or data.get("name")
    if not tag or not isinstance(tag, str):
        return None
    ver = tag.strip().lstrip("v")
    if not ver:
        return None
    return RemoteVersion(version=ver, source=f"github:{_repo()}/releases/latest", tag=tag.strip())


def best_available(local: str | None, remote: RemoteVersion | None) -> tuple[str | None, str]:
    """Pick the newer of local template version and remote release.

    Returns (version, source_label).
    """
    from .version import is_newer  # local import avoids cycles at module load

    if local and remote:
        if is_newer(remote.version, local):
            return remote.version, remote.source
        return local.lstrip("v"), "local_template"
    if remote:
        return remote.version, remote.source
    if local:
        return local.lstrip("v"), "local_template"
    return None, "none"


__all__ = [
    "DEFAULT_GITHUB_REPO",
    "RemoteVersion",
    "best_available",
    "fetch_latest_release_version",
    "release_wheel_url",
    "remote_version_suppressed",
]

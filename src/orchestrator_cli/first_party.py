"""First-party org detection for license bypass (Phase 3.5).

Network-free: reads ``git remote get-url origin`` on the target project and
matches the host/org segment against ``ORCHESTRATOR_FIRST_PARTY_ORGS`` (comma-
separated, default ``ndestates``).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _parse_org(remote_url: str) -> str | None:
    url = remote_url.strip()
    if url.startswith("git@"):
        # git@github.com:org/repo.git
        m = re.match(r"git@[^:]+:(?P<org>[^/]+)/", url)
        return m.group("org") if m else None
    if "://" not in url:
        url = f"https://{url}"
    parsed = urlparse(url)
    path = (parsed.path or "").strip("/")
    if not path:
        return None
    return path.split("/")[0]


def first_party_orgs() -> set[str]:
    raw = os.environ.get("ORCHESTRATOR_FIRST_PARTY_ORGS", "ndestates")
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def git_remote_origin(project_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    url = (proc.stdout or "").strip()
    return url or None


def is_first_party(project_root: Path) -> bool:
    """Return True when the project's origin remote matches the allowlist."""
    remote = git_remote_origin(project_root.resolve())
    if not remote:
        return False
    org = _parse_org(remote)
    if not org:
        return False
    return org.lower() in first_party_orgs()
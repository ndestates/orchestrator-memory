"""Read/write the per-target `.orchestrator-version` lock.

Records which orchestrator release a project is installed from, so `status`
(and daily-standup/health) can detect when a newer release exists.
"""

from __future__ import annotations

import json
from pathlib import Path

LOCK_NAME = ".orchestrator-version"


def lock_path(target: Path) -> Path:
    return target / LOCK_NAME


def read_lock(target: Path) -> dict | None:
    p = lock_path(target)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_lock(
    target: Path,
    *,
    version: str,
    release_tag: str | None,
    profile: str | None,
    cli_version: str,
    installed_at: str,
) -> Path:
    # Always store normalized versions (no leading v) so app/host/template compare cleanly.
    ver = (version or "").strip().lstrip("v")
    cli_ver = (cli_version or "").strip().lstrip("v")
    tag = (release_tag or "").strip()
    if not tag:
        tag = f"v{ver}"
    elif not tag.startswith("v"):
        tag = f"v{tag.lstrip('v')}"
    data = {
        "version": ver,
        "release_tag": tag,
        "profile": profile,
        "cli_version": cli_ver,
        "installed_at": installed_at,
        "ssot": "VERSION",
    }
    p = lock_path(target)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p

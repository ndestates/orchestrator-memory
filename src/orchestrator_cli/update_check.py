"""Detect missing install or available template upgrades and announce them.

Used by:
- CLI auto-check on most commands (cwd)
- ``orchestrator check`` / ``orchestrator status``
- session-start (``scripts/session-orchestrator-check.py``)

Opt out: set ``ORCHESTRATOR_NO_UPDATE_CHECK=1``.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TextIO

from .lock import read_lock
from .remote_version import best_available, fetch_latest_release_version
from .template_root import template_root
from .version import is_newer, is_template_source_tree, normalize_version, template_version


class UpdateKind(str, Enum):
    UP_TO_DATE = "up_to_date"
    UPGRADE_AVAILABLE = "upgrade_available"
    NOT_INSTALLED = "not_installed"
    TEMPLATE_SOURCE = "template_source"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class UpdateNotice:
    kind: UpdateKind
    target: Path
    installed: str | None
    available: str
    message: str
    """One-line human message (empty when quiet/skipped)."""

    action: str | None = None
    """Suggested command, if any."""

    available_source: str = "local_template"
    """Where *available* came from (local_template, github:…, env, …)."""

    preview_action: str | None = None
    """Dry-run / if-available preview command."""

    apply_action: str | None = None
    """Apply command (requires --yes with --if-available)."""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "target": str(self.target),
            "installed": self.installed,
            "available": self.available,
            "available_source": self.available_source,
            "message": self.message,
            "action": self.action,
            "preview_action": self.preview_action,
            "apply_action": self.apply_action,
            "update_available": self.kind == UpdateKind.UPGRADE_AVAILABLE,
            "not_installed": self.kind == UpdateKind.NOT_INSTALLED,
        }


def resolve_available_version() -> tuple[str, str]:
    """Local template version vs GitHub latest — return (version, source)."""
    try:
        local = template_version().lstrip("v")
    except Exception:
        local = None
    remote = fetch_latest_release_version()
    ver, source = best_available(local, remote)
    if not ver:
        return "0.0.0", "none"
    return ver, source


def updates_suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_NO_UPDATE_CHECK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def looks_like_project(target: Path) -> bool:
    """Heuristic: this tree is (or should be) an orchestrator consumer app."""
    t = target.resolve()
    if is_template_source_tree(t):
        return False
    if (t / ".orchestrator-version").is_file():
        return True
    if (t / ".grok").is_dir():
        return True
    if (t / "chains" / "registry.yaml").is_file() or (t / "CHAIN.md").is_file():
        return True
    if (t / ".claude" / "commands").is_dir() and (t / ".git").exists():
        return True
    return False


def evaluate(target: Path | None = None) -> UpdateNotice:
    """Evaluate install/upgrade state for *target* (default: cwd)."""
    target = (target or Path.cwd()).resolve()
    available, avail_source = resolve_available_version()

    # Template monorepo: never offer app init (works even when CLI is bundled
    # and template_root() points at site-packages).
    if is_template_source_tree(target):
        return UpdateNotice(
            kind=UpdateKind.TEMPLATE_SOURCE,
            target=target,
            installed=None,
            available=available,
            message="",
            action=None,
            available_source=avail_source,
        )

    try:
        if target == template_root().resolve():
            return UpdateNotice(
                kind=UpdateKind.TEMPLATE_SOURCE,
                target=target,
                installed=None,
                available=available,
                message="",
                action=None,
                available_source=avail_source,
            )
    except Exception:
        pass

    lock = read_lock(target)
    installed = (
        normalize_version(str(lock["version"])) if lock and lock.get("version") else None
    )

    if installed is None:
        if not looks_like_project(target):
            return UpdateNotice(
                kind=UpdateKind.SKIPPED,
                target=target,
                installed=None,
                available=available,
                message="",
                action=None,
                available_source=avail_source,
            )
        action = f"orchestrator init {target} --no-pr"
        return UpdateNotice(
            kind=UpdateKind.NOT_INSTALLED,
            target=target,
            installed=None,
            available=available,
            message=(
                f"orchestrator: not installed in {target} "
                f"(template {available} available via {avail_source}) — "
                f"run `orchestrator init . --no-pr`"
            ),
            action=action,
            available_source=avail_source,
            apply_action=action,
        )

    if is_newer(available, installed):
        preview = f"orchestrator upgrade {target} --if-available --no-pr"
        apply = f"orchestrator upgrade {target} --if-available --yes --no-pr"
        # Prefer host CLI if-available path; classic upgrade still valid when CLI is current
        action = apply
        return UpdateNotice(
            kind=UpdateKind.UPGRADE_AVAILABLE,
            target=target,
            installed=installed,
            available=available,
            message=(
                f"orchestrator: upgrade available — installed {installed}, "
                f"template {available} ({avail_source}) — "
                f"preview: `{preview}` · apply: `{apply}`"
            ),
            action=action,
            available_source=avail_source,
            preview_action=preview,
            apply_action=apply,
        )

    return UpdateNotice(
        kind=UpdateKind.UP_TO_DATE,
        target=target,
        installed=installed,
        available=available,
        message=(
            f"orchestrator: {installed} installed "
            f"(available {available} via {avail_source}) ✓ up to date"
        ),
        action=None,
        available_source=avail_source,
    )


def announce(
    target: Path | None = None,
    *,
    stream: TextIO | None = None,
    quiet_if_current: bool = True,
    force: bool = False,
) -> UpdateNotice:
    """Print a user-facing notice when install/upgrade action is needed.

    By default silent when up-to-date or skipped (unless *force*).
    """
    notice = evaluate(target)
    if updates_suppressed() and not force:
        return notice

    out = stream if stream is not None else sys.stderr
    if notice.kind in (UpdateKind.UPGRADE_AVAILABLE, UpdateKind.NOT_INSTALLED):
        print(notice.message, file=out)
        if notice.preview_action:
            print(f"  → preview: {notice.preview_action}", file=out)
        if notice.apply_action:
            print(f"  → apply:   {notice.apply_action}", file=out)
        elif notice.action:
            print(f"  → {notice.action}", file=out)
    elif force and notice.message:
        print(notice.message, file=out)
    elif not quiet_if_current and notice.message:
        print(notice.message, file=out)
    return notice


def should_auto_announce(command: str | None) -> bool:
    """Whether CLI *command* should trigger an automatic cwd check."""
    if updates_suppressed():
        return False
    # Avoid noise / recursion on pure status json, long servers, or the check itself
    skip = {
        None,
        "check",  # check always announces explicitly
        "status",  # status already prints full detail
        "license-server",
        "wave",
        "self-upgrade",  # host package path; avoid noise/recursion
        "ensure",  # host preflight; keep output clean
        "install-persist",  # project-global repair; keep output clean
        "memory",  # always-on memory; keep JSON/CLI clean
    }
    return command not in skip

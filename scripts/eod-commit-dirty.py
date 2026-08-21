#!/usr/bin/env python3
"""Preserve dirty WIP across eod-shutdown. Operator never stashes.

Some dirty files are tomorrow's work. EOD must not drop them or punt
``git stash`` to the human.

Policy:
  - On ``feature/*``: **commit** remaining dirty so the next session has it on HEAD.
  - When EOD must leave ``master``/``develop`` (or ``--switch-to``): **stash -u,
    switch, stash pop**, then commit on the destination. Stash is internal and
    always restored before this process exits.
  - Secret basenames (``.env`` etc.) still block. Never discard.

Usage:
  python3 scripts/eod-commit-dirty.py
  python3 scripts/eod-commit-dirty.py --switch-to feature/work-2026-08-22
  python3 scripts/eod-commit-dirty.py --dry-run --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

PROTECTED_BRANCHES = frozenset(
    {"master", "develop", "main", "staging", "production"}
)
BLOCKED_BASENAMES = frozenset(
    {
        ".env",
        ".env.backup",
        ".env.production",
        ".env.testing",
        ".env.dusk",
        ".env.local",
    }
)
DEFAULT_MESSAGE = "chore(eod): remaining session work and artifacts"
STASH_MESSAGE = "eod-preserve-wip"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def _porcelain_path(line: str) -> str:
    raw = (line or "").rstrip("\n")
    if len(raw) < 2:
        return ""
    path = raw[2:].lstrip()
    if path.startswith('"') and path.endswith('"') and len(path) >= 2:
        path = path[1:-1]
    if " -> " in path:
        path = path.split(" -> ", 1)[-1].strip().strip('"')
    return path.strip()


def porcelain_lines(root: Path) -> list[str]:
    code, out, _ = _run(["git", "status", "--porcelain"], root)
    if code != 0:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def current_branch(root: Path) -> str:
    code, out, _ = _run(["git", "branch", "--show-current"], root)
    return out if code == 0 else ""


def _stash_list(root: Path) -> str:
    _, out, _ = _run(["git", "stash", "list"], root)
    return out


def _blocked_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if Path(p).name in BLOCKED_BASENAMES]


def commit_dirty(
    root: Path,
    *,
    message: str = DEFAULT_MESSAGE,
    dry_run: bool = False,
) -> dict:
    """Commit remaining porcelain on a feature branch. Does not stash."""
    lines = porcelain_lines(root)
    paths = [p for p in (_porcelain_path(ln) for ln in lines) if p]
    result: dict = {
        "status": "clean",
        "committed": False,
        "stash": False,
        "stash_restored": False,
        "paths": paths,
        "branch": current_branch(root),
        "message": message,
        "mode": "commit",
    }
    if not paths:
        return result

    branch = result["branch"]
    if branch in PROTECTED_BRANCHES:
        result["status"] = "blocked_branch"
        result["error"] = (
            f"Will not commit on `{branch}` — use --switch-to feature/* "
            "(stash→switch→restore) so WIP follows"
        )
        return result

    blocked = _blocked_paths(paths)
    if blocked:
        result["status"] = "blocked_secrets"
        result["blocked"] = blocked
        result["error"] = "EOD will not commit secret paths: " + ", ".join(blocked)
        return result

    if dry_run:
        result["status"] = "would_commit"
        return result

    code, _, err = _run(["git", "add", "-A"], root)
    if code != 0:
        result["status"] = "add_failed"
        result["error"] = err or "git add -A failed"
        return result

    code, out, err = _run(["git", "commit", "-m", message], root)
    if code != 0:
        result["status"] = "commit_failed"
        result["error"] = (err or out or "git commit failed")[:400]
        return result

    leftover = porcelain_lines(root)
    result["committed"] = True
    result["commit"] = out.splitlines()[0] if out else "ok"
    if leftover:
        result["status"] = "still_dirty"
        result["paths"] = [p for p in (_porcelain_path(ln) for ln in leftover) if p]
        result["error"] = "porcelain still non-empty after EOD commit"
        return result
    result["status"] = "committed"
    result["paths"] = paths
    return result


def stash_switch_restore(
    root: Path,
    dest: str,
    *,
    dry_run: bool = False,
) -> dict:
    """Internal stash → checkout dest → stash pop. Always restore if we stashed."""
    dest = (dest or "").strip()
    result: dict = {
        "status": "clean",
        "committed": False,
        "stash": False,
        "stash_restored": False,
        "paths": [p for p in (_porcelain_path(ln) for ln in porcelain_lines(root)) if p],
        "branch": current_branch(root),
        "dest": dest,
        "mode": "stash_restore",
    }
    if not dest:
        result["status"] = "no_dest"
        result["error"] = "--switch-to is required for stash-restore"
        return result
    if dest in PROTECTED_BRANCHES:
        result["status"] = "blocked_branch"
        result["error"] = f"Refusing to switch onto protected `{dest}`"
        return result

    blocked = _blocked_paths(result["paths"])
    if blocked:
        result["status"] = "blocked_secrets"
        result["blocked"] = blocked
        result["error"] = "EOD will not stash secret paths: " + ", ".join(blocked)
        return result

    if dry_run:
        result["status"] = "would_stash_restore"
        return result

    before_stash = _stash_list(root)
    if result["paths"]:
        code, out, err = _run(
            ["git", "stash", "push", "-u", "-m", STASH_MESSAGE],
            root,
        )
        if code != 0:
            result["status"] = "stash_failed"
            result["error"] = (err or out or "git stash push failed")[:400]
            return result
        result["stash"] = _stash_list(root) != before_stash

    branch_now = current_branch(root)
    if branch_now != dest:
        code, _, err = _run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{dest}"], root)
        if code == 0:
            c2, _, e2 = _run(["git", "checkout", dest], root)
        else:
            c2, _, e2 = _run(["git", "checkout", "-b", dest], root)
        if c2 != 0:
            if result["stash"]:
                _run(["git", "stash", "pop"], root)
                result["stash_restored"] = True
            result["status"] = "checkout_failed"
            result["error"] = (e2 or f"could not checkout {dest}")[:400]
            result["branch"] = current_branch(root)
            return result

    if result["stash"]:
        code, out, err = _run(["git", "stash", "pop"], root)
        if code != 0:
            result["status"] = "restore_failed"
            result["error"] = (err or out or "git stash pop failed")[:400]
            result["branch"] = current_branch(root)
            return result
        result["stash_restored"] = True
        result["stash"] = False  # no leftover stash

    result["branch"] = current_branch(root)
    result["paths"] = [p for p in (_porcelain_path(ln) for ln in porcelain_lines(root)) if p]
    result["status"] = "restored"
    return result


def preserve_wip(
    root: Path,
    *,
    switch_to: str | None = None,
    message: str = DEFAULT_MESSAGE,
    dry_run: bool = False,
) -> dict:
    """Commit on feature/*, or stash-switch-restore then commit when moving."""
    dest = (switch_to or "").strip() or None
    branch = current_branch(root)
    must_move = bool(dest and dest != branch) or (
        branch in PROTECTED_BRANCHES and porcelain_lines(root)
    )
    if must_move:
        if dest is None:
            dest = f"feature/work-{date.today().isoformat()}"
        moved = stash_switch_restore(root, dest, dry_run=dry_run)
        if dry_run:
            return moved
        if moved["status"] not in ("restored", "clean"):
            return moved
        # Durable on the destination so next session does not depend on a leftover stash
        committed = commit_dirty(root, message=message, dry_run=dry_run)
        committed["mode"] = "stash_restore_then_commit"
        committed["stash_restored"] = True
        committed["dest"] = dest
        return committed
    return commit_dirty(root, message=message, dry_run=dry_run)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--message", default=DEFAULT_MESSAGE)
    ap.add_argument(
        "--switch-to",
        default="",
        help="If set (or current is master/develop), stash→checkout→restore then commit",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", type=Path, default=None)
    args = ap.parse_args(argv)
    root = (args.root or Path.cwd()).resolve()
    data = preserve_wip(
        root,
        switch_to=args.switch_to or None,
        message=args.message,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(
            f"eod-preserve-wip status={data['status']} "
            f"mode={data.get('mode')} committed={data.get('committed')} "
            f"stash_restored={data.get('stash_restored')} "
            f"branch={data.get('branch')} "
            f"paths={len(data.get('paths') or [])}"
        )
        if data.get("error"):
            print(data["error"], file=sys.stderr)
    ok = {
        "clean",
        "committed",
        "would_commit",
        "would_stash_restore",
        "restored",
    }
    return 0 if data["status"] in ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

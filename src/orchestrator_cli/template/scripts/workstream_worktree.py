#!/usr/bin/env python3
"""Git worktree helpers for multi-workstream isolation.

Safeguards:
  - Never create worktrees for held/held_ready/parked unless --force
  - Never touch protected branches (master, main, develop, staging, release/*)
  - Never merge/push/force-push
  - Worktree path must stay under repo parent (no arbitrary paths)
  - Remove only worktrees registered for a workstream

Used by: python3 scripts/workstream.py worktree …
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = frozenset({"master", "main", "develop", "staging", "production", "prod"})
PROTECTED_PREFIXES = ("release/", "hotfix/")


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    # Resolve ROOT at call time so tests (and any future rebinding) see the current root.
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, check=False)


def _git_worktrees() -> list[dict[str, str]]:
    r = _run(["git", "worktree", "list", "--porcelain"])
    if r.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in (r.stdout or "").splitlines():
        if not line.strip():
            if cur:
                entries.append(cur)
                cur = {}
            continue
        if line.startswith("worktree "):
            cur["path"] = line[len("worktree ") :].strip()
        elif line.startswith("HEAD "):
            cur["head"] = line[len("HEAD ") :].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch ") :].replace("refs/heads/", "").strip()
        elif line == "bare":
            cur["bare"] = "1"
        elif line == "detached":
            cur["detached"] = "1"
    if cur:
        entries.append(cur)
    return entries


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s).strip("-").lower()
    return s[:48] or "ws"


def _default_worktree_path(wid: str) -> Path:
    parent = ROOT.parent
    return parent / f"{ROOT.name}-ws-{_slug(wid)}"


def _is_protected_branch(branch: str) -> bool:
    b = (branch or "").strip()
    if not b:
        return True
    if b in PROTECTED:
        return True
    return any(b.startswith(p) for p in PROTECTED_PREFIXES)


def _assert_safe_ws(ws: dict, *, force: bool) -> None:
    status = str(ws.get("status") or "")
    if status in {"held", "held_ready", "parked", "done"} and not force:
        raise SystemExit(
            f"refusing worktree for status={status} id={ws.get('id')} "
            "(activate first, or pass --force)"
        )
    branch = str(ws.get("branch") or "")
    if _is_protected_branch(branch):
        raise SystemExit(
            f"refusing worktree on protected/missing branch: {branch or '(empty)'} "
            f"(set a feature/* branch on the workstream)"
        )


def _path_allowed(path: Path) -> bool:
    try:
        path = path.resolve()
        parent = ROOT.parent.resolve()
        return path == ROOT.resolve() or parent in path.parents or path.parent == parent
    except Exception:
        return False


def cmd_list(data: dict) -> int:
    wts = {Path(e["path"]).resolve(): e for e in _git_worktrees() if e.get("path")}
    print(f"{'#':>3}  {'id':<22} {'branch':<40} worktree")
    print("-" * 100)
    for i, ws in enumerate(data.get("workstreams") or [], start=1):
        wid = str(ws.get("id") or "")
        branch = str(ws.get("branch") or "—")
        wtp = ws.get("worktree") or ""
        state = "—"
        if wtp:
            rp = Path(wtp).resolve() if Path(wtp).exists() else Path(wtp)
            if rp.resolve() in wts if rp.exists() else False:
                state = str(rp)
            elif Path(wtp).exists():
                state = f"{wtp} (not in git worktree list?)"
            else:
                state = f"{wtp} (missing)"
        print(f"{i:>3}  {wid:<22} {branch:<40} {state}")
    print("main:", ROOT)
    return 0


def _find(data: dict, wid: str) -> dict:
    for ws in data.get("workstreams") or []:
        if ws.get("id") == wid:
            return ws
    raise SystemExit(f"unknown workstream id: {wid}")


def _save(path: Path, data: dict) -> None:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML required") from exc
    data["updated"] = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def cmd_add(data: dict, path: Path, wid: str, *, force: bool) -> int:
    """Create git worktree for workstream branch; record path on registry entry."""
    ws = _find(data, wid)
    _assert_safe_ws(ws, force=force)
    branch = str(ws.get("branch") or "")
    dest = Path(ws["worktree"]) if ws.get("worktree") else _default_worktree_path(wid)
    dest = dest if dest.is_absolute() else (ROOT / dest)
    if not _path_allowed(dest):
        raise SystemExit(f"worktree path not allowed (must be under {ROOT.parent}): {dest}")
    if dest.resolve() == ROOT.resolve():
        raise SystemExit("refusing to use main repo path as worktree")

    if dest.exists():
        for e in _git_worktrees():
            if Path(e.get("path", "")).resolve() == dest.resolve():
                ws["worktree"] = str(dest.resolve())
                ws["updated"] = date.today().isoformat()
                _save(path, data)
                print(f"worktree exists: {dest}")
                print(f"branch={e.get('branch') or e.get('head')}")
                return 0
        raise SystemExit(f"path exists but is not a git worktree: {dest}")

    br = _run(["git", "rev-parse", "--verify", branch])
    if br.returncode != 0:
        r2 = _run(["git", "rev-parse", "--verify", f"origin/{branch}"])
        if r2.returncode != 0:
            raise SystemExit(
                f"branch not found locally or on origin: {branch} "
                "(create feature branch first)"
            )
        r = _run(
            ["git", "worktree", "add", "--track", "-b", branch, str(dest), f"origin/{branch}"]
        )
        if r.returncode != 0:
            r = _run(["git", "worktree", "add", str(dest), f"origin/{branch}"])
    else:
        r = _run(["git", "worktree", "add", str(dest), branch])

    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print(err, file=sys.stderr)
        if "already checked out" in err.lower() or "is already used by worktree" in err.lower():
            print(
                f"hint: branch `{branch}` is already checked out in another worktree "
                f"(often the main repo). Switch main off that branch, or use a "
                f"different feature branch for this workstream.",
                file=sys.stderr,
            )
        return r.returncode

    ws["worktree"] = str(dest.resolve())
    ws["updated"] = date.today().isoformat()
    _save(path, data)
    print(f"worktree added: {dest}")
    print(f"id={wid} branch={branch}")
    print("SAFEGUARD: no merge/push performed — work only inside this path")
    return 0


def cmd_remove(data: dict, path: Path, wid: str, *, force: bool) -> int:
    ws = _find(data, wid)
    wtp = ws.get("worktree")
    if not wtp:
        print(f"no worktree registered for {wid}")
        return 0
    dest = Path(wtp)
    if dest.resolve() == ROOT.resolve():
        raise SystemExit("refusing to remove main repo worktree")
    if not _path_allowed(dest):
        raise SystemExit(f"path not allowed: {dest}")
    args = ["git", "worktree", "remove", str(dest)]
    if force:
        args.append("--force")
    r = _run(args)
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return r.returncode
    ws.pop("worktree", None)
    ws["updated"] = date.today().isoformat()
    _save(path, data)
    print(f"worktree removed: {dest}")
    return 0


def cmd_status_json(data: dict) -> int:
    wts = _git_worktrees()
    payload = {
        "main": str(ROOT),
        "worktrees": wts,
        "registered": [
            {
                "id": ws.get("id"),
                "branch": ws.get("branch"),
                "status": ws.get("status"),
                "worktree": ws.get("worktree"),
            }
            for ws in data.get("workstreams") or []
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0

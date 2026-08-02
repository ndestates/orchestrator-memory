#!/usr/bin/env python3
"""Sync orchestrator surfaces onto the current branch from orchestrator/installed.

Used by .githooks/post-checkout so the **in-app** install feels project-global.
**Stdlib + git only** — must work inside app repos without ``pip install orchestrator``
and without a template ``src/`` tree (that was the 1.9.5 persistence bug).

Usage:
  python3 scripts/orchestrator-branch-sync.py
  python3 scripts/orchestrator-branch-sync.py --quiet
  python3 scripts/orchestrator-branch-sync.py --dry-run
  python3 scripts/orchestrator-branch-sync.py --establish-baseline
    # point orchestrator/installed at HEAD (current tree must already have install)

Opt out: ORCHESTRATOR_NO_BRANCH_SYNC=1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

INSTALLED_BRANCH = "orchestrator/installed"

# Keep in sync with orchestrator_cli.project_install (duplicated so apps need no package)
SYNC_EXACT = frozenset(
    {
        ".orchestrator-version",
        "CHAIN.md",
        "LOOP.md",
        "loop-budget.md",
        "CLAUDE.md",
        ".github/copilot-instructions.md",
        "docs/guides/prompt-injection-installed-apps.md",
        "docs/reference/session-context-token-budget.md",
        ".githooks/post-checkout",
    }
)
SYNC_PREFIXES = (
    ".grok/",
    ".claude/commands/",
    ".claude/agents/",
    ".github/skills/",
    ".github/agents/",
    ".github/prompts/",
    ".copilot/skills/",
    "chains/",
    "patterns/",
    "scripts/",
    ".githooks/",
)

BATCH = 80


def _suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_NO_BRANCH_SYNC", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "off",
    )


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_root(start: Path | None = None) -> Path | None:
    r = _git(start or Path.cwd(), "rev-parse", "--show-toplevel")
    if r.returncode != 0 or not (r.stdout or "").strip():
        return None
    return Path(r.stdout.strip())


def _customized_paths(target: Path) -> set[str]:
    out: set[str] = set()
    state = target / ".grok" / "deploy-state.json"
    if not state.is_file():
        return out
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return out
    files = data.get("files")
    if isinstance(files, dict):
        # deploy-state variants: {path: {customized: true}}
        for path, meta in files.items():
            if isinstance(meta, dict) and meta.get("customized"):
                out.add(str(path).lstrip("./"))
        return out
    if isinstance(files, list):
        for f in files:
            if isinstance(f, dict) and f.get("customized") and f.get("path"):
                out.add(str(f["path"]).lstrip("./"))
    return out


def _want_path(p: str, customized: set[str]) -> bool:
    if not p or p in customized:
        return False
    if any(p == c or p.startswith(c.rstrip("/") + "/") for c in customized):
        return False
    if p in SYNC_EXACT:
        return True
    return any(p.startswith(pref) for pref in SYNC_PREFIXES)


def _list_paths_on_ref(target: Path, ref: str) -> list[str]:
    r = _git(target, "ls-tree", "-r", "--name-only", ref)
    if r.returncode != 0:
        return []
    customized = _customized_paths(target)
    return [
        line.strip()
        for line in (r.stdout or "").splitlines()
        if _want_path(line.strip(), customized)
    ]


def _lock_version(target: Path, ref: str | None = None) -> str | None:
    try:
        if ref is None:
            p = target / ".orchestrator-version"
            if not p.is_file():
                return None
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            r = _git(target, "show", f"{ref}:.orchestrator-version")
            if r.returncode != 0:
                return None
            data = json.loads(r.stdout)
        v = data.get("version")
        return str(v).lstrip("v") if v else None
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def establish_baseline(target: Path) -> dict:
    """Point orchestrator/installed at HEAD (current commit must hold the install)."""
    r = _git(target, "rev-parse", "HEAD")
    if r.returncode != 0:
        return {"ok": False, "message": "cannot resolve HEAD"}
    head = r.stdout.strip()
    if not (target / ".orchestrator-version").is_file():
        return {
            "ok": False,
            "message": "no .orchestrator-version on HEAD — run orchestrator init/upgrade first",
        }
    br = _git(target, "branch", "-f", INSTALLED_BRANCH, head)
    if br.returncode != 0:
        return {
            "ok": False,
            "message": (br.stderr or br.stdout or "branch -f failed").strip()[:200],
        }
    return {
        "ok": True,
        "message": f"baseline {INSTALLED_BRANCH} → {head[:12]}",
        "sha": head[:12],
    }


def sync_from_baseline(
    target: Path, *, commit: bool = True, dry_run: bool = False
) -> dict:
    """Restore orchestrator paths from baseline onto the current branch."""
    out: dict = {
        "ok": False,
        "paths": 0,
        "committed": False,
        "message": "",
        "dry_run": dry_run,
    }
    if _suppressed():
        out["ok"] = True
        out["message"] = "skipped (ORCHESTRATOR_NO_BRANCH_SYNC)"
        return out

    has = _git(target, "rev-parse", "--verify", INSTALLED_BRANCH)
    if has.returncode != 0:
        out["message"] = (
            f"no {INSTALLED_BRANCH} baseline — run: "
            f"python3 scripts/orchestrator-branch-sync.py --establish-baseline "
            f"(on a branch that already has the install), or: "
            f"orchestrator install-persist ."
        )
        return out

    base_v = _lock_version(target, INSTALLED_BRANCH)
    cur_v = _lock_version(target, None)
    has_surfaces = (target / "chains" / "registry.yaml").is_file() and (
        target / ".grok" / "skills"
    ).is_dir()
    if base_v and cur_v and base_v == cur_v and has_surfaces:
        out["ok"] = True
        out["message"] = f"already at {cur_v}"
        return out

    paths = _list_paths_on_ref(target, INSTALLED_BRANCH)
    if not paths:
        out["message"] = f"no orchestrator paths on {INSTALLED_BRANCH}"
        return out

    out["paths"] = len(paths)
    if dry_run:
        out["ok"] = True
        out["message"] = f"dry-run: would restore {len(paths)} path(s) from {INSTALLED_BRANCH}"
        return out

    # Batch to avoid ARG_MAX
    for i in range(0, len(paths), BATCH):
        chunk = paths[i : i + BATCH]
        r = _git(target, "checkout", INSTALLED_BRANCH, "--", *chunk)
        if r.returncode != 0:
            out["message"] = (r.stderr or r.stdout or "checkout failed")[:240]
            return out

    if commit:
        _git(target, "add", "-A", "--", *paths[:BATCH] if len(paths) <= BATCH else [])
        # add all orchestrator paths via pathspecs
        for i in range(0, len(paths), BATCH):
            _git(target, "add", "-A", "--", *paths[i : i + BATCH])
        branch = _git(target, "branch", "--show-current").stdout.strip() or "HEAD"
        msg = f"chore(orchestrator): sync project install onto {branch}"
        cr = _git(target, "commit", "-m", msg)
        if cr.returncode == 0:
            out["committed"] = True
        elif "nothing to commit" not in ((cr.stdout or "") + (cr.stderr or "")).lower():
            # still ok if clean after checkout
            if _git(target, "diff", "--quiet").returncode == 0 and _git(
                target, "diff", "--cached", "--quiet"
            ).returncode == 0:
                out["committed"] = False
            else:
                out["message"] = (cr.stderr or cr.stdout or "commit failed")[:240]
                return out

    out["ok"] = True
    out["message"] = (
        f"synced {len(paths)} path(s) from {INSTALLED_BRANCH}"
        + (" (committed)" if out["committed"] else " (tree clean)")
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", "-q", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--establish-baseline",
        action="store_true",
        help="set orchestrator/installed = HEAD (current tree must have install)",
    )
    ap.add_argument(
        "--no-commit",
        action="store_true",
        help="restore paths but do not commit",
    )
    args = ap.parse_args()

    if _suppressed():
        if not args.quiet:
            print("orchestrator-branch-sync: suppressed", file=sys.stderr)
        return 0

    root = _git_root()
    if root is None:
        if not args.quiet:
            print("orchestrator-branch-sync: not a git repo", file=sys.stderr)
        return 0

    if args.establish_baseline:
        res = establish_baseline(root)
    else:
        res = sync_from_baseline(
            root, commit=not args.no_commit, dry_run=args.dry_run
        )

    if not args.quiet and res.get("message"):
        print(f"orchestrator-branch-sync: {res['message']}")
    # Never block checkout / CI
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

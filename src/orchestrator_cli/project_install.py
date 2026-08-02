"""Optional project-global orchestrator install helpers.

**Default after init/upgrade (safe):** only the **current branch** is modified.
No multi-branch commits. No post-checkout thrash.

**Opt-in only** (dangerous on large repos — can rewrite every local branch):

1. Point branch ``orchestrator/installed`` at the install commit (baseline).
2. Broadcast orchestrator paths onto **all local branches** —
   requires ``ORCHESTRATOR_BRANCH_BROADCAST=1``.
3. Install a ``post-checkout`` hook that may auto-commit on switch —
   requires ``ORCHESTRATOR_INSTALL_BRANCH_HOOK=1``.

Always off: ``ORCHESTRATOR_NO_BRANCH_SYNC=1`` (legacy full suppress).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

INSTALLED_BRANCH = "orchestrator/installed"

# Paths/prefixes restored from the baseline (never full app source)
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


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def branch_sync_suppressed() -> bool:
    """Full kill-switch for any branch sync behaviour."""
    return os.environ.get("ORCHESTRATOR_NO_BRANCH_SYNC", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "off",
    )


def branch_broadcast_enabled() -> bool:
    """Multi-branch commit blast — OFF unless explicitly enabled."""
    if branch_sync_suppressed():
        return False
    return _env_truthy("ORCHESTRATOR_BRANCH_BROADCAST")


def branch_hook_enabled() -> bool:
    """Install post-checkout auto-sync hook — OFF unless explicitly enabled."""
    if branch_sync_suppressed():
        return False
    return _env_truthy("ORCHESTRATOR_INSTALL_BRANCH_HOOK")


def _run_git(cwd: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _customized_paths(target: Path) -> set[str]:
    """Paths marked customized in deploy-state — never overwrite from baseline."""
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
        for path, meta in files.items():
            if isinstance(meta, dict) and meta.get("customized"):
                out.add(str(path).lstrip("./"))
        return out
    for f in files or []:
        if not isinstance(f, dict):
            continue
        if f.get("customized") and f.get("path"):
            out.add(str(f["path"]).lstrip("./"))
    return out


def _list_paths_on_ref(target: Path, ref: str) -> list[str]:
    r = _run_git(target, "ls-tree", "-r", "--name-only", ref)
    if r.returncode != 0:
        return []
    paths: list[str] = []
    customized = _customized_paths(target)
    for line in (r.stdout or "").splitlines():
        p = line.strip()
        if not p or p in customized:
            continue
        if p in SYNC_EXACT or any(p.startswith(pref) for pref in SYNC_PREFIXES):
            # Also skip customized prefixes
            if any(p == c or p.startswith(c.rstrip("/") + "/") for c in customized):
                continue
            paths.append(p)
    return paths


def update_installed_baseline(target: Path) -> dict[str, Any]:
    """Force branch orchestrator/installed → current HEAD (install commit)."""
    result: dict[str, Any] = {"ok": False, "branch": INSTALLED_BRANCH, "message": ""}
    if branch_sync_suppressed():
        result["message"] = "branch sync suppressed (ORCHESTRATOR_NO_BRANCH_SYNC=1)"
        result["ok"] = True
        result["skipped"] = True
        return result
    r = _run_git(target, "rev-parse", "HEAD")
    if r.returncode != 0:
        result["message"] = "cannot resolve HEAD for installed baseline"
        return result
    head = r.stdout.strip()
    r = _run_git(target, "branch", "-f", INSTALLED_BRANCH, head)
    if r.returncode != 0:
        result["message"] = (r.stderr or r.stdout or "branch -f failed").strip()
        return result
    result["ok"] = True
    result["sha"] = head[:12]
    result["message"] = f"baseline {INSTALLED_BRANCH} → {head[:12]}"
    return result


def sync_branch_from_baseline(
    target: Path,
    *,
    branch: str | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    """Checkout orchestrator paths from orchestrator/installed onto *branch*."""
    out: dict[str, Any] = {
        "ok": False,
        "branch": branch,
        "paths": 0,
        "committed": False,
        "message": "",
    }
    if branch_sync_suppressed():
        out["ok"] = True
        out["message"] = "skipped"
        return out

    # Ensure baseline exists
    has = _run_git(target, "rev-parse", "--verify", INSTALLED_BRANCH)
    if has.returncode != 0:
        out["message"] = f"no {INSTALLED_BRANCH} baseline yet"
        return out

    current = _run_git(target, "branch", "--show-current").stdout.strip()
    if branch and branch != current:
        r = _run_git(target, "checkout", branch)
        if r.returncode != 0:
            out["message"] = f"cannot checkout {branch}: {(r.stderr or '')[:120]}"
            return out

    # Skip if already same or newer version as baseline
    base_lock = _run_git(
        target, "show", f"{INSTALLED_BRANCH}:.orchestrator-version"
    )
    cur_lock_path = target / ".orchestrator-version"
    if base_lock.returncode == 0 and cur_lock_path.is_file():
        try:
            base_v = json.loads(base_lock.stdout).get("version")
            cur_v = json.loads(cur_lock_path.read_text(encoding="utf-8")).get("version")
            if base_v and cur_v and str(base_v) == str(cur_v):
                # Still refresh paths if lock matches but files missing
                if (target / "chains" / "registry.yaml").is_file() and (
                    target / ".grok" / "skills"
                ).is_dir():
                    out["ok"] = True
                    out["message"] = f"already at {cur_v}"
                    if branch and branch != current:
                        _run_git(target, "checkout", current)
                    return out
        except (json.JSONDecodeError, OSError, TypeError):
            pass

    paths = _list_paths_on_ref(target, INSTALLED_BRANCH)
    if not paths:
        out["message"] = "no orchestrator paths on baseline"
        if branch and branch != current:
            _run_git(target, "checkout", current)
        return out

    # Restore paths from baseline (does not bring feature commits). Batch for ARG_MAX.
    batch = 80
    for i in range(0, len(paths), batch):
        chunk = paths[i : i + batch]
        r = _run_git(target, "checkout", INSTALLED_BRANCH, "--", *chunk)
        if r.returncode != 0:
            out["message"] = (r.stderr or r.stdout or "checkout paths failed")[:200]
            if branch and branch != current:
                _run_git(target, "checkout", current)
            return out

    out["paths"] = len(paths)
    if commit:
        for i in range(0, len(paths), batch):
            _run_git(target, "add", "-A", "--", *paths[i : i + batch])
        msg = "chore(orchestrator): sync project install from orchestrator/installed"
        cr = _run_git(target, "commit", "-m", msg)
        if cr.returncode == 0:
            out["committed"] = True
        elif "nothing to commit" not in ((cr.stdout or "") + (cr.stderr or "")):
            out["message"] = (cr.stderr or cr.stdout or "commit failed")[:200]
            if branch and branch != current:
                _run_git(target, "checkout", current)
            return out

    out["ok"] = True
    out["message"] = (
        f"synced {len(paths)} path(s) from {INSTALLED_BRANCH}"
        + (" (committed)" if out["committed"] else " (already clean)")
    )
    if branch and branch != current:
        _run_git(target, "checkout", current)
    return out


def broadcast_to_local_branches(target: Path) -> dict[str, Any]:
    """Apply baseline paths onto every local branch (user does not choose)."""
    summary: dict[str, Any] = {
        "ok": True,
        "branches": [],
        "errors": [],
        "message": "",
    }
    if branch_sync_suppressed():
        summary["message"] = "branch broadcast skipped (ORCHESTRATOR_NO_BRANCH_SYNC=1)"
        return summary

    start = _run_git(target, "branch", "--show-current").stdout.strip()
    r = _run_git(target, "for-each-ref", "--format=%(refname:short)", "refs/heads/")
    if r.returncode != 0:
        summary["ok"] = False
        summary["message"] = "cannot list local branches"
        return summary

    branches = [
        b.strip()
        for b in (r.stdout or "").splitlines()
        if b.strip() and b.strip() != INSTALLED_BRANCH
    ]
    for b in branches:
        # Skip detached
        res = sync_branch_from_baseline(target, branch=b, commit=True)
        summary["branches"].append({"branch": b, **res})
        if not res.get("ok"):
            summary["errors"].append(f"{b}: {res.get('message')}")

    if start:
        _run_git(target, "checkout", start)
    summary["ok"] = len(summary["errors"]) == 0
    summary["message"] = (
        f"broadcast to {len(branches)} branch(es); "
        f"{len(summary['errors'])} error(s)"
    )
    return summary


def install_post_checkout_hook(target: Path) -> dict[str, Any]:
    """Ensure .githooks/post-checkout syncs orchestrator on branch switch."""
    out: dict[str, Any] = {"ok": False, "message": ""}
    hooks = target / ".githooks"
    hooks.mkdir(parents=True, exist_ok=True)
    marker = "# orchestrator-install-sync"
    hook = hooks / "post-checkout"
    body = f"""#!/usr/bin/env bash
{marker}
# After branch checkout, restore orchestrator surfaces from orchestrator/installed.
# Stdlib script preferred (no pip package required). Bash fallback if script missing.
# Opt out: ORCHESTRATOR_NO_BRANCH_SYNC=1
set -euo pipefail
prev_head="${{1:-}}"
new_head="${{2:-}}"
branch_flag="${{3:-0}}"
# Only on branch switch (not file checkout)
[[ "${{branch_flag}}" == "1" ]] || exit 0
[[ -z "${{ORCHESTRATOR_NO_BRANCH_SYNC:-}}" ]] || exit 0
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT"
git rev-parse --verify {INSTALLED_BRANCH} >/dev/null 2>&1 || exit 0
# App-local stdlib helper (must not require orchestrator_cli package)
if [[ -f scripts/orchestrator-branch-sync.py ]]; then
  if python3 scripts/orchestrator-branch-sync.py --quiet; then
    exit 0
  fi
  # fall through to bash restore on non-zero (should be rare; script returns 0)
fi
# Bash fallback: always restore core surfaces when lock missing OR version differs
need=0
if [[ ! -f .orchestrator-version ]]; then
  need=1
else
  base_v="$(git show {INSTALLED_BRANCH}:.orchestrator-version 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"version\",\"\"))' 2>/dev/null || true)"
  cur_v="$(python3 -c 'import json; print(json.load(open(\".orchestrator-version\")).get(\"version\",\"\"))' 2>/dev/null || true)"
  if [[ -n "$base_v" && -n "$cur_v" && "$base_v" != "$cur_v" ]]; then
    need=1
  elif [[ ! -d .grok/skills || ! -f chains/registry.yaml ]]; then
    need=1
  fi
fi
if [[ "$need" -eq 1 ]]; then
  git checkout {INSTALLED_BRANCH} -- .orchestrator-version 2>/dev/null || true
  git checkout {INSTALLED_BRANCH} -- .grok chains scripts patterns .githooks 2>/dev/null || true
  git checkout {INSTALLED_BRANCH} -- CHAIN.md LOOP.md loop-budget.md CLAUDE.md 2>/dev/null || true
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    git add -A -- .orchestrator-version .grok chains scripts patterns .githooks \\
      CHAIN.md LOOP.md loop-budget.md CLAUDE.md 2>/dev/null || true
    git commit -m "chore(orchestrator): sync project install onto $(git branch --show-current)" 2>/dev/null || true
  fi
fi
exit 0
"""
    if hook.is_file() and marker in hook.read_text(encoding="utf-8", errors="replace"):
        out["ok"] = True
        out["message"] = "post-checkout hook already present"
    else:
        if hook.is_file():
            existing = hook.read_text(encoding="utf-8", errors="replace")
            if marker not in existing:
                hook.write_text(existing.rstrip() + "\n\n" + body, encoding="utf-8")
            out["message"] = "appended post-checkout orchestrator sync"
        else:
            hook.write_text(body, encoding="utf-8")
            out["message"] = "created post-checkout orchestrator sync"
        out["ok"] = True
    try:
        hook.chmod(hook.stat().st_mode | 0o111)
    except OSError:
        pass
    # Point core.hooksPath at .githooks when possible
    _run_git(target, "config", "core.hooksPath", ".githooks")
    return out


def project_global_install(target: Path) -> dict[str, Any]:
    """Post-deploy install step. Default is **safe**: no multi-branch blast.

    Historical behaviour (broadcast every local branch + post-checkout hook)
    was opt-out and caused severe damage on large app repos. It is now
    **opt-in** via env flags only.
    """
    report: dict[str, Any] = {"ok": True, "steps": [], "message": ""}
    if branch_sync_suppressed():
        report["message"] = "ORCHESTRATOR_NO_BRANCH_SYNC=1 — skipped project-global sync"
        return report

    # Always cheap: pointer branch for optional manual restore (no checkout thrash)
    base = update_installed_baseline(target)
    report["steps"].append(base)

    if branch_hook_enabled():
        hook = install_post_checkout_hook(target)
        report["steps"].append(hook)
        if hook.get("ok"):
            _run_git(target, "add", ".githooks/post-checkout")
            _run_git(
                target,
                "commit",
                "-m",
                "chore(orchestrator): post-checkout sync for project-global install",
            )
            update_installed_baseline(target)
    else:
        report["steps"].append(
            {
                "ok": True,
                "message": (
                    "post-checkout hook skipped (default). "
                    "Opt-in: ORCHESTRATOR_INSTALL_BRANCH_HOOK=1"
                ),
            }
        )

    if branch_broadcast_enabled():
        broadcast = broadcast_to_local_branches(target)
        report["steps"].append(broadcast)
        report["ok"] = base.get("ok", False) and broadcast.get("ok", True)
        report["message"] = (
            f"project-global install: baseline={base.get('message')}; "
            f"{broadcast.get('message')}; "
            f"hook={report['steps'][1].get('message')}"
        )
    else:
        report["ok"] = bool(base.get("ok", False))
        report["message"] = (
            f"project-global install (safe default): baseline={base.get('message')}; "
            "no multi-branch broadcast (opt-in ORCHESTRATOR_BRANCH_BROADCAST=1); "
            "no post-checkout hook unless ORCHESTRATOR_INSTALL_BRANCH_HOOK=1"
        )
        report["steps"].append(
            {
                "ok": True,
                "message": "broadcast skipped (safe default — current branch only)",
            }
        )
    return report

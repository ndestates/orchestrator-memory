"""Git helpers for the clean-deploy flow (branch → commit → optional PR)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitOpsError(RuntimeError):
    pass


@dataclass
class GitState:
    branch: str
    had_changes: bool


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def is_repo(path: Path) -> bool:
    r = _run_git(path, "rev-parse", "--git-dir", check=False)
    return r.returncode == 0


def current_branch(path: Path) -> str:
    r = _run_git(path, "branch", "--show-current", check=False)
    if r.returncode != 0 or not r.stdout.strip():
        raise GitOpsError("cannot determine current branch (detached HEAD?)")
    return r.stdout.strip()


def working_tree_clean(path: Path) -> bool:
    r = _run_git(path, "status", "--porcelain", check=False)
    return r.returncode == 0 and not r.stdout.strip()


def has_staged_or_unstaged_changes(path: Path) -> bool:
    return not working_tree_clean(path)


def stash_push_including_untracked(path: Path, message: str) -> bool:
    """Stash tracked + untracked (not ignored). Returns True if a stash was created."""
    before = _run_git(path, "rev-parse", "-q", "--verify", "refs/stash", check=False)
    before_ok = before.returncode == 0
    before_sha = before.stdout.strip() if before_ok else ""
    r = _run_git(
        path,
        "stash",
        "push",
        "-u",
        "-m",
        message,
        check=False,
    )
    if r.returncode != 0:
        raise GitOpsError(
            (r.stderr or r.stdout or "").strip()
            or "git stash push failed"
        )
    after = _run_git(path, "rev-parse", "-q", "--verify", "refs/stash", check=False)
    if after.returncode != 0:
        return False  # nothing to stash
    return after.stdout.strip() != before_sha or not before_ok


def stash_pop(path: Path) -> None:
    """Restore most recent stash. Raises GitOpsError on hard failure (conflicts still raise)."""
    r = _run_git(path, "stash", "pop", check=False)
    if r.returncode != 0:
        # Conflicts leave index/worktree dirty with stash often dropped or kept — surface both streams
        raise GitOpsError(
            (r.stderr or r.stdout or "").strip()
            or "git stash pop failed — resolve conflicts; check git stash list"
        )


def create_branch(path: Path, name: str) -> GitState:
    """Create *or reuse* branch ``name`` (Phase C BH-006).

    If already on ``name``, no-op. If ``name`` exists, check it out.
    Otherwise ``git checkout -b name``.
    """
    prior = current_branch(path)
    if prior == name:
        return GitState(branch=prior, had_changes=False)
    exists = _run_git(path, "rev-parse", "--verify", f"refs/heads/{name}", check=False)
    if exists.returncode == 0:
        r = _run_git(path, "checkout", name, check=False)
        if r.returncode != 0:
            raise GitOpsError(r.stderr.strip() or f"cannot checkout existing branch {name}")
    else:
        r = _run_git(path, "checkout", "-b", name, check=False)
        if r.returncode != 0:
            raise GitOpsError(r.stderr.strip() or f"cannot create branch {name}")
    return GitState(branch=prior, had_changes=False)


def restore_branch(path: Path, previous: str, delete_branch: str | None = None) -> None:
    _run_git(path, "checkout", previous, check=False)
    if delete_branch:
        _run_git(path, "branch", "-D", delete_branch, check=False)


def merge_into_branch(
    path: Path,
    *,
    source_branch: str,
    dest_branch: str,
) -> None:
    """Checkout *dest_branch* and merge *source_branch* into it (no-ff not required).

    Used after PR-style chore/* install so the user's original branch also carries
    orchestrator files (install must persist across subsequent branch work).
    """
    if source_branch == dest_branch:
        return
    r = _run_git(path, "checkout", dest_branch, check=False)
    if r.returncode != 0:
        raise GitOpsError(
            r.stderr.strip() or f"cannot checkout {dest_branch} to merge install"
        )
    # Already up to date or fast-forward preferred
    r = _run_git(
        path,
        "merge",
        "--no-edit",
        "-m",
        f"chore(orchestrator): merge {source_branch} into {dest_branch}",
        source_branch,
        check=False,
    )
    if r.returncode != 0:
        # Leave dest checked out with conflict markers if any — do not force
        raise GitOpsError(
            (r.stderr or r.stdout or "").strip()
            or f"merge {source_branch} into {dest_branch} failed — resolve conflicts"
        )


def commit_all(path: Path, message: str) -> str | None:
    _run_git(path, "add", "-A")
    r = _run_git(path, "commit", "-m", message, check=False)
    if r.returncode != 0:
        if "nothing to commit" in (r.stdout + r.stderr):
            return None
        raise GitOpsError(r.stderr.strip() or r.stdout.strip() or "git commit failed")
    rev = _run_git(path, "rev-parse", "--short", "HEAD")
    return rev.stdout.strip()


def try_create_pr(
    path: Path,
    *,
    title: str,
    body: str,
    head_branch: str,
    base: str = "develop",
) -> str | None:
    """Open a PR via gh when available; return URL or None."""
    r = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--head",
            head_branch,
            "--base",
            base,
        ],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return None
    url = r.stdout.strip()
    return url or None


def detect_default_base(path: Path) -> str:
    for candidate in ("develop", "main", "master"):
        r = _run_git(path, "rev-parse", "--verify", f"origin/{candidate}", check=False)
        if r.returncode == 0:
            return candidate
    try:
        return current_branch(path)
    except GitOpsError:
        return "main"
"""Smoke tests for scripts/resume-branch.sh (used by session-start / daily-standup).

Tests output format + the divergence reporting (remote_last_behind / remote_last_ahead)
added to support multi-machine "pull latest remote work branch" guarantees.

Runnable directly:
    python3 tests/test_resume_branch.py

When pytest + dev deps available it is also collected by the normal harness
(kept compatible with patterns in test_sync_all_projects.py).

These are Phase 0 smoke tests using subprocess + isolated git repos.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "resume-branch.sh"


def _git(cwd: Path, *args, env=None, check=True):
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check, capture_output=True, text=True, env=full_env
    )


def _init_repo(path: Path, branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@t.test")
    _git(path, "config", "user.name", "tester")
    _git(path, "checkout", "-b", branch)
    (path / "README.md").write_text("init\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(
        path,
        "commit",
        "-q",
        "-m",
        "init",
        env={"GIT_COMMITTER_DATE": "2026-06-20T10:00:00", "GIT_AUTHOR_DATE": "2026-06-20T10:00:00"},
    )
    # harmless fake remote (script guards fetch failures)
    _git(path, "remote", "add", "origin", "https://example.invalid/noop.git")


def _create_commit_object(cwd: Path, parent: str, msg: str, date: str) -> str:
    """Create an unattached commit object (for simulating remote-only work)."""
    tree = _git(cwd, "rev-parse", f"{parent}^{{tree}}").stdout.strip()
    env = {"GIT_COMMITTER_DATE": date, "GIT_AUTHOR_DATE": date}
    res = _git(cwd, "commit-tree", "-p", parent, "-m", msg, tree, env=env)
    return res.stdout.strip()


def _update_ref(cwd: Path, ref: str, sha: str) -> None:
    _git(cwd, "update-ref", ref, sha)


def _run(cwd: Path, *extra_args: str):
    """Execute resume-branch.sh with cwd inside the test git repo."""
    return subprocess.run(
        ["bash", str(SCRIPT), *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _parse_kv(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in stdout.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def _with_temp_repo(fn):
    """Helper to run a test function with an isolated temp git repo path."""
    with tempfile.TemporaryDirectory() as td:
        fn(Path(td))


def _test_basic_output_and_zero_divergence():
    def body(repo: Path):
        _init_repo(repo, branch="main")
        head = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/main", head)

        res = _run(repo)
        assert res.returncode == 0, f"nonzero exit\n{res.stderr}"
        data = _parse_kv(res.stdout)
        for key in (
            "current",
            "remote_last",
            "remote_last_behind",
            "remote_last_ahead",
            "sync_status",
            "sync_message",
            "working_tree",
            "vs_remote_last_behind",
            "vs_remote_last_ahead",
            "vs_remote_last_summary",
            "switch_offer",
            "integration_ff_offer",
        ):
            assert key in data, f"missing {key} in {data}"
        assert data["remote_last_behind"] == "0"
        assert data["remote_last_ahead"] == "0"
        assert data["vs_remote_last_behind"] == "0"
        assert data["vs_remote_last_ahead"] == "0"
        assert data["switch_offer"] == "no"
        assert data["sync_status"] == "up_to_date"
        assert "up to date" in data["sync_message"].lower()
    _with_temp_repo(body)


def _test_reports_behind_when_remote_ahead():
    """remote_last_behind == N means other machine pushed work we don't have locally."""
    def body(repo: Path):
        _init_repo(repo, branch="feature/resume-test")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/resume-test", base)

        # Remote-only extra commit (other machine)
        remote_tip = _create_commit_object(
            repo, base, "remote work from other machine", "2026-06-27T15:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/resume-test", remote_tip)

        res = _run(repo)
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["remote_last"] == "feature/resume-test"
        assert data["remote_last_behind"] == "1"
        assert data["remote_last_ahead"] == "0"
        assert data["sync_status"] == "behind"
        assert "Behind" in data["sync_message"]
    _with_temp_repo(body)


def _test_reports_ahead_when_local_ahead_of_remote():
    """remote_last_ahead > 0 means local has unpushed commits on the resume target."""
    def body(repo: Path):
        _init_repo(repo, branch="feature/resume-test")
        # Local commit
        (repo / "work.txt").write_text("c1\n", encoding="utf-8")
        _git(repo, "add", "work.txt")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "local c1",
            env={"GIT_COMMITTER_DATE": "2026-06-27T14:00:00"},
        )
        local_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/resume-test", local_head)

        # One more local only (unpushed)
        (repo / "work.txt").write_text("c2\n", encoding="utf-8")
        _git(repo, "add", "work.txt")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "local unpushed",
            env={"GIT_COMMITTER_DATE": "2026-06-27T16:00:00"},
        )

        res = _run(repo)
        assert res.returncode == 0
        data = _parse_kv(res.stdout)
        assert data["remote_last"] == "feature/resume-test"
        assert int(data.get("remote_last_ahead", "0")) >= 1
        assert data["remote_last_behind"] == "0"
        assert data["sync_status"] == "ahead"
        assert "up to date with remote" in data["sync_message"].lower()
    _with_temp_repo(body)


def _test_graceful_with_no_remote_refs():
    def body(repo: Path):
        _init_repo(repo, branch="main")
        # deliberately no origin/* refs created
        res = _run(repo)
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert "current" in data and "remote_last" in data
        assert "remote_last_behind" in data
    _with_temp_repo(body)


def _test_vs_remote_last_diff_and_switch_offer():
    """current HEAD vs a different remote-last tip → vs_remote_last_* + switch_offer."""

    def body(repo: Path):
        _init_repo(repo, branch="feature/stay")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/stay", base)

        # Newer remote-only work branch (becomes remote_last by date)
        other = _create_commit_object(
            repo, base, "remote last tip", "2026-07-12T12:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/work-remote", other)

        # Local-only commit on current (ahead of remote-last fork)
        (repo / "local.txt").write_text("x\n", encoding="utf-8")
        _git(repo, "add", "local.txt")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "local only",
            env={
                "GIT_COMMITTER_DATE": "2026-07-11T10:00:00",
                "GIT_AUTHOR_DATE": "2026-07-11T10:00:00",
            },
        )

        res = _run(repo)
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["remote_last"] == "feature/work-remote"
        assert data["switch_offer"] == "yes"
        assert data["current"] == "feature/stay"
        assert int(data["vs_remote_last_behind"]) >= 1
        assert int(data["vs_remote_last_ahead"]) >= 1
        assert "vs" in data["vs_remote_last_summary"].lower() or "commit" in data[
            "vs_remote_last_summary"
        ].lower()
        assert "only_on_remote_last" in data.get("vs_remote_last_subjects", "")

    _with_temp_repo(body)


def _test_integration_ff_offer_when_develop_behind():
    """Local develop behind origin/develop → integration_ff_offer=yes."""

    def body(repo: Path):
        _init_repo(repo, branch="feature/work")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/work", base)

        # Local develop at base
        _git(repo, "branch", "develop", base)
        # Remote develop one commit ahead
        tip = _create_commit_object(
            repo, base, "develop remote", "2026-07-13T09:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/develop", tip)

        res = _run(repo)
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["integration_branch"] == "develop"
        assert data["integration_ff_offer"] == "yes"
        assert int(data["integration_behind"]) == 1
        assert int(data["integration_ahead"]) == 0
        assert "behind" in data["integration_offer_message"].lower()

    _with_temp_repo(body)


def _test_apply_switches_to_remote_last_when_clean():
    def body(repo: Path):
        _init_repo(repo, branch="feature/old")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/old", base)
        newer = _create_commit_object(
            repo, base, "newer remote branch", "2026-07-18T12:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/new", newer)

        res = _run(repo, "--apply")
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["remote_last"] == "feature/new"
        assert data["switch_result"] in ("switched", "already_on")
        assert data["switch_applied"] == "yes"
        assert data["current"] == "feature/new"
        assert data["switch_policy"] == "auto_remote_last"
        assert data["switch_result"] != "checkout_failed"

    _with_temp_repo(body)


def _test_apply_blocks_when_dirty():
    def body(repo: Path):
        _init_repo(repo, branch="feature/old")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/old", base)
        newer = _create_commit_object(
            repo, base, "newer remote branch", "2026-07-18T12:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/new", newer)
        (repo / "wip.txt").write_text("dirty\n", encoding="utf-8")

        res = _run(repo, "--apply")
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["switch_result"] == "blocked_dirty"
        assert data["switch_applied"] == "no"
        assert data["current"] == "feature/old"
        assert data["working_tree"] == "dirty"

    _with_temp_repo(body)


def _test_apply_soft_dirty_session_noise_allows_switch():
    """context-latest only is soft-dirty — does not block remote_last switch."""

    def body(repo: Path):
        _init_repo(repo, branch="feature/old")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/old", base)
        newer = _create_commit_object(
            repo, base, "newer remote branch", "2026-07-18T12:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/new", newer)
        sessions = repo / "reports" / "sessions"
        sessions.mkdir(parents=True)
        ctx = sessions / "context-latest.json"
        ctx.write_text('{"v":1}\n', encoding="utf-8")
        _git(repo, "add", "reports/sessions/context-latest.json")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "session ctx",
            env={"GIT_COMMITTER_DATE": "2026-07-10T10:00:00", "GIT_AUTHOR_DATE": "2026-07-10T10:00:00"},
        )
        # Older local commit on feature/old must not beat remote_last by date
        ctx.write_text('{"dirty":true}\n', encoding="utf-8")

        res = _run(repo, "--apply")
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data.get("startup_policy") == "fetch_then_remote_last_then_card"
        assert data.get("soft_dirty_only") == "yes"
        assert data["remote_last"] == "feature/new"
        assert data["switch_applied"] == "yes"
        assert data["current"] == "feature/new"
        assert data["switch_result"] in ("switched", "already_on")
        assert data.get("on_remote_last") == "yes"

    _with_temp_repo(body)


def _test_apply_prefers_remote_last_over_stale_vault_branch():
    """remote_last wins for --apply; vault is not the switch authority.

    Also refreshes vault pointer after switch so the next session is not stuck.
    """

    def body(repo: Path):
        _init_repo(repo, branch="feature/stale-vault")
        base = _git(repo, "rev-parse", "HEAD").stdout.strip()
        _update_ref(repo, "refs/remotes/origin/feature/stale-vault", base)
        newer = _create_commit_object(
            repo, base, "true last session", "2026-07-22T20:00:00"
        )
        _update_ref(repo, "refs/remotes/origin/feature/last-session", newer)

        # Do not write vault before apply (untracked ledger would block dirty-guard).
        # Switch authority is remote_last alone.
        res = _run(repo, "--apply")
        assert res.returncode == 0, res.stderr
        data = _parse_kv(res.stdout)
        assert data["remote_last"] == "feature/last-session", data
        assert data["switch_applied"] == "yes", data
        assert data["current"] == "feature/last-session", data
        assert data["switch_result"] in ("switched", "already_on"), data
        # Best-effort vault refresh after switch
        assert data.get("operator_last_branch") in (
            "feature/last-session",
            "",
        ), data

    _with_temp_repo(body)


def main():
    tests = [
        ("basic_output_zero_divergence", _test_basic_output_and_zero_divergence),
        ("reports_behind_remote_ahead", _test_reports_behind_when_remote_ahead),
        ("reports_ahead_local_unpushed", _test_reports_ahead_when_local_ahead_of_remote),
        ("graceful_no_remotes", _test_graceful_with_no_remote_refs),
        ("vs_remote_last_diff_switch_offer", _test_vs_remote_last_diff_and_switch_offer),
        ("integration_ff_offer_develop_behind", _test_integration_ff_offer_when_develop_behind),
        ("apply_switches_clean", _test_apply_switches_to_remote_last_when_clean),
        ("apply_blocks_dirty", _test_apply_blocks_when_dirty),
        ("apply_soft_dirty_allows_switch", _test_apply_soft_dirty_session_noise_allows_switch),
        (
            "apply_prefers_remote_over_stale_vault",
            _test_apply_prefers_remote_last_over_stale_vault_branch,
        ),
    ]
    failures = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            failures.append(name)
        except Exception as e:
            print(f"ERROR {name}: {e}")
            import traceback
            traceback.print_exc()
            failures.append(name)
    if failures:
        print(f"\n{len(failures)} test(s) failed: {failures}")
        sys.exit(1)
    print("\nAll resume-branch smoke tests passed.")


if __name__ == "__main__":
    main()

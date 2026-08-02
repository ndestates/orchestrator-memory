"""Phase 3: clean-deploy flow (init/upgrade) integration tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestrator_cli.__main__ import main
from orchestrator_cli.flow import FlowOptions, run_flow
from orchestrator_cli.lock import lock_path, read_lock
from orchestrator_cli.version import template_version


def _git(repo: Path, *args: str, check: bool = True) -> None:
    subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "flow@test.local")
    _git(path, "config", "user.name", "flow-test")
    (path / "README.md").write_text("# app\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "init")


@pytest.fixture(autouse=True)
def _skip_host_cli_hygiene(monkeypatch):
    """Flow tests must not reinstall the host pip package."""
    monkeypatch.setenv("ORCHESTRATOR_SKIP_CLI_HYGIENE", "1")


@pytest.fixture
def git_target(tmp_path):
    t = tmp_path / "mailchimp"
    _init_git_repo(t)
    manifest = t / ".claude"
    manifest.mkdir()
    (manifest / "project-manifest.yaml").write_text(
        'project:\n  name: "Mailchimp"\nstack:\n  framework: "python"\n  profile: "python-flask"\n',
        encoding="utf-8",
    )
    _git(t, "add", ".claude/project-manifest.yaml")
    _git(t, "commit", "-q", "-m", "manifest")
    return t


def test_init_dry_run_leaves_lock_unset(git_target):
    rc = main(["init", str(git_target), "--dry-run", "--no-pr", "--profile", "python-flask"])
    assert rc == 0
    assert not lock_path(git_target).exists()


def test_init_materializes_template(git_target):
    # 1. Run init without --dry-run or PR creation
    rc = main(["init", str(git_target), "--no-pr", "--profile", "python-flask"])
    assert rc == 0

    # 2. Verify lock file created with correct version
    assert lock_path(git_target).exists()
    lock = read_lock(git_target)
    assert lock and lock["version"] == template_version()

    # 3. Verify template files materialized
    assert (git_target / ".grok" / "skills").is_dir()
    assert (git_target / "chains" / "registry.yaml").is_file()

    # 4. Verify commit happened on the flow branch (message contains "orchestrator")
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=git_target,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "orchestrator" in log.stdout


def test_init_rejects_dirty_tree(git_target):
    # 1. Make the working tree dirty
    (git_target / "dirty.txt").write_text("x", encoding="utf-8")

    # 2. Run init; expect failure (rc=1) and no lock created
    rc = main(["init", str(git_target), "--no-pr", "--profile", "python-flask"])
    assert rc == 1
    assert not lock_path(git_target).exists()


def test_init_rejects_when_already_installed(git_target):
    # 1. Install on current branch (--no-pr stays on feature branch / master)
    assert main(["init", str(git_target), "--no-pr", "--profile", "python-flask"]) == 0
    assert lock_path(git_target).exists()

    # 2. Second init must reject (lock already present on same branch)
    rc = main(["init", str(git_target), "--no-pr", "--profile", "python-flask"])
    assert rc == 1


def test_no_pr_install_persists_after_branch_switch(git_target):
    """Install must remain after checking out another branch (only if merged/history).

    With --no-pr the commit is on the *current* branch, so a new branch created
    from it still has orchestrator files.
    """
    start = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=git_target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert main(["init", str(git_target), "--no-pr", "--profile", "python-flask"]) == 0
    assert (git_target / ".orchestrator-version").is_file()
    assert (git_target / "chains" / "registry.yaml").is_file()

    # Branch from current HEAD (includes install commit)
    _git(git_target, "checkout", "-b", "feature/next-work")
    assert (git_target / ".orchestrator-version").is_file()
    assert (git_target / ".grok" / "skills").is_dir()
    # Parent branch still has it
    _git(git_target, "checkout", start)
    assert (git_target / ".orchestrator-version").is_file()

def test_upgrade_requires_prior_install(git_target):
    rc = main(["upgrade", str(git_target), "--no-pr", "--profile", "python-flask"])
    assert rc == 1


def test_upgrade_after_init(git_target):
    # 1. Perform initial install
    assert main(["init", str(git_target), "--no-pr", "--profile", "python-flask"]) == 0

    # 2. Simulate an older installed version by overwriting the lock file and committing it
    lock_path(git_target).write_text(
        json.dumps({"version": "1.0.0", "release_tag": "v1.0.0"}) + "\n",
        encoding="utf-8",
    )
    _git(git_target, "add", ".orchestrator-version")
    _git(git_target, "commit", "-q", "-m", "older lock")

    # 3. Upgrade should succeed and update the lock to current version
    rc = main(["upgrade", str(git_target), "--no-pr", "--profile", "python-flask"])
    assert rc == 0
    assert read_lock(git_target)["version"] == template_version()


def test_flow_result_json_shape(git_target):
    result = run_flow(
        FlowOptions(
            target=git_target,
            mode="init",
            profile="python-flask",
            dry_run=True,
            no_pr=True,
        )
    )
    assert result.ok is True
    assert result.mode == "init"


def test_license_gate_disabled_by_default():
    from orchestrator_cli.license import LicenseGate
    gate = LicenseGate(url=None, key=None)
    assert not gate.enabled
    assert gate.check() is True  # fail-open


def test_cli_license_command_disabled():
    from orchestrator_cli.__main__ import main
    rc = main(["license"])
    assert rc == 0
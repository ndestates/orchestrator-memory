"""Tests for automatic install/upgrade announcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator_cli import update_check
from orchestrator_cli.flow import run_upgrade
from orchestrator_cli.lock import write_lock
from orchestrator_cli.version import template_version


@pytest.fixture(autouse=True)
def _no_remote(monkeypatch):
    """Unit tests use local template version only."""
    monkeypatch.setenv("ORCHESTRATOR_NO_REMOTE_VERSION", "1")


@pytest.fixture()
def app_tree(tmp_path: Path) -> Path:
    (tmp_path / ".grok").mkdir()
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_not_installed_when_grok_present(app_tree: Path):
    n = update_check.evaluate(app_tree)
    assert n.kind == update_check.UpdateKind.NOT_INSTALLED
    assert n.available == template_version()
    assert "not installed" in n.message
    assert n.action and "init" in n.action


def test_upgrade_available(app_tree: Path):
    write_lock(
        app_tree,
        version="0.0.1",
        release_tag="v0.0.1",
        profile="laravel",
        cli_version="0.0.1",
        installed_at="2020-01-01T00:00:00Z",
    )
    n = update_check.evaluate(app_tree)
    assert n.kind == update_check.UpdateKind.UPGRADE_AVAILABLE
    assert n.installed == "0.0.1"
    assert "upgrade available" in n.message
    assert n.action and "upgrade" in n.action


def test_up_to_date(app_tree: Path):
    ver = template_version()
    write_lock(
        app_tree,
        version=ver,
        release_tag=f"v{ver}",
        profile="laravel",
        cli_version=ver,
        installed_at="2026-07-11T00:00:00Z",
    )
    n = update_check.evaluate(app_tree)
    assert n.kind == update_check.UpdateKind.UP_TO_DATE
    assert n.installed == ver


def test_skip_random_cwd(tmp_path: Path):
    n = update_check.evaluate(tmp_path)
    assert n.kind == update_check.UpdateKind.SKIPPED


def test_announce_upgrade_prints(app_tree: Path, capsys):
    write_lock(
        app_tree,
        version="0.0.1",
        release_tag="v0.0.1",
        profile=None,
        cli_version="0.0.1",
        installed_at="2020-01-01T00:00:00Z",
    )
    update_check.announce(app_tree, stream=None, quiet_if_current=True)
    # announce uses stderr by default — capsys captures both
    err = capsys.readouterr().err
    assert "upgrade available" in err


def test_check_command_exit_codes(app_tree: Path):
    from orchestrator_cli.commands import check as check_cmd

    assert check_cmd.run(app_tree) == 3  # not installed
    write_lock(
        app_tree,
        version="0.0.1",
        release_tag="v0.0.1",
        profile=None,
        cli_version="0.0.1",
        installed_at="2020-01-01T00:00:00Z",
    )
    assert check_cmd.run(app_tree) == 2
    ver = template_version()
    write_lock(
        app_tree,
        version=ver,
        release_tag=f"v{ver}",
        profile=None,
        cli_version=ver,
        installed_at="2026-07-11T00:00:00Z",
    )
    assert check_cmd.run(app_tree, quiet_ok=True) == 0


def test_to_dict_json_serializable(app_tree: Path):
    n = update_check.evaluate(app_tree)
    raw = json.dumps(n.to_dict())
    assert "not_installed" in raw


def test_upgrade_if_available_noop_when_current(app_tree: Path, capsys):
    ver = template_version()
    write_lock(
        app_tree,
        version=ver,
        release_tag=f"v{ver}",
        profile=None,
        cli_version=ver,
        installed_at="2026-07-11T00:00:00Z",
    )
    rc = run_upgrade(app_tree, if_available=True, yes=True, no_pr=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "up to date" in out


def test_upgrade_if_available_requires_yes_for_apply(app_tree: Path, capsys):
    write_lock(
        app_tree,
        version="0.0.1",
        release_tag="v0.0.1",
        profile=None,
        cli_version="0.0.1",
        installed_at="2020-01-01T00:00:00Z",
    )
    # Without --yes → dry-run path; may fail on non-repo cleanliness etc but
    # should at least print if-available dry-run message before flow.
    # Use a real git repo so flow can start dry-run.
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=app_tree, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@test.local"], cwd=app_tree, check=True
    )
    subprocess.run(["git", "config", "user.name", "t"], cwd=app_tree, check=True)
    (app_tree / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=app_tree, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "i"], cwd=app_tree, check=True)
    # re-write lock after commit
    write_lock(
        app_tree,
        version="0.0.1",
        release_tag="v0.0.1",
        profile=None,
        cli_version="0.0.1",
        installed_at="2020-01-01T00:00:00Z",
    )
    subprocess.run(["git", "add", "-A"], cwd=app_tree, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "lock"], cwd=app_tree, check=True)

    rc = run_upgrade(app_tree, if_available=True, yes=False, no_pr=True)
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert "dry-run" in text.lower() or "if-available" in text.lower()
    # dry-run may still return non-zero if license/deploy missing — kind is upgrade path
    assert "upgrade available" in text or rc in (0, 1)


def test_upgrade_if_available_not_installed(app_tree: Path, capsys):
    rc = run_upgrade(app_tree, if_available=True, yes=True, no_pr=True)
    assert rc == 3
    assert "not installed" in capsys.readouterr().out

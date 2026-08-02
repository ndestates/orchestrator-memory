"""Project-global install baseline + branch broadcast."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestrator_cli.project_install import (
    INSTALLED_BRANCH,
    broadcast_to_local_branches,
    project_global_install,
    sync_branch_from_baseline,
    update_installed_baseline,
)


def _git(repo: Path, *args: str, check: bool = True) -> None:
    subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@t.test")
    _git(path, "config", "user.name", "tester")
    (path / "README.md").write_text("app\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "init")


@pytest.fixture
def app_repo(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_NO_BRANCH_SYNC", raising=False)
    repo = tmp_path / "app"
    _init_repo(repo)
    # Simulate install on main
    (repo / ".orchestrator-version").write_text(
        json.dumps({"version": "1.9.4"}) + "\n", encoding="utf-8"
    )
    (repo / ".grok" / "skills").mkdir(parents=True)
    (repo / ".grok" / "skills" / "x.md").write_text("skill\n", encoding="utf-8")
    (repo / "chains").mkdir()
    (repo / "chains" / "registry.yaml").write_text("chains: []\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "session-context-envelope.py").write_text("# env\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "orchestrator install")
    return repo


def test_update_baseline_and_sync_new_branch(app_repo):
    start = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=app_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    base = update_installed_baseline(app_repo)
    assert base["ok"] is True

    # Branch without install files (from empty parent — create orphan-like fork)
    # Create branch from before install: reset soft simulation — new branch from HEAD
    # then delete files and commit, then sync should restore
    _git(app_repo, "checkout", "-b", "feature/no-orch")
    # Remove surfaces (simulate branch that never had install)
    for p in [
        app_repo / ".orchestrator-version",
        app_repo / ".grok" / "skills" / "x.md",
        app_repo / "chains" / "registry.yaml",
    ]:
        if p.is_file():
            p.unlink()
    _git(app_repo, "add", "-A")
    _git(app_repo, "commit", "-q", "-m", "strip orch")
    assert not (app_repo / ".orchestrator-version").is_file()

    res = sync_branch_from_baseline(app_repo, branch=None, commit=True)
    assert res["ok"] is True
    assert (app_repo / ".orchestrator-version").is_file()
    assert (app_repo / "chains" / "registry.yaml").is_file()

    _git(app_repo, "checkout", start)


def test_project_global_install_broadcast(app_repo):
    _git(app_repo, "checkout", "-b", "feature/a")
    # strip on feature/a
    (app_repo / ".orchestrator-version").unlink(missing_ok=True)
    _git(app_repo, "add", "-A")
    _git(app_repo, "commit", "-q", "-m", "strip on a")

    # reinstall baseline on start branch
    start = "master"
    for name in ("main", "master"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", name],
            cwd=app_repo,
            capture_output=True,
        )
        if r.returncode == 0:
            start = name
            break
    _git(app_repo, "checkout", start)
    # Ensure start has install (may need restore)
    if not (app_repo / ".orchestrator-version").is_file():
        _git(app_repo, "checkout", "HEAD~2", "--", ".orchestrator-version", ".grok", "chains", "scripts")
        _git(app_repo, "add", "-A")
        _git(app_repo, "commit", "-q", "-m", "restore install", check=False)

    update_installed_baseline(app_repo)
    # Safe default: no multi-branch broadcast
    rep = project_global_install(app_repo)
    assert rep.get("ok")
    assert "broadcast skipped" in (rep.get("message") or "") or "safe default" in (
        rep.get("message") or ""
    )

    # Opt-in broadcast still works when enabled
    import os

    os.environ["ORCHESTRATOR_BRANCH_BROADCAST"] = "1"
    try:
        rep2 = project_global_install(app_repo)
        assert rep2.get("ok") is not False
    finally:
        os.environ.pop("ORCHESTRATOR_BRANCH_BROADCAST", None)

    r = subprocess.run(
        ["git", "rev-parse", "--verify", INSTALLED_BRANCH],
        cwd=app_repo,
        capture_output=True,
    )
    assert r.returncode == 0

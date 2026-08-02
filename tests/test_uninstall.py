"""Tests for orchestrator uninstall (project + host plan)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestrator_cli.__main__ import main
from orchestrator_cli.lock import write_lock
from orchestrator_cli.uninstall import (
    apply_project_uninstall,
    collect_project_paths,
    uninstall_host_cli,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "u@test.local")
    _git(path, "config", "user.name", "test")
    (path / "README.md").write_text("# app\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "init")


@pytest.fixture
def app_repo(tmp_path: Path) -> Path:
    app = tmp_path / "myapp"
    _init_repo(app)
    # Simulate orchestrator install footprint
    (app / ".grok" / "skills" / "demo").mkdir(parents=True)
    (app / ".grok" / "skills" / "demo" / "SKILL.md").write_text("# x\n", encoding="utf-8")
    (app / ".grok" / "memories").mkdir(parents=True)
    (app / ".grok" / "memories" / "who-i-am.md").write_text("me\n", encoding="utf-8")
    (app / "CHAIN.md").write_text("# chains\n", encoding="utf-8")
    (app / "chains").mkdir()
    (app / "chains" / "registry.yaml").write_text("chains: []\n", encoding="utf-8")
    (app / "chains" / "registry.app.yaml").write_text("chains: []\n", encoding="utf-8")
    (app / "app").mkdir()
    (app / "app" / "Models").mkdir()
    (app / "app" / "Models" / "User.php").write_text("<?php\n", encoding="utf-8")
    write_lock(
        app,
        version="1.8.3",
        release_tag="v1.8.3",
        profile="laravel",
        cli_version="1.8.3",
        installed_at="2026-07-01T00:00:00Z",
    )
    return app


def test_collect_includes_lock_and_skills(app_repo: Path):
    plan = collect_project_paths(app_repo)
    assert not plan.errors
    assert ".orchestrator-version" in plan.paths or any(
        p.rstrip("/") == ".orchestrator-version" for p in plan.paths
    )
    assert any("skills" in p for p in plan.paths)
    # app source protected
    assert not any(p.startswith("app/") for p in plan.paths)


def test_keeps_who_i_am_and_registry_app(app_repo: Path):
    plan = collect_project_paths(app_repo)
    joined = " ".join(plan.paths)
    assert "who-i-am.md" not in joined
    assert "registry.app.yaml" not in joined


def test_apply_removes_lock(app_repo: Path):
    plan = collect_project_paths(app_repo)
    removed = apply_project_uninstall(plan, dry_run=False)
    assert removed
    assert not (app_repo / ".orchestrator-version").exists()
    assert (app_repo / "app" / "Models" / "User.php").is_file()
    assert (app_repo / "chains" / "registry.app.yaml").is_file()
    assert (app_repo / ".grok" / "memories" / "who-i-am.md").is_file()


def test_cli_dry_run(app_repo: Path):
    rc = main(["uninstall", str(app_repo), "--json"])
    assert rc == 0
    # lock still present
    assert (app_repo / ".orchestrator-version").is_file()


def test_cli_apply_requires_yes(app_repo: Path):
    rc = main(["uninstall", str(app_repo), "--apply"])
    assert rc == 2
    assert (app_repo / ".orchestrator-version").is_file()


def test_cli_apply_yes(app_repo: Path):
    rc = main(["uninstall", str(app_repo), "--apply", "--yes"])
    assert rc == 0
    assert not (app_repo / ".orchestrator-version").exists()


def test_refuse_template_source():
    # monorepo root is template source
    root = Path(__file__).resolve().parents[1]
    plan = collect_project_paths(root)
    assert plan.errors
    assert any("template source" in e for e in plan.errors)


def test_host_plan_dry_run():
    r = uninstall_host_cli(dry_run=True)
    assert r.actions
    assert any("npm" in a for a in r.actions)

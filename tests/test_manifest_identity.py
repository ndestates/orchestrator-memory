"""Tests for project-manifest identity (not orchestrator template residue)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.manifest_identity import (  # noqa: E402
    check_manifest_identity,
    detect_stack_signals,
    is_orchestrator_source_repo,
    parse_manifest_identity_fields,
)


TEMPLATE_MANIFEST = """\
project:
  name: "Project Template"
  description: "Reusable orchestrator template for fast start-to-beta delivery"
  default_branch: "master"

stack:
  framework: "generic"
  language: "generic"
  uses_database: false
  database_engine: "none"

runtime:
  environment_manager: "local"
"""


CUSTOM_LARAVEL = """\
project:
  name: "e-ndsign"
  description: "Electronic signing platform"
  default_branch: "master"

stack:
  framework: "laravel"
  language: "php"
  uses_database: true
  database_engine: "mysql"

runtime:
  environment_manager: "ddev"
"""


def test_orchestrator_source_is_ok():
    assert is_orchestrator_source_repo(REPO_ROOT)
    result = check_manifest_identity(REPO_ROOT)
    assert result["status"] == "ok"
    assert result["ok"] is True
    assert result["is_orchestrator_source"] is True


def test_template_residue_on_app_dir(tmp_path: Path):
    (tmp_path / "artisan").write_text("#!/usr/bin/env php\n", encoding="utf-8")
    (tmp_path / "composer.json").write_text('{"name":"app/x"}', encoding="utf-8")
    (tmp_path / ".ddev").mkdir()
    (tmp_path / ".ddev" / "config.yaml").write_text("name: app\n", encoding="utf-8")
    mf = tmp_path / ".grok"
    mf.mkdir()
    (mf / "project-manifest.yaml").write_text(TEMPLATE_MANIFEST, encoding="utf-8")

    result = check_manifest_identity(tmp_path)
    assert result["status"] == "template_residue"
    assert result["ok"] is False
    assert any("template placeholder" in i for i in result["issues"])
    assert "laravel" in result["detected_stack"]


def test_customized_laravel_ok(tmp_path: Path):
    (tmp_path / "artisan").write_text("#!/usr/bin/env php\n", encoding="utf-8")
    (tmp_path / "composer.json").write_text('{"name":"app/x"}', encoding="utf-8")
    mf = tmp_path / ".github"
    mf.mkdir()
    (mf / "project-manifest.yaml").write_text(CUSTOM_LARAVEL, encoding="utf-8")

    result = check_manifest_identity(tmp_path)
    assert result["status"] == "ok"
    assert result["ok"] is True
    assert result["project_name"] == "e-ndsign"


def test_missing_manifest(tmp_path: Path):
    result = check_manifest_identity(tmp_path)
    assert result["status"] == "missing"
    assert result["ok"] is False


def test_parse_fields():
    fields = parse_manifest_identity_fields(CUSTOM_LARAVEL)
    assert fields["project_name"] == "e-ndsign"
    assert fields["framework"] == "laravel"
    assert fields["uses_database"] is True


def test_detect_stack_nextjs(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"next": "14.0.0"}}), encoding="utf-8"
    )
    assert "nextjs" in detect_stack_signals(tmp_path)


def test_cli_json_on_repo():
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check-project-manifest.py"), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["status"] == "ok"
    assert data["is_orchestrator_source"] is True

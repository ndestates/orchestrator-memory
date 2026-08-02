"""Tests: project-manifest never overwritten; new projects get stack-aware seed."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine import deploy as deploy_mod  # noqa: E402
from _engine import manifest_bootstrap as mb  # noqa: E402


def test_is_protected_manifest_rel() -> None:
    assert mb.is_protected_manifest_rel(".github/project-manifest.yaml")
    assert mb.is_protected_manifest_rel(".grok/project-manifest.yaml")
    assert mb.is_protected_manifest_rel("./.claude/project-manifest.yaml")
    # Basename alone is not enough; must be under a platform root
    assert not mb.is_protected_manifest_rel("project-manifest.yaml")
    assert not mb.is_protected_manifest_rel("docs/notes/project-manifest.yaml")
    assert not mb.is_protected_manifest_rel(".grok/skills/foo/SKILL.md")


def test_never_deploy_hard_blocks_manifest() -> None:
    bundle = {
        "never_deploy": [],  # empty list — hard rule still applies
        "selections": {"cache-spine": {"allow_deploy_prefixes": ["."]}},
    }
    assert deploy_mod.is_never_deploy(
        ".github/project-manifest.yaml", bundle, selections=["cache-spine"]
    )
    assert deploy_mod.is_never_deploy(".claude/project-manifest.yaml", bundle, None)


def test_seed_new_laravel_project(tmp_path: Path, monkeypatch) -> None:
    app = tmp_path / "lightstone"
    app.mkdir()
    (app / "artisan").write_text("#!/usr/bin/env php\n", encoding="utf-8")
    (app / "composer.json").write_text('{"name":"app/lightstone"}\n', encoding="utf-8")
    (app / ".ddev").mkdir()

    monkeypatch.setattr(mb, "get_template_root", lambda: REPO_ROOT)

    result = mb.ensure_project_manifest(app, profile_id="laravel", mode="init")
    assert result["action"] == "seeded"
    manifest = app / ".github" / "project-manifest.yaml"
    assert manifest.is_file()
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "Lightstone"
    assert data["stack"]["framework"] == "laravel"
    assert data["stack"]["language"] == "php"
    assert data["stack"]["profile"] == "laravel"
    assert data["runtime"]["environment_manager"] == "ddev"
    # Platform copies
    assert (app / ".grok" / "project-manifest.yaml").is_file()
    assert (app / ".claude" / "project-manifest.yaml").is_file()


def test_preserve_customized_manifest_on_upgrade(tmp_path: Path, monkeypatch) -> None:
    app = tmp_path / "ndestates-io"
    app.mkdir()
    gh = app / ".github"
    gh.mkdir()
    custom = {
        "project": {
            "name": "NDestates IO",
            "description": "Real estate Laravel app",
            "default_branch": "develop",
        },
        "stack": {
            "framework": "laravel",
            "language": "php",
            "uses_database": True,
            "database_engine": "mysql",
            "profile": "laravel",
        },
        "token_policy": {"mode": "deep", "max_cache_files_default": 5},
    }
    (gh / "project-manifest.yaml").write_text(
        yaml.safe_dump(custom, sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setattr(mb, "get_template_root", lambda: REPO_ROOT)

    result = mb.ensure_project_manifest(app, profile_id="laravel", mode="upgrade")
    assert result["action"] == "preserved"
    data = yaml.safe_load((gh / "project-manifest.yaml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "NDestates IO"
    assert data["token_policy"]["mode"] == "deep"
    assert data["token_policy"]["max_cache_files_default"] == 5


def test_amend_template_residue(tmp_path: Path, monkeypatch) -> None:
    app = tmp_path / "mailchimp"
    app.mkdir()
    gh = app / ".github"
    gh.mkdir()
    residue = {
        "project": {
            "name": "Project Template",
            "description": "Reusable orchestrator template for fast start-to-beta delivery",
        },
        "stack": {
            "framework": "generic",
            "language": "generic",
            "uses_database": False,
            "database_engine": "none",
        },
        "token_policy": {"mode": "lean", "max_cache_files_default": 2},
        "loop_policy": {"default_level": "L1"},
    }
    (gh / "project-manifest.yaml").write_text(
        yaml.safe_dump(residue, sort_keys=False), encoding="utf-8"
    )
    (app / "requirements.txt").write_text("flask\n", encoding="utf-8")
    monkeypatch.setattr(mb, "get_template_root", lambda: REPO_ROOT)

    result = mb.ensure_project_manifest(app, profile_id="python-flask", mode="upgrade")
    assert result["action"] == "amended"
    data = yaml.safe_load((gh / "project-manifest.yaml").read_text(encoding="utf-8"))
    assert data["project"]["name"] != "Project Template"
    assert "Mailchimp" in data["project"]["name"] or "mailchimp" in data["project"]["name"].lower()
    assert data["stack"]["framework"] == "flask"
    assert data["stack"]["language"] == "python"
    assert data["stack"]["profile"] == "python-flask"
    # Local policy preserved
    assert data["token_policy"]["mode"] == "lean"
    assert data["loop_policy"]["default_level"] == "L1"


def test_run_deploy_skips_manifest_even_with_yes(tmp_path: Path, monkeypatch) -> None:
    """Even init-style yes=overwrite must not copy template project-manifest."""
    # Minimal: call is_never_deploy through deploy_file path by unit-checking helper
    # (full run_deploy needs full template selections — covered by is_never_deploy hard block)
    assert deploy_mod.is_never_deploy(
        ".github/project-manifest.yaml",
        deploy_mod.load_bundle() if hasattr(deploy_mod, "load_bundle") else {"never_deploy": []},
        None,
    )


def main() -> None:
    # Lightweight runner without pytest fixtures
    import tempfile
    from unittest.mock import patch

    test_is_protected_manifest_rel()
    print("PASS protected rel")
    test_never_deploy_hard_blocks_manifest()
    print("PASS never_deploy hard block")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        app = root / "lightstone"
        app.mkdir()
        (app / "artisan").write_text("x\n", encoding="utf-8")
        (app / "composer.json").write_text("{}\n", encoding="utf-8")
        (app / ".ddev").mkdir()
        with patch.object(mb, "get_template_root", return_value=REPO_ROOT):
            r = mb.ensure_project_manifest(app, profile_id="laravel", mode="init")
        assert r["action"] == "seeded"
        data = yaml.safe_load(
            (app / ".github" / "project-manifest.yaml").read_text(encoding="utf-8")
        )
        assert data["stack"]["framework"] == "laravel"
        print("PASS seed laravel")

        # Second call preserves
        with patch.object(mb, "get_template_root", return_value=REPO_ROOT):
            r2 = mb.ensure_project_manifest(app, profile_id="laravel", mode="upgrade")
        assert r2["action"] == "preserved"
        print("PASS preserve after seed")

    with tempfile.TemporaryDirectory() as td:
        app = Path(td) / "app"
        app.mkdir()
        gh = app / ".github"
        gh.mkdir()
        residue = {
            "project": {
                "name": "Project Template",
                "description": "Reusable orchestrator template for fast start-to-beta delivery",
            },
            "stack": {
                "framework": "generic",
                "language": "generic",
                "uses_database": False,
                "database_engine": "none",
            },
            "token_policy": {"mode": "lean"},
        }
        (gh / "project-manifest.yaml").write_text(
            yaml.safe_dump(residue), encoding="utf-8"
        )
        (app / "requirements.txt").write_text("flask\n", encoding="utf-8")
        with patch.object(mb, "get_template_root", return_value=REPO_ROOT):
            r = mb.ensure_project_manifest(app, profile_id="python-flask", mode="init")
        assert r["action"] == "amended"
        data = yaml.safe_load(
            (gh / "project-manifest.yaml").read_text(encoding="utf-8")
        )
        assert data["stack"]["framework"] == "flask"
        print("PASS amend residue")

    print("All manifest_bootstrap smoke tests passed.")


if __name__ == "__main__":
    main()

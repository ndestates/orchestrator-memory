"""Phase 2: template_root injection via scripts/_engine shims."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    path = SCRIPTS / name
    mod_name = "orchtest_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec.loader.exec_module(module)
    return module


def test_deploy_uses_explicit_template_root(tmp_path):
    from _engine.roots import reset_template_root, set_template_root
    from _engine import deploy as deploy_engine

    reset_template_root()
    (tmp_path / "scripts").mkdir(parents=True)
    bundle = tmp_path / "scripts" / "deploy-bundle.yaml"
    bundle.write_text(
        "version: 2\nselections: {}\ndefault_selections: []\n",
        encoding="utf-8",
    )
    set_template_root(tmp_path)
    assert deploy_engine.bundle_path() == bundle
    reset_template_root()


def test_customize_profiles_dir_follows_template_root(tmp_path):
    from _engine.roots import reset_template_root, set_template_root
    from _engine import customize as customize_engine

    reset_template_root()
    profiles = tmp_path / "scripts" / "stack-profiles"
    profiles.mkdir(parents=True)
    (profiles / "manifest-map.yaml").write_text("by_dirname: {}\n", encoding="utf-8")
    set_template_root(tmp_path)
    assert customize_engine.profiles_dir() == profiles
    reset_template_root()


def test_contamination_engine_locates_scan_script():
    from _engine.contamination import script_path
    from _engine.roots import reset_template_root, set_template_root

    reset_template_root()
    set_template_root(REPO_ROOT)
    assert script_path().name == "scan-template-contamination.sh"
    assert script_path().is_file()
    reset_template_root()


def test_sync_projects_engine_locates_bash_script():
    from _engine.sync_projects import script_path
    from _engine.roots import reset_template_root, set_template_root

    reset_template_root()
    set_template_root(REPO_ROOT)
    assert script_path().name == "sync-all-projects.sh"
    assert script_path().is_file()
    reset_template_root()


def test_phase0_deploy_shim_still_exports_api():
    deploy_mod = _load("deploy_grok_to_project.py")
    assert callable(deploy_mod.sha256_file)
    assert callable(deploy_mod.deploy_file)
    assert callable(deploy_mod.resolve_selections)


@pytest.mark.parametrize(
    "script",
    [
        "deploy_grok_to_project.py",
        "customize-skills-for-project.py",
        "sync_grok_to_github_claude.py",
        "check_name_alignment.py",
    ],
)
def test_shim_imports(script: str):
    _load(script)
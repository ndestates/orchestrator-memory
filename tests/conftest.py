"""Shared fixtures + module loaders for the orchestrator tooling test harness.

The scripts under scripts/ are not a package and some have hyphenated filenames
(e.g. customize-skills-for-project.py) that cannot be imported by name, so we
load them via importlib from their absolute path. This mirrors how the Phase 2
`scripts/_engine/` shims and the CLI will import them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"

# Make the orchestrator_cli package importable without an install (CI also runs
# `pip install -e .`, but local/dev runs work via this path insert).
_SRC = str(REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def load_script(filename: str):
    """Import a scripts/<filename> module by absolute path (handles hyphens)."""
    path = SCRIPTS / filename
    mod_name = "orchtest_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def deploy_mod():
    return load_script("deploy_grok_to_project.py")


@pytest.fixture(scope="session")
def customize_mod():
    return load_script("customize-skills-for-project.py")


@pytest.fixture
def stats():
    """Fresh deploy stats dict matching deploy_grok_to_project.main()."""
    return {
        "new": 0,
        "updated": 0,
        "unchanged": 0,
        "conflict": 0,
        "skipped": 0,
        "overwritten": 0,
        "merged": 0,
    }


@pytest.fixture
def target(tmp_path):
    """An empty target project dir."""
    t = tmp_path / "target"
    t.mkdir()
    return t

"""Public product defaults for remote version / wheel URLs."""

from __future__ import annotations

import os

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hatch_template import template_is_vcs_tracked
from orchestrator_cli.remote_version import (
    DEFAULT_GITHUB_REPO,
    _repo,
    release_wheel_url,
)


def test_default_repo_is_public_product() -> None:
    old = os.environ.pop("ORCHESTRATOR_GITHUB_REPO", None)
    try:
        assert DEFAULT_GITHUB_REPO == "ndestates/orchestrator-memory"
        assert _repo() == "ndestates/orchestrator-memory"
    finally:
        if old is not None:
            os.environ["ORCHESTRATOR_GITHUB_REPO"] = old


def test_maintainer_can_override_factory_repo() -> None:
    old = os.environ.get("ORCHESTRATOR_GITHUB_REPO")
    os.environ["ORCHESTRATOR_GITHUB_REPO"] = "ndestates/orchestrator"
    try:
        assert _repo() == "ndestates/orchestrator"
        assert release_wheel_url("3.0.0") == (
            "https://github.com/ndestates/orchestrator/releases/download/"
            "v3.0.0/orchestrator-3.0.0-py3-none-any.whl"
        )
    finally:
        if old is None:
            os.environ.pop("ORCHESTRATOR_GITHUB_REPO", None)
        else:
            os.environ["ORCHESTRATOR_GITHUB_REPO"] = old


def test_public_template_is_tracked_so_wheel_skips_force_include() -> None:
    dest = ROOT / "src" / "orchestrator_cli" / "template"
    assert template_is_vcs_tracked(ROOT, dest) is True


def test_release_wheel_url_matches_version() -> None:
    old = os.environ.pop("ORCHESTRATOR_GITHUB_REPO", None)
    try:
        assert release_wheel_url("3.0.0") == (
            "https://github.com/ndestates/orchestrator-memory/releases/download/"
            "v3.0.0/orchestrator-3.0.0-py3-none-any.whl"
        )
    finally:
        if old is not None:
            os.environ["ORCHESTRATOR_GITHUB_REPO"] = old

"""Tests for ci-branch-readiness.py trigger matching."""

from __future__ import annotations

import sys
from pathlib import Path

import importlib.util

SCRIPT = Path(__file__).resolve().parents[1] / ".grok/skills/github-ci-readiness-expert/scripts/ci-branch-readiness.py"
_spec = importlib.util.spec_from_file_location("ci_branch_readiness", SCRIPT)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

glob_branch_match = _mod.glob_branch_match
pr_triggers = _mod.pr_triggers
push_triggers = _mod.push_triggers
workflow_on_block = _mod.workflow_on_block


def test_glob_feature_branch():
    assert glob_branch_match("feature/**", "feature/foo-bar")
    assert not glob_branch_match("develop", "feature/foo")


def test_push_feature_trigger():
    on = {"push": {"branches": ["develop", "feature/**"]}}
    ok, _ = push_triggers(on, "feature/test")
    assert ok


def test_pr_to_develop():
    on = {"pull_request": {"branches": ["develop", "master"]}}
    ok, detail = pr_triggers(on, "feature/x", "develop")
    assert ok
    assert "develop" in detail


def test_workflow_on_true_key():
    data = {True: {"push": {"branches": ["main"]}}, "name": "CI", "jobs": {}}
    on = workflow_on_block(data)
    ok, _ = push_triggers(on, "main")
    assert ok
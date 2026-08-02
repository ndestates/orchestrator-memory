"""Tests for scripts/lint-skill-descriptions.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lint-skill-descriptions.py"


def _load():
    spec = importlib.util.spec_from_file_location("lint_skill_descriptions", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lint():
    return _load()


def test_shorten_under_budget(lint):
    s = "Short skill description for tests."
    assert lint.shorten_description(s, 220) == s


def test_shorten_first_sentence(lint):
    long = (
        "Does the thing well for many platforms and frameworks. "
        "Also has a lot of extra detail that should not be injected into the catalog "
        "because it would bloat every Grok system_reminder turn dramatically over time."
    )
    out = lint.shorten_description(long, 220)
    assert len(out) <= 220
    assert out.startswith("Does the thing well")


def test_shorten_hard_truncate(lint):
    long = "word " * 200
    out = lint.shorten_description(long, 80)
    assert len(out) <= 80
    assert out.endswith("…")


def test_format_description_yaml_safe(lint):
    line = lint._format_description_line('Web build & design lead: portals.')
    assert line.startswith('description: "')
    assert "&" in line
    assert line.strip().endswith('"')


def test_repo_skills_pass_budget(lint):
    """Template .grok/skills must stay within the description budget."""
    paths = sorted((ROOT / ".grok" / "skills").rglob("SKILL.md"))
    assert paths, "expected skills"
    max_chars = lint._load_max_chars(ROOT, None)
    failures = []
    for path in paths:
        f = lint.scan_skill(path, max_chars)
        if f and f.get("severity") == "critical":
            failures.append(f"{path.relative_to(ROOT)}: {f['length']} > {max_chars}")
    assert not failures, "description budget violations:\n" + "\n".join(failures[:20])

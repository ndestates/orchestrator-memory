"""Tests for split registry compose (Option B)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.registry_compose import (  # noqa: E402
    compose_registry,
    extract_app_overlay,
    merge_chains,
    merge_skills,
    split_monolithic,
    write_composed,
)


def test_split_orchestrator_matches_monolith():
    """registry.yaml must equal compose(template, app).

    Failures mean someone edited registry.yaml without updating
    registry.template.yaml (or vice versa). Fix: edit the template,
    then run ``python3 scripts/compose-registry.py``.
    """
    root = Path(__file__).resolve().parents[1]
    mono = yaml.safe_load((root / "chains/registry.yaml").read_text(encoding="utf-8"))
    template = yaml.safe_load((root / "chains/registry.template.yaml").read_text(encoding="utf-8"))
    app = yaml.safe_load((root / "chains/registry.app.yaml").read_text(encoding="utf-8"))
    composed = compose_registry(template, app)
    mono_skills = {s["id"] for s in mono["skills"]}
    comp_skills = {s["id"] for s in composed["skills"]}
    mono_chains = {c["id"] for c in mono["chains"]}
    comp_chains = {c["id"] for c in composed["chains"]}
    if mono_skills != comp_skills:
        raise AssertionError(
            "skills mismatch (edit registry.template.yaml + compose-registry.py):\n"
            f"  only in registry.yaml: {sorted(mono_skills - comp_skills)}\n"
            f"  only in compose(template,app): {sorted(comp_skills - mono_skills)}"
        )
    if mono_chains != comp_chains:
        raise AssertionError(
            "chains mismatch (edit registry.template.yaml + compose-registry.py):\n"
            f"  only in registry.yaml: {sorted(mono_chains - comp_chains)}\n"
            f"  only in compose(template,app): {sorted(comp_chains - mono_chains)}"
        )


def test_app_overlay_wins_on_skill_id():
    template = {"version": 2, "skills": [{"id": "a", "tier": "shared"}], "chains": []}
    app = {"version": 2, "skills": [{"id": "a", "tier": "app", "path": ".grok/skills/a/SKILL.md"}], "chains": []}
    merged = compose_registry(template, app)
    assert merged["skills"][0]["tier"] == "app"


def test_app_chain_override():
    template = {
        "version": 2,
        "skills": [],
        "chains": [{"id": "session-start", "steps": [{"invoke": "load-project-cache-first"}]}],
    }
    app = {
        "version": 2,
        "skills": [],
        "chains": [{"id": "session-start", "tier": "app", "steps": [{"invoke": "daily-standup"}]}],
    }
    merged = compose_registry(template, app)
    assert merged["chains"][0]["steps"][0]["invoke"] == "daily-standup"


def test_extract_app_only_skills():
    template = {
        "version": 2,
        "skills": [{"id": "chain", "tier": "orchestrator"}],
        "chains": [{"id": "session-start", "steps": []}],
    }
    target = {
        "version": 2,
        "skills": [
            {"id": "chain", "tier": "orchestrator"},
            {"id": "google-stats-ops", "tier": "app", "path": ".grok/skills/google-stats-ops/SKILL.md"},
            {"id": "custom-skill", "path": ".grok/skills/custom-skill/SKILL.md"},
        ],
        "chains": [{"id": "session-start", "steps": [{"invoke": "daily-standup"}]}],
    }
    overlay = extract_app_overlay(target, template)
    ids = {s["id"] for s in overlay["skills"]}
    assert "google-stats-ops" in ids
    assert "custom-skill" in ids
    assert "chain" not in ids
    assert len(overlay["chains"]) == 1


def test_skills_only_overlay_has_no_chains():
    template = {
        "version": 2,
        "skills": [{"id": "chain", "tier": "orchestrator"}],
        "chains": [{"id": "session-start", "steps": [{"invoke": "a"}]}],
    }
    target = {
        "version": 2,
        "skills": [{"id": "lightstone-expert-agent", "tier": "app"}],
        "chains": [{"id": "session-start", "steps": [{"invoke": "b"}]}],
    }
    overlay = extract_app_overlay(target, template)
    overlay["chains"] = []
    merged = compose_registry(template, overlay)
    assert merged["chains"][0]["steps"][0]["invoke"] == "a"
    assert any(s["id"] == "lightstone-expert-agent" for s in merged["skills"])


def test_write_composed_roundtrip(tmp_path):
    chains = tmp_path / "chains"
    chains.mkdir()
    (chains / "registry.template.yaml").write_text(
        yaml.dump({"version": 2, "skills": [{"id": "x", "tier": "shared"}], "chains": []}),
        encoding="utf-8",
    )
    (chains / "registry.app.yaml").write_text(
        yaml.dump({"version": 2, "skills": [{"id": "y", "tier": "app"}], "chains": []}),
        encoding="utf-8",
    )
    write_composed(chains)
    out = yaml.safe_load((chains / "registry.yaml").read_text(encoding="utf-8"))
    assert {s["id"] for s in out["skills"]} == {"x", "y"}
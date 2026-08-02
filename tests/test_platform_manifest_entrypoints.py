"""Project-manifest + per-host entrypoints for every AI platform surface.

Guarantees:
1. Each host has a project-manifest.yaml that parses and matches the canonical body.
2. Each host has a session-start entrypoint under *its* tree (not a sibling host).
3. Entrypoints name the correct surface root so models do not load the wrong tools.
4. Manifest identity engine can evaluate this repo (orchestrator source = ok).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine import manifest_sync as ms  # noqa: E402
from _engine.manifest_identity import check_manifest_identity  # noqa: E402
from _engine.platform_surface import PLATFORM_SURFACES, surface_for  # noqa: E402

# Host id → files that must exist as that host's session-context entrypoint(s)
HOST_ENTRYPOINTS: dict[str, tuple[str, ...]] = {
    "grok": (".grok/skills/session-context-envelope/SKILL.md",),
    "claude": (
        ".claude/commands/session-context-envelope.md",
        "CLAUDE.md",  # top-level Claude instruction surface
    ),
    "copilot": (
        ".github/skills/session-context-envelope/SKILL.md",
        ".github/copilot-instructions.md",
        ".copilot/skills/session-context-envelope/SKILL.md",
    ),
    "gemini": (
        ".gemini/prompts/session-context-envelope.md",
        ".gemini/instructions/gemini-orchestrator-instructions.md",
    ),
    "cursor": (
        ".cursor/rules/session-context-envelope.mdc",
        ".cursor/README.md",
    ),
    "chatgpt": (
        ".chatgpt/prompts/session-context-envelope.md",
        ".chatgpt/instructions/chatgpt-orchestrator-instructions.md",
        ".chatgpt/README.md",
        ".chatgpt/mcp.chatgpt.example.json",
    ),
}

# Phrases that pin the host (at least one must appear in the primary entrypoint)
HOST_PIN_MARKERS: dict[str, tuple[str, ...]] = {
    "grok": (".grok", "Grok", "THIS SURFACE IS GROK"),
    "claude": (".claude", "Claude", "THIS SURFACE IS CLAUDE"),
    "copilot": (".github", "Copilot", "THIS SURFACE IS GITHUB", "GitHub Copilot"),
    "gemini": (".gemini", "Gemini", "THIS SURFACE IS GEMINI"),
    "cursor": (".cursor", "Cursor", "THIS SURFACE IS CURSOR"),
    "chatgpt": (".chatgpt", "ChatGPT", "THIS SURFACE IS CHATGPT", "OpenAI"),
}

REQUIRED_MANIFEST_TOP_KEYS = (
    "project",
    "stack",
    "runtime",
    "paths",
    "token_policy",
)


def _read(rel: str) -> str:
    path = REPO_ROOT / rel
    assert path.is_file(), f"missing required path: {rel}"
    return path.read_text(encoding="utf-8", errors="replace")


@pytest.mark.parametrize("host_id", sorted(PLATFORM_SURFACES.keys()))
def test_platform_surface_manifest_path_exists(host_id: str):
    surf = surface_for(host_id)
    rel = surf["manifest"]
    path = REPO_ROOT / rel
    assert path.is_file(), f"{host_id}: missing manifest {rel}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{host_id}: manifest is not a mapping"
    for key in REQUIRED_MANIFEST_TOP_KEYS:
        assert key in data, f"{host_id}: manifest missing top-level key {key!r}"


@pytest.mark.parametrize("host_id", sorted(PLATFORM_SURFACES.keys()))
def test_platform_manifest_body_matches_canonical(host_id: str):
    """Policy body must stay synced across hosts (header may differ)."""
    surf = surface_for(host_id)
    rel = surf["manifest"]
    body = ms.extract_manifest_body(_read(rel))
    canonical = ms.extract_manifest_body(_read(ms.CANONICAL_REL))
    assert body == canonical, f"{host_id}: {rel} body drifted from {ms.CANONICAL_REL}"


def test_all_manifest_sync_targets_present():
    """manifest_sync targets (full set) exist on the template."""
    for rel, _label in ms.MANIFEST_TARGETS:
        assert (REPO_ROOT / rel).is_file(), f"missing sync target {rel}"


@pytest.mark.parametrize("host_id", sorted(HOST_ENTRYPOINTS.keys()))
def test_host_session_entrypoints_exist(host_id: str):
    for rel in HOST_ENTRYPOINTS[host_id]:
        assert (REPO_ROOT / rel).is_file(), f"{host_id}: missing entrypoint {rel}"


@pytest.mark.parametrize("host_id", sorted(HOST_ENTRYPOINTS.keys()))
def test_host_entrypoint_pins_correct_surface(host_id: str):
    """Primary entrypoint must tell the model to use this host's tree."""
    primary = HOST_ENTRYPOINTS[host_id][0]
    text = _read(primary)
    markers = HOST_PIN_MARKERS[host_id]
    assert any(m in text for m in markers), (
        f"{host_id}: {primary} must mention surface pin among {markers!r}"
    )
    # Must point at shared session script
    assert "session-context-envelope.py" in text, (
        f"{host_id}: {primary} must invoke session-context-envelope.py"
    )
    # Must not exclusively point models at a *different* host as primary
    # (shared docs paths are fine; wrong primary tree as sole instruction is not)
    surf = surface_for(host_id)
    root = surf["root"]
    assert root in text or root.lstrip(".") in text or host_id in text.lower(), (
        f"{host_id}: entrypoint should name surface root {root!r}"
    )


@pytest.mark.parametrize("host_id", sorted(PLATFORM_SURFACES.keys()))
def test_surface_skills_dir_exists(host_id: str):
    surf = surface_for(host_id)
    skills_rel = surf.get("skills")
    if not skills_rel:
        pytest.skip("no skills path")
    path = REPO_ROOT / skills_rel
    assert path.is_dir(), f"{host_id}: skills/commands dir missing: {skills_rel}"


def test_platform_surfaces_doc_lists_all_hosts():
    doc = _read("docs/reference/platform-surfaces.md")
    for host_id, surf in PLATFORM_SURFACES.items():
        assert surf["root"] in doc, f"platform-surfaces.md missing root {surf['root']}"
        assert host_id in doc.lower() or surf["label"].split()[0] in doc


def test_manifest_identity_orchestrator_source_ok():
    result = check_manifest_identity(REPO_ROOT)
    assert result["status"] == "ok"
    assert result["ok"] is True
    assert result["is_orchestrator_source"] is True
    assert result.get("manifest_path")


def test_check_project_manifest_cli_ok():
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check-project-manifest.py"), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    import json

    data = json.loads(proc.stdout)
    assert data["status"] == "ok"


def test_envelope_emits_surface_fields():
    from _engine.session_envelope import format_compact

    env = {
        "v": 1,
        "project": "demo",
        "template_version": "1.8.3",
        "identity": "ok",
        "mcp": "yes",
        "mcp_policy": "off",
        "mcp_env_safe": "yes",
        "sec": "PASS",
        "vault": "OK",
        "platform": "claude",
        "surface_root": ".claude",
        "surface_manifest": ".claude/project-manifest.yaml",
        "stack": "generic@local",
        "branch": "feature/x",
        "sync": "up_to_date",
        "behind_develop": "0",
        "resume_first": "no",
        "max_cache_files": 0,
        "pickup_offer": "no",
        "operator_last_branch": "none",
        "operator_resume_match": "yes",
        "continue_target": "feature/x",
        "pickup_ask": "On `feature/x` — no alternate last-branch offer [stay]",
        "open": [],
        "next": "work",
        "expand": [],
        "ptrs": {},
    }
    text = format_compact(env)
    assert "surface platform=claude" in text
    assert "root=.claude" in text
    assert "manifest=.claude/project-manifest.yaml" in text
    assert "USE THIS TREE" in text


def test_host_entrypoints_live_under_correct_tree():
    """Primary session entrypoint path must sit under that host's surface root."""
    expected_prefix = {
        "grok": ".grok/",
        "claude": ".claude/",
        "copilot": ".github/",
        "gemini": ".gemini/",
        "cursor": ".cursor/",
        "chatgpt": ".chatgpt/",
    }
    for host_id, paths in HOST_ENTRYPOINTS.items():
        primary = paths[0]
        prefix = expected_prefix[host_id]
        assert primary.startswith(prefix), (
            f"{host_id}: primary entrypoint {primary!r} must start with {prefix!r}"
        )

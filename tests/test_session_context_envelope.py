"""Tests for session-context-envelope (multi-platform spin-up)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.session_envelope import build_envelope, format_compact  # noqa: E402


def test_build_envelope_on_orchestrator():
    # Report-only: do not mutate the developer's checkout during unit tests
    env = build_envelope(REPO_ROOT, apply_remote_last=False)
    assert env["v"] == 1
    assert env["identity"] == "ok"
    assert env["mcp_policy"] == "off"
    assert env["branch"]
    assert env.get("template_version")
    assert "pickup_offer" in env
    assert "pickup_ask" in env
    assert "briefing_compact" in env
    assert env.get("auto_switch_policy") == "remote_last_when_clean" or env.get(
        "switch_result"
    ) is not None
    compact = env["briefing_compact"]
    assert compact.startswith("CTX v1")
    assert "identity=" in compact
    assert "mcp=" in compact
    assert "pickup" in compact
    assert "ask:" in compact
    assert "ver=" in compact
    assert "surface" in compact
    assert "switch applied=" in compact
    assert "AUTO-SWITCH" in compact or "auto_remote_last" in compact
    assert env.get("surface_root") or env.get("platform")
    assert "orch kind=" in compact
    # Multi-workstream Phase 2 (registry optional but present on this repo)
    assert "ws " in compact or "ws primary=" in compact or "ws present=" in compact
    # Token budget target: compact under ~900 tokens after policy + orch lines
    assert len(compact) < 3800


def test_format_compact_stable_keys():
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
        "stack": "laravel@ddev",
        "branch": "feature/x",
        "sync": "up_to_date",
        "behind_develop": "0",
        "resume_first": "yes",
        "max_cache_files": 0,
        "pickup_offer": "yes",
        "operator_last_branch": "feature/prior",
        "operator_resume_match": "no",
        "continue_target": "feature/prior",
        "pickup_ask": "Pick up where you left off on `feature/prior`? [continue=feature/prior | stay=feature/x]",
        "open": ["ship it"],
        "next": "ship it",
        "expand": ["pickup"],
        "ptrs": {"todo": "TODO/x.md"},
    }
    text = format_compact(env)
    assert "project=demo" in text
    assert "ver=1.8.3" in text
    assert "pickup offer=yes" in text
    assert "ask:" in text
    assert "expand: pickup" in text


def test_cli_writes_artifacts():
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "session-context-envelope.py"),
            "--write",
            "--no-apply",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "CTX v1" in proc.stdout
    txt = REPO_ROOT / "reports" / "sessions" / "context-latest.txt"
    js = REPO_ROOT / "reports" / "sessions" / "context-latest.json"
    assert txt.is_file()
    assert js.is_file()
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data.get("mcp_policy") == "off"
    assert "switch applied=" in (txt.read_text(encoding="utf-8"))


def test_platform_pointers_exist():
    """All target platforms ship a thin entry pointing at the same script."""
    required = [
        REPO_ROOT / ".grok" / "skills" / "session-context-envelope" / "SKILL.md",
        REPO_ROOT / ".claude" / "commands" / "session-context-envelope.md",
        REPO_ROOT / ".copilot" / "skills" / "session-context-envelope" / "SKILL.md",
        REPO_ROOT / ".github" / "skills" / "session-context-envelope" / "SKILL.md",
        REPO_ROOT / ".gemini" / "prompts" / "session-context-envelope.md",
        REPO_ROOT / ".cursor" / "rules" / "session-context-envelope.mdc",
        REPO_ROOT / "docs" / "reference" / "session-context-token-budget.md",
    ]
    for path in required:
        assert path.is_file(), f"missing platform pointer: {path}"
        text = path.read_text(encoding="utf-8")
        assert "session-context-envelope" in text


def test_multi_workstream_platform_pointers_exist():
    """Multi-workstream + Phase 2 ws line on every AI surface."""
    required = [
        REPO_ROOT / ".grok" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".claude" / "commands" / "multi-workstream.md",
        REPO_ROOT / ".copilot" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".github" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".gemini" / "prompts" / "multi-workstream.md",
        REPO_ROOT / ".cursor" / "rules" / "multi-workstream.mdc",
        REPO_ROOT / ".chatgpt" / "prompts" / "multi-workstream.md",
        REPO_ROOT / "scripts" / "workstream.py",
        REPO_ROOT / "reports" / "sessions" / "workstreams.yaml",
        REPO_ROOT / "docs" / "guides" / "multi-workstream" / "IMPLEMENTATION.md",
        REPO_ROOT / "scripts" / "sync-multi-workstream-surfaces.py",
    ]
    for path in required:
        assert path.is_file(), f"missing multi-workstream surface: {path}"
    brief = subprocess.run(
        [sys.executable, str(SCRIPTS / "workstream.py"), "brief"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert brief.returncode == 0, brief.stderr
    assert "ws primary=" in brief.stdout


def test_multi_workstream_surfaces_in_sync():
    """All host procedures share the same implementation body."""
    sync = REPO_ROOT / "scripts" / "sync-multi-workstream-surfaces.py"
    proc = subprocess.run(
        [sys.executable, str(sync), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    # Shared slash map present on every surface
    surfaces = [
        REPO_ROOT / ".grok" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".claude" / "commands" / "multi-workstream.md",
        REPO_ROOT / ".github" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".copilot" / "skills" / "multi-workstream" / "SKILL.md",
        REPO_ROOT / ".chatgpt" / "prompts" / "multi-workstream.md",
        REPO_ROOT / ".gemini" / "prompts" / "multi-workstream.md",
        REPO_ROOT / ".cursor" / "rules" / "multi-workstream.mdc",
    ]
    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert "/multi-workstream list" in text
        assert "/multi-workstream example" in text
        assert "python3 scripts/workstream.py list" in text
        assert "Same implementation on every AI host" in text

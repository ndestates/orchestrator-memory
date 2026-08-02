"""Platform surface map — each host uses its own tool tree."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.platform_surface import (  # noqa: E402
    PLATFORM_SURFACES,
    detect_platform,
    platform_brief,
    surface_for,
)


def test_all_hosts_mapped():
    for key in ("grok", "claude", "copilot", "gemini", "cursor", "chatgpt"):
        assert key in PLATFORM_SURFACES
        s = surface_for(key)
        assert s["root"].startswith(".")
        assert "manifest" in s


def test_detect_explicit_env():
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "claude"}) == "claude"
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "grok"}) == "grok"
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "github-copilot"}) == "copilot"
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "chatgpt"}) == "chatgpt"
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "codex"}) == "chatgpt"
    assert detect_platform({"ORCHESTRATOR_AI_PLATFORM": "openai"}) == "chatgpt"


def test_detect_hints():
    assert detect_platform({"CLAUDE_CODE": "1"}) == "claude"
    assert detect_platform({"CURSOR_TRACE_ID": "abc"}) == "cursor"
    assert detect_platform({"CHATGPT_CODEX": "1"}) == "chatgpt"
    assert detect_platform({"CODEX_HOME": "/tmp/codex"}) == "chatgpt"


def test_brief_unknown():
    b = platform_brief({})
    assert b["platform"] == "unknown"
    assert "surface" in b["briefing_line"] or "root" in b["briefing_line"]


def test_grok_does_not_prefer_claude():
    s = surface_for("grok")
    assert ".claude" in s["do_not_prefer"]
    assert ".chatgpt" in s["do_not_prefer"]
    assert s["root"] == ".grok"


def test_chatgpt_surface():
    s = surface_for("chatgpt")
    assert s["root"] == ".chatgpt"
    assert s["manifest"] == ".chatgpt/project-manifest.yaml"
    assert ".grok" in s["do_not_prefer"]
    assert s.get("mcp")

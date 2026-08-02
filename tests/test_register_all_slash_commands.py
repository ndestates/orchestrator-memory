"""Smoke tests for multi-surface slash registration helpers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _engine.roots import set_template_root

set_template_root(ROOT)

from _engine.sync_grok import claude_command_name  # noqa: E402


def test_claude_command_name_defaults_and_aliases():
    assert claude_command_name("chain") == "chain"
    assert claude_command_name("always-on-memory") == "always-on-memory"
    assert claude_command_name("laravel-expert-agent") == "laravel-expert"
    assert claude_command_name("copilot-instructions") is None
    assert claude_command_name("eval/maintenance-task") == "eval-maintenance-task"


def test_slash_catalog_exists_and_session_canonical():
    cat = ROOT / "chains" / "slash-catalog.yaml"
    assert cat.is_file(), "run python3 scripts/register-all-slash-commands.py"
    text = cat.read_text(encoding="utf-8")
    assert "canonical_session: /chain session-start" in text or "/chain session-start" in text
    assert (ROOT / ".claude" / "commands" / "chain.md").is_file()
    assert (ROOT / ".cursor" / "commands" / "chain.md").is_file()

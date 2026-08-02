"""Smoke client helpers + optional live stdio smoke when package is importable."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "mcp-server" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from orchestrator_mcp.smoke import _resolve_root, _server_command  # noqa: E402


def test_resolve_root_explicit(tmp_path: Path):
    assert _resolve_root(str(tmp_path)) == tmp_path.resolve()


def test_server_command_prefers_venv_or_module(tmp_path: Path):
    cmd, args = _server_command(tmp_path)
    assert "--transport" in args
    assert "stdio" in args
    assert str(tmp_path) in args or any(str(tmp_path) in a for a in args)
    assert cmd  # non-empty


def test_live_stdio_smoke():
    """Full handshake — skipped if mcp package or server deps missing."""
    pytest.importorskip("mcp")
    from orchestrator_mcp.smoke import run_smoke
    import asyncio

    result = asyncio.run(run_smoke(ROOT, quiet=True))
    assert result.get("ok") is True, result
    assert result.get("has_health_check") is True
    assert result.get("tool_count", 0) >= 1
    assert "health_check" in (result.get("tools") or [])

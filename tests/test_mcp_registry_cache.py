"""Phase B BH-003: MCP load_chains_registry mtime cache + id index."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mcp-server" / "src"))

from orchestrator_mcp import helpers as h  # noqa: E402


def test_registry_cache_hit_and_chain_by_id():
    h.clear_registry_cache()
    root = REPO
    r1 = h.load_chains_registry(root)
    assert r1.get("chains"), "expected chains in registry"
    r2 = h.load_chains_registry(root)
    assert r1 is r2  # same cached object

    chain = h.get_chain_by_id(root, "session-start")
    assert chain is not None
    assert chain.get("id") == "session-start"
    assert h.get_chain_by_id(root, "no-such-chain-xyz") is None


def test_clear_registry_cache():
    h.clear_registry_cache()
    a = h.load_chains_registry(REPO)
    h.clear_registry_cache(REPO)
    b = h.load_chains_registry(REPO)
    assert a is not b
    assert a.get("chains") and b.get("chains")

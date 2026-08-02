"""Security tests for the orchestrator MCP server.

Covers the path sandbox allowlist integrity (CONCERNS §7 risk 1), bearer auth
semantics, and the fail-closed HTTP startup gate (risk 2). These import only the
sandbox/auth/config modules so they run without the optional ``mcp`` runtime;
the HTTP-gate test importorskips when ``mcp`` is absent.
"""

from __future__ import annotations

import pytest

from orchestrator_mcp.auth import make_bearer_verifier
from orchestrator_mcp.config import is_loopback_host
from orchestrator_mcp.sandbox import (
    SandboxError,
    assert_readable,
    read_bounded,
    resolve_audit_script,
)


def _make_root(tmp_path):
    cache = tmp_path / "docs" / "codebase"
    cache.mkdir(parents=True)
    (cache / "README.md").write_text("ok", encoding="utf-8")
    return tmp_path


# --- Sandbox allowlist integrity (risk 1) -------------------------------------

@pytest.mark.parametrize(
    "denied",
    [
        ".env",                       # secrets must never be readable
        ".env.local",
        ".git/config",                # VCS internals not allowlisted
        "config/secrets.yaml",        # arbitrary top-level dir
        "app/Models/User.php",        # host-app source
        "../outside.txt",             # path traversal escape
        "docs/codebase/../../.env",   # traversal via allowed prefix
    ],
)
def test_sandbox_denies_sensitive_and_escaping_paths(tmp_path, denied):
    root = _make_root(tmp_path)
    with pytest.raises(SandboxError):
        assert_readable(root, denied)


def test_sandbox_denies_symlink_escape(tmp_path):
    root = _make_root(tmp_path)
    secret = tmp_path.parent / "secret-outside-root.txt"
    secret.write_text("topsecret", encoding="utf-8")
    link = root / "docs" / "codebase" / "leak"
    link.symlink_to(secret)
    with pytest.raises(SandboxError):
        assert_readable(root, "docs/codebase/leak")


def test_sandbox_allows_allowlisted_cache(tmp_path):
    root = _make_root(tmp_path)
    assert read_bounded(root, "docs/codebase/README.md", 1024) == "ok"


def test_read_bounded_truncates_large_files(tmp_path):
    root = _make_root(tmp_path)
    (root / "docs" / "codebase" / "big.md").write_text("x" * 100, encoding="utf-8")
    out = read_bounded(root, "docs/codebase/big.md", 10)
    assert out.startswith("x" * 10)
    assert "truncated at 10 bytes" in out


def test_resolve_audit_rejects_unknown_script(tmp_path):
    with pytest.raises(SandboxError):
        resolve_audit_script(tmp_path, "rm-rf")


# --- Bearer auth semantics (risk 2) -------------------------------------------

def test_bearer_no_key_allows_all():
    verify = make_bearer_verifier(None)
    assert verify(None) is True
    assert verify("anything") is True


def test_bearer_with_key_rejects_missing_or_wrong():
    verify = make_bearer_verifier("s3cret")
    assert verify(None) is False
    assert verify("") is False
    assert verify("wrong") is False
    assert verify("s3cret") is True


def test_loopback_classification():
    assert is_loopback_host("127.0.0.1")
    assert is_loopback_host("localhost")
    assert is_loopback_host("::1")
    assert not is_loopback_host("0.0.0.0")      # binds all interfaces
    assert not is_loopback_host("192.168.1.10")


# --- Fail-closed HTTP startup gate (risk 2) -----------------------------------

def test_http_gate_fails_closed_without_key(monkeypatch, tmp_path):
    pytest.importorskip("mcp.server.fastmcp")
    monkeypatch.delenv("ORCHESTRATOR_MCP_API_KEY", raising=False)
    from orchestrator_mcp import config, server

    server._config = config.load_server_config(_make_root(tmp_path))
    assert server._config.api_key is None

    # Non-loopback without a key: always refuse.
    with pytest.raises(SystemExit):
        server._run_http("0.0.0.0", 8090, allow_insecure=False)

    # Loopback without a key and without explicit opt-in: refuse.
    with pytest.raises(SystemExit):
        server._run_http("127.0.0.1", 8090, allow_insecure=False)

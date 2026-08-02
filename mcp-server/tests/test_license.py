"""Tests for the Phase 2 license gate.

No network and no real clock: ``urlopen`` and ``now`` are injected. Covers the
fail-open default (dev needs no license server), lease caching, expiry ->
revalidate, and deny paths (server rejection / transport error).
"""

from __future__ import annotations

import io
import json

import pytest

from orchestrator_mcp.license import LicenseError, LicenseGate


class _FakeResponse:
    """Minimal context-manager response exposing ``read``."""

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return io.BytesIO(self._body)

    def __exit__(self, *exc):
        return False


def _stub(payload: dict, *, calls: list | None = None):
    def urlopen(request, timeout=None):
        if calls is not None:
            calls.append(request)
        return _FakeResponse(payload)

    return urlopen


def test_disabled_gate_allows_without_url():
    # Dev default: no license URL -> gate off, check() allows, no network.
    gate = LicenseGate(url=None, key=None, lease_ttl=10, urlopen=_stub({}))
    assert gate.enabled is False
    assert gate.check() is True
    assert gate.validate() is None


def test_validate_stores_lease_and_caps_ttl():
    clock = {"t": 1000.0}
    calls: list = []
    gate = LicenseGate(
        url="https://lic.example/validate",
        key="k",
        lease_ttl=100,
        urlopen=_stub({"valid": True, "lease_token": "abc", "ttl": 30, "is_first_party": True}, calls=calls),
        now=lambda: clock["t"],
    )
    lease = gate.validate()
    assert lease is not None
    assert lease.token == "abc"
    assert lease.expires_at == 1030.0  # min(lease_ttl=100, server ttl=30)
    assert lease.is_first_party is True
    assert len(calls) == 1


def test_check_caches_lease_then_revalidates_on_expiry():
    clock = {"t": 1000.0}
    calls: list = []
    gate = LicenseGate(
        url="https://lic.example/validate",
        key="k",
        lease_ttl=50,
        urlopen=_stub({"valid": True, "lease_token": "abc"}, calls=calls),
        now=lambda: clock["t"],
    )
    assert gate.check() is True  # first call validates
    assert gate.check() is True  # cached, no new call
    assert len(calls) == 1
    clock["t"] = 1100.0  # past expiry (1000 + 50)
    assert gate.check() is True  # revalidates
    assert len(calls) == 2


def test_server_rejection_denies():
    gate = LicenseGate(
        url="https://lic.example/validate",
        key="k",
        lease_ttl=50,
        urlopen=_stub({"valid": False}),
    )
    with pytest.raises(LicenseError):
        gate.check()


def test_transport_error_denies():
    def boom(request, timeout=None):
        raise OSError("connection refused")

    gate = LicenseGate(
        url="https://lic.example/validate",
        key="k",
        lease_ttl=50,
        urlopen=boom,
    )
    with pytest.raises(LicenseError):
        gate.validate()


def test_tool_handler_denies_when_gate_configured(monkeypatch):
    # Wiring: a configured-but-failing gate turns a tool call into a ValueError;
    # the default disabled gate lets the same tool run (dev unaffected).
    server = pytest.importorskip("orchestrator_mcp.server")

    def boom(request, timeout=None):
        raise OSError("no license server")

    denying = LicenseGate("https://lic.example/validate", "k", 50, urlopen=boom)
    monkeypatch.setattr(server, "_license", denying)
    with pytest.raises(ValueError, match="license check failed"):
        server.get_project_manifest()

    monkeypatch.setattr(server, "_license", LicenseGate(None, None, 50))
    assert isinstance(server.get_project_manifest(), dict)


def test_first_party_vs_trial_from_payload():
    # First party (ndestates allowlist): is_first_party=True
    gate1 = LicenseGate(
        url="https://lic.example/validate",
        key="first",
        lease_ttl=86400,
        urlopen=_stub({"valid": True, "lease_token": "fp", "ttl": 3600, "is_first_party": True}),
    )
    lease1 = gate1.validate()
    assert lease1.is_first_party is True
    assert not lease1.is_trial

    # Third party trial
    gate2 = LicenseGate(
        url="https://lic.example/validate",
        key="third",
        lease_ttl=86400,
        urlopen=_stub({"valid": True, "lease_token": "tr", "ttl": 86400, "is_first_party": False}),
    )
    lease2 = gate2.validate()
    assert lease2.is_first_party is False
    assert lease2.is_trial

    # Server can deny third party after trial by returning invalid on revalidate
    def after_trial(request, timeout=None):
        return _FakeResponse({"valid": False})
    gate3 = LicenseGate("https://lic.example", "third", 50, urlopen=after_trial)
    with pytest.raises(LicenseError):
        gate3.check()  # would have validated before, but now server denies

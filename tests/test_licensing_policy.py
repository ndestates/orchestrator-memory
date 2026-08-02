"""Tests for unified licensing policy (Phase 1)."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator_cli.license import LicenseError, LicenseGate, Lease
from orchestrator_cli.licensing_policy import (
    EntitlementKind,
    enforce_for_flow,
    evaluate,
    gate_enabled,
    is_dev_exempt,
    resolve_flow_selections,
)


def _init_repo(path: Path, remote: str) -> None:
    if not (path / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", remote],
            cwd=path,
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote],
            cwd=path,
            check=True,
            capture_output=True,
        )


class _Fake(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _stub(payload: dict):
    def urlopen(req, timeout=None):
        return _Fake(json.dumps(payload).encode())

    return urlopen


def test_dev_exempt_in_source_repo(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_URL", raising=False)
    assert is_dev_exempt() is True
    assert gate_enabled() is False


def test_gate_enabled_with_default_url(monkeypatch):
    monkeypatch.setattr(
        "orchestrator_cli.licensing_policy.dev_repo_root",
        lambda: None,
    )
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_URL", raising=False)
    import orchestrator_cli.defaults as defaults_mod

    monkeypatch.setattr(defaults_mod, "DEFAULT_LICENSE_URL", "")
    assert gate_enabled() is False

    monkeypatch.setattr(defaults_mod, "DEFAULT_LICENSE_URL", "https://ex.test/validate")
    assert gate_enabled() is True


def test_first_party_target_skips_network(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "orchestrator_cli.licensing_policy.dev_repo_root",
        lambda: None,
    )
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    _init_repo(tmp_path, "https://github.com/ndestates/app.git")
    ent = enforce_for_flow(tmp_path)
    assert ent.kind == EntitlementKind.FIRST_PARTY
    assert ent.selections is None


def test_light_caps_selections(monkeypatch):
    from orchestrator_cli.licensing_policy import Entitlement
    from orchestrator_cli import defaults

    pro_ent = Entitlement(kind=EntitlementKind.PRO_FULL)
    assert resolve_flow_selections("all", pro_ent) == "all"

    light_ent = Entitlement(
        kind=EntitlementKind.TRIAL_LITE,
        selections=defaults.LIGHT_SELECTIONS,
        lease=Lease(token="t", expires_at=9999999999.0, tier="trial"),
    )
    assert resolve_flow_selections("all", light_ent) == defaults.LIGHT_SELECTIONS
    assert resolve_flow_selections("grok,loops,scripts", light_ent) == defaults.LIGHT_SELECTIONS


def test_pro_allows_user_selections(monkeypatch):
    pro = evaluate(Path("/tmp"))
    pro_ent = type(pro)(
        kind=EntitlementKind.PRO_FULL,
        lease=Lease(token="p", expires_at=9999999999.0, tier="pro"),
    )
    assert resolve_flow_selections("grok,chains", pro_ent) == "grok,chains"


def test_enforce_no_key_is_light(tmp_path, monkeypatch):
    """Gate on + no key → free Light without network."""
    monkeypatch.setattr(
        "orchestrator_cli.licensing_policy.dev_repo_root",
        lambda: None,
    )
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_KEY", raising=False)
    _init_repo(tmp_path, "https://github.com/acme/app.git")
    monkeypatch.setenv("ORCHESTRATOR_LICENSE_URL", "https://ex.test/validate")
    from orchestrator_cli import defaults

    gate = LicenseGate(url="https://ex.test/validate", key=None, lease_ttl=3600)
    ent = enforce_for_flow(tmp_path, gate=gate)
    assert ent.kind == EntitlementKind.TRIAL_LITE
    assert ent.selections == defaults.LIGHT_SELECTIONS


def test_enforce_validates_light_lease(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "orchestrator_cli.licensing_policy.dev_repo_root",
        lambda: None,
    )
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    _init_repo(tmp_path, "https://github.com/acme/app.git")
    monkeypatch.setenv("ORCHESTRATOR_LICENSE_URL", "https://ex.test/validate")
    gate = LicenseGate(
        url="https://ex.test/validate",
        key="trial-key",
        lease_ttl=3600,
        urlopen=_stub(
            {
                "valid": True,
                "lease_token": "tr",
                "ttl": 86400,
                "tier": "trial",
                "allowed_selections": ["grok", "chains", "cache-spine"],
            }
        ),
    )
    ent = enforce_for_flow(tmp_path, gate=gate)
    assert ent.kind == EntitlementKind.TRIAL_LITE
    assert ent.selections == "grok,chains,cache-spine"


def test_enforce_denied_on_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "orchestrator_cli.licensing_policy.dev_repo_root",
        lambda: None,
    )
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DEV", raising=False)
    _init_repo(tmp_path, "https://github.com/acme/app.git")
    gate = LicenseGate(
        url="https://ex.test/validate",
        key="bad-key",
        urlopen=_stub({"valid": False}),
    )
    with pytest.raises(LicenseError):
        enforce_for_flow(tmp_path, gate=gate)


def test_light_alias_expands_via_deploy_bundle(deploy_mod):
    """light/trial aliases expand to free selection set."""
    from orchestrator_cli.licensing_policy import Entitlement, resolve_flow_selections
    from orchestrator_cli import defaults

    light_ent = Entitlement(
        kind=EntitlementKind.TRIAL_LITE, selections=defaults.LIGHT_SELECTIONS
    )
    assert resolve_flow_selections("all", light_ent) == defaults.LIGHT_SELECTIONS
    bundle = deploy_mod.load_bundle()
    for alias in ("light", "trial", "free"):
        expanded = deploy_mod.resolve_selections(bundle, alias)
        assert set(expanded) >= {"grok", "chains", "loops", "scripts", "cache-spine"}
        assert "mcp" not in expanded
        assert "wiki" not in expanded


def test_lease_parses_tier_and_selections():
    gate = LicenseGate(
        url="https://ex.test/validate",
        urlopen=_stub(
            {
                "valid": True,
                "lease_token": "x",
                "ttl": 100,
                "tier": "pro",
                "is_first_party": False,
            }
        ),
    )
    lease = gate.validate()
    assert lease is not None
    assert lease.tier == "pro"
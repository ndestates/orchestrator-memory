"""Unit tests for license validate/issue/revoke server (stdlib)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from orchestrator_cli.license_server import (
    ISSUE_PATH,
    REVOKE_PATH,
    VALIDATE_PATH,
    LicenseStore,
    SqliteLicenseDb,
    extract_key_from_request,
    serve,
)
from orchestrator_cli.license import LicenseGate
from orchestrator_cli import defaults


def test_store_anonymous_light_and_unknown():
    store = LicenseStore(allowlist={"good"}, first_party=set(), dev_accept_any=False)
    # No key → free Light (anonymous)
    anon = store.validate_key(None)
    assert anon["valid"] is True
    assert anon["tier"] == "trial"
    assert anon.get("anonymous_light") is True
    assert "grok" in (anon.get("allowed_selections") or [])

    assert store.validate_key("")["valid"] is True  # empty treated as no key path via falsy
    # empty string is falsy → anonymous light
    assert store.validate_key("bad")["valid"] is False


def test_store_allowlist_and_first_party():
    store = LicenseStore(
        allowlist={"trial-key", "fp-key"},
        first_party={"fp-key"},
        dev_accept_any=False,
        lease_ttl=120,
    )
    trial = store.validate_key("trial-key")
    assert trial["valid"] is True
    assert trial["is_first_party"] is False
    assert trial["tier"] == "trial"
    assert trial["ttl"] == 120
    assert trial["lease_token"]
    assert trial["allowed_selections"]

    fp = store.validate_key("fp-key")
    assert fp["valid"] is True
    assert fp["is_first_party"] is True
    assert fp["tier"] == "pro"
    assert fp["allowed_selections"] is None


def test_store_dev_accept_any():
    store = LicenseStore(allowlist=set(), first_party=set(), dev_accept_any=True)
    out = store.validate_key("anything-local")
    assert out["valid"] is True
    assert out["is_first_party"] is False


def test_store_from_environ_csv(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_LICENSE_ALLOWLIST", "a, b")
    monkeypatch.setenv("ORCHESTRATOR_LICENSE_FIRST_PARTY", "b")
    monkeypatch.setenv("ORCHESTRATOR_LICENSE_DEV_ACCEPT_ANY", "0")
    monkeypatch.delenv("ORCHESTRATOR_LICENSE_DB", raising=False)
    store = LicenseStore.from_environ()
    assert "a" in store.allowlist and "b" in store.allowlist
    assert "b" in store.first_party
    assert store.validate_key("a")["is_first_party"] is False
    assert store.validate_key("b")["is_first_party"] is True


def test_extract_key_bearer_and_body():
    assert extract_key_from_request(headers={"Authorization": "Bearer sk-1"}, body=b"") == "sk-1"
    body = json.dumps({"license_key": "sk-2"}).encode()
    assert extract_key_from_request(headers={}, body=body) == "sk-2"


def test_sqlite_issue_validate_revoke(tmp_path):
    db_path = tmp_path / "licenses.sqlite3"
    store = LicenseStore(
        allowlist=set(),
        first_party=set(),
        db=SqliteLicenseDb(db_path),
        admin_token="admin-secret",
        lease_ttl=100,
        pro_ttl=1000,
    )
    issued = store.issue(tier="pro", email="buyer@example.com", note="£99 company")
    assert issued["ok"] is True
    key = issued["license_key"]
    assert key.startswith("orch_")
    assert issued["scope"] == defaults.LICENSE_SCOPE
    assert issued["price_gbp"] == defaults.LICENSE_PRICE_GBP_MONTHLY
    assert issued["price_gbp_monthly"] == 99
    assert issued["price_gbp_annual"] == 990  # 10× monthly (2 months free)
    assert issued["pricing"]["annual_free_months"] == 2

    ok = store.validate_key(key)
    assert ok["valid"] is True
    assert ok["tier"] == "pro"
    assert ok["ttl"] == 1000

    rev = store.revoke(key=key)
    assert rev["ok"] is True
    assert store.validate_key(key)["valid"] is False
    assert store.validate_key(key)["error"] == "revoked_key"


def test_http_validate_issue_and_cli_gate_roundtrip(tmp_path):
    db_path = tmp_path / "lic.db"
    store = LicenseStore(
        allowlist=set(),
        first_party=set(),
        db=SqliteLicenseDb(db_path),
        admin_token="adm",
        lease_ttl=90,
        pro_ttl=900,
    )
    httpd = serve("127.0.0.1", 0, store=store)
    host, port = httpd.server_address[:2]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://{host}:{port}"
        # anonymous light
        req = urllib.request.Request(
            base + VALIDATE_PATH,
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            payload = json.loads(resp.read().decode())
        assert payload["valid"] is True
        assert payload["tier"] == "trial"

        # issue pro
        body = json.dumps({"tier": "pro", "email": "c@x.test"}).encode()
        req = urllib.request.Request(
            base + ISSUE_PATH,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer adm",
            },
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            issued = json.loads(resp.read().decode())
        key = issued["license_key"]

        # CLI gate
        gate = LicenseGate(
            url=base + VALIDATE_PATH,
            key=key,
            lease_ttl=3600,
        )
        lease = gate.validate()
        assert lease is not None
        assert lease.tier == "pro"

        # revoke
        body = json.dumps({"license_key": key}).encode()
        req = urllib.request.Request(
            base + REVOKE_PATH,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer adm",
            },
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            rev = json.loads(resp.read().decode())
        assert rev["ok"] is True
    finally:
        httpd.shutdown()


def test_issue_requires_admin(tmp_path):
    store = LicenseStore(db=SqliteLicenseDb(tmp_path / "x.db"), admin_token="secret")
    httpd = serve("127.0.0.1", 0, store=store)
    host, port = httpd.server_address[:2]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://{host}:{port}{ISSUE_PATH}",
            data=b'{"tier":"pro"}',
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req, timeout=2)
        assert exc.value.code == 403
    finally:
        httpd.shutdown()

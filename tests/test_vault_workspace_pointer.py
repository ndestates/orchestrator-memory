"""Smoke tests for per-operator vault workspace_pointer events."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts._engine import vault as vmod  # noqa: E402

SCRIPT = REPO_ROOT / "scripts" / "vault-workspace-pointer.py"


def _with_ledger(fn):
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / "events.jsonl"
        fn(ledger)


def test_emit_and_read_latest_per_operator():
    def body(ledger: Path):
        ev1 = vmod.emit_workspace_pointer(
            "feature/alice",
            operator="alice@example.com",
            remote_last="feature/bob",
            ledger_path=ledger,
        )
        ev2 = vmod.emit_workspace_pointer(
            "feature/alice-v2",
            operator="alice@example.com",
            ledger_path=ledger,
        )
        bob = vmod.emit_workspace_pointer(
            "feature/bob",
            operator="bob@example.com",
            ledger_path=ledger,
        )
        assert ev1["type"] == "workspace_pointer"
        assert ev1["payload"].get("startup_policy") == vmod.SESSION_STARTUP_POLICY
        assert "fetch" in (ev1["payload"].get("next_start_order") or "")
        ptr = vmod.get_operator_workspace_pointer(ledger, operator="alice@example.com")
        assert ptr is not None
        assert ptr["payload"]["branch"] == "feature/alice-v2"
        assert ptr["ts"] >= ev1["ts"]
        bob_ptr = vmod.get_operator_workspace_pointer(ledger, operator="bob@example.com")
        assert bob_ptr["payload"]["branch"] == "feature/bob"
        ok, issues = vmod.verify_ledger(ledger)
        assert ok, issues
        assert bob["payload"]["operator"] == "bob@example.com"

    _with_ledger(body)


def test_emit_session_startup_chain():
    def body(ledger: Path):
        a = vmod.emit_session_startup(
            branch="feature/eod",
            remote_last="feature/eod",
            switch_result="already_on",
            switch_applied="yes",
            on_remote_last="yes",
            phase="session-start",
            source="session-start",
            operator="op@test.com",
            ledger_path=ledger,
        )
        b = vmod.emit_session_startup(
            branch="feature/eod",
            remote_last="feature/eod",
            phase="eod-shutdown",
            source="eod-shutdown",
            operator="op@test.com",
            ledger_path=ledger,
            extra={"next_action": "/chain session-start"},
        )
        assert a["type"] == "session_startup"
        assert a["payload"]["startup_policy"] == vmod.SESSION_STARTUP_POLICY
        assert b["payload"]["phase"] == "eod-shutdown"
        latest = vmod.get_latest_session_startup(
            ledger, operator="op@test.com"
        )
        assert latest is not None
        assert latest["payload"]["phase"] == "eod-shutdown"
        start_only = vmod.get_latest_session_startup(
            ledger, operator="op@test.com", phase="session-start"
        )
        assert start_only is not None
        assert start_only["payload"]["switch_result"] == "already_on"
        ok, issues = vmod.verify_ledger(ledger)
        assert ok, issues

    _with_ledger(body)


def test_cli_read_json_none():
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / "events.jsonl"
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--read", "--format", "json", "--ledger", str(ledger), "--operator", "x@y.z"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["status"] == "none"


def test_append_event_skips_duplicate_content_hash():
    """Double-emit of identical pointer must not break verify_ledger (event 40 class of bug)."""

    def body(ledger: Path):
        vmod.clear_ledger_hash_cache(ledger)
        vmod.emit_workspace_pointer(
            "feature/same",
            operator="dup@example.com",
            remote_last="develop",
            subject="same subject",
            ledger_path=ledger,
        )
        vmod.emit_workspace_pointer(
            "feature/same",
            operator="dup@example.com",
            remote_last="develop",
            subject="same subject",
            ledger_path=ledger,
        )
        lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected 1 line after idempotent append, got {len(lines)}"
        ok, issues = vmod.verify_ledger(ledger)
        assert ok, issues

    _with_ledger(body)


def test_append_event_hash_cache_bulk():
    """After first load, bulk appends stay idempotent and do not re-duplicate hashes."""

    def body(ledger: Path):
        vmod.clear_ledger_hash_cache()
        for i in range(30):
            vmod.append_event(
                ledger,
                vmod.emit_lesson_event(
                    f"bulk lesson {i} unique body",
                    source=f"bulk:{i}",
                    parents=[],
                    root=REPO_ROOT,
                ),
            )
        # re-append first lesson (same content_hash) — must no-op
        first = vmod.emit_lesson_event(
            "bulk lesson 0 unique body",
            source="bulk:0",
            parents=[],
            root=REPO_ROOT,
        )
        vmod.append_event(ledger, first)
        lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 30
        ok, issues = vmod.verify_ledger(ledger)
        assert ok, issues

    _with_ledger(body)


def test_loop_compound_imports_from_repo_root():
    """scripts/loop_compound.py must resolve scripts._engine when run as a script (parents[1])."""
    script = REPO_ROOT / "scripts" / "loop_compound.py"
    r = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "Promote loop lessons" in (r.stdout + r.stderr)


def main():
    tests = [
        ("emit_read_per_operator", test_emit_and_read_latest_per_operator),
        ("emit_session_startup_chain", test_emit_session_startup_chain),
        ("cli_read_json_none", test_cli_read_json_none),
        ("append_skips_dup_hash", test_append_event_skips_duplicate_content_hash),
        ("append_hash_cache_bulk", test_append_event_hash_cache_bulk),
        ("loop_compound_import", test_loop_compound_imports_from_repo_root),
    ]
    failures = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:
            print(f"FAIL {name}: {e}")
            failures.append(name)
    if failures:
        sys.exit(1)
    print("\nAll vault workspace pointer tests passed.")


if __name__ == "__main__":
    main()
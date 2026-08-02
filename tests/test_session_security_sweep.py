"""Smoke tests for session-security-sweep + cyber-essentials false-positive guards."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SWEEP = REPO / "scripts" / "session-security-sweep.sh"
CSE = (
    REPO
    / ".grok"
    / "skills"
    / "cyber-security-essentials"
    / "scripts"
    / "cyber-essentials-scan.sh"
)


def test_cyber_essentials_scan_no_self_match() -> None:
    res = subprocess.run(
        ["bash", str(CSE), str(REPO)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    )
    assert res.returncode == 0, res.stderr
    out = res.stdout
    # Must not list the scanner itself as a finding
    assert "cyber-essentials-scan.sh:" not in out
    assert "session-security-sweep.sh:" not in out


def test_session_security_sweep_no_false_cse_warns_on_clean_template() -> None:
    res = subprocess.run(
        ["bash", str(SWEEP), "--active-only", "--no-report", "--force"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    out = res.stdout
    # Parse kv lines
    data = {}
    for line in out.splitlines():
        if "=" in line and not line.startswith("---") and not line.startswith("==="):
            k, _, v = line.partition("=")
            if re.fullmatch(r"[a-z_]+", k):
                data[k] = v
    assert data.get("cse_status") == "ran"
    # Clean template: no self-match code hits
    assert int(data.get("cse_findings", "0")) == 0
    assert "session-security-sweep.sh:" not in out
    assert "cyber-essentials-scan.sh:" not in out
    # overall must not be FAIL solely from CSE false positives
    assert data.get("overall") in {"PASS", "WARN"}


def test_security_sweep_fingerprint_policy_documented() -> None:
    text = SWEEP.read_text(encoding="utf-8")
    assert "fingerprint_changed" in text
    assert "fingerprint_match_pass" in text
    assert "context-latest" in text  # excluded noise


def test_security_sweep_cache_roundtrip() -> None:
    """Full scan then second run with same fingerprint should cache-hit if PASS."""
    # First: force write report + meta
    r1 = subprocess.run(
        ["bash", str(SWEEP), "--active-only", "--force"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    )
    assert r1.returncode == 0, r1.stderr + r1.stdout
    assert "cache_hit=no" in r1.stdout or "cache_reason=" in r1.stdout
    # Second: default (use cache) — only hits if overall PASS
    r2 = subprocess.run(
        ["bash", str(SWEEP), "--active-only"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    )
    assert r2.returncode == 0, r2.stderr + r2.stdout
    data = {}
    for line in r2.stdout.splitlines():
        if "=" in line and not line.startswith("---") and not line.startswith("==="):
            k, _, v = line.partition("=")
            if re.fullmatch(r"[a-z_]+", k):
                data[k] = v
    # If PASS, expect cache hit; if WARN (hooks etc.) expect rescan
    if data.get("overall") == "PASS" or "cache_hit=yes" in r2.stdout:
        assert "cache_hit=yes" in r2.stdout or data.get("cache_hit") == "yes"
    else:
        assert "cache_hit=no" in r2.stdout or data.get("cache_reason", "").startswith(
            "prior_"
        ) or data.get("cache_reason") == "full"


if __name__ == "__main__":
    test_cyber_essentials_scan_no_self_match()
    test_session_security_sweep_no_false_cse_warns_on_clean_template()
    test_security_sweep_fingerprint_policy_documented()
    test_security_sweep_cache_roundtrip()
    print("PASS session security sweep smoke tests")
    sys.exit(0)

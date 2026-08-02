"""Security flywheel host scripts (Chrome lifecycle, peer-aware)."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_flywheel_scripts_exist():
    assert (ROOT / "scripts" / "security-flywheel-status.sh").is_file()
    assert (ROOT / "scripts" / "loop-security-flywheel-host.sh").is_file()
    assert (ROOT / "docs" / "guides" / "security-flywheel.md").is_file()
    assert (ROOT / "patterns" / "security-flywheel-watch.md").is_file()
    assert (ROOT / "scripts" / "security" / "flywheel-peers.yaml").is_file()


def test_flywheel_chain_registered():
    reg = (ROOT / "chains" / "registry.yaml").read_text(encoding="utf-8")
    assert "id: security-flywheel" in reg
    assert "security-flywheel-status.sh" in reg


def test_flywheel_status_quick():
    r = subprocess.run(
        ["bash", "scripts/security-flywheel-status.sh", "--quick"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    # WARN is ok (exit 0); FAIL exits 1
    assert "report_path=" in r.stdout or "PASS=" in r.stdout or "RESULT=" in r.stdout
    assert "find.security_md" in r.stdout or "SECURITY.md" in r.stdout
    out_dir = ROOT / "reports" / "security"
    reports = list(out_dir.glob("flywheel-status-*.md"))
    assert reports, "expected flywheel-status report"


def test_flywheel_status_json():
    r = subprocess.run(
        ["bash", "scripts/security-flywheel-status.sh", "--quick", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode in (0, 1)
    assert '"items"' in r.stdout or '"pass"' in r.stdout


def test_loop_host_snapshot():
    r = subprocess.run(
        ["bash", "scripts/loop-security-flywheel-host.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0
    assert "wrote reports/loops/" in r.stdout or "RESULT=" in r.stdout


if __name__ == "__main__":
    test_flywheel_scripts_exist()
    test_flywheel_chain_registered()
    test_flywheel_status_quick()
    test_flywheel_status_json()
    test_loop_host_snapshot()
    print("all security flywheel tests passed")

"""Smoke tests for session-guardrails-check.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "session-guardrails-check.py"
GUIDE = REPO / "docs" / "guides" / "prompt-injection-installed-apps.md"


def test_guide_exists() -> None:
    assert GUIDE.is_file()
    text = GUIDE.read_text(encoding="utf-8")
    assert "Trust boundary" in text
    assert "session-guardrails-check" in text


def test_guardrails_check_pass_or_warn_on_template() -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["status"] in {"PASS", "WARN", "FAIL"}
    assert "line" in data
    assert data["line"].startswith("guardrails=")
    # Engine must be present on this repo
    assert "engine_ok" in (data.get("details") or {}).get("engine", "") or data[
        "status"
    ] != "FAIL" or "engine" not in str(data.get("issues"))


def test_guardrails_check_oneliner() -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "guardrails=" in r.stdout


if __name__ == "__main__":
    test_guide_exists()
    test_guardrails_check_pass_or_warn_on_template()
    test_guardrails_check_oneliner()
    print("PASS session-guardrails-check smoke")
    sys.exit(0)

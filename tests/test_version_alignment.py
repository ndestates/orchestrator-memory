"""Version alignment + pre-release-aware compare for session-orchestrator-check."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load_session_check():
    path = REPO / "scripts" / "session-orchestrator-check.py"
    spec = importlib.util.spec_from_file_location("session_orch_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_is_newer_pre_release_aware() -> None:
    m = _load_session_check()
    assert m._is_newer("1.9.1", "1.9.0") is True
    assert m._is_newer("1.9.0-pre.5", "1.9.0-pre.3") is True
    assert m._is_newer("1.9.0", "1.9.0-pre.5") is True  # final > pre
    assert m._is_newer("1.9.0-pre.5", "1.9.0") is False
    assert m._is_newer("1.9.1", "1.9.1") is False
    # Old bug: core-only compare treated pre.3 == pre.5
    assert m._is_newer("1.9.0-pre.5", "1.9.0-pre.3") is True


def test_check_version_alignment_script_pass() -> None:
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check-version-alignment.py"), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["status"] in {"PASS", "WARN"}
    assert data["data"]["VERSION"]
    assert data["data"]["stamp"] == data["data"]["VERSION"]
    assert data["data"]["package.json"] == data["data"]["VERSION"]


def test_version_mirrors_on_disk() -> None:
    ver = (REPO / "VERSION").read_text(encoding="utf-8").strip().lstrip("v")
    stamp = (
        (REPO / "scripts" / "orchestrator-template-version")
        .read_text(encoding="utf-8")
        .strip()
        .lstrip("v")
    )
    pkg = json.loads((REPO / "package.json").read_text(encoding="utf-8"))["version"]
    assert stamp == ver
    assert pkg == ver
    bundle_path = REPO / "reports" / "security" / "bundle-hashes.json"
    if bundle_path.is_file():
        bver = json.loads(bundle_path.read_text(encoding="utf-8")).get("version")
        assert bver == ver, f"bundle {bver} != VERSION {ver}"


if __name__ == "__main__":
    test_is_newer_pre_release_aware()
    test_check_version_alignment_script_pass()
    test_version_mirrors_on_disk()
    print("PASS version alignment tests")
    sys.exit(0)

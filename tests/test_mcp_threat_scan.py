"""MCP threat scan: path-aware allowlist + vendor exclude; fail closed on CRIT."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "scripts" / "mcp-threat-scan.sh"


def _run_scan(out_dir: Path, *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["bash", str(SCAN), str(out_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=run_env,
    )


def _main_report(out_dir: Path) -> Path:
    """Prefer the human report, never the empty ``*.raw.txt`` dump."""
    reports = sorted(
        p
        for p in out_dir.glob("mcp-threat-*.txt")
        if not p.name.endswith(".raw.txt")
    )
    assert reports, f"expected threat report in {out_dir}"
    return reports[-1]


def test_vendor_venv_soft_noise_excluded(tmp_path: Path):
    """Real-repo scan must pass: 0 CRIT, vendor trees excluded, paths present."""
    out_dir = tmp_path / "sec"
    r = _run_scan(out_dir)
    assert r.returncode == 0, (r.stderr or "") + (r.stdout or "")
    text = _main_report(out_dir).read_text(encoding="utf-8", errors="replace")
    assert "vendor_excluded=yes" in text
    assert "critical_hits=0" in text
    # Vendor noise must not appear even as SOFT when exclusions work
    assert ".venv/" not in text
    assert "site-packages" not in text


def test_rg_invocation_keeps_filenames():
    """Regression: never use rg --no-filename / -I (broke CI allowlist)."""
    src = SCAN.read_text(encoding="utf-8")
    # The actual scan invocation (must keep paths for allowlist/vendor filters)
    invocs = [
        ln.strip()
        for ln in src.splitlines()
        if re.search(r"\brg\s+-n\b", ln) and not ln.strip().startswith("#")
    ]
    assert invocs, "expected `rg -n …` scan invocation in mcp-threat-scan.sh"
    for ln in invocs:
        assert re.search(r"(^|[\s])-I([\s]|$)", ln) is None, ln
        assert "--no-filename" not in ln
        assert "-H" in ln or "--with-filename" in ln



def test_rg_crit_lines_include_path_when_available(tmp_path: Path):
    if not shutil.which("rg"):
        return
    out_dir = tmp_path / "sec-rg"
    r = _run_scan(out_dir)
    assert r.returncode == 0, r.stderr
    text = _main_report(out_dir).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith(("CRIT  ", "ALLOW ", "SOFT  ")):
            body = line.split(None, 1)[1]
            assert ":" in body, f"expected path:line:… got {line!r}"
            path_part = body.split(":", 1)[0]
            assert path_part and not path_part.isdigit(), (
                f"rg lost filename (path is numeric line only): {line!r}"
            )


def test_scan_script_defines_excludes():
    src = SCAN.read_text(encoding="utf-8")
    assert "site-packages" in src
    assert "is_vendor_path" in src
    assert "vendor_excluded=yes" in src
    assert "is_allowlisted" in src


def test_malware_lint_self_hits_allowlisted_with_rg(tmp_path: Path):
    """Scanner definition strings must not fail CI when rg is present."""
    if not shutil.which("rg"):
        return
    out_dir = tmp_path / "sec"
    r = _run_scan(out_dir)
    assert r.returncode == 0, r.stderr
    text = _main_report(out_dir).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("CRIT  "):
            raise AssertionError(f"unexpected CRIT with rg present: {line}")

"""Tests for orchestrator-skill-governance (Phase 3)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = REPO_ROOT / "scripts" / "orchestrator-skill-governance.py"
    spec = importlib.util.spec_from_file_location("orch_skill_gov", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flags_unrestricted_shell_skill(tmp_path: Path):
    m = _load()
    skill_dir = tmp_path / ".grok" / "skills" / "evil"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: evil\nallowed-tools:\n  - bash\n---\n"
        "You may run unrestricted shell access on the host.\n",
        encoding="utf-8",
    )
    findings = m.scan(tmp_path, allow=[])
    critical = [f for f in findings if f["severity"] == "critical"]
    assert critical, findings
    assert critical[0]["rule"] == "unrestricted-shell-without-governance"


def test_justified_skips_critical(tmp_path: Path):
    m = _load()
    skill_dir = tmp_path / ".grok" / "skills" / "ok"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: ok\ntool_governance: justified\nallowed-tools:\n  - bash\n---\n"
        "run unrestricted shell access for deploy only.\n",
        encoding="utf-8",
    )
    findings = m.scan(tmp_path, allow=[])
    critical = [f for f in findings if f["severity"] == "critical"]
    assert critical == []


def test_benign_any_command_not_critical(tmp_path: Path):
    m = _load()
    skill_dir = tmp_path / ".grok" / "skills" / "ddev"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: ddev\nallowed-tools:\n  - bash\n---\n"
        "Use ddev for any command that touches application code.\n",
        encoding="utf-8",
    )
    findings = m.scan(tmp_path, allow=[])
    critical = [f for f in findings if f["severity"] == "critical"]
    assert critical == []


def test_default_scan_skips_info_findings(tmp_path: Path):
    """Phase A BH-007: default scan is critical-only (no info flood)."""
    m = _load()
    skill_dir = tmp_path / ".grok" / "skills" / "shellish"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: shellish\nallowed-tools:\n  - bash\n---\n"
        "Run bash scripts for deploy.\n",
        encoding="utf-8",
    )
    default = m.scan(tmp_path, allow=[])
    assert all(f["severity"] == "critical" for f in default)
    assert default == []
    with_info = m.scan(tmp_path, allow=[], include_info=True)
    info = [f for f in with_info if f["severity"] == "info"]
    assert len(info) == 1

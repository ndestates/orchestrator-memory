"""Phase 0 tests for scripts/scan-template-contamination.sh (the hard gate).

Driven via subprocess (bash), mirroring how the clean-deploy flow and CI invoke
it. Pins: clean tree passes, planted residue fails, source repo short-circuits.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN = REPO_ROOT / "scripts" / "scan-template-contamination.sh"


def _run(target: Path, slug: str):
    return subprocess.run(
        ["bash", str(SCAN), str(target), slug],
        capture_output=True, text=True,
    )


def _skill(target: Path, body: str):
    d = target / ".grok" / "skills" / "demo"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")


def test_clean_tree_passes(tmp_path):
    target = tmp_path / "acme"
    target.mkdir()
    _skill(target, "# Acme skill\nNothing template-y here.\n")
    res = _run(target, "acme")
    assert res.returncode == 0, res.stdout + res.stderr


def test_planted_placeholder_fails(tmp_path):
    target = tmp_path / "acme"
    target.mkdir()
    _skill(target, "# Skill for {project_slug}\nProject Template residue.\n")
    res = _run(target, "acme")
    assert res.returncode == 1, res.stdout + res.stderr


def test_source_repo_short_circuits(tmp_path):
    # slug 'orchestrator' + presence of the deploy script => template source repo,
    # whose template identifiers are legitimate -> exit 0 regardless of content.
    target = tmp_path / "orchestrator"
    (target / "scripts").mkdir(parents=True)
    (target / "scripts" / "deploy_grok_to_project.py").write_text("# stub\n", encoding="utf-8")
    _skill(target, "Project Template ndestates/orchestrator everywhere\n")
    res = _run(target, "orchestrator")
    assert res.returncode == 0, res.stdout + res.stderr

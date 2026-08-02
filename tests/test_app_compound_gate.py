"""Tests for per-app compound gate."""

from __future__ import annotations

import json
from pathlib import Path

from _engine.app_compound import assess, loop_enabled


def _write_loop_root(tmp_path: Path, *, spine: bool = True, app_lesson: bool = False) -> Path:
    (tmp_path / "LOOP.md").write_text("# loops\n", encoding="utf-8")
    if not spine:
        return tmp_path
    (tmp_path / "STATE.md").write_text("# STATE\n\n## Lessons → skills\n\n", encoding="utf-8")
    (tmp_path / "VISION.md").write_text("# VISION\n", encoding="utf-8")
    (tmp_path / "patterns").mkdir(exist_ok=True)
    (tmp_path / "patterns/compound-learning.md").write_text("# compound\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir(exist_ok=True)
    (tmp_path / "scripts/loop-compound.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    (tmp_path / "scripts/loop_compound.py").write_text("# compound\n", encoding="utf-8")
    (tmp_path / ".grok/skills/loop-compound").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".grok/skills/loop-compound/SKILL.md").write_text("# skill\n", encoding="utf-8")
    lessons = {
        "lessons_learned": [
            {
                "text": "Full `.codebase-scan.txt` can lag README `[UPDATED]` markers.",
                "source": "template",
            }
        ],
        "gate_history": [{"at": "2026-01-01", "gates": []}],
    }
    if app_lesson:
        lessons["lessons_learned"].append(
            {
                "text": "demo-app: session-start gate recorded an app-specific lesson.",
                "source": "reports/loops/2026-07-03-session-compound-gate.md",
            }
        )
    loops = tmp_path / "reports/loops"
    loops.mkdir(parents=True, exist_ok=True)
    (loops / "lessons-state.json").write_text(json.dumps(lessons), encoding="utf-8")
    return tmp_path


def test_skip_without_loop_md(tmp_path: Path) -> None:
    assert not loop_enabled(tmp_path)
    result = assess(tmp_path)
    assert result["status"] == "skip"
    assert result["action"] == "none"


def test_gap_when_spine_missing(tmp_path: Path) -> None:
    (tmp_path / "LOOP.md").write_text("# loops\n", encoding="utf-8")
    result = assess(tmp_path)
    assert result["status"] == "gap"
    assert result["action"] == "offer_scaffold"


def test_scaffold_with_spine_no_app_lesson(tmp_path: Path) -> None:
    _write_loop_root(tmp_path, spine=True, app_lesson=False)
    result = assess(tmp_path)
    assert result["status"] == "scaffold"
    assert result["action"] == "close_compound"


def test_ready_with_app_lesson(tmp_path: Path) -> None:
    _write_loop_root(tmp_path, spine=True, app_lesson=True)
    result = assess(tmp_path)
    assert result["status"] == "ready"
    assert result["action"] == "load_state"
    assert result["app_lessons"] == 1


def test_unclosed_report(tmp_path: Path) -> None:
    root = _write_loop_root(tmp_path, spine=True, app_lesson=True)
    report = root / "reports/loops/2026-07-03-cache-freshness.md"
    report.write_text(
        "# report\n\n## Lessons\n\n- New lesson not yet in lessons-state.json\n",
        encoding="utf-8",
    )
    result = assess(root)
    assert result["status"] == "unclosed_report"
    assert result["action"] == "close_compound"
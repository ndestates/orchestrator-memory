"""Tests for scripts/workstream_recommend.py — Shape B diamond recommendation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from conftest import load_script  # noqa: E402

rec = load_script("workstream_recommend.py")


class TestClassifyText:
    def test_blocked_keywords(self):
        assert rec._classify_text("Swap Apache LICENSE and EULA") == "blocked"
        assert rec._classify_text("PayPal production billing") == "blocked"
        assert rec._classify_text("force-push master") == "blocked"
        assert rec._classify_text("deploy secret keys") == "blocked"

    def test_safe_keywords(self):
        assert rec._classify_text("Update docs and README wording") == "safe_parallel"
        assert rec._classify_text("fix typo in changelog") == "safe_parallel"
        assert rec._classify_text("add unit test for lint") == "safe_parallel"

    def test_serial_hints(self):
        assert rec._classify_text("Implement new API feature") == "serial_focus"
        assert rec._classify_text("schema migration refactor") == "serial_focus"

    def test_default_serial(self):
        assert rec._classify_text("something obscure") == "serial_focus"


class TestClassifyWorkstream:
    def test_held_blocked(self):
        c = rec._classify_workstream(
            {"id": "lic", "status": "held_ready", "title": "docs polish", "open": "", "next": ""}
        )
        assert c["risk"] == "blocked"
        assert "held_ready" in c["reason"]

    def test_parked_blocked(self):
        c = rec._classify_workstream(
            {"id": "p", "status": "parked", "title": "x", "open": "", "next": ""}
        )
        assert c["risk"] == "blocked"

    def test_active_safe(self):
        c = rec._classify_workstream(
            {
                "id": "d",
                "status": "active",
                "title": "Docs guide polish",
                "open": "readme",
                "next": "fix typo",
            }
        )
        assert c["risk"] == "safe_parallel"

    def test_active_high_risk(self):
        c = rec._classify_workstream(
            {
                "id": "pay",
                "status": "active",
                "title": "PayPal",
                "open": "production billing",
                "next": "",
            }
        )
        assert c["risk"] == "blocked"


class TestBuildRecommendation:
    def test_preserves_primary_and_no_auto_exec(self):
        candidates = [
            rec._classify_workstream(
                {"id": "main-ws", "status": "active", "title": "Implement feature", "open": "", "next": "ship"}
            ),
            rec._classify_workstream(
                {"id": "docs", "status": "active", "title": "Docs chore", "open": "readme", "next": "typo"}
            ),
            rec._classify_workstream(
                {"id": "held", "status": "held", "title": "license", "open": "apache", "next": ""}
            ),
        ]
        out = rec.build_recommendation(primary="main-ws", candidates=candidates)
        assert out["auto_execute"] is False
        assert out["preserve_focus"] is True
        assert out["shape"] == "B"
        assert out["primary"] == "main-ws"
        # L0 is primary
        assert out["lanes"][0]["lane"] == "L0-primary"
        assert out["lanes"][0]["items"][0]["id"] == "main-ws"
        # held is blocked
        assert any(b["id"] == "held" for b in out["blocked"])
        # docs may be safe parallel lane
        safe_lanes = [l for l in out["lanes"] if l["risk"] == "safe_parallel"]
        assert any(i["id"] == "docs" for l in safe_lanes for i in l["items"])

    def test_caps_parallel(self):
        candidates = []
        for i in range(10):
            candidates.append(
                {
                    "id": f"d{i}",
                    "source": "todo",
                    "title": f"docs chore {i}",
                    "status": "open",
                    "next": "readme",
                    "branch": "",
                    "risk": "safe_parallel",
                    "reason": "test",
                }
            )
        out = rec.build_recommendation(primary="", candidates=candidates)
        safe_lanes = [l for l in out["lanes"] if l["risk"] == "safe_parallel"]
        assert len(safe_lanes) <= rec.MAX_PARALLEL
        assert len(out["deferred_safe"]) >= 1

    def test_format_compact(self):
        candidates = [
            rec._classify_workstream(
                {"id": "a", "status": "active", "title": "Docs", "open": "readme", "next": ""}
            )
        ]
        out = rec.build_recommendation(primary="a", candidates=candidates)
        text = rec.format_compact(out)
        assert "auto_execute=no" in text
        assert "primary=a" in text
        assert "approve parallel" in text

    def test_format_markdown_has_safety(self):
        candidates = [
            rec._classify_workstream(
                {"id": "a", "status": "held", "title": "x", "open": "", "next": ""}
            )
        ]
        out = rec.build_recommendation(primary="a", candidates=candidates)
        md = rec.format_markdown(out, "TODO/x.md")
        assert "auto-execute" in md.lower() or "Auto-execute" in md
        assert "Does **not** unhold" in md
        assert "Shape B" in md


class TestTodoHelpers:
    def test_open_todo_items(self, tmp_path):
        p = tmp_path / "2026-07-22_TODO.md"
        p.write_text(
            "# TODO\n\n- [ ] Fix docs typo\n- [x] Done thing\n- [ ] Implement feature X\n",
            encoding="utf-8",
        )
        items = rec._open_todo_items(p)
        assert len(items) == 2
        assert "Fix docs typo" in items[0]
        assert "Implement feature X" in items[1]

    def test_open_todo_missing(self):
        assert rec._open_todo_items(None) == []
        assert rec._open_todo_items(Path("/no/such/file.md")) == []

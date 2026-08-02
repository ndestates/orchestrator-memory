"""Tests for scripts/workstream_prompts.py — merge-ready / phase assessment."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from conftest import load_script  # noqa: E402

prompts = load_script("workstream_prompts.py")


def _base_ws(**overrides) -> dict:
    ws = {
        "id": "track-a",
        "title": "Track A",
        "status": "active",
        "branch": "feature/a",
        "next": "do things",
        "open": "",
    }
    ws.update(overrides)
    return ws


class TestAssessPhases:
    def test_parked(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts, "_branch_ahead_behind", lambda b, base="origin/develop": {"ok": True, "ahead": 0, "behind": 0}
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(status="parked"), index=1, primary="x")
        assert r["phase"] == "parked"
        assert r["merge_ready"] is False
        assert any("parked" in p for p in r["prompts"])

    def test_held(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts, "_branch_ahead_behind", lambda b, base="origin/develop": {"ok": True, "ahead": 1, "behind": 0}
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(status="held"), index=2, primary="other")
        assert r["phase"] == "held"
        assert any("activate" in rec for rec in r["recommendations"])

    def test_wip_dirty(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: True)
        monkeypatch.setattr(
            prompts, "_branch_ahead_behind", lambda b, base="origin/develop": {"ok": True, "ahead": 2, "behind": 0}
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(status="active"), index=1, primary="track-a")
        assert r["phase"] == "wip"
        assert r["dirty"] is True

    def test_no_commits(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 0, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(), index=1, primary="track-a")
        assert r["phase"] == "no_commits"

    def test_ready_for_pr(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 3, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(), index=1, primary="track-a")
        assert r["phase"] == "ready_for_pr"
        assert r["merge_ready"] is False
        assert any("gh pr create" in rec for rec in r["recommendations"])

    def test_needs_rebase(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 2, "behind": 5, "base": "origin/develop"},
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(), index=1, primary="track-a")
        assert r["phase"] == "needs_rebase"

    def test_merge_ready_open_pr(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 2, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(
            prompts,
            "_gh_pr",
            lambda b: {
                "number": 42,
                "url": "https://example/pr/42",
                "state": "OPEN",
                "mergeable": "MERGEABLE",
                "statusCheckRollup": [],
            },
        )
        r = prompts._assess(_base_ws(), index=1, primary="track-a")
        assert r["phase"] == "merge_ready"
        assert r["merge_ready"] is True
        assert any("READY TO MERGE" in p for p in r["prompts"])

    def test_pr_failing(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 1, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(
            prompts,
            "_gh_pr",
            lambda b: {
                "number": 7,
                "url": "https://example/pr/7",
                "state": "OPEN",
                "mergeable": True,
                "statusCheckRollup": [{"conclusion": "FAILURE", "state": "COMPLETED"}],
            },
        )
        r = prompts._assess(_base_ws(), index=1, primary="track-a")
        assert r["phase"] == "pr_failing"

    def test_protected_branch_active(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts, "_branch_ahead_behind", lambda b, base="origin/develop": {"ok": True, "ahead": 0, "behind": 0}
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(branch="develop"), index=1, primary="track-a")
        assert any("protected" in p.lower() or "STOP" in p for p in r["prompts"])

    def test_no_branch(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts, "_branch_ahead_behind", lambda b, base="origin/develop": {"ok": False, "ahead": 0, "behind": 0, "note": "no branch"}
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)
        r = prompts._assess(_base_ws(branch=""), index=1, primary="track-a")
        assert any("no branch" in p for p in r["prompts"])


class TestBuildReport:
    def test_summary_and_headlines(self, monkeypatch):
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 2, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)

        data = {
            "primary": "a",
            "workstreams": [
                _base_ws(id="a", status="active", branch="feature/a"),
                _base_ws(id="b", status="held", branch="feature/b"),
                _base_ws(id="c", status="parked", branch="feature/c"),
            ],
        }
        report = prompts.build_report(data)
        assert report["primary"] == "a"
        assert report["summary"]["total"] == 3
        assert report["summary"]["frozen"] == 2
        assert report["summary"]["ready_for_pr"] == 1
        text = prompts.format_text(report)
        assert "MULTI-WORKSTREAM prompts" in text
        assert "auto_merge=no" in text
        assert "SAFEGUARD" in text
        assert any("never merges" in h for h in report["headline_prompts"])


class TestMainCLI:
    def test_main_writes_report(self, tmp_path, monkeypatch, capsys):
        reg = tmp_path / "ws.yaml"
        out = tmp_path / "prompts.md"
        reg.write_text(
            yaml.safe_dump(
                {
                    "primary": "a",
                    "workstreams": [
                        {
                            "id": "a",
                            "status": "held",
                            "branch": "feature/a",
                            "title": "A",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(prompts, "_dirty", lambda cwd: False)
        monkeypatch.setattr(
            prompts,
            "_branch_ahead_behind",
            lambda b, base="origin/develop": {"ok": True, "ahead": 0, "behind": 0, "base": "origin/develop"},
        )
        monkeypatch.setattr(prompts, "_gh_pr", lambda b: None)

        rc = prompts.main(["--registry", str(reg), "--out", str(out)])
        assert rc == 0
        assert out.is_file()
        assert out.with_suffix(".json").is_file()
        payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        assert payload["streams"][0]["phase"] == "held"

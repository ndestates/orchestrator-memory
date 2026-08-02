"""Tests for scripts/workstream.py — registry CLI, selectors, status transitions.

Uses temp registries only (no mutation of reports/sessions/workstreams.yaml).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from conftest import load_script  # noqa: E402

ws = load_script("workstream.py")


def _sample_registry() -> dict:
    return {
        "version": 1,
        "primary": "alpha",
        "updated": "2026-07-01",
        "workstreams": [
            {
                "id": "alpha",
                "title": "Alpha track",
                "status": "active",
                "branch": "feature/alpha",
                "next": "ship alpha",
                "open": "",
                "updated": "2026-07-01",
            },
            {
                "id": "beta",
                "title": "Beta track",
                "status": "held",
                "branch": "feature/beta",
                "next": "wait",
                "open": "",
                "updated": "2026-07-01",
            },
            {
                "id": "gamma",
                "title": "Gamma track",
                "status": "parked",
                "branch": "feature/gamma",
                "next": "",
                "open": "",
                "updated": "2026-07-01",
            },
            {
                "id": "delta",
                "title": "Delta track",
                "status": "held_ready",
                "branch": "feature/delta",
                "next": "unhold later",
                "open": "",
                "updated": "2026-07-01",
            },
        ],
    }


def _write_reg(path: Path, data: dict | None = None) -> Path:
    data = data or _sample_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


# ── selectors ──────────────────────────────────────────────────────────────


class TestResolveSpec:
    def test_single_index(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "1") == ["alpha"]
        assert ws._resolve_spec(data, "2") == ["beta"]

    def test_comma_list(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "1,3") == ["alpha", "gamma"]
        assert ws._resolve_spec(data, "2,4,1") == ["beta", "delta", "alpha"]

    def test_range(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "1-3") == ["alpha", "beta", "gamma"]
        assert ws._resolve_spec(data, "3-1") == ["alpha", "beta", "gamma"]  # swapped

    def test_all(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "all") == ["alpha", "beta", "gamma", "delta"]
        assert ws._resolve_spec(data, "ALL") == ["alpha", "beta", "gamma", "delta"]

    def test_slug(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "beta") == ["beta"]
        assert ws._resolve_spec(data, "gamma") == ["gamma"]

    def test_mixed_tokens(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "1,gamma") == ["alpha", "gamma"]
        assert ws._resolve_spec(data, "2-3,delta") == ["beta", "gamma", "delta"]

    def test_dedupe(self):
        data = _sample_registry()
        assert ws._resolve_spec(data, "1,1,alpha") == ["alpha"]

    def test_empty_selector(self):
        with pytest.raises(SystemExit, match="empty"):
            ws._resolve_spec(_sample_registry(), "")

    def test_empty_registry(self):
        with pytest.raises(SystemExit, match="no workstreams"):
            ws._resolve_spec({"workstreams": []}, "1")

    def test_index_out_of_range(self):
        with pytest.raises(SystemExit, match="out of range"):
            ws._resolve_spec(_sample_registry(), "99")

    def test_unknown_slug(self):
        with pytest.raises(SystemExit, match="unknown workstream"):
            ws._resolve_spec(_sample_registry(), "nope")

    def test_resolve_one_requires_single(self):
        data = _sample_registry()
        assert ws._resolve_one(data, "2") == "beta"
        with pytest.raises(SystemExit, match="exactly one"):
            ws._resolve_one(data, "1,2")
        with pytest.raises(SystemExit, match="exactly one"):
            ws._resolve_one(data, "all")


# ── brief ──────────────────────────────────────────────────────────────────


class TestBrief:
    def test_brief_dict_counts(self):
        b = ws.brief_dict(_sample_registry())
        assert b["present"] == "yes"
        assert b["primary"] == "alpha"
        assert b["active_n"] == 1
        assert b["held_n"] == 2  # held + held_ready
        assert b["parked_n"] == 1
        assert b["total"] == 4
        assert "alpha" in b["show"]

    def test_format_brief_line(self):
        line = ws.format_brief_line(ws.brief_dict(_sample_registry()))
        assert line.startswith("ws primary=alpha")
        assert "active=1" in line
        assert "held=2" in line
        assert "parked=1" in line

    def test_load_brief_missing(self, tmp_path):
        b = ws.load_brief(tmp_path / "missing.yaml")
        assert b == {"present": "no"}
        assert ws.format_brief_line(b) == "ws present=no"

    def test_load_brief_valid(self, tmp_path):
        p = _write_reg(tmp_path / "workstreams.yaml")
        b = ws.load_brief(p)
        assert b["present"] == "yes"
        assert b["primary"] == "alpha"


# ── load / save ────────────────────────────────────────────────────────────


class TestLoadSave:
    def test_load_invalid(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("not: a registry\n", encoding="utf-8")
        with pytest.raises(SystemExit, match="invalid registry"):
            ws._load(p)

    def test_save_sets_updated(self, tmp_path):
        p = tmp_path / "reg.yaml"
        data = _sample_registry()
        ws._save(p, data)
        assert data["updated"] == date.today().isoformat()
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert loaded["primary"] == "alpha"
        assert len(loaded["workstreams"]) == 4


# ── status transitions ─────────────────────────────────────────────────────


class TestStatusCommands:
    def test_focus_by_number(self, tmp_path, capsys):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_focus(data, p, "2", apply=False)
        assert rc == 0
        assert ws._load(p)["primary"] == "beta"
        out = capsys.readouterr().out
        assert "primary → #2 beta" in out
        assert "branch=feature/beta" in out

    def test_hold_ready_and_primary_handoff(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        # hold primary → primary should move to another active if any
        # only alpha is active; after hold, primary may stay or hand off
        rc = ws.cmd_hold(data, p, "1", ready=True)
        assert rc == 0
        loaded = ws._load(p)
        assert loaded["workstreams"][0]["status"] == "held_ready"

    def test_hold_multiple(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        # activate beta first so we can hold two
        ws.cmd_set_status(data, p, "2", "active")
        data = ws._load(p)
        rc = ws.cmd_hold(data, p, "1,2", ready=False)
        assert rc == 0
        loaded = ws._load(p)
        statuses = {w["id"]: w["status"] for w in loaded["workstreams"]}
        assert statuses["alpha"] == "held"
        assert statuses["beta"] == "held"

    def test_activate_all(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_set_status(data, p, "all", "active")
        assert rc == 0
        loaded = ws._load(p)
        assert all(w["status"] == "active" for w in loaded["workstreams"])

    def test_park_range(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_set_status(data, p, "2-3", "parked")
        assert rc == 0
        loaded = ws._load(p)
        by_id = {w["id"]: w["status"] for w in loaded["workstreams"]}
        assert by_id["beta"] == "parked"
        assert by_id["gamma"] == "parked"
        assert by_id["alpha"] == "active"

    def test_add_new_workstream(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_add(
            data,
            p,
            "epsilon",
            title="Epsilon",
            branch="feature/epsilon",
            status="active",
            next_text="go",
        )
        assert rc == 0
        loaded = ws._load(p)
        ids = [w["id"] for w in loaded["workstreams"]]
        assert "epsilon" in ids
        ep = next(w for w in loaded["workstreams"] if w["id"] == "epsilon")
        assert ep["branch"] == "feature/epsilon"
        assert ep["next"] == "go"

    def test_add_duplicate_fails(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_add(
            data, p, "alpha", title=None, branch=None, status="active", next_text=None
        )
        assert rc == 2

    def test_note_updates(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_note(data, p, "1", next_text="new next", open_text="new open")
        assert rc == 0
        loaded = ws._load(p)
        assert loaded["workstreams"][0]["next"] == "new next"
        assert loaded["workstreams"][0]["open"] == "new open"

    def test_invalid_status(self, tmp_path, capsys):
        p = _write_reg(tmp_path / "ws.yaml")
        data = ws._load(p)
        rc = ws.cmd_set_status(data, p, "1", "bogus")
        assert rc == 2


# ── CLI entry ──────────────────────────────────────────────────────────────


class TestMainCLI:
    def test_list_and_brief(self, tmp_path, capsys):
        p = _write_reg(tmp_path / "ws.yaml")
        assert ws.main(["--registry", str(p), "list"]) == 0
        out = capsys.readouterr().out
        assert "primary=alpha" in out
        assert "alpha" in out
        assert "hint:" in out

        assert ws.main(["--registry", str(p), "brief"]) == 0
        out = capsys.readouterr().out
        assert "ws primary=alpha" in out

    def test_serial(self, tmp_path, capsys):
        p = _write_reg(tmp_path / "ws.yaml")
        assert ws.main(["--registry", str(p), "serial"]) == 0
        out = capsys.readouterr().out
        assert "SERIAL plan" in out
        assert "primary=alpha" in out
        assert "no auto-merge" in out.lower() or "SAFEGUARD" in out

    def test_graph_mermaid(self, tmp_path, capsys):
        p = _write_reg(tmp_path / "ws.yaml")
        assert ws.main(["--registry", str(p), "graph"]) == 0
        out = capsys.readouterr().out
        assert "```mermaid" in out
        assert "flowchart TD" in out
        assert "alpha" in out

    def test_activate_via_cli(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        assert ws.main(["--registry", str(p), "activate", "2,3"]) == 0
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        by_id = {w["id"]: w["status"] for w in loaded["workstreams"]}
        assert by_id["beta"] == "active"
        assert by_id["gamma"] == "active"

    def test_focus_multi_fails(self, tmp_path):
        p = _write_reg(tmp_path / "ws.yaml")
        with pytest.raises(SystemExit):
            ws.main(["--registry", str(p), "focus", "1,2"])

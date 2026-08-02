"""orchestrator ensure — wrappers around host scripts."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from orchestrator_cli import ensure_host
from orchestrator_cli.__main__ import main


def _fake_script_ok(script: Path, args: list[str], **kwargs):
    return {
        "ok": True,
        "exit_code": 0,
        "script": str(script),
        "args": args,
        "stdout": "ok",
        "stderr": "",
        "skipped": False,
        "command": ["bash", str(script), *args],
    }


def test_resolve_prefers_path_with_scripts(tmp_path):
    app = tmp_path / "app"
    (app / "scripts").mkdir(parents=True)
    (app / "scripts" / "ensure-mcp-host.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    root = ensure_host.resolve_project_root(app)
    assert root == app.resolve()


def test_run_ensure_default_is_host_tools_only(monkeypatch, tmp_path):
    """Product default: MCP off — ensure only host tools unless mcp=True."""
    app = tmp_path / "app"
    scripts = app / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ensure-mcp-host.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (scripts / "install-host-tools.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    with patch.object(ensure_host, "_run_script", side_effect=_fake_script_ok) as run:
        rep = ensure_host.run_ensure(path=app, check=True)
    assert rep["ok"] is True
    assert "mcp" not in rep["steps"]
    assert "host_tools" in rep["steps"]
    assert run.call_count == 1


def test_run_ensure_both_check(monkeypatch, tmp_path):
    app = tmp_path / "app"
    scripts = app / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ensure-mcp-host.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (scripts / "install-host-tools.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    with patch.object(ensure_host, "_run_script", side_effect=_fake_script_ok) as run:
        rep = ensure_host.run_ensure(path=app, mcp=True, host_tools=True, check=True)
    assert rep["ok"] is True
    assert "mcp" in rep["steps"]
    assert "host_tools" in rep["steps"]
    assert run.call_count == 2
    # check flags passed
    mcp_args = run.call_args_list[0][0][1]
    assert "--check" in mcp_args


def test_run_ensure_mcp_only(monkeypatch, tmp_path):
    app = tmp_path / "app"
    scripts = app / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ensure-mcp-host.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    with patch.object(ensure_host, "_run_script", side_effect=_fake_script_ok):
        rep = ensure_host.run_ensure(path=app, mcp=True, host_tools=False, force=True)
    assert rep["ok"] is True
    assert "mcp" in rep["steps"]
    assert "host_tools" not in rep["steps"]


def test_run_ensure_nothing_selected(tmp_path):
    rep = ensure_host.run_ensure(path=tmp_path, mcp=False, host_tools=False)
    assert rep["ok"] is False


def test_cli_ensure_json(capsys, tmp_path):
    app = tmp_path / "app"
    scripts = app / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ensure-mcp-host.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (scripts / "install-host-tools.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    with patch.object(ensure_host, "_run_script", side_effect=_fake_script_ok):
        assert main(["ensure", str(app), "--check", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "ensure"
    assert payload["ok"] is True

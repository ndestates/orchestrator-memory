"""Tests for MCP develop-only policy and start options."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.mcp_runtime_policy import (  # noqa: E402
    build_mcp_start_options,
    detect_public_or_prod_env,
    session_mcp_brief,
)


def test_local_env_is_safe():
    r = detect_public_or_prod_env({})
    assert r["mcp_env_safe"] == "yes"
    assert r["mcp_policy"] == "dev_only"  # env detector only; product enablement is separate
    assert r["mcp_public_forbidden"] == "yes"


def test_mcp_disabled_by_default():
    brief = session_mcp_brief(
        root=REPO_ROOT,
        runtime="local",
        has_ddev=False,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="yes",
        ddev_running="n/a",
        compose_running="n/a",
        mcp_note="",
        environ={},
    )
    assert brief["mcp_policy"] == "off"
    assert brief["mcp_ready"] == "off"
    assert brief["mcp_start_offer"] == "no"
    assert brief["mcp_start_options"] == []


def test_digitalocean_blocked():
    r = detect_public_or_prod_env({"DIGITALOCEAN_APP_ID": "abc-123"})
    assert r["mcp_env_safe"] == "no"
    assert any("DigitalOcean" in s for s in r["mcp_public_signals"])


def test_app_env_production_blocked():
    r = detect_public_or_prod_env({"APP_ENV": "production"})
    assert r["mcp_env_safe"] == "no"


def test_start_options_refuse_when_public():
    opts = build_mcp_start_options(
        runtime="local",
        has_ddev=True,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="pending",
        ddev_running="no",
        compose_running="n/a",
        mcp_env_safe="no",
    )
    assert len(opts) == 1
    assert opts[0]["id"] == "refuse_public"


def test_start_options_include_ddev_and_host():
    opts = build_mcp_start_options(
        runtime="ddev",
        has_ddev=True,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="pending",
        ddev_running="no",
        compose_running="n/a",
        mcp_env_safe="yes",
    )
    ids = {o["id"] for o in opts}
    assert "ddev" in ids
    assert "host_stdio" in ids


def test_session_brief_blocks_ready_on_prod():
    brief = session_mcp_brief(
        root=REPO_ROOT,
        runtime="local",
        has_ddev=False,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="yes",
        ddev_running="n/a",
        compose_running="n/a",
        mcp_note="",
        environ={"HEROKU_APP_NAME": "myapp", "ORCHESTRATOR_MCP": "1"},
    )
    assert brief["mcp_ready"] == "blocked"
    assert brief["mcp_start_offer"] == "yes"


def test_start_options_handshake_fail_offers_smoke():
    opts = build_mcp_start_options(
        runtime="local",
        has_ddev=False,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="fail",
        ddev_running="n/a",
        compose_running="n/a",
        mcp_env_safe="yes",
    )
    ids = {o["id"] for o in opts}
    assert "handshake_repair" in ids
    assert any("mcp-smoke" in (o.get("commands") or "") for o in opts)


def test_session_brief_fail_offers_and_warns():
    brief = session_mcp_brief(
        root=REPO_ROOT,
        runtime="local",
        has_ddev=False,
        has_compose=False,
        has_mcp_server=True,
        mcp_ready="fail",
        ddev_running="n/a",
        compose_running="n/a",
        mcp_note="handshake failed",
        environ={"ORCHESTRATOR_MCP": "1"},
    )
    assert brief["mcp_ready"] == "fail"
    assert brief["mcp_start_offer"] == "yes"
    assert "HANDSHAKE_FAIL" in brief["briefing_line"]


def test_detect_project_runtime_json_includes_policy():
    proc = subprocess.run(
        ["bash", str(SCRIPTS / "detect-project-runtime.sh"), "--json", "--with-manifest-identity"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data.get("mcp_policy") == "off"
    assert data.get("mcp_public_forbidden") == "yes"
    assert "mcp_start_options" in data
    assert "manifest_identity" in data
    assert data["manifest_identity"]["status"] == "ok"

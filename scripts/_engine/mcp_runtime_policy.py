"""MCP runtime policy helpers — optional, default OFF.

MCP is not required for host CLI, chains, or cache-first file sessions.
Default product policy: **disabled**. Opt-in: ORCHESTRATOR_MCP=1 or
runtime.mcp: enabled|dev_only in project-manifest.

When enabled, still develop-only (never public/production hosts).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def mcp_is_enabled(
    root: Path | None = None,
    environ: dict[str, str] | None = None,
) -> bool:
    """Return True only when MCP is explicitly opted in.

    Precedence:
    1. ORCHESTRATOR_MCP env (0/false/off → False; 1/true/on → True)
    2. project-manifest runtime.mcp / mcp_policy (enabled|dev_only|on → True; off|disabled|false → False)
    3. Default: **False** (MCP disabled)
    """
    env = environ if environ is not None else dict(os.environ)
    raw = (env.get("ORCHESTRATOR_MCP") or "").strip().lower()
    if raw in ("0", "false", "no", "off", "disabled"):
        return False
    if raw in ("1", "true", "yes", "on", "enabled", "dev_only", "dev-only"):
        return True

    # Manifest (optional)
    if root is not None:
        for rel in (
            ".github/project-manifest.yaml",
            ".grok/project-manifest.yaml",
            ".claude/project-manifest.yaml",
        ):
            p = root / rel
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # runtime.mcp: off | enabled | dev_only
            m = re.search(r"(?m)^\s*mcp:\s*[\"']?([\w.-]+)[\"']?\s*$", text)
            if m:
                val = m.group(1).strip().lower()
                if val in ("off", "disabled", "false", "no", "0"):
                    return False
                if val in ("on", "enabled", "dev_only", "dev-only", "true", "yes", "1"):
                    return True
            m2 = re.search(r"(?m)^\s*mcp_policy:\s*[\"']?([\w.-]+)[\"']?\s*$", text)
            if m2:
                val = m2.group(1).strip().lower()
                if val in ("off", "disabled", "false", "no", "0"):
                    return False
                if val in ("on", "enabled", "dev_only", "dev-only", "true", "yes", "1"):
                    return True
            break

    return False  # product default: disabled

# Environment variable names that strongly suggest a public/production host.
PUBLIC_ENV_MARKERS: tuple[tuple[str, str], ...] = (
    ("DIGITALOCEAN_APP_ID", "DigitalOcean App Platform"),
    ("DO_APP_NAME", "DigitalOcean App Platform"),
    ("K_SERVICE", "Google Cloud Run"),
    ("KUBERNETES_SERVICE_HOST", "Kubernetes"),
    ("HEROKU_APP_NAME", "Heroku"),
    ("AWS_EXECUTION_ENV", "AWS managed runtime"),
    ("ECS_CONTAINER_METADATA_URI", "AWS ECS"),
    ("ECS_CONTAINER_METADATA_URI_V4", "AWS ECS"),
    ("FLY_APP_NAME", "Fly.io"),
    ("RENDER", "Render"),
    ("RAILWAY_ENVIRONMENT", "Railway"),
    ("VCENTER_RESOURCE_POOL", "vSphere managed"),  # rare; keep soft
)

# Values of APP_ENV / ENVIRONMENT / NODE_ENV that mean non-dev.
PROD_ENV_VALUES = frozenset(
    {
        "production",
        "prod",
        "staging",
        "live",
        "public",
    }
)

DEV_ENV_VALUES = frozenset(
    {
        "local",
        "development",
        "dev",
        "test",
        "testing",
        "ddev",
    }
)


def detect_public_or_prod_env(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Return whether the current process looks like a public/production host."""
    env = environ if environ is not None else dict(os.environ)
    hits: list[str] = []

    for key, label in PUBLIC_ENV_MARKERS:
        if env.get(key):
            hits.append(f"{label} ({key} set)")

    for key in ("APP_ENV", "ENVIRONMENT", "NODE_ENV", "RAILS_ENV", "PHP_ENV"):
        raw = (env.get(key) or "").strip().lower()
        if not raw:
            continue
        if raw in PROD_ENV_VALUES:
            hits.append(f"{key}={raw}")
        # explicit allow for local/dev even if other markers present is handled by caller

    # DO App Platform also sets PLATFORM_APPLICATION_NAME on some runtimes
    if env.get("PLATFORM_APPLICATION_NAME") and env.get("PORT"):
        # Ambiguous alone — only add if another signal or PLATFORM_* family
        if any(k.startswith("PLATFORM_") for k in env if k != "PLATFORM_APPLICATION_NAME"):
            hits.append("PaaS PLATFORM_* + PORT (likely hosted app runtime)")

    safe = len(hits) == 0
    return {
        "mcp_env_safe": "yes" if safe else "no",
        "mcp_public_signals": hits,
        "mcp_policy": "dev_only",
        "mcp_public_forbidden": "yes",
        "mcp_env_note": (
            "MCP is develop-only (local DDEV / docker-compose / host stdio). "
            "Do not run on publicly hosted environments."
            if safe
            else (
                "MCP blocked for public/production-like environment: "
                + "; ".join(hits)
                + ". Use local DDEV, Docker, or host stdio on a developer machine only."
            )
        ),
    }


def build_mcp_start_options(
    *,
    runtime: str,
    has_ddev: bool,
    has_compose: bool,
    has_mcp_server: bool,
    mcp_ready: str,
    ddev_running: str,
    compose_running: str,
    mcp_env_safe: str,
) -> list[dict[str, str]]:
    """Human-offerable start options when MCP is not ready (or always for briefing)."""
    if mcp_env_safe == "no":
        return [
            {
                "id": "refuse_public",
                "label": "Do not start MCP here",
                "detail": (
                    "This environment looks public/production. MCP is develop-only. "
                    "Use a local checkout with DDEV, Docker Compose, or host stdio."
                ),
                "commands": "",
            }
        ]

    options: list[dict[str, str]] = []

    if has_ddev or runtime == "ddev":
        cmds = []
        if ddev_running != "yes":
            cmds.append("ddev start")
        cmds.append("mkdir -p .ddev/web-build && cp mcp-server/ddev/Dockerfile.mcp .ddev/web-build/Dockerfile.mcp")
        cmds.append("ddev restart   # once after Dockerfile.mcp")
        cmds.append(
            "Enable Grok MCP: orchestrator-ddev in .grok/config.toml "
            "(see mcp-server/config/mcp.grok.project.example.toml); disable orchestrator-host"
        )
        options.append(
            {
                "id": "ddev",
                "label": "DDEV (recommended for app repos)",
                "detail": "stdio MCP inside DDEV web container — no public port",
                "commands": " && ".join(cmds) if len(cmds) > 1 else (cmds[0] if cmds else "ddev start"),
            }
        )

    if has_compose or runtime == "docker-compose":
        cmds = []
        if compose_running != "yes":
            cmds.append("docker compose up -d")
        cmds.append(
            "Host MCP (cache reads): ensure python3-venv or uv; "
            "bash scripts/mcp-host-stdio.sh  # or enable orchestrator-host in .grok/config.toml"
        )
        options.append(
            {
                "id": "docker_compose",
                "label": "Docker Compose + host MCP",
                "detail": "App via compose; MCP on developer host stdio (not published ports)",
                "commands": " && ".join(cmds),
            }
        )

    # Always offer local/host for template and non-DDEV
    options.append(
        {
            "id": "host_stdio",
            "label": "Local host stdio",
            "detail": "Orchestrator template / local runtime — developer machine only",
            "commands": (
                "bash scripts/ensure-mcp-host.sh   # uv preferred, or python3-venv; "
                "enable orchestrator-host in .grok/config.toml "
                "(args = [\"scripts/mcp-host-stdio.sh\"]); "
                "session-start / detect-project-runtime auto-repair the venv"
            ),
        }
    )

    if not has_mcp_server:
        options.insert(
            0,
            {
                "id": "deploy_mcp",
                "label": "Deploy MCP package into this app",
                "detail": "mcp-server/ missing at repo root",
                "commands": (
                    "From orchestrator: orchestrator upgrade /path/to/app "
                    "--selections mcp --no-pr (or add mcp to default selections)"
                ),
            },
        )

    if mcp_ready == "fail":
        options.insert(
            0,
            {
                "id": "handshake_repair",
                "label": "Repair MCP handshake",
                "detail": (
                    "Server binary/venv may exist but stdio list_tools/health_check failed"
                ),
                "commands": (
                    "bash scripts/mcp-smoke.sh ; "
                    "bash scripts/ensure-mcp-host.sh --force ; "
                    "bash scripts/mcp-smoke.sh --quiet"
                ),
            },
        )

    if mcp_ready == "yes":
        # Still list enablement if ready but agent may not have connected
        options.append(
            {
                "id": "client_enable",
                "label": "Enable MCP in the IDE client",
                "detail": "Runtime ready — client may still have MCP disabled",
                "commands": (
                    "Grok: /mcps enable orchestrator-ddev or orchestrator-host; "
                    "Cursor: .cursor/mcp.json from mcp-server/config/"
                ),
            }
        )

    return options


def format_start_options_text(options: list[dict[str, str]]) -> str:
    if not options:
        return "(none)"
    lines: list[str] = []
    for i, opt in enumerate(options, 1):
        lines.append(f"{i}. [{opt.get('id')}] {opt.get('label')}: {opt.get('detail')}")
        cmds = (opt.get("commands") or "").strip()
        if cmds:
            lines.append(f"   commands: {cmds}")
    return "\n".join(lines)


def session_mcp_brief(
    *,
    root: Path,
    runtime: str,
    has_ddev: bool,
    has_compose: bool,
    has_mcp_server: bool,
    mcp_ready: str,
    ddev_running: str,
    compose_running: str,
    mcp_note: str,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Combine enablement + env policy + start options for session-start briefing."""
    env = environ if environ is not None else dict(os.environ)
    if not mcp_is_enabled(root, env):
        note = (
            "MCP disabled (default). Cache-first via files/CLI only. "
            "Opt-in: ORCHESTRATOR_MCP=1 or runtime.mcp: dev_only in project-manifest."
        )
        return {
            "mcp_env_safe": "yes",
            "mcp_public_signals": [],
            "mcp_policy": "off",
            "mcp_public_forbidden": "yes",
            "mcp_env_note": note,
            "mcp_ready": "off",
            "mcp_note": note,
            "mcp_start_offer": "no",
            "mcp_start_options": [],
            "mcp_start_options_text": "(mcp disabled)",
            "briefing_line": "MCP: ready=off policy=off (not required for orchestrator)",
        }

    policy = detect_public_or_prod_env(env)
    if policy["mcp_env_safe"] == "no":
        ready = "blocked"
        note = policy["mcp_env_note"]
    else:
        ready = mcp_ready
        note = mcp_note or policy["mcp_env_note"]

    options = build_mcp_start_options(
        runtime=runtime,
        has_ddev=has_ddev,
        has_compose=has_compose,
        has_mcp_server=has_mcp_server,
        mcp_ready=ready,
        ddev_running=ddev_running,
        compose_running=compose_running,
        mcp_env_safe=policy["mcp_env_safe"],
    )

    offer = ready not in {"yes", "off"}
    brief_extra = ""
    if ready == "fail":
        brief_extra = " HANDSHAKE_FAIL run bash scripts/mcp-smoke.sh"
    elif note and ready != "yes":
        brief_extra = f" — {note}"
    return {
        **policy,
        "mcp_policy": "dev_only",  # when enabled, still develop-only
        "mcp_ready": ready,
        "mcp_note": note,
        "mcp_start_offer": "yes" if offer else "no",
        "mcp_start_options": options,
        "mcp_start_options_text": format_start_options_text(options),
        "briefing_line": (
            f"MCP: ready={ready} policy=dev_only env_safe={policy['mcp_env_safe']}"
            + brief_extra
        ),
    }

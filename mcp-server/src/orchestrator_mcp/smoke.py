"""MCP stdio smoke client — list_tools + health_check (no IDE required).

Used by scripts/mcp-smoke.sh and CI. Spawns orchestrator-mcp as a stdio server
and exercises the real MCP protocol (initialize → list_tools → call_tool).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path


def _resolve_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    # Prefer git root when available
    try:
        import subprocess

        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip()).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


def _server_command(root: Path) -> tuple[str, list[str]]:
    """Return (command, args) to run the MCP server over stdio."""
    venv_bin = root / "mcp-server" / ".venv" / "bin" / "orchestrator-mcp"
    if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
        return str(venv_bin), ["--transport", "stdio", "--project-root", str(root)]
    # Editable / PATH install (CI: pip install -e mcp-server/)
    which = shutil.which("orchestrator-mcp")
    if which:
        return which, ["--transport", "stdio", "--project-root", str(root)]
    # Module fallback
    return (
        sys.executable,
        [
            "-m",
            "orchestrator_mcp.server",
            "--transport",
            "stdio",
            "--project-root",
            str(root),
        ],
    )


async def run_smoke(root: Path, *, quiet: bool = False) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    cmd, args = _server_command(root)
    env = {**os.environ, "PROJECT_ROOT": str(root)}
    params = StdioServerParameters(command=cmd, args=args, env=env, cwd=str(root))

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools_result = await session.list_tools()
            tools = [t.name for t in (tools_result.tools or [])]
            health = await session.call_tool("health_check", {})
            # content is list of TextContent / structured
            health_payload: object = None
            if getattr(health, "structuredContent", None):
                health_payload = health.structuredContent
            elif health.content:
                texts = []
                for block in health.content:
                    text = getattr(block, "text", None)
                    if text is not None:
                        texts.append(text)
                if len(texts) == 1:
                    try:
                        health_payload = json.loads(texts[0])
                    except json.JSONDecodeError:
                        health_payload = texts[0]
                else:
                    health_payload = texts
            else:
                health_payload = {"status": "unknown"}

    out = {
        "ok": True,
        "project_root": str(root),
        "server_command": cmd,
        "server_args": args,
        "protocol": str(getattr(init, "protocolVersion", "") or ""),
        "tool_count": len(tools),
        "tools": tools,
        "health": health_payload,
        "has_health_check": "health_check" in tools,
    }
    if not out["has_health_check"]:
        out["ok"] = False
        out["error"] = "health_check tool missing from list_tools"
    elif isinstance(health_payload, dict) and health_payload.get("status") not in (
        "ok",
        None,
    ):
        # status ok is expected; missing status still counts if tool returned
        if health_payload.get("status") and health_payload.get("status") != "ok":
            out["ok"] = False
            out["error"] = f"health_check status={health_payload.get('status')}"
    if not quiet:
        print(json.dumps(out, indent=2, default=str))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MCP smoke: list_tools + health_check")
    ap.add_argument("--project-root", default=None, help="PROJECT_ROOT (default: git/cwd)")
    ap.add_argument("--quiet", action="store_true", help="Exit code only; no JSON stdout")
    ap.add_argument("--json", action="store_true", help="Force JSON on stdout (default)")
    args = ap.parse_args(argv)
    root = _resolve_root(args.project_root)
    try:
        result = asyncio.run(run_smoke(root, quiet=args.quiet))
    except Exception as exc:
        err = {
            "ok": False,
            "project_root": str(root),
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
        if args.quiet:
            print(f"mcp-smoke: FAIL {exc}", file=sys.stderr)
        else:
            print(json.dumps(err, indent=2))
        return 1
    if not result.get("ok"):
        if args.quiet:
            print(f"mcp-smoke: FAIL {result.get('error')}", file=sys.stderr)
        return 1
    if args.quiet:
        print(
            f"mcp-smoke: OK tools={result.get('tool_count')} health=ok",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

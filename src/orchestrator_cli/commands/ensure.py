"""`orchestrator ensure` — host MCP + host tools preflight."""

from __future__ import annotations

from pathlib import Path

from ..ensure_host import format_human, run_ensure, to_json


def run(
    *,
    path: Path | None = None,
    mcp: bool = True,
    host_tools: bool = True,
    check: bool = False,
    force: bool = False,
    yes: bool = False,
    quiet: bool = False,
    as_json: bool = False,
) -> int:
    report = run_ensure(
        path=path,
        mcp=mcp,
        host_tools=host_tools,
        check=check,
        force=force,
        yes=yes,
        quiet=quiet,
    )
    if as_json:
        print(to_json(report))
    else:
        print(format_human(report))
    return 0 if report.get("ok") else 1

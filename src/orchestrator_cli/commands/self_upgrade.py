"""`orchestrator self-upgrade` — refresh host CLI package."""

from __future__ import annotations

from typing import Any

from ..self_upgrade import format_human, run_self_upgrade, to_json


def run(
    *,
    to_version: str | None = None,
    from_github: str | bool | None = None,
    method: str = "auto",
    yes: bool = False,
    dry_run: bool = False,
    as_json: bool = False,
) -> int:
    code, result = run_self_upgrade(
        to_version=to_version,
        from_github=from_github,
        method=method,
        yes=yes,
        dry_run=dry_run,
        as_json=as_json,
    )
    if as_json:
        print(to_json(result))
    else:
        print(format_human(result))
    return code

"""`orchestrator version` — host / template / app lock matrix."""

from __future__ import annotations

import json
from pathlib import Path

from ..version import format_version_report, version_report


def run(*, as_json: bool = False, path: Path | None = None) -> int:
    target = (path or Path.cwd()).resolve()
    rep = version_report(target)
    if as_json:
        print(json.dumps(rep, indent=2, default=str))
        return 0
    print(format_version_report(rep))
    return 0

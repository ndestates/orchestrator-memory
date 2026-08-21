"""`orchestrator check` — announce install/upgrade status for a target."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .. import update_check


def run(target: Path, *, as_json: bool = False, quiet_ok: bool = False) -> int:
    notice = update_check.evaluate(target)
    if as_json:
        print(json.dumps(notice.to_dict(), indent=2))
        if notice.kind == update_check.UpdateKind.UPGRADE_AVAILABLE:
            return 2
        if notice.kind == update_check.UpdateKind.NOT_INSTALLED:
            return 3
        return 0

    if notice.kind == update_check.UpdateKind.UPGRADE_AVAILABLE:
        print(notice.message)
        if notice.action:
            print(f"  → {notice.action}")
        return 2
    if notice.kind == update_check.UpdateKind.NOT_INSTALLED:
        print(notice.message)
        if notice.action:
            print(f"  → {notice.action}")
        return 3
    if notice.kind == update_check.UpdateKind.TEMPLATE_SOURCE:
        print(f"orchestrator: template source tree ({notice.available}) — not an app install")
        return 0
    if notice.kind == update_check.UpdateKind.SKIPPED:
        print(
            f"orchestrator: no install lock and tree does not look like an app "
            f"({target}) — template {notice.available}"
        )
        return 0
    # up to date
    if not quiet_ok:
        print(notice.message)
    return 0

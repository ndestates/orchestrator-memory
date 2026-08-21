"""`orchestrator install-persist` — optional baseline for THIS app only.

Never fleet/wave. Never multi-app. Multi-branch broadcast is opt-in env only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..project_install import INSTALLED_BRANCH, project_global_install
from .. import gitops


def run(
    target: Path,
    *,
    as_json: bool = False,
    dry_run: bool = False,
) -> int:
    """Record baseline for this app repo (current branch install already present).

    Does **not** deploy to other apps. Does **not** broadcast to all branches
    unless ``ORCHESTRATOR_BRANCH_BROADCAST=1`` (discouraged).
    """
    target = target.resolve()
    report: dict = {
        "action": "install-persist",
        "target": str(target),
        "ok": False,
        "message": "",
        "baseline": INSTALLED_BRANCH,
    }

    if not (target / ".git").exists() and not (target / ".git").is_file():
        report["message"] = "not a git repository"
        _emit(report, as_json)
        return 1

    lock = target / ".orchestrator-version"
    if not lock.is_file():
        report["message"] = (
            "no .orchestrator-version on this branch — "
            "run `orchestrator init` or `upgrade` first, then install-persist"
        )
        _emit(report, as_json)
        return 1

    if dry_run:
        report["ok"] = True
        report["dry_run"] = True
        report["message"] = (
            f"dry-run: would set {INSTALLED_BRANCH} from HEAD on this app only "
            f"(no multi-branch broadcast unless ORCHESTRATOR_BRANCH_BROADCAST=1)"
        )
        try:
            ver = json.loads(lock.read_text(encoding="utf-8")).get("version")
            report["version"] = ver
        except (json.JSONDecodeError, OSError):
            pass
        _emit(report, as_json)
        return 0

    if not gitops.working_tree_clean(target):
        report["message"] = (
            "working tree is not clean — commit or stash before install-persist"
        )
        _emit(report, as_json)
        return 1

    try:
        ver = json.loads(lock.read_text(encoding="utf-8")).get("version")
        report["version"] = ver
    except (json.JSONDecodeError, OSError):
        ver = None

    result = project_global_install(target)
    report["ok"] = bool(result.get("ok"))
    report["message"] = result.get("message") or "install-persist done"
    report["detail"] = result
    report["hint"] = (
        f"Push baseline for other machines: git push -u origin {INSTALLED_BRANCH} "
        f"(optional). New branches: checkout runs post-checkout sync automatically "
        f"when core.hooksPath=.githooks."
    )
    _emit(report, as_json)
    return 0 if report["ok"] else 1


def _emit(report: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return
    print(report.get("message") or "install-persist")
    if report.get("version"):
        print(f"  version={report['version']}  target={report.get('target')}")
    if report.get("hint") and report.get("ok"):
        print(f"  note: {report['hint']}")
    if not report.get("ok"):
        print("  failed — see message above", file=sys.stderr)

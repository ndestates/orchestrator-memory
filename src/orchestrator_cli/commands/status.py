"""`orchestrator status` — installed vs available version + drift for a target.

Read-only. Consumed by humans and by daily-standup/health (via --json) to warn
when a newer orchestrator release exists.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..lock import read_lock
from ..licensing_policy import entitlement_summary, gate_enabled
from ..version import (
    cli_version,
    is_newer,
    is_template_source_tree,
    normalize_version,
    template_version,
)


def collect_status(target: Path) -> dict:
    lock = read_lock(target)
    installed = normalize_version(str(lock["version"])) if lock and lock.get("version") else None
    available = template_version()
    host = cli_version()
    source = is_template_source_tree(target)

    state_path = target / ".grok" / "deploy-state.json"
    customized = 0
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            files = state.get("files") or {}
            if isinstance(files, dict):
                customized = sum(
                    1
                    for f in files.values()
                    if isinstance(f, dict) and f.get("customized")
                )
            elif isinstance(files, list):
                customized = sum(
                    1 for f in files if isinstance(f, dict) and f.get("customized")
                )
        except (json.JSONDecodeError, OSError):
            pass

    license_info = entitlement_summary(target)

    return {
        "target": str(target),
        "ssot": "VERSION",
        "host_cli": host,
        "installed": installed,
        "available": available,
        "update_available": bool(installed)
        and not source
        and is_newer(available, installed),
        "uninstalled": installed is None and not source,
        "is_template_source": source,
        "customized_files": customized,
        "license": license_info,
        "cli_version_at_install": normalize_version(str(lock["cli_version"]))
        if lock and lock.get("cli_version")
        else None,
    }


def run(target: Path, *, as_json: bool) -> int:
    info = collect_status(target)
    if as_json:
        print(json.dumps(info, indent=2))
        return 0

    if info.get("is_template_source"):
        print(f"orchestrator: template source tree ({info['target']})")
        print(f"  host CLI: {info.get('host_cli')}  template: {info['available']}")
        print("  app install: N/A — use init/upgrade on consumer apps only")
        return 0

    if info["uninstalled"]:
        print(f"orchestrator: not installed in {info['target']}")
        print(f"  host CLI: {info.get('host_cli')}  template: {info['available']}")
        print(f"  → orchestrator init {info['target']} --no-pr")
        lic = info.get("license", {})
        if lic.get("gate_enabled"):
            print("  license: gate enabled — run `orchestrator license`")
        return 0

    line = f"orchestrator app {info['installed']}  (host {info.get('host_cli')})"
    if info["update_available"]:
        line += f"  ⚠ template {info['available']} available — run `orchestrator upgrade`"
    else:
        line += "  ✓ app up to date vs this CLI template"
    print(line)
    if info["customized_files"]:
        print(f"  {info['customized_files']} project-customized file(s) (preserved on upgrade)")

    lic = info.get("license", {})
    ent = lic.get("entitlement", {})
    kind = ent.get("kind", "unknown")
    if lic.get("dev_exempt"):
        print("  license: dev exempt")
    elif lic.get("gate_enabled"):
        print(f"  license: enforced (entitlement={kind})")
    else:
        print("  license: disabled (open for dev)")
    if ent.get("selections"):
        print(f"  deploy_selections: {ent['selections']}")
    return 0

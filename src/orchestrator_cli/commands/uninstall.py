"""CLI: uninstall host packages and/or project template surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..uninstall import (
    apply_project_uninstall,
    collect_project_paths,
    uninstall_host_cli,
)


def run(
    target: Path,
    *,
    dry_run: bool = True,
    yes: bool = False,
    host: bool = False,
    project: bool = True,
    selections: str | None = None,
    remove_cache: bool = False,
    remove_todo: bool = False,
    remove_state: bool = False,
    remove_memories: bool = False,
    remove_manifests: bool = False,
    force_template_source: bool = False,
    as_json: bool = False,
    npm: bool = True,
    pip: bool = True,
) -> int:
    """Uninstall orchestrator from a project and/or this machine's CLI packages.

    Default: project dry-run. Host uninstall: ``--host``. Apply deletes: ``--yes``.
    """
    target = target.resolve()
    out: dict = {"target": str(target), "dry_run": dry_run}
    mode = "DRY-RUN" if dry_run else "APPLY"
    exit_code = 0

    if not host and not project:
        print(
            "[uninstall] ERROR: nothing to do — pass --project and/or --host",
            file=sys.stderr,
        )
        return 2

    if host:
        host_result = uninstall_host_cli(dry_run=dry_run, npm=npm, pip=pip)
        out["host"] = host_result.to_dict()
        if not as_json:
            print(f"[uninstall:{mode}] host CLI packages (npm / pip)")
            for a in host_result.actions:
                print(f"  $ {a}")
            for e in host_result.errors:
                print(f"  WARNING: {e}", file=sys.stderr)
        if host_result.errors and not dry_run:
            exit_code = 1

    if project:
        plan = collect_project_paths(
            target,
            selections=selections,
            remove_cache=remove_cache,
            remove_todo=remove_todo,
            remove_state=remove_state,
            remove_memories=remove_memories,
            remove_manifests=remove_manifests,
            force_template_source=force_template_source,
        )
        out["project"] = plan.to_dict()
        if plan.errors:
            if as_json:
                print(json.dumps(out, indent=2))
            else:
                for e in plan.errors:
                    print(f"[uninstall] ERROR: {e}", file=sys.stderr)
            return 2

        if not as_json:
            lock_v = (plan.lock or {}).get("version", "none")
            print(f"[uninstall:{mode}] project={target}")
            print(f"  lock_version={lock_v}  paths_to_remove={len(plan.paths)}")
            for rel in plan.paths[:80]:
                print(f"  - {rel}")
            if len(plan.paths) > 80:
                print(f"  … +{len(plan.paths) - 80} more")
            if plan.skipped_protected:
                print(f"  skipped_protected={len(plan.skipped_protected)}")

        if dry_run:
            if not as_json:
                print(
                    "[uninstall] dry-run only — re-run with --yes to delete project paths"
                )
                if host:
                    print(
                        "[uninstall] host: re-run without --dry-run (and with --host) to uninstall packages"
                    )
        else:
            if not yes:
                print(
                    "[uninstall] ERROR: refusing to delete project files without --yes",
                    file=sys.stderr,
                )
                return 2
            removed = apply_project_uninstall(plan, dry_run=False)
            out["removed"] = removed
            if plan.errors:
                if as_json:
                    print(json.dumps(out, indent=2))
                for e in plan.errors:
                    print(f"[uninstall] ERROR: {e}", file=sys.stderr)
                return 1
            if not as_json:
                print(f"[uninstall] removed {len(removed)} path(s)")

    if as_json:
        print(json.dumps(out, indent=2))
    return exit_code

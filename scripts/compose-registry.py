#!/usr/bin/env python3
"""Compose chains/registry.yaml from registry.template.yaml + registry.app.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.registry_compose import registry_paths, write_composed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose chains/registry.yaml from split files")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root (default: orchestrator repo root)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compose in memory only; print summary")
    args = parser.parse_args()

    chains_dir = args.project_root / "chains"
    paths = registry_paths(chains_dir)
    if not paths["template"].is_file():
        print(f"compose-registry: missing {paths['template']}", file=sys.stderr)
        return 1

    composed = write_composed(chains_dir, dry_run=args.dry_run)
    n_skills = len(composed.get("skills") or [])
    n_chains = len(composed.get("chains") or [])
    if args.dry_run:
        print(f"compose-registry (dry-run): would write {paths['composed']}")
    else:
        print(f"compose-registry: wrote {paths['composed']}")
    print(f"  skills={n_skills} chains={n_chains}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""One-time split of monolithic chains/registry.yaml into template + app files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.registry_compose import (  # noqa: E402
    dump_yaml,
    load_yaml,
    registry_paths,
    split_monolithic,
    write_composed,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Split registry.yaml into template + app")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing split files")
    args = parser.parse_args()

    chains_dir = args.project_root / "chains"
    paths = registry_paths(chains_dir)
    if not paths["composed"].is_file():
        print(f"split-registry: missing {paths['composed']}", file=sys.stderr)
        return 1

    if paths["template"].is_file() and not args.force:
        print(f"split-registry: {paths['template']} exists (use --force)", file=sys.stderr)
        return 1

    monolithic = load_yaml(paths["composed"])
    template, app = split_monolithic(monolithic)

    if args.dry_run:
        print(
            f"split-registry (dry-run): template skills={len(template['skills'])} "
            f"chains={len(template['chains'])} | app skills={len(app['skills'])}"
        )
        return 0

    paths["template"].write_text(dump_yaml(template), encoding="utf-8")
    paths["app"].write_text(dump_yaml(app), encoding="utf-8")
    write_composed(chains_dir)
    print(f"split-registry: wrote {paths['template']}")
    print(f"split-registry: wrote {paths['app']}")
    print(f"split-registry: recomposed {paths['composed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
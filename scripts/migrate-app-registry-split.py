#!/usr/bin/env python3
"""
Migrate a wave app from monolithic chains/registry.yaml to split template + app files.

Preserves app-owned skills/chains by diffing against orchestrator template registry.
Never overwrites an existing registry.app.yaml unless --force.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.registry_compose import (  # noqa: E402
    dump_yaml,
    extract_app_overlay,
    load_yaml,
    registry_paths,
    write_composed,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate target app to split registry")
    parser.add_argument("--target", type=Path, required=True, help="App project root")
    parser.add_argument(
        "--orchestrator",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Orchestrator template root",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--skills-only",
        action="store_true",
        help="App overlay: skills only; chains come from template (slim migrate)",
    )
    parser.add_argument(
        "--chains-if-steps-differ",
        action="store_true",
        help="Include chain override only when step invoke list differs from template",
    )
    args = parser.parse_args()

    target = args.target.resolve()
    orch = args.orchestrator.resolve()
    t_paths = registry_paths(target / "chains")
    o_paths = registry_paths(orch / "chains")

    if not t_paths["composed"].is_file():
        print(f"migrate: missing {t_paths['composed']}", file=sys.stderr)
        return 1

    if t_paths["app"].is_file() and not args.force:
        print(f"migrate: {t_paths['app']} exists (use --force)", file=sys.stderr)
        return 1

    if o_paths["template"].is_file():
        template_registry = load_yaml(o_paths["template"])
    elif o_paths["composed"].is_file():
        from _engine.registry_compose import split_monolithic

        template_registry, _ = split_monolithic(load_yaml(o_paths["composed"]))
    else:
        print("migrate: orchestrator has no registry.template.yaml or registry.yaml", file=sys.stderr)
        return 1

    target_registry = load_yaml(t_paths["composed"])
    app_doc = extract_app_overlay(target_registry, template_registry)

    if args.skills_only:
        app_doc["chains"] = []
    elif args.chains_if_steps_differ:
        template_chains = {c["id"]: c for c in template_registry.get("chains", []) if c.get("id")}
        kept: list[dict] = []
        for chain in app_doc.get("chains") or []:
            cid = chain.get("id")
            tpl = template_chains.get(cid)
            if not tpl:
                kept.append(chain)
                continue
            t_steps = [s.get("invoke") for s in tpl.get("steps", [])]
            c_steps = [s.get("invoke") for s in chain.get("steps", [])]
            if t_steps != c_steps:
                kept.append(chain)
        app_doc["chains"] = kept

    if args.dry_run:
        print(
            f"migrate (dry-run) {target.name}: app skills={len(app_doc['skills'])} "
            f"chains={len(app_doc['chains'])}"
        )
        for s in app_doc["skills"]:
            print(f"  skill: {s['id']}")
        for c in app_doc["chains"]:
            print(f"  chain: {c['id']}")
        return 0

    if not args.dry_run:
        t_paths["template"].write_text(dump_yaml(template_registry), encoding="utf-8")
        t_paths["app"].write_text(dump_yaml(app_doc), encoding="utf-8")
        write_composed(target / "chains")
        print(f"migrate: wrote {t_paths['template']}")
        print(f"migrate: wrote {t_paths['app']}")
        print(f"migrate: recomposed {t_paths['composed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
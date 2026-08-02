#!/usr/bin/env python3
"""Session-start lean memory brief (always-on memory layer).

Surfaces store stats + model/agent picks + optional situation query.
Does not re-derive world from a stale feature-branch TODO alone.

Usage:
  python3 scripts/session-memory-brief.py
  python3 scripts/session-memory-brief.py --json
  python3 scripts/session-memory-brief.py --seed   # seed situation then brief
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from _engine import memory_agents as magents  # noqa: E402
from _engine import memory_models as mmodels  # noqa: E402
from _engine import memory_store as mstore  # noqa: E402


def build_brief(root: Path, *, seed: bool = False) -> dict:
    if seed:
        import memory_agent as ma

        seed_result = ma.seed_situation(root)
    else:
        seed_result = None

    path = mstore.default_db_path(root)
    stats = mstore.get_stats(path)
    models = mmodels.models_inventory_brief(root)
    agents = magents.agents_inventory_brief(root)
    recent = mstore.read_memories(path, limit=5)["memories"]
    cons = mstore.read_consolidations(path, limit=3)["consolidations"]

    # Light situation answer without forcing LLM
    import memory_agent as ma

    situation = ma.do_query(root, "Where are we and what is open next?")

    return {
        "status": "ok" if stats["total_memories"] or seed_result else "empty",
        "stats": stats,
        "models_catalog_total": models["catalog_total"],
        "oss_count": models["oss_count"],
        "free_cloud_count": models["free_cloud_count"],
        "frontier_count": models["frontier_count"],
        "agents_count": agents["count"],
        "picks": {
            "ingest_model": models["picks"]["ingest"].get("id"),
            "consolidate_model": models["picks"]["consolidate"].get("id"),
            "query_model": models["picks"]["query"].get("id"),
            "ingest_agent": agents["role_picks"].get("ingest"),
            "consolidate_agent": agents["role_picks"].get("consolidate"),
            "query_agent": agents["role_picks"].get("query"),
        },
        "recent_summaries": [m.get("summary") for m in recent],
        "insights": [c.get("insight") or c.get("summary") for c in cons],
        "situation": situation.get("answer"),
        "situation_agent": situation.get("agent"),
        "situation_model": (situation.get("model_pick") or {}).get("id"),
        "seed": seed_result,
    }


def print_human(brief: dict) -> None:
    print(
        f"Memory: {brief.get('status')} · "
        f"memories={brief['stats'].get('total_memories', 0)} · "
        f"unconsolidated={brief['stats'].get('unconsolidated', 0)} · "
        f"consolidations={brief['stats'].get('consolidations', 0)}"
    )
    picks = brief.get("picks") or {}
    print(
        f"  models catalog={brief.get('models_catalog_total')} "
        f"(oss={brief.get('oss_count')} free_cloud={brief.get('free_cloud_count')} "
        f"frontier={brief.get('frontier_count')}) · agents={brief.get('agents_count')}"
    )
    print(
        f"  picks: ingest={picks.get('ingest_model')}/{picks.get('ingest_agent')} · "
        f"consolidate={picks.get('consolidate_model')}/{picks.get('consolidate_agent')} · "
        f"query={picks.get('query_model')}/{picks.get('query_agent')}"
    )
    if brief.get("situation"):
        print("  situation:")
        for line in str(brief["situation"]).splitlines()[:12]:
            print(f"    {line}")
    if brief.get("insights"):
        print("  insights:")
        for ins in brief["insights"][:3]:
            print(f"    - {ins}")
    print("  → CLI: python3 scripts/memory_agent.py query|ingest|serve|models|agents")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--seed", action="store_true", help="Seed situation snapshot first")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    brief = build_brief(args.root.resolve(), seed=args.seed)
    if args.json:
        print(json.dumps(brief, indent=2))
    else:
        print_human(brief)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

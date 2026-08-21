"""Vault Graph Synthesis (self-building).

L1 report-only. Walks the secure vault graph (events.jsonl) and proposes higher-order knowledge updates.

Strong security: reads only verified events; proposals never auto-apply (human gate + compound queue).

Use after compound or in watches:
  python3 scripts/_engine/vault_synthesis.py --ledger reports/vault/events.jsonl --json

Future: integrate with loop-compound or dedicated chain step for autonomous vault growth.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Robust import when run directly or as module
try:
    from scripts._engine import vault as vault_mod
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts._engine import vault as vault_mod


def synthesize(
    ledger_path: Path,
    query: str | None = None,
    query_type: str | None = None,
    area: str | None = None,
    build_chain: bool = False,
    hint: bool = False,
) -> dict:
    events = vault_mod.load_events(ledger_path)
    if not events:
        return {"status": "no_events", "proposals": []}

    ok, issues = vault_mod.verify_ledger(ledger_path)
    graph = vault_mod.build_simple_graph(events)

    proposals = []
    # Simple clustering example (self-building logic)
    lesson_events = [e for e in events if e.get("type") == "lesson"]
    if len(lesson_events) >= 2:
        proposals.append({
            "type": "meta_pattern",
            "summary": f"Observed {len(lesson_events)} lessons. Consider promoting recurring themes to patterns or CONCERNS.",
            "confidence": "low",
            "action": "human review via compound queue",
        })

    if issues:
        proposals.append({
            "type": "integrity",
            "summary": f"Vault ledger has {len(issues)} integrity issues. Investigate immediately.",
            "severity": "high",
        })

    similar = []
    precedents = []
    if query:
        if hint:
            # Use auto-hint mode (via vault_query if available, fallback)
            try:
                from scripts._engine import vault_query as vq_mod
                hres = vq_mod.auto_hint_for_task(query, ledger_path=ledger_path, limit=3)
                proposals.append({
                    "type": "auto_hint",
                    "summary": f"Auto-hint for task (area={hres.get('detected_area')})",
                    "hints": hres.get("hints", []),
                })
            except Exception:
                pass  # fall through

        # Prefer the richer Lane 2 find_precedents
        try:
            precedents = vault_mod.find_precedents(
                ledger_path, query, area=area, event_type=query_type, limit=3, build_chain=build_chain
            )
        except Exception:
            precedents = []
            similar = vault_mod.find_similar_events(ledger_path, query, event_type=query_type, area=area, min_ratio=0.4)

        if precedents:
            proposals.append({
                "type": "similar_precedent",
                "summary": f"Found {len(precedents)} precedents for '{query[:50]}' (area={area or 'any'}). Judgment + fixes + chains (Lane 2).",
                "precedents": precedents,
            })
        elif similar:
            # Legacy path
            fixes = []
            for m in similar[:3]:
                ev = m["event"]
                ev_id = ev.get("id") or ev.get("content_hash")
                for p in ev.get("parents", []):
                    for e in events:
                        if e.get("content_hash") == p and e.get("type") in ("fix", "solution", "resolution", "outcome"):
                            fixes.append({"for": ev_id, "via": "parent", "fix": e.get("payload")})
                for rel in ev.get("relations", []) or []:
                    if isinstance(rel, dict) and rel.get("target"):
                        for e in events:
                            if e.get("content_hash") == rel["target"] and e.get("type") in ("fix", "solution", "precedent", "outcome"):
                                fixes.append({"for": ev_id, "via": rel.get("type", "relation"), "fix": e.get("payload")})
            proposals.append({
                "type": "similar_precedent",
                "summary": f"Found {len(similar)} similar events for query '{query[:50]}' (type={query_type or 'any'}, area={area or 'any'}).",
                "matches": similar[:3],
                "fixes": fixes[:3] if fixes else "No direct fix linked yet; check full graph.",
            })

    return {
        "status": "ok" if ok else "issues",
        "events": len(events),
        "graph_nodes": len(graph["nodes"]),
        "verify_ok": ok,
        "issues": issues[:3],
        "proposals": proposals,
        "similar": similar if query and not precedents else [],
        "precedents": precedents if query else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault synthesis + Lane 2 query enhancements (precedents, chains, hints)")
    parser.add_argument("--ledger", type=Path, default=Path("reports/vault/events.jsonl"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--query", type=str, help="Query text for similar precedents (e.g. error message)")
    parser.add_argument("--query-type", type=str, help="Filter by event type e.g. error, lesson")
    parser.add_argument("--area", type=str, help="Filter by area e.g. reasoning, code, deploy")
    parser.add_argument("--build-chain", action="store_true", help="Build reasoning chain via parents + relations (Lane 2)")
    parser.add_argument("--hint", action="store_true", help="Auto-hint mode for task-like queries")
    args = parser.parse_args()

    result = synthesize(
        args.ledger,
        query=args.query,
        query_type=args.query_type,
        area=args.area,
        build_chain=args.build_chain,
        hint=args.hint,
    )
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Vault synthesis: {result['status']} events={result['events']} nodes={result.get('graph_nodes')}")
        for p in result.get("proposals", []):
            print(f"  Proposal: {p}")
        if result.get("precedents"):
            print("Precedents (Lane 2):")
            for p in result["precedents"][:2]:
                print(f"  {p.get('judgment')} sim={p.get('similarity')}: {str(p.get('event',{}).get('payload',{}))[:70]}")
                if p.get("reasoning_chain"):
                    ch = p["reasoning_chain"]
                    print(f"    chain: depth={ch.get('depth')} steps={[s.get('type') for s in ch.get('steps', [])[:3]]}")
        elif result.get("similar"):
            print("Similar matches:")
            for m in result["similar"][:3]:
                print(f"  sim={m['similarity']}: {m['event'].get('payload', {}) }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

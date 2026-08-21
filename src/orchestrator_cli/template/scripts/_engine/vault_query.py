"""Vault Query (Lane 2).

Richer query interface over the secure vault graph for self-learning precedents,
reasoning chains, and auto-hints.

- find_precedents / build_reasoning_chain wrappers
- auto_hint_for_task: detects error/code/deploy queries and returns actionable precedents
- CLI: python3 scripts/_engine/vault_query.py --query "..." [--area deploy] [--build-chain] [--hint]

Pure stdlib + existing vault primitives. L1 report-only. No auto-mutation.

Usage in code / chains:
  from scripts._engine import vault_query as vq
  hints = vq.auto_hint_for_task("fix the branch promotion error in wave deploy")
  chain = vq.build_chain_for_query(ledger, "the error msg", build_chain=True)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Robust import
try:
    from scripts._engine import vault as vault_mod
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts._engine import vault as vault_mod


DEFAULT_LEDGER = Path("reports/vault/events.jsonl")


def query_precedents(
    query: str,
    ledger_path: Path = DEFAULT_LEDGER,
    area: str | None = None,
    event_type: str | None = None,
    limit: int = 5,
    build_chain: bool = False,
) -> dict[str, Any]:
    """High-level wrapper. Returns synthesis-style result with precedents."""
    if not ledger_path.exists():
        return {"status": "no_ledger", "precedents": []}

    precedents = vault_mod.find_precedents(
        ledger_path, query, area=area, event_type=event_type, limit=limit, build_chain=build_chain
    )
    ok, issues = vault_mod.verify_ledger(ledger_path)
    return {
        "status": "ok" if ok else "issues",
        "query": query,
        "area": area,
        "precedents": precedents,
        "issues": issues[:2] if issues else [],
        "verify_ok": ok,
    }


def build_chain_for_query(
    query: str,
    ledger_path: Path = DEFAULT_LEDGER,
    area: str | None = None,
    limit: int = 1,
) -> dict[str, Any]:
    """Convenience: run find + build reasoning chain for top match."""
    res = query_precedents(query, ledger_path=ledger_path, area=area, limit=limit, build_chain=True)
    chains = []
    for p in res.get("precedents", []):
        if "reasoning_chain" in p:
            chains.append({"for": p.get("judgment"), "chain": p["reasoning_chain"]})
    res["chains"] = chains
    return res


def auto_hint_for_task(
    task_description: str,
    ledger_path: Path = DEFAULT_LEDGER,
    limit: int = 3,
) -> dict[str, Any]:
    """Auto 'hint' mode (Lane 2).
    If the task smells like error/fix/code/deploy, auto-query precedents + chains.
    Returns hints ready to inject into orchestrator / skills / user prompts.
    Simple heuristics; no ML.
    """
    q = task_description.lower()
    hint_area = None
    hint_type = None
    if any(k in q for k in ("error", "fail", "exception", "traceback", "bug", "crash")):
        hint_type = "error"
        hint_area = "deploy" if any(k in q for k in ("deploy", "wave", "branch", "promotion")) else None
    elif any(k in q for k in ("deploy", "wave", "branch", "promotion", "ci", "workflow")):
        hint_area = "deploy"
    elif any(k in q for k in ("code", "implement", "refactor", "pattern")):
        hint_area = "code"

    res = query_precedents(
        task_description,
        ledger_path=ledger_path,
        area=hint_area,
        event_type=hint_type,
        limit=limit,
        build_chain=True,
    )

    # Extract concise hints
    hints = []
    for prec in res.get("precedents", []):
        ev = prec.get("event", {})
        payload = ev.get("payload", {})
        hint = {
            "judgment": prec.get("judgment"),
            "similarity": prec.get("similarity"),
            "summary": str(payload)[:140],
            "type": ev.get("type"),
            "area": ev.get("area"),
            "fixes": prec.get("linked_fixes", []),
        }
        if "reasoning_chain" in prec:
            ch = prec["reasoning_chain"]
            hint["chain_depth"] = ch.get("depth")
            hint["chain_steps"] = [s.get("type") for s in ch.get("steps", [])]
        hints.append(hint)

    return {
        "status": res.get("status"),
        "task": task_description[:80],
        "detected_area": hint_area,
        "detected_type": hint_type,
        "hints": hints,
        "raw": res,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault query CLI (Lane 2) — precedents, chains, auto-hints")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--query", type=str, required=True, help="Query text e.g. error message or task")
    parser.add_argument("--area", type=str, help="Filter area e.g. deploy, reasoning, code")
    parser.add_argument("--query-type", type=str, help="Event type filter e.g. error, problem")
    parser.add_argument("--build-chain", action="store_true", help="Traverse parents+relations for reasoning chain")
    parser.add_argument("--hint", action="store_true", help="Auto-hint mode (detect task type and return actionable hints)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    if args.hint:
        result = auto_hint_for_task(args.query, ledger_path=args.ledger, limit=args.limit)
    elif args.build_chain:
        result = build_chain_for_query(args.query, ledger_path=args.ledger, area=args.area, limit=args.limit)
    else:
        result = query_precedents(
            args.query,
            ledger_path=args.ledger,
            area=args.area,
            event_type=args.query_type,
            limit=args.limit,
            build_chain=args.build_chain,
        )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Vault query: {result.get('status')} query='{args.query[:60]}' area={args.area or 'any'}")
        if args.hint and "hints" in result:
            for i, h in enumerate(result["hints"], 1):
                print(f"  Hint {i} ({h.get('judgment')}): {h.get('summary')}")
                if h.get("fixes"):
                    print(f"    fixes: {h['fixes'][:1]}")
        elif "precedents" in result:
            for p in result["precedents"][:2]:
                print(f"  {p.get('judgment')} sim={p.get('similarity')}: {str(p.get('event',{}).get('payload',{}))[:80]}")
                if "reasoning_chain" in p:
                    ch = p["reasoning_chain"]
                    print(f"    chain depth={ch.get('depth')}: {[s.get('type') for s in ch.get('steps',[])[:4]]}")
        if result.get("chains"):
            print("Chains:", len(result["chains"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

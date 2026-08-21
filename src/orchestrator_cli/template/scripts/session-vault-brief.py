#!/usr/bin/env python3
"""Session-start vault brief — mandatory lean load of durable lessons.

The vault graph is the cross-session brain. Session-start MUST surface recent
lessons (and optional task-area hints) so agents do not re-plan finished work.

Usage:
  python3 scripts/session-vault-brief.py              # last lessons + verify
  python3 scripts/session-vault-brief.py --json
  python3 scripts/session-vault-brief.py --query "installer fleet npm"
  python3 scripts/session-vault-brief.py --limit 5 --area deploy

Exit 0 always when ledger missing (status=no_ledger); non-zero only on crash.

Deployed to apps via the ``scripts`` selection (this file + ``scripts/_engine``).
Apps without a vault ledger get status=no_ledger (continue session; do not invent
lessons). Apps that have not been upgraded yet will lack this script — standup
must report vault brief unavailable once and continue.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts._engine import vault as vault_mod
    from scripts._engine import vault_query as vault_query_mod
except ImportError:
    from _engine import vault as vault_mod  # type: ignore
    from _engine import vault_query as vault_query_mod  # type: ignore

DEFAULT_LEDGER = ROOT / "reports" / "vault" / "events.jsonl"
LEARNING_TYPES = frozenset(
    {
        "lesson",
        "synthesis",
        "codebase_knowledge",
        "pattern",
        "precedent",
        "fix",
    }
)
# session_startup is process metadata (remote_last-first double-check), not a "lesson"


def _payload_text(ev: dict[str, Any]) -> str:
    p = ev.get("payload") or {}
    if not isinstance(p, dict):
        return str(p)[:300]
    for key in ("text", "summary", "lesson", "message"):
        if p.get(key):
            return str(p[key]).strip()
    return json.dumps(p, ensure_ascii=False)[:300]


def recent_lessons(
    ledger: Path,
    *,
    limit: int = 5,
    types: frozenset[str] = LEARNING_TYPES,
) -> list[dict[str, Any]]:
    if not ledger.is_file():
        return []
    events = vault_mod.load_events(ledger)
    out: list[dict[str, Any]] = []
    for ev in reversed(events):
        if ev.get("type") not in types:
            continue
        raw = _payload_text(ev)[:400]
        safe, hits = vault_mod.scrub_for_ai_context(raw)
        item: dict[str, Any] = {
            "type": ev.get("type"),
            "content_hash": (ev.get("content_hash") or "")[:16],
            "source": ev.get("source"),
            "area": (ev.get("metadata") or {}).get("area") or ev.get("area"),
            "text": safe,
            "ts": ev.get("ts") or ev.get("timestamp"),
        }
        if hits:
            item["content_filtered"] = hits
        out.append(item)
        if len(out) >= limit:
            break
    return out


def build_brief(
    ledger: Path,
    *,
    limit: int = 5,
    query: str | None = None,
    area: str | None = None,
) -> dict[str, Any]:
    if not ledger.is_file():
        return {
            "status": "no_ledger",
            "ledger": str(ledger),
            "verify_ok": None,
            "lessons": [],
            "precedents": [],
            "briefing_lines": [
                "Vault: no ledger at reports/vault/events.jsonl — brain empty for this checkout.",
            ],
        }

    ok, issues = vault_mod.verify_ledger(ledger)
    lessons = recent_lessons(ledger, limit=limit)
    precedents: list[Any] = []
    if query:
        q = vault_query_mod.query_precedents(
            query, ledger_path=ledger, area=area, limit=min(3, limit)
        )
        precedents = q.get("precedents") or []

    # Double-check: last recorded remote_last-first startup (session-start / end / eod)
    startup = vault_mod.get_latest_session_startup(ledger)
    startup_brief: dict[str, Any] | None = None
    if startup:
        sp = startup.get("payload") or {}
        startup_brief = {
            "phase": sp.get("phase"),
            "startup_policy": sp.get("startup_policy"),
            "branch": sp.get("branch"),
            "remote_last": sp.get("remote_last"),
            "on_remote_last": sp.get("on_remote_last"),
            "switch_result": sp.get("switch_result"),
            "content_hash": (startup.get("content_hash") or "")[:16],
            "ts": startup.get("ts"),
            "source": startup.get("source"),
        }

    lines = [
        f"Vault: ledger={'OK' if ok else 'ISSUES'} · lessons={len(lessons)}"
        + (f" · query_hits={len(precedents)}" if query else ""),
    ]
    if not ok and issues:
        lines.append(f"  verify: {issues[0][:120]}")
    if startup_brief:
        lines.append(
            f"  startup: phase={startup_brief.get('phase')} "
            f"policy={startup_brief.get('startup_policy')} "
            f"branch={startup_brief.get('branch')} "
            f"remote_last={startup_brief.get('remote_last')} "
            f"on_tip={startup_brief.get('on_remote_last')} "
            f"({startup_brief.get('content_hash')})"
        )
        lines.append(
            "  → Startup order double-check: fetch→remote_last switch/pull→THEN card"
        )
    for i, les in enumerate(lessons, 1):
        area_s = f" [{les.get('area')}]" if les.get("area") else ""
        flag = " ⚠filtered" if les.get("injection_filtered") else ""
        lines.append(
            f"  L{i}{area_s}{flag} ({les.get('content_hash')}): {les.get('text', '')[:180]}"
        )
    for i, p in enumerate(precedents[:3], 1):
        judgment = p.get("judgment") or p.get("text") or str(p)[:180]
        lines.append(f"  Q{i}: {str(judgment)[:180]}")

    if lessons:
        lines.append(
            "  → Cite vault lessons in briefing; do not re-plan work already recorded as done."
        )

    return {
        "status": "ok" if ok else "issues",
        "ledger": str(ledger),
        "verify_ok": ok,
        "issues": (issues or [])[:3],
        "lessons": lessons,
        "precedents": precedents,
        "session_startup": startup_brief,
        "briefing_lines": lines,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--query", default=None, help="Optional precedent query")
    ap.add_argument("--area", default=None, help="Optional area filter for query")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    brief = build_brief(
        args.ledger, limit=args.limit, query=args.query, area=args.area
    )
    if args.json:
        print(json.dumps(brief, indent=2, ensure_ascii=False))
    else:
        for line in brief["briefing_lines"]:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

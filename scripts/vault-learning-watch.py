#!/usr/bin/env python3
"""Show when the vault brain learned something new.

Learning types: lesson, workspace_pointer, synthesis, problem, fix, reasoning_trace,
outcome, precedent, self_improvement, meta_pattern.

Usage:
  python3 scripts/vault-learning-watch.py              # last 8 learning events
  python3 scripts/vault-learning-watch.py --since 10m  # events in last 10 minutes
  python3 scripts/vault-learning-watch.py --baseline   # save count for --diff
  python3 scripts/vault-learning-watch.py --diff       # show events since baseline
  python3 scripts/vault-learning-watch.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts._engine import vault as vmod  # noqa: E402

DEFAULT_LEDGER = Path("reports/vault/events.jsonl")
BASELINE_FILE = Path("reports/vault/.learning-baseline.json")

LEARNING_TYPES = frozenset({
    "lesson",
    "workspace_pointer",
    "synthesis",
    "problem",
    "fix",
    "reasoning_trace",
    "outcome",
    "precedent",
    "self_improvement",
    "meta_pattern",
})


def _parse_since(spec: str) -> datetime:
    m = re.fullmatch(r"(\d+)(m|h|d)", spec.strip())
    if not m:
        raise ValueError(f"bad --since value: {spec!r} (use e.g. 10m, 2h, 1d)")
    n, unit = int(m.group(1)), m.group(2)
    delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n), "d": timedelta(days=n)}[unit]
    return datetime.now(timezone.utc) - delta


def _event_summary(ev: dict) -> str:
    p = ev.get("payload") or {}
    if ev.get("type") == "workspace_pointer":
        return f"operator={p.get('operator')} branch={p.get('branch')}"
    return str(p.get("text") or p.get("summary") or p.get("description") or p)[:120]


def _filter_learning(events: list[dict], since: datetime | None) -> list[dict]:
    out = []
    for ev in events:
        if ev.get("type") not in LEARNING_TYPES:
            continue
        if since:
            ts = ev.get("ts", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt < since:
                    continue
            except Exception:
                pass
        out.append(ev)
    return out


def _save_baseline(ledger: Path, events: list[dict]) -> dict:
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "ledger": str(ledger),
        "total_events": len(events),
        "learning_events": len(_filter_learning(events, None)),
        "last_content_hash": events[-1].get("content_hash") if events else None,
    }
    BASELINE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def _events_since_baseline(events: list[dict]) -> list[dict]:
    if not BASELINE_FILE.exists():
        return _filter_learning(events, None)
    data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    last = data.get("last_content_hash")
    if not last:
        return []
    seen_last = False
    new: list[dict] = []
    for ev in events:
        if seen_last:
            if ev.get("type") in LEARNING_TYPES:
                new.append(ev)
        if ev.get("content_hash") == last:
            seen_last = True
    return new


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch vault brain learning events")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--tail", type=int, default=8)
    parser.add_argument("--since", help="e.g. 10m, 2h, 1d")
    parser.add_argument("--baseline", action="store_true", help="Save baseline for --diff")
    parser.add_argument("--diff", action="store_true", help="Events since last --baseline")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ledger = Path(args.ledger)
    events = vmod.load_events(ledger)
    ok, issues = vmod.verify_ledger(ledger)

    if args.baseline:
        data = _save_baseline(ledger, events)
        print(f"Baseline saved: {data['total_events']} total, {data['learning_events']} learning")
        print(f"  file: {BASELINE_FILE}")
        return 0

    since = _parse_since(args.since) if args.since else None
    if args.diff:
        picked = _events_since_baseline(events)
        label = "since baseline"
    elif since:
        picked = _filter_learning(events, since)
        label = f"since {args.since}"
    else:
        all_learning = _filter_learning(events, None)
        picked = all_learning[-args.tail :]
        label = f"last {len(picked)}"

    payload = {
        "verify_ok": ok,
        "issues": issues[:3],
        "total_events": len(events),
        "learning_shown": len(picked),
        "label": label,
        "events": [
            {
                "ts": e.get("ts"),
                "type": e.get("type"),
                "area": e.get("area"),
                "id": e.get("id"),
                "summary": _event_summary(e),
            }
            for e in picked
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"Vault brain: {len(events)} events | verify={'PASS' if ok else 'FAIL'} | showing {label}")
    if not picked:
        print("  (no learning events in range)")
        return 0
    for e in picked:
        ts = (e.get("ts") or "")[:19]
        print(f"  [{ts}] {e.get('type'):18} {e.get('area') or '-':10} {_event_summary(e)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
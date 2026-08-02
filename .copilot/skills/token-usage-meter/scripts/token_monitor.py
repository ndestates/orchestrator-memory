#!/usr/bin/env python3
"""
Always-on Grok session token monitor.

Parses ~/.grok/sessions/<encoded-project>/<session-id>/updates.jsonl for
totalTokens per turn, appends to reports/tokens/session-log.jsonl, and prints
a compact summary for agents to surface every response.

Usage:
  python token_monitor.py --sync --project /path/to/repo
  python token_monitor.py --report
  python token_monitor.py --analyze /path/to/updates.jsonl
  python token_monitor.py --footer   # one-line footer from latest sync
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from token_lib import (
    analyze_context_growth,
    analyze_session_costs,
    analyze_turn_efficiency,
    format_cost_report,
    format_session_footer,
)


GROK_SESSIONS_ROOT = Path.home() / ".grok" / "sessions"
DEFAULT_LOG = "reports/tokens/session-log.jsonl"
DEFAULT_STATE = "reports/tokens/.sync-state.json"
DEFAULT_SUMMARY = "reports/tokens/latest-summary.json"


def encode_project_path(project_path: Path) -> str:
    return quote(str(project_path.resolve()), safe="")


def find_latest_session(project_path: Path) -> Optional[Tuple[Path, str]]:
    """Return (session_dir, session_id) for the most recently modified session."""
    encoded = encode_project_path(project_path)
    sessions_dir = GROK_SESSIONS_ROOT / encoded
    if not sessions_dir.is_dir():
        return None

    candidates: List[Tuple[float, Path, str]] = []
    for child in sessions_dir.iterdir():
        if not child.is_dir():
            continue
        updates = child / "updates.jsonl"
        if updates.is_file():
            candidates.append((updates.stat().st_mtime, child, child.name))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, session_dir, session_id = candidates[0]
    return session_dir, session_id


def parse_session_updates(updates_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
    """Single-pass parse of updates.jsonl → (model_id, turns).

    Avoids double full-file read/parse (Phase A BH-004).
    """
    model_counts: Dict[str, int] = {}
    turn_tokens: Dict[int, int] = {}
    turn_user: Dict[int, str] = {}

    try:
        raw = updates_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "grok-composer-2.5-fast", []

    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        params = obj.get("params", {})
        update = params.get("update", {})
        meta = params.get("_meta", {}) or obj.get("_meta", {})

        kind = update.get("sessionUpdate", "")
        if kind == "user_message_chunk":
            text = update.get("content", {}).get("text", "")
            ts = meta.get("agentTimestampMs") or obj.get("timestamp")
            if ts:
                turn_user[ts] = text.strip().replace("\n", " ")[:120]
            model_id = update.get("content", {}).get("_meta", {}).get("modelId")
            if not model_id:
                model_id = params.get("_meta", {}).get("modelId")
            if model_id:
                model_counts[model_id] = model_counts.get(model_id, 0) + 1

        if "totalTokens" not in meta:
            continue

        turn_start = meta.get("turnStartMs")
        if turn_start is None:
            continue

        turn_tokens[turn_start] = max(turn_tokens.get(turn_start, 0), meta["totalTokens"])

    model = (
        max(model_counts, key=model_counts.get)  # type: ignore[arg-type]
        if model_counts
        else "grok-composer-2.5-fast"
    )

    turns: List[Dict[str, Any]] = []
    prev_context = 0
    for idx, turn_start in enumerate(sorted(turn_tokens), start=1):
        context = turn_tokens[turn_start]
        delta = context - prev_context
        prev_context = context
        user_preview = turn_user.get(turn_start, "")
        turns.append(
            {
                "turn_index": idx,
                "turn_start_ms": turn_start,
                "context_tokens": context,
                "turn_delta": delta,
                "user_preview": user_preview,
            }
        )

    return model, turns


def parse_session_model_id(updates_path: Path) -> str:
    """Return the most common modelId seen in user messages."""
    model_id, _ = parse_session_updates(updates_path)
    return model_id


def parse_session_turns(updates_path: Path) -> List[Dict[str, Any]]:
    """Extract per-turn context size and user message preview from updates.jsonl."""
    _, turns = parse_session_updates(updates_path)
    return turns


def load_json(path: Path) -> Dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def append_log(log_path: Path, records: List[Dict[str, Any]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_summary(
    turns: List[Dict[str, Any]],
    *,
    session_id: str,
    project_path: str,
    model_id: str = "grok-composer-2.5-fast",
) -> Dict[str, Any]:
    if not turns:
        return {
            "session_id": session_id,
            "project_path": project_path,
            "turn_count": 0,
            "context_tokens": 0,
            "turn_delta": 0,
            "status": "ok",
            "warnings": [],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    last = turns[-1]
    growth = analyze_context_growth(last["context_tokens"], last["turn_delta"])
    total_delta = sum(t["turn_delta"] for t in turns)
    costs = analyze_session_costs(turns, model_id=model_id)
    warnings = list(growth["warnings"])
    warnings.extend(analyze_turn_efficiency(turns))

    return {
        "session_id": session_id,
        "project_path": project_path,
        "model_id": costs.get("model_id", model_id),
        "model_label": costs.get("label", model_id),
        "turn_count": len(turns),
        "context_tokens": last["context_tokens"],
        "turn_delta": last["turn_delta"],
        "session_total_growth": total_delta,
        "status": growth["status"],
        "warnings": warnings,
        "last_user_preview": last.get("user_preview", ""),
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "session_cost_usd": costs.get("session_cost_usd", 0.0),
        "last_turn_cost_usd": costs.get("last_turn_cost_usd", 0.0),
        "cost_per_turn_avg_usd": costs.get("cost_per_turn_avg_usd", 0.0),
        "cache_savings_usd": costs.get("cache_savings_usd", 0.0),
        "cost_is_estimate": costs.get("is_estimate", True),
        "pricing_note": costs.get("pricing_note"),
        "turns": turns[-5:],
        "cost": costs,
    }


def sync_project(
    project_path: Path,
    *,
    log_path: Path,
    state_path: Path,
    summary_path: Path,
) -> Dict[str, Any]:
    found = find_latest_session(project_path)
    if not found:
        return {"error": f"No Grok session found for {project_path}"}

    session_dir, session_id = found
    updates_path = session_dir / "updates.jsonl"
    model_id, turns = parse_session_updates(updates_path)
    summary = build_summary(
        turns,
        session_id=session_id,
        project_path=str(project_path.resolve()),
        model_id=model_id,
    )

    state = load_json(state_path)
    prev_key = state.get("session_key")
    current_key = f"{session_id}:{updates_path.stat().st_mtime_ns}:{len(turns)}"

    if prev_key != current_key and turns:
        now = datetime.now(timezone.utc).isoformat()
        new_records = []
        start_idx = state.get("logged_turns", 0) if state.get("session_id") == session_id else 0
        cost_by_turn = {
            tc["turn_index"]: tc for tc in summary.get("cost", {}).get("turn_costs", [])
        }
        for turn in turns[start_idx:]:
            tc = cost_by_turn.get(turn["turn_index"], {})
            new_records.append({
                "recorded_at": now,
                "session_id": session_id,
                "project_path": str(project_path.resolve()),
                "model_id": summary.get("model_id", model_id),
                "turn_cost_usd": tc.get("turn_cost_usd"),
                **turn,
            })
        if new_records:
            append_log(log_path, new_records)

    state = {
        "session_id": session_id,
        "session_key": current_key,
        "logged_turns": len(turns),
        "updates_path": str(updates_path),
        "last_sync": datetime.now(timezone.utc).isoformat(),
    }
    save_json(state_path, state)
    save_json(summary_path, summary)
    return summary


def report_from_log(log_path: Path, days: int = 7) -> str:
    if not log_path.is_file():
        return "No session log yet. Run: python token_monitor.py --sync --project ."

    lines = log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(ln) for ln in lines if ln.strip()]

    if not records:
        return "Session log is empty."

    by_session: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        by_session.setdefault(rec.get("session_id", "unknown"), []).append(rec)

    out = ["=== TOKEN SESSION LOG REPORT ===", f"Records: {len(records)}", ""]
    for sid, recs in by_session.items():
        last = recs[-1]
        total_growth = sum(r.get("turn_delta", 0) for r in recs)
        total_cost = sum(r.get("turn_cost_usd", 0) or 0 for r in recs)
        model = last.get("model_id", "unknown")
        out.append(f"Session {sid[:8]}… ({model})")
        out.append(f"  Turns logged: {len(recs)}")
        out.append(f"  Latest context: {last.get('context_tokens', 0):,}")
        out.append(f"  Session growth: +{total_growth:,}")
        out.append(f"  Est. session cost: ~${total_cost:.4f}")
        out.append("")

    out.append("=== END REPORT ===")
    return "\n".join(out)


def cmd_sync(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    repo_root = Path(args.repo_root).resolve()
    summary = sync_project(
        project,
        log_path=repo_root / args.log,
        state_path=repo_root / args.state,
        summary_path=repo_root / args.summary,
    )
    if "error" in summary:
        print(summary["error"], file=sys.stderr)
        return 1

    print(format_session_footer(summary))
    if summary.get("cost"):
        print()
        print(format_cost_report(summary["cost"], title="SESSION COST ANALYSIS"))
    if summary.get("warnings"):
        print("\nWARNINGS:")
        for w in summary["warnings"]:
            print(f"  - {w}")
    return 0


def cmd_footer(args: argparse.Namespace) -> int:
    summary_path = Path(args.repo_root).resolve() / args.summary
    summary = load_json(summary_path)
    if not summary:
        print("Token meter: no data yet (run --sync)", file=sys.stderr)
        return 1
    print(format_session_footer(summary))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    model_id, turns = parse_session_updates(Path(args.analyze))
    if not turns:
        print("No turns found in session file.")
        return 1

    print("=== SESSION TURN ANALYSIS ===")
    for t in turns:
        growth = analyze_context_growth(t["context_tokens"], t["turn_delta"])
        flag = f" [{growth['status'].upper()}]" if growth["status"] != "ok" else ""
        preview = t.get("user_preview", "")[:60]
        print(
            f"Turn {t['turn_index']:2d}: ctx {t['context_tokens']:>7,}  "
            f"+{t['turn_delta']:>6,}{flag}  {preview}"
        )

    summary = build_summary(turns, session_id="manual", project_path="", model_id=model_id)
    print("\n" + format_session_footer(summary))
    if summary.get("cost"):
        print()
        print(format_cost_report(summary["cost"], title="SESSION COST ANALYSIS"))
    if summary.get("warnings"):
        print("\nWARNINGS:")
        for w in summary["warnings"]:
            print(f"  - {w}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok session token monitor")
    parser.add_argument("--repo-root", default=".", help="Repository root for logs/state")
    parser.add_argument("--log", default=DEFAULT_LOG)
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    parser.add_argument("--project", default=".", help="Project path for session lookup")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="Sync latest Grok session to log").set_defaults(func=cmd_sync)

    footer_p = sub.add_parser("footer", help="Print one-line footer from latest summary")
    footer_p.set_defaults(func=cmd_footer)

    report_p = sub.add_parser("report", help="Report from session log")
    report_p.add_argument("--days", type=int, default=7)
    report_p.set_defaults(
        func=lambda a: (print(report_from_log(Path(a.repo_root) / a.log, a.days)), 0)[1]
    )

    analyze_p = sub.add_parser("analyze", help="Analyze a specific updates.jsonl")
    analyze_p.add_argument("analyze", help="Path to updates.jsonl")
    analyze_p.set_defaults(func=cmd_analyze)

    # Default: --sync if no subcommand but --sync flag; support legacy style
    parser.add_argument("--sync", action="store_true", help="Sync (alias for sync subcommand)")
    parser.add_argument("--report", action="store_true", help="Report (alias)")
    parser.add_argument("--footer", action="store_true", help="Footer (alias)")
    parser.add_argument("--analyze", metavar="PATH", help="Analyze path (alias)")
    parser.add_argument("--cost", action="store_true", help="Print cost analysis from latest summary")

    args = parser.parse_args()

    if args.command:
        return args.func(args)
    if args.sync:
        return cmd_sync(args)
    if args.footer:
        return cmd_footer(args)
    if args.report:
        print(report_from_log(Path(args.repo_root) / args.log))
        return 0
    if args.cost:
        summary = load_json(Path(args.repo_root).resolve() / args.summary)
        if not summary.get("cost"):
            print("No cost data. Run --sync first.", file=sys.stderr)
            return 1
        print(format_cost_report(summary["cost"], title="SESSION COST ANALYSIS"))
        return 0
    if args.analyze:
        args.analyze = args.analyze  # noqa: B018 — set for cmd_analyze
        return cmd_analyze(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
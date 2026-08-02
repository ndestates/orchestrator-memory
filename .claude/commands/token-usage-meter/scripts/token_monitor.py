#!/usr/bin/env python3
"""
Always-on Claude Code session token monitor.

Reads Claude Code session transcripts (NOT Grok) from
  ~/.claude/projects/<encoded-project>/<session-id>.jsonl
extracts real Anthropic `usage` per turn, appends to
reports/tokens/session-log.jsonl, and prints a compact one-line footer.

The <encoded-project> segment is the absolute project path with every
non-alphanumeric character replaced by '-' (e.g. /home/nickd/projects/orchestrator
-> -home-nickd-projects-orchestrator), matching Claude Code's own convention.

Usage:
  python3 token_monitor.py --sync --project .
  python3 token_monitor.py --footer
  python3 token_monitor.py --report
  python3 token_monitor.py --analyze ~/.claude/projects/<enc>/<id>.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from token_lib import (
    analyze_context_growth,
    analyze_session_costs,
    analyze_turn_efficiency,
    format_cost_report,
    format_session_footer,
    load_pricing_config,
    parse_usage,
)

CLAUDE_PROJECTS_ROOT = Path.home() / ".claude" / "projects"
DEFAULT_LOG = "reports/tokens/session-log.jsonl"
DEFAULT_STATE = "reports/tokens/.sync-state.json"
DEFAULT_SUMMARY = "reports/tokens/latest-summary.json"


def encode_project_path(project_path: Path) -> str:
    """Replicate Claude Code's project-dir encoding: non-alphanumeric -> '-'."""
    return re.sub(r"[^a-zA-Z0-9]", "-", str(project_path.resolve()))


def find_latest_session(project_path: Path) -> Optional[Tuple[Path, str]]:
    """Return (transcript_path, session_id) for the most recently modified session."""
    encoded = encode_project_path(project_path)
    sessions_dir = CLAUDE_PROJECTS_ROOT / encoded
    if not sessions_dir.is_dir():
        return None

    candidates: List[Tuple[float, Path, str]] = []
    for child in sessions_dir.glob("*.jsonl"):
        if child.is_file():
            candidates.append((child.stat().st_mtime, child, child.stem))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, transcript_path, session_id = candidates[0]
    return transcript_path, session_id


def _iter_records(transcript_path: Path):
    for line in transcript_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _is_real_user_turn(obj: Dict[str, Any]) -> bool:
    """True for a genuine human/SDK prompt, False for tool_result continuations."""
    if obj.get("type") != "user":
        return False
    msg = obj.get("message", {}) or {}
    content = msg.get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        # A real prompt leads with text; tool results lead with a tool_result block.
        first = content[0] if content else {}
        return isinstance(first, dict) and first.get("type") == "text"
    return False


def _user_preview(obj: Dict[str, Any]) -> str:
    msg = obj.get("message", {}) or {}
    content = msg.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = next((b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text"), "")
    else:
        text = ""
    return text.strip().replace("\n", " ")[:120]


def parse_session_model_id(transcript_path: Path) -> str:
    """Return the most common assistant model id in the transcript."""
    counts: Dict[str, int] = {}
    for obj in _iter_records(transcript_path):
        if obj.get("type") != "assistant":
            continue
        model = (obj.get("message", {}) or {}).get("model")
        if model:
            counts[model] = counts.get(model, 0) + 1
    if not counts:
        return "claude-opus-4-8"
    return max(counts, key=counts.get)


def parse_session_turns(transcript_path: Path) -> List[Dict[str, Any]]:
    """Group the transcript into user turns with per-turn context size and real usage.

    A turn starts at a genuine user prompt and includes every unique assistant API
    call up to the next user prompt. context_tokens is the peak prompt size
    (input+cache_read+cache_creation) seen in the turn; each turn also carries the
    list of parsed usage metrics (deduped by message id) for exact cost.
    """
    turns: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    seen_msg_ids: set = set()

    def close(turn: Optional[Dict[str, Any]]) -> None:
        if turn is not None:
            turns.append(turn)

    for obj in _iter_records(transcript_path):
        t = obj.get("type")

        if _is_real_user_turn(obj):
            close(current)
            current = {
                "turn_index": len(turns) + 1,
                "context_tokens": 0,
                "turn_delta": 0,
                "user_preview": _user_preview(obj),
                "usage_calls": [],
            }
            continue

        if t == "assistant":
            msg = obj.get("message", {}) or {}
            msg_id = msg.get("id")
            usage = msg.get("usage")
            if not usage:
                continue
            # Streaming writes the same assistant message several times; count once.
            if msg_id and msg_id in seen_msg_ids:
                continue
            if msg_id:
                seen_msg_ids.add(msg_id)
            if current is None:
                # Assistant activity before any captured user prompt (e.g. resumed
                # session). Open an implicit turn so nothing is dropped.
                current = {
                    "turn_index": len(turns) + 1,
                    "context_tokens": 0,
                    "turn_delta": 0,
                    "user_preview": "",
                    "usage_calls": [],
                }
            metrics = parse_usage(usage)
            current["usage_calls"].append(metrics)
            current["context_tokens"] = max(current["context_tokens"], metrics["prompt_tokens"])

    close(current)

    # Drop turns with no assistant usage (e.g. a trailing user prompt not yet answered)
    turns = [t for t in turns if t["usage_calls"]]
    # Re-index and compute deltas.
    prev = 0
    for idx, turn in enumerate(turns, start=1):
        turn["turn_index"] = idx
        turn["turn_delta"] = turn["context_tokens"] - prev
        prev = turn["context_tokens"]
    return turns


def _session_cache_stats(turns: List[Dict[str, Any]]) -> Tuple[int, float]:
    """Return (cache_read_last_turn, session cache-hit-rate %)."""
    total_prompt = 0
    total_cached = 0
    last_cached = 0
    for turn in turns:
        for m in turn.get("usage_calls", []):
            total_prompt += m["prompt_tokens"]
            total_cached += m["cached_tokens"]
    if turns:
        last_cached = sum(m["cached_tokens"] for m in turns[-1].get("usage_calls", []))
    hit = 0.0 if total_prompt == 0 else (total_cached / total_prompt) * 100
    return last_cached, round(hit, 1)


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
    model_id: str = "claude-opus-4-8",
) -> Dict[str, Any]:
    if not turns:
        return {
            "session_id": session_id,
            "project_path": project_path,
            "provider": "claude",
            "model_id": model_id,
            "turn_count": 0,
            "context_tokens": 0,
            "turn_delta": 0,
            "status": "ok",
            "warnings": [],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    cfg = load_pricing_config()
    thresholds = cfg.get("context_thresholds", {})

    last = turns[-1]
    growth = analyze_context_growth(
        last["context_tokens"],
        last["turn_delta"],
        warn_context=thresholds.get("warn_context", 200_000),
        critical_context=thresholds.get("critical_context", 400_000),
        warn_turn_delta=thresholds.get("warn_turn_delta", 30_000),
    )
    total_delta = sum(t["turn_delta"] for t in turns)
    costs = analyze_session_costs(turns, model_id=model_id, config=cfg)
    _, hit_rate = _session_cache_stats(turns)
    warnings = list(growth["warnings"])
    warnings.extend(analyze_turn_efficiency(turns))

    return {
        "session_id": session_id,
        "project_path": project_path,
        "provider": "claude",
        "model_id": costs.get("model_id", model_id),
        "model_label": costs.get("label", model_id),
        "turn_count": len(turns),
        "context_tokens": last["context_tokens"],
        "turn_delta": last["turn_delta"],
        "session_total_growth": total_delta,
        "status": growth["status"],
        "warnings": warnings,
        "cache_hit_rate_percent": hit_rate,
        "last_user_preview": last.get("user_preview", ""),
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "session_cost_usd": costs.get("session_cost_usd", 0.0),
        "last_turn_cost_usd": costs.get("last_turn_cost_usd", 0.0),
        "cost_per_turn_avg_usd": costs.get("cost_per_turn_avg_usd", 0.0),
        "cache_savings_usd": costs.get("cache_savings_usd", 0.0),
        "cost_is_estimate": False,
        "turns": [{k: v for k, v in t.items() if k != "usage_calls"} for t in turns[-5:]],
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
        return {"error": f"No Claude Code session found for {project_path} "
                         f"(looked in {CLAUDE_PROJECTS_ROOT / encode_project_path(project_path)})"}

    transcript_path, session_id = found
    model_id = parse_session_model_id(transcript_path)
    turns = parse_session_turns(transcript_path)
    summary = build_summary(
        turns,
        session_id=session_id,
        project_path=str(project_path.resolve()),
        model_id=model_id,
    )

    state = load_json(state_path)
    prev_key = state.get("session_key")
    current_key = f"{session_id}:{transcript_path.stat().st_mtime_ns}:{len(turns)}"

    if prev_key != current_key and turns:
        now = datetime.now(timezone.utc).isoformat()
        start_idx = state.get("logged_turns", 0) if state.get("session_id") == session_id else 0
        cost_by_turn = {tc["turn_index"]: tc for tc in summary.get("cost", {}).get("turn_costs", [])}
        new_records = []
        for turn in turns[start_idx:]:
            tc = cost_by_turn.get(turn["turn_index"], {})
            new_records.append({
                "recorded_at": now,
                "provider": "claude",
                "session_id": session_id,
                "project_path": str(project_path.resolve()),
                "model_id": summary.get("model_id", model_id),
                "turn_index": turn["turn_index"],
                "context_tokens": turn["context_tokens"],
                "turn_delta": turn["turn_delta"],
                "turn_cost_usd": tc.get("turn_cost_usd"),
                "user_preview": turn.get("user_preview", ""),
            })
        if new_records:
            append_log(log_path, new_records)

    save_json(state_path, {
        "provider": "claude",
        "session_id": session_id,
        "session_key": current_key,
        "logged_turns": len(turns),
        "transcript_path": str(transcript_path),
        "last_sync": datetime.now(timezone.utc).isoformat(),
    })
    save_json(summary_path, summary)
    return summary


def report_from_log(log_path: Path, days: int = 7) -> str:
    if not log_path.is_file():
        return "No session log yet. Run: python3 token_monitor.py --sync --project ."

    records = [json.loads(ln) for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not records:
        return "Session log is empty."

    by_session: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        by_session.setdefault(rec.get("session_id", "unknown"), []).append(rec)

    out = ["=== TOKEN SESSION LOG REPORT (Claude) ===", f"Records: {len(records)}", ""]
    for sid, recs in by_session.items():
        last = recs[-1]
        total_growth = sum(r.get("turn_delta", 0) for r in recs)
        total_cost = sum(r.get("turn_cost_usd", 0) or 0 for r in recs)
        model = last.get("model_id", "unknown")
        out.append(f"Session {sid[:8]}… ({model})")
        out.append(f"  Turns logged: {len(recs)}")
        out.append(f"  Latest context: {last.get('context_tokens', 0):,}")
        out.append(f"  Session growth: +{total_growth:,}")
        out.append(f"  Session cost: ${total_cost:.4f}")
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
    summary = load_json(Path(args.repo_root).resolve() / args.summary)
    if not summary:
        print("Token meter: no data yet (run --sync)", file=sys.stderr)
        return 1
    print(format_session_footer(summary))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    path = Path(args.analyze)
    turns = parse_session_turns(path)
    if not turns:
        print("No turns found in session file.")
        return 1

    print("=== SESSION TURN ANALYSIS (Claude) ===")
    for t in turns:
        growth = analyze_context_growth(t["context_tokens"], t["turn_delta"])
        flag = f" [{growth['status'].upper()}]" if growth["status"] != "ok" else ""
        preview = t.get("user_preview", "")[:60]
        print(f"Turn {t['turn_index']:2d}: ctx {t['context_tokens']:>8,}  "
              f"+{t['turn_delta']:>7,}{flag}  {preview}")

    model_id = parse_session_model_id(path)
    summary = build_summary(turns, session_id=path.stem, project_path="", model_id=model_id)
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
    parser = argparse.ArgumentParser(description="Claude Code session token monitor")
    parser.add_argument("--repo-root", default=".", help="Repository root for logs/state")
    parser.add_argument("--log", default=DEFAULT_LOG)
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    parser.add_argument("--project", default=".", help="Project path for session lookup")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("sync").set_defaults(func=cmd_sync)
    sub.add_parser("footer").set_defaults(func=cmd_footer)
    report_p = sub.add_parser("report")
    report_p.add_argument("--days", type=int, default=7)
    report_p.set_defaults(func=lambda a: (print(report_from_log(Path(a.repo_root) / a.log, a.days)), 0)[1])
    analyze_p = sub.add_parser("analyze")
    analyze_p.add_argument("analyze")
    analyze_p.set_defaults(func=cmd_analyze)

    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--footer", action="store_true")
    parser.add_argument("--analyze", metavar="PATH")
    parser.add_argument("--cost", action="store_true")

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
        return cmd_analyze(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

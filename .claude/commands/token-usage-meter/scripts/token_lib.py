#!/usr/bin/env python3
"""Shared token parsing, cache-efficiency, and cost analysis for Claude Code sessions.

This is the .claude variant of the token-usage-meter. It reads Anthropic `usage`
objects (input_tokens / cache_read_input_tokens / cache_creation_input_tokens /
output_tokens) — NOT xAI/Grok usage. The .grok copy handles Grok.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

PRICING_PATH = Path(__file__).resolve().parent.parent / "references" / "pricing.json"


def parse_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metrics from an Anthropic API usage object.

    Anthropic splits input into three buckets:
      - input_tokens              : uncached input (full price)
      - cache_read_input_tokens   : served from cache (~0.1x)
      - cache_creation_input_tokens : written to cache (~1.25x 5m / 2x 1h)
    prompt_tokens is the sum of all three (the full prompt sent that call).
    """
    metrics: Dict[str, Any] = {
        "prompt_tokens": 0,
        "input_tokens": 0,
        "cached_tokens": 0,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "api_type": "anthropic",
    }
    if not usage:
        return metrics

    input_tokens = usage.get("input_tokens", 0) or 0
    cache_read = usage.get("cache_read_input_tokens", 0) or 0
    cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
    output_tokens = usage.get("output_tokens", 0) or 0

    creation = usage.get("cache_creation") or {}
    write_5m = creation.get("ephemeral_5m_input_tokens", 0) if isinstance(creation, dict) else 0
    write_1h = creation.get("ephemeral_1h_input_tokens", 0) if isinstance(creation, dict) else 0
    # Fall back to the flat cache_creation_input_tokens if the split is absent.
    if (write_5m + write_1h) == 0 and cache_creation:
        write_5m = cache_creation

    prompt = input_tokens + cache_read + cache_creation
    metrics.update(
        prompt_tokens=prompt,
        input_tokens=input_tokens,
        cached_tokens=cache_read,
        cache_write_5m_tokens=write_5m,
        cache_write_1h_tokens=write_1h,
        completion_tokens=output_tokens,
        total_tokens=prompt + output_tokens,
    )
    return metrics


def analyze_cache_efficiency(
    metrics: Dict[str, Any],
    conversation_turn: Optional[int] = None,
) -> Dict[str, Any]:
    """Analyze cache usage and generate warnings/recommendations."""
    prompt = metrics["prompt_tokens"]
    cached = metrics["cached_tokens"]

    hit_rate = 0.0 if prompt == 0 else (cached / prompt) * 100

    analysis: Dict[str, Any] = {
        "metrics": metrics,
        "cache_hit_rate_percent": round(hit_rate, 1),
        "warnings": [],
        "recommendations": [],
        "efficiency_status": "good",
    }

    if cached == 0 and prompt > 1000:
        analysis["warnings"].append(
            "CACHE MISS: cache_read_input_tokens=0 on a >1k-token prompt. Prefix cache is NOT being reused."
        )
        analysis["efficiency_status"] = "poor"
        analysis["recommendations"].extend([
            "Keep the system prompt / early context byte-identical between turns (no timestamps or UUIDs in the prefix).",
            "Avoid changing tool definitions or the model mid-session — both invalidate the whole cache.",
        ])
    elif cached == 0 and prompt > 0:
        analysis["warnings"].append(
            "First request or short prompt: cache_read=0 is expected (cache being established or below the ~1-4k min prefix)."
        )
    elif hit_rate < 30 and prompt > 4000:
        analysis["warnings"].append(
            f"LOW CACHE EFFICIENCY: only {hit_rate:.1f}% of the prompt was cache-read ({cached:,}/{prompt:,})."
        )
        analysis["efficiency_status"] = "fair"
        analysis["recommendations"].append(
            "Review the conversation prefix: keep early context stable and identical across requests."
        )
    elif hit_rate >= 80:
        analysis["efficiency_status"] = "excellent"
    elif hit_rate >= 50:
        analysis["efficiency_status"] = "good"

    if conversation_turn is not None:
        analysis["conversation_turn"] = conversation_turn

    return analysis


def analyze_context_growth(
    context_tokens: int,
    turn_delta: int,
    *,
    warn_context: int = 200_000,
    critical_context: int = 400_000,
    warn_turn_delta: int = 30_000,
) -> Dict[str, Any]:
    """Analyze Claude session context size (input+cache_read+cache_creation per turn)."""
    warnings: List[str] = []
    status = "ok"

    if context_tokens >= critical_context:
        status = "critical"
        warnings.append(
            f"Context at {context_tokens:,} tokens (≥{critical_context:,}). Summarize or start a fresh session soon."
        )
    elif context_tokens >= warn_context:
        status = "warning"
        warnings.append(
            f"Context at {context_tokens:,} tokens (≥{warn_context:,}). Prefer cache-first reads and lean replies."
        )

    if turn_delta < 0:
        warnings.append(
            f"Context shrank by {turn_delta:,} tokens (likely compaction). Cost/session totals may reset partially."
        )
    elif turn_delta >= warn_turn_delta:
        if status == "ok":
            status = "warning"
        warnings.append(
            f"Last turn added +{turn_delta:,} tokens (≥{warn_turn_delta:,}). Review large reads or verbose output."
        )

    return {
        "context_tokens": context_tokens,
        "turn_delta": turn_delta,
        "status": status,
        "warnings": warnings,
    }


def analyze_turn_efficiency(
    turns: List[Dict[str, Any]],
    *,
    high_delta_threshold: int = 20_000,
    consecutive_limit: int = 3,
) -> List[str]:
    """Warn when repeated turns add large context (cache-unfriendly pattern)."""
    warnings: List[str] = []
    streak = 0
    for turn in turns:
        delta = turn.get("turn_delta", 0)
        if delta >= high_delta_threshold:
            streak += 1
        else:
            streak = 0
    if streak >= consecutive_limit:
        warnings.append(
            f"{streak} consecutive turns added ≥{high_delta_threshold:,} tokens each — "
            "use grep-before-read, cap cache files, and avoid full registry/skill reads."
        )
    return warnings


def load_pricing_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pricing.json; returns empty dict if missing."""
    p = path or PRICING_PATH
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_model_pricing(model_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Resolve per-1M token rates for a Claude model id."""
    cfg = config or load_pricing_config()
    models = cfg.get("models", {})
    default_id = cfg.get("default_model", "claude-opus-4-8")

    resolved_id = model_id
    entry = models.get(model_id)
    if entry and "alias_of" in entry:
        resolved_id = entry["alias_of"]
        entry = models.get(resolved_id, {})

    if not entry or "input_per_1m" not in entry:
        resolved_id = default_id
        entry = models.get(default_id, {})

    return {
        "model_id": resolved_id,
        "label": entry.get("label", resolved_id),
        "input_per_1m": float(entry.get("input_per_1m", 5.0)),
        "cache_read_per_1m": float(entry.get("cache_read_per_1m", 0.5)),
        "cache_write_5m_per_1m": float(entry.get("cache_write_5m_per_1m", 6.25)),
        "cache_write_1h_per_1m": float(entry.get("cache_write_1h_per_1m", 10.0)),
        "output_per_1m": float(entry.get("output_per_1m", 25.0)),
    }


def cost_from_usage(
    metrics: Dict[str, Any],
    *,
    model_id: str = "claude-opus-4-8",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Precise cost from a parsed Anthropic usage object (real billing, not estimated)."""
    pricing = resolve_model_pricing(model_id, config)
    uncached = metrics.get("input_tokens", 0)
    cache_read = metrics.get("cached_tokens", 0)
    write_5m = metrics.get("cache_write_5m_tokens", 0)
    write_1h = metrics.get("cache_write_1h_tokens", 0)
    completion = metrics.get("completion_tokens", 0)

    input_cost = (uncached / 1_000_000) * pricing["input_per_1m"]
    cache_read_cost = (cache_read / 1_000_000) * pricing["cache_read_per_1m"]
    write_cost = (
        (write_5m / 1_000_000) * pricing["cache_write_5m_per_1m"]
        + (write_1h / 1_000_000) * pricing["cache_write_1h_per_1m"]
    )
    output_cost = (completion / 1_000_000) * pricing["output_per_1m"]
    total = input_cost + cache_read_cost + write_cost + output_cost

    # Savings vs. sending the whole prompt uncached at full input price.
    prompt = uncached + cache_read + write_5m + write_1h
    no_cache_input_cost = (prompt / 1_000_000) * pricing["input_per_1m"]
    cache_savings = max(no_cache_input_cost - (input_cost + cache_read_cost + write_cost), 0.0)

    return {
        "model_id": pricing["model_id"],
        "label": pricing["label"],
        "currency": "USD",
        "input_tokens": uncached,
        "cached_tokens": cache_read,
        "cache_write_tokens": write_5m + write_1h,
        "output_tokens": completion,
        "input_cost_usd": round(input_cost, 6),
        "cache_read_cost_usd": round(cache_read_cost, 6),
        "cache_write_cost_usd": round(write_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total, 6),
        "cache_savings_usd": round(cache_savings, 6),
        "is_estimate": False,
    }


def analyze_session_costs(
    turns: List[Dict[str, Any]],
    *,
    model_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Aggregate real session cost by summing each turn's per-call costs.

    Each turn must carry a `usage_calls` list of parsed metrics (one per unique
    assistant API call) — parse_session_turns produces these.
    """
    if not turns:
        return {"session_cost_usd": 0.0, "turn_costs": [], "model_id": model_id}

    pricing = resolve_model_pricing(model_id, config)
    turn_costs: List[Dict[str, Any]] = []
    session_total = 0.0
    savings_total = 0.0

    for turn in turns:
        turn_total = 0.0
        turn_savings = 0.0
        for m in turn.get("usage_calls", []):
            c = cost_from_usage(m, model_id=model_id, config=config)
            turn_total += c["total_cost_usd"]
            turn_savings += c["cache_savings_usd"]
        turn_costs.append({
            "turn_index": turn.get("turn_index"),
            "turn_cost_usd": round(turn_total, 6),
            "cache_savings_usd": round(turn_savings, 6),
        })
        session_total += turn_total
        savings_total += turn_savings

    last = turn_costs[-1]
    return {
        "model_id": pricing["model_id"],
        "label": pricing["label"],
        "currency": "USD",
        "turn_count": len(turns),
        "session_cost_usd": round(session_total, 4),
        "last_turn_cost_usd": round(last["turn_cost_usd"], 4),
        "cache_savings_usd": round(savings_total, 4),
        "cost_per_turn_avg_usd": round(session_total / len(turns), 4),
        "is_estimate": False,
        "turn_costs": turn_costs,
    }


def format_cache_report(analysis: Dict[str, Any], *, cost: Optional[Dict[str, Any]] = None) -> str:
    """Human-readable cache-efficiency report for a single Anthropic usage object."""
    m = analysis["metrics"]
    lines = [
        "=== TOKEN USAGE METER & CACHE EFFICIENCY REPORT (Claude) ===",
        f"Prompt Tokens (input+cache_read+cache_write): {m['prompt_tokens']:,}",
        f"  Uncached input: {m['input_tokens']:,}",
        f"  Cache read: {m['cached_tokens']:,}",
        f"  Cache write: {m['cache_write_5m_tokens'] + m['cache_write_1h_tokens']:,}",
        f"Output Tokens: {m['completion_tokens']:,}",
        f"Cache Hit Rate: {analysis['cache_hit_rate_percent']}%",
        f"Efficiency Status: {analysis['efficiency_status'].upper()}",
    ]

    if cost:
        lines.append(f"Estimated Cost: ${cost['total_cost_usd']:.6f} ({cost.get('label', cost.get('model_id'))})")
        lines.append(f"Cache Savings: ${cost.get('cache_savings_usd', 0):.6f}")

    if analysis.get("conversation_turn"):
        lines.append(f"Conversation Turn: {analysis['conversation_turn']}")

    if analysis["warnings"]:
        lines.append("\nWARNINGS:")
        for w in analysis["warnings"]:
            lines.append(f"  - {w}")

    if analysis["recommendations"]:
        lines.append("\nRECOMMENDATIONS:")
        for r in analysis["recommendations"]:
            lines.append(f"  - {r}")

    lines.append("=== END REPORT ===")
    return "\n".join(lines)


def format_cost_report(cost: Dict[str, Any], *, title: str = "COST ANALYSIS") -> str:
    """Human-readable cost breakdown."""
    lines = [
        f"=== {title} ===",
        f"Model: {cost.get('label', cost.get('model_id', 'unknown'))}",
        f"Currency: {cost.get('currency', 'USD')}",
    ]

    if cost.get("is_estimate"):
        lines.append("Mode: ESTIMATED")
    else:
        lines.append("Mode: ACTUAL (from Anthropic usage objects in the session transcript)")

    if "session_cost_usd" in cost:
        lines.extend([
            f"Session cost: ${cost['session_cost_usd']:.4f}",
            f"Last turn cost: ${cost.get('last_turn_cost_usd', 0):.4f}",
            f"Avg per turn: ${cost.get('cost_per_turn_avg_usd', 0):.4f}",
            f"Cache savings vs no-cache: ${cost.get('cache_savings_usd', 0):.4f}",
        ])
    else:
        lines.extend([
            f"Uncached input: {cost.get('input_tokens', 0):,}  "
            f"cache-read: {cost.get('cached_tokens', 0):,}  "
            f"cache-write: {cost.get('cache_write_tokens', 0):,}",
            f"Output tokens: {cost.get('output_tokens', 0):,}",
            f"Input cost: ${cost.get('input_cost_usd', 0):.6f}",
            f"Cache read cost: ${cost.get('cache_read_cost_usd', 0):.6f}",
            f"Cache write cost: ${cost.get('cache_write_cost_usd', 0):.6f}",
            f"Output cost: ${cost.get('output_cost_usd', 0):.6f}",
            f"Total cost: ${cost.get('total_cost_usd', 0):.6f}",
            f"Cache savings: ${cost.get('cache_savings_usd', 0):.6f}",
        ])

    lines.append("=== END COST ===")
    return "\n".join(lines)


def format_session_footer(summary: Dict[str, Any]) -> str:
    """One-line footer for agent responses (always-on monitoring)."""
    ctx = summary.get("context_tokens", 0)
    delta = summary.get("turn_delta", 0)
    turns = summary.get("turn_count", 0)
    status = summary.get("status", "ok")
    hit = summary.get("cache_hit_rate_percent")
    session_cost = summary.get("session_cost_usd")
    turn_cost = summary.get("last_turn_cost_usd")

    delta_label = f"{delta:+,}" if delta != 0 else "+0"
    parts = [f"ctx {ctx:,}", f"{delta_label} this turn", f"{turns} turns"]
    if session_cost is not None:
        parts.append(f"${session_cost:.2f} session")
    if turn_cost is not None:
        parts.append(f"${turn_cost:.2f} turn")
    if hit is not None:
        parts.append(f"cache {hit:.0f}%")
    parts.append(status.upper())
    return "Token meter: " + " · ".join(parts)

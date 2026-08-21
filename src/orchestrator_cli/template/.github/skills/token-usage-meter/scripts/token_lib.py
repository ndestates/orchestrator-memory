#!/usr/bin/env python3
"""Shared token usage parsing, cache-efficiency, and cost analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

PRICING_PATH = Path(__file__).resolve().parent.parent / "references" / "pricing.json"


def parse_usage(usage: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metrics from xAI usage object (Chat Completions or Responses API)."""
    metrics: Dict[str, Any] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "api_type": "unknown",
    }

    if not usage:
        return metrics

    if "input_tokens" in usage:
        metrics["api_type"] = "responses"
        metrics["prompt_tokens"] = usage.get("input_tokens", 0)
        metrics["completion_tokens"] = usage.get("output_tokens", 0)
        metrics["total_tokens"] = usage.get("total_tokens", 0)
        details = usage.get("input_tokens_details", {})
        metrics["cached_tokens"] = details.get("cached_tokens", 0) if isinstance(details, dict) else 0
    elif "prompt_tokens" in usage:
        metrics["api_type"] = "chat_completions"
        metrics["prompt_tokens"] = usage.get("prompt_tokens", 0)
        metrics["completion_tokens"] = usage.get("completion_tokens", 0)
        metrics["total_tokens"] = usage.get("total_tokens", 0)
        details = usage.get("prompt_tokens_details", {})
        metrics["cached_tokens"] = details.get("cached_tokens", 0) if isinstance(details, dict) else 0

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

    if cached == 0 and prompt > 50:
        analysis["warnings"].append(
            "CACHE MISS: cached_tokens=0 for prompt_tokens >50. Cache is NOT being used!"
        )
        analysis["efficiency_status"] = "poor"
        analysis["recommendations"].extend([
            "Ensure you are setting the `x-grok-conv-id` HTTP header (or `prompt_cache_key` for Responses API).",
            "Verify that the prefix (first messages) has NOT changed since the previous request.",
            "Avoid modifying system prompts, tool definitions, or early messages between turns.",
        ])
    elif cached == 0 and prompt > 0:
        analysis["warnings"].append(
            "First request or small prompt: cached_tokens=0 is expected (cache being established)."
        )
    elif hit_rate < 30 and prompt > 100:
        analysis["warnings"].append(
            f"LOW CACHE EFFICIENCY: Only {hit_rate:.1f}% of prompt tokens cached ({cached}/{prompt})."
        )
        analysis["efficiency_status"] = "fair"
        analysis["recommendations"].append(
            "Review conversation history: keep early context stable and identical across requests."
        )
    elif hit_rate >= 80:
        analysis["efficiency_status"] = "excellent"
    elif hit_rate >= 50:
        analysis["efficiency_status"] = "good"

    if analysis["efficiency_status"] in ("poor", "fair"):
        analysis["recommendations"].append(
            "For multi-turn conversations, keep the conversation prefix consistent and use a stable conversation ID."
        )

    if conversation_turn is not None:
        analysis["conversation_turn"] = conversation_turn

    return analysis


def analyze_context_growth(
    context_tokens: int,
    turn_delta: int,
    *,
    warn_context: int = 100_000,
    critical_context: int = 128_000,
    warn_turn_delta: int = 15_000,
) -> Dict[str, Any]:
    """Analyze Grok session context size from updates.jsonl totalTokens."""
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
            f"Context shrank by {turn_delta:,} tokens (likely summarization). Cost/session totals may reset partially."
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
    high_delta_threshold: int = 10_000,
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


def format_cache_report(analysis: Dict[str, Any], *, cost: Optional[Dict[str, Any]] = None) -> str:
    """Human-readable cache-efficiency report."""
    m = analysis["metrics"]
    lines = [
        "=== TOKEN USAGE METER & CACHE EFFICIENCY REPORT ===",
        f"API Type: {m['api_type'].upper()}",
        f"Prompt/Input Tokens: {m['prompt_tokens']}",
        f"Completion/Output Tokens: {m['completion_tokens']}",
        f"Total Tokens: {m['total_tokens']}",
        f"Cached Tokens: {m['cached_tokens']}",
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

    if analysis["efficiency_status"] == "poor":
        lines.append(
            "\nACTION NEEDED: Cache is not being utilized efficiently. Review headers and prompt structure."
        )
    elif analysis["efficiency_status"] == "fair":
        lines.append("\nOPTIMIZATION OPPORTUNITY: Cache utilization can be improved.")

    lines.append("=== END REPORT ===")
    return "\n".join(lines)


def load_pricing_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pricing.json; returns empty dict if missing."""
    p = path or PRICING_PATH
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_model_pricing(model_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Resolve per-1M token rates for a model id."""
    cfg = config or load_pricing_config()
    models = cfg.get("models", {})
    default_id = cfg.get("default_model", "grok-build-0.1")

    entry = models.get(model_id)
    if entry and "alias_of" in entry:
        entry = models.get(entry["alias_of"], entry)

    if not entry or "input_per_1m" not in entry:
        entry = models.get(default_id, {})
        resolved_id = default_id
    else:
        resolved_id = model_id
        if "alias_of" in models.get(model_id, {}):
            resolved_id = models[model_id]["alias_of"]

    return {
        "model_id": resolved_id,
        "label": entry.get("label", resolved_id),
        "input_per_1m": float(entry.get("input_per_1m", 1.0)),
        "cached_input_per_1m": float(entry.get("cached_input_per_1m", 0.2)),
        "output_per_1m": float(entry.get("output_per_1m", 2.0)),
        "pricing_note": entry.get("pricing_note"),
        "source": entry.get("source"),
        "is_estimate": resolved_id == "grok-composer-2.5-fast",
    }


def cost_from_usage(
    metrics: Dict[str, Any],
    *,
    model_id: str = "grok-build-0.1",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Precise cost from API usage object (input/output/cached split)."""
    pricing = resolve_model_pricing(model_id, config)
    prompt = metrics.get("prompt_tokens", 0)
    completion = metrics.get("completion_tokens", 0)
    cached = min(metrics.get("cached_tokens", 0), prompt)
    uncached = max(prompt - cached, 0)

    input_cost = (uncached / 1_000_000) * pricing["input_per_1m"]
    cached_cost = (cached / 1_000_000) * pricing["cached_input_per_1m"]
    output_cost = (completion / 1_000_000) * pricing["output_per_1m"]
    total = input_cost + cached_cost + output_cost

    no_cache_input_cost = (prompt / 1_000_000) * pricing["input_per_1m"]
    cache_savings = max(no_cache_input_cost - (input_cost + cached_cost), 0.0)

    return {
        "model_id": pricing["model_id"],
        "label": pricing["label"],
        "currency": "USD",
        "input_tokens": prompt,
        "cached_tokens": cached,
        "uncached_tokens": uncached,
        "output_tokens": completion,
        "input_cost_usd": round(input_cost, 6),
        "cached_input_cost_usd": round(cached_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total, 6),
        "cache_savings_usd": round(cache_savings, 6),
        "is_estimate": pricing.get("is_estimate", False),
        "pricing_note": pricing.get("pricing_note"),
    }


def estimate_session_turn_cost(
    turn: Dict[str, Any],
    *,
    model_id: str,
    config: Optional[Dict[str, Any]] = None,
    prev_context: int = 0,
) -> Dict[str, Any]:
    """
    Estimate per-turn cost from Grok session context deltas.

    Each turn re-sends full context as input; output approximated from turn_delta.
    Applies assumed cache hit rate on prior context when no API usage is available.
    """
    cfg = config or load_pricing_config()
    est = cfg.get("session_estimation", {})
    pricing = resolve_model_pricing(model_id, cfg)

    context = turn.get("context_tokens", 0)
    delta = max(turn.get("turn_delta", 0), 0)
    turn_index = turn.get("turn_index", 1)
    summarized = turn.get("turn_delta", 0) < 0

    output_frac = float(est.get("output_fraction_of_turn_delta", 0.30))
    cache_hit = float(est.get("assumed_cache_hit_rate_after_turn_1", 0.75))
    min_output = int(est.get("min_output_tokens_per_turn", 200))

    output_tokens = max(int(delta * output_frac), min_output if delta > 0 else 0)

    if summarized or turn_index <= 1:
        cached_input = 0
        uncached_input = context
    else:
        cached_input = int(min(prev_context, context) * cache_hit)
        uncached_input = max(context - cached_input, 0)

    input_cost = (uncached_input / 1_000_000) * pricing["input_per_1m"]
    cached_cost = (cached_input / 1_000_000) * pricing["cached_input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total = input_cost + cached_cost + output_cost

    no_cache = (context / 1_000_000) * pricing["input_per_1m"] + output_cost

    return {
        "turn_index": turn_index,
        "model_id": pricing["model_id"],
        "context_tokens": context,
        "turn_delta": delta,
        "estimated_input_tokens": context,
        "estimated_cached_input": cached_input,
        "estimated_output_tokens": output_tokens,
        "input_cost_usd": round(input_cost + cached_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "turn_cost_usd": round(total, 6),
        "cache_savings_usd": round(max(no_cache - total, 0.0), 6),
        "is_estimate": True,
    }


def analyze_session_costs(
    turns: List[Dict[str, Any]],
    *,
    model_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Aggregate session cost from turn list."""
    if not turns:
        return {"session_cost_usd": 0.0, "turn_costs": [], "model_id": model_id}

    pricing = resolve_model_pricing(model_id, config)
    turn_costs: List[Dict[str, Any]] = []
    prev_context = 0
    session_total = 0.0
    savings_total = 0.0

    for turn in turns:
        tc = estimate_session_turn_cost(
            turn, model_id=model_id, config=config, prev_context=prev_context
        )
        turn_costs.append(tc)
        session_total += tc["turn_cost_usd"]
        savings_total += tc.get("cache_savings_usd", 0.0)
        prev_context = turn.get("context_tokens", 0)

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
        "is_estimate": True,
        "pricing_note": pricing.get("pricing_note"),
        "turn_costs": turn_costs,
    }


def format_cost_report(cost: Dict[str, Any], *, title: str = "COST ANALYSIS") -> str:
    """Human-readable cost breakdown."""
    lines = [
        f"=== {title} ===",
        f"Model: {cost.get('label', cost.get('model_id', 'unknown'))}",
        f"Currency: {cost.get('currency', 'USD')}",
    ]

    if cost.get("is_estimate"):
        lines.append("Mode: ESTIMATED (session heuristics — paste API usage JSON for precise billing)")

    if "session_cost_usd" in cost:
        lines.extend([
            f"Session estimated cost: ${cost['session_cost_usd']:.4f}",
            f"Last turn estimated cost: ${cost.get('last_turn_cost_usd', 0):.4f}",
            f"Avg per turn: ${cost.get('cost_per_turn_avg_usd', 0):.4f}",
            f"Est. cache savings vs no-cache: ${cost.get('cache_savings_usd', 0):.4f}",
        ])
    else:
        lines.extend([
            f"Input tokens: {cost.get('input_tokens', 0):,} "
            f"(cached {cost.get('cached_tokens', 0):,}, uncached {cost.get('uncached_tokens', 0):,})",
            f"Output tokens: {cost.get('output_tokens', 0):,}",
            f"Input cost: ${cost.get('input_cost_usd', 0) + cost.get('cached_input_cost_usd', 0):.6f}",
            f"Output cost: ${cost.get('output_cost_usd', 0):.6f}",
            f"Total cost: ${cost.get('total_cost_usd', 0):.6f}",
            f"Cache savings: ${cost.get('cache_savings_usd', 0):.6f}",
        ])

    if cost.get("pricing_note"):
        lines.append(f"Note: {cost['pricing_note']}")

    lines.append("=== END COST ===")
    return "\n".join(lines)


def format_session_footer(summary: Dict[str, Any]) -> str:
    """One-line footer for agent responses (always-on monitoring)."""
    ctx = summary.get("context_tokens", 0)
    delta = summary.get("turn_delta", 0)
    turns = summary.get("turn_count", 0)
    status = summary.get("status", "ok")
    cached = summary.get("cached_tokens")
    hit = summary.get("cache_hit_rate_percent")
    session_cost = summary.get("session_cost_usd")
    turn_cost = summary.get("last_turn_cost_usd")

    delta_label = f"{delta:+,}" if delta != 0 else "+0"
    parts = [f"ctx {ctx:,}", f"{delta_label} this turn", f"{turns} turns"]
    if session_cost is not None:
        est = "~" if summary.get("cost_is_estimate") else ""
        parts.append(f"{est}${session_cost:.2f} session")
    if turn_cost is not None:
        est = "~" if summary.get("cost_is_estimate") else ""
        parts.append(f"{est}${turn_cost:.2f} turn")
    if cached is not None and hit is not None:
        parts.append(f"cache {hit:.0f}%")
    parts.append(status.upper())
    return "Token meter: " + " · ".join(parts)
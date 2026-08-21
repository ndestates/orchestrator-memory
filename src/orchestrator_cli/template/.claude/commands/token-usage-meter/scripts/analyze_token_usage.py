#!/usr/bin/env python3
"""
Token Usage Meter & Cache Efficiency Analyzer for Anthropic API responses.

Reads an Anthropic `usage` object (input_tokens / cache_read_input_tokens /
cache_creation_input_tokens / output_tokens) — the shape Claude returns.

Usage:
  python3 analyze_token_usage.py <usage_json_file>
  cat response.json | python3 analyze_token_usage.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from token_lib import (  # noqa: E402
    analyze_cache_efficiency,
    cost_from_usage,
    format_cache_report,
    format_cost_report,
    parse_usage,
)


def main() -> None:
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    if not isinstance(data, dict):
        print("Error: expected a JSON object with a 'usage' field, or usage fields directly.")
        sys.exit(1)

    usage = data.get("usage", data)
    model_id = data.get("model", data.get("model_id", "claude-opus-4-8"))

    metrics = parse_usage(usage)
    analysis = analyze_cache_efficiency(metrics)
    cost = cost_from_usage(metrics, model_id=model_id)
    print(format_cache_report(analysis, cost=cost))
    print()
    print(format_cost_report(cost, title="API CALL COST ANALYSIS"))


if __name__ == "__main__":
    main()

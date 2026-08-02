#!/usr/bin/env python3
"""
Token Usage Meter & Cache Efficiency Analyzer for xAI API responses.

Usage:
  python analyze_token_usage.py <usage_json_file>
  or pipe JSON: cat response.json | python analyze_token_usage.py
"""

import json
import sys
from pathlib import Path

# Allow import when run as script from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from token_lib import (
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

    if isinstance(data, dict):
        usage = data.get("usage", data)
    else:
        print("Error: Expected JSON object with 'usage' or usage fields directly.")
        sys.exit(1)

    metrics = parse_usage(usage)
    analysis = analyze_cache_efficiency(metrics)
    model_id = "grok-build-0.1"
    if isinstance(data, dict):
        model_id = data.get("model", data.get("model_id", model_id))
    cost = cost_from_usage(metrics, model_id=model_id)
    print(format_cache_report(analysis, cost=cost))
    print()
    print(format_cost_report(cost, title="API CALL COST ANALYSIS"))


if __name__ == "__main__":
    main()
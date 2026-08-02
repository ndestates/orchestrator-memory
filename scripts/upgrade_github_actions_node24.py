#!/usr/bin/env python3
"""Upgrade .github/workflows/*.yml to Node 24-native GitHub Actions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FORCE_NODE24_ENV = 'env:\n  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"\n'

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5\s*(?:#\s*v4)?"
        ),
        "actions/checkout@v6",
    ),
    (re.compile(r"actions/checkout@v[1-4]\b"), "actions/checkout@v6"),
    # Invalid/non-existent micro-tags (e.g. v6.2.2) — use major tag only
    (re.compile(r"actions/checkout@v6\.\d+(?:\.\d+)?\b"), "actions/checkout@v6"),
    (
        re.compile(
            r"actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02\s*(?:#\s*v4)?"
        ),
        "actions/upload-artifact@v7  # Node 24 native",
    ),
    (
        re.compile(r"actions/upload-artifact@v[1-4]\b"),
        "actions/upload-artifact@v7  # Node 24 native",
    ),
    (
        re.compile(
            r"actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065\s*(?:#\s*v5)?"
        ),
        "actions/setup-python@v6",
    ),
    (re.compile(r"actions/setup-python@v[1-5]\b"), "actions/setup-python@v6"),
    (
        re.compile(
            r"actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020\s*(?:#\s*v4)?"
        ),
        "actions/setup-node@v5",
    ),
    (re.compile(r"actions/setup-node@v[1-4]\b"), "actions/setup-node@v5"),
]


def upgrade_workflow(text: str) -> str:
    for pattern, replacement in REPLACEMENTS:
        text = pattern.sub(replacement, text)

    if "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" not in text:
        if re.match(r"^name:\s*.+\n", text):
            text = re.sub(
                r"^(name:\s*.+\n)",
                r"\1\n" + FORCE_NODE24_ENV,
                text,
                count=1,
            )
        else:
            text = FORCE_NODE24_ENV + text

    return text


def upgrade_repo(root: Path, dry_run: bool = False) -> list[str]:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return []

    changed: list[str] = []
    for workflow in sorted(workflows.glob("*.yml")):
        original = workflow.read_text(encoding="utf-8")
        updated = upgrade_workflow(original)
        if updated != original:
            changed.append(str(workflow.relative_to(root)))
            if not dry_run:
                workflow.write_text(updated, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root (default: orchestrator)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    changed = upgrade_repo(root, dry_run=args.dry_run)
    if not changed:
        print(f"OK: no workflow upgrades needed under {root}")
        return 0

    verb = "would upgrade" if args.dry_run else "upgraded"
    print(f"{verb} {len(changed)} workflow(s) under {root}:")
    for rel in changed:
        print(f"  - {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
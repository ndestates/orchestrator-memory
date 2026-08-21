#!/usr/bin/env python3
"""Fail CI if GitHub Actions workflows still use Node 20-era JavaScript actions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

LEGACY_UPLOAD = re.compile(
    r"actions/upload-artifact@(?:v[1-4]\b|ea165f8d65b6e75b540449e92b4886f43607fa02)"
)
LEGACY_CHECKOUT = re.compile(
    r"actions/checkout@(?:v[1-4]\b|34e114876b0b11c390a56381ad16ebd13914f8d5)"
)
INVALID_CHECKOUT_PIN = re.compile(r"actions/checkout@v6\.\d")
LEGACY_SETUP_PYTHON = re.compile(
    r"actions/setup-python@(?:v[1-5]\b|a26af69be951a213d495a4c3e4e4022e16d87065)"
)
LEGACY_SETUP_NODE = re.compile(
    r"actions/setup-node@(?:v[1-4]\b|49933ea5288caeca8642d1e84afbd3f7d6820020)"
)
NODE20_OPT_OUT = re.compile(r"ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION")
FORCE_NODE24 = "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"


def main() -> int:
    errors: list[str] = []

    if not WORKFLOWS.is_dir():
        print(f"ERROR: missing {WORKFLOWS}")
        return 1

    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        rel = workflow.relative_to(ROOT)

        if LEGACY_CHECKOUT.search(text):
            errors.append(f"{rel}: must use actions/checkout@v6+ (Node 24 native)")

        if INVALID_CHECKOUT_PIN.search(text):
            errors.append(f"{rel}: use actions/checkout@v6 (major tag only; micro-tags like v6.2.2 do not exist)")

        if LEGACY_UPLOAD.search(text):
            errors.append(f"{rel}: must use actions/upload-artifact@v6+ (Node 24 native)")

        if LEGACY_SETUP_PYTHON.search(text):
            errors.append(f"{rel}: must use actions/setup-python@v6+ (Node 24 native)")

        if LEGACY_SETUP_NODE.search(text):
            errors.append(f"{rel}: must use actions/setup-node@v5+ (Node 24 native)")

        if NODE20_OPT_OUT.search(text):
            errors.append(
                f"{rel}: must not opt out of Node 24 (ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION)"
            )

        if FORCE_NODE24 not in text:
            errors.append(f'{rel}: must set env {FORCE_NODE24}: "true" at workflow level')

    if errors:
        print("GitHub Actions Node 24 policy violations:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        "OK: all workflows enforce Node 24 "
        "(FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 + Node 24-native actions)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
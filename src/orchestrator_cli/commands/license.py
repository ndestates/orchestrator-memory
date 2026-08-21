"""`orchestrator license` — check / validate installer license gate (Phase 3.5)."""

from __future__ import annotations

import os
import sys

from ..license import LicenseError, LicenseGate
from ..licensing_policy import (
    evaluate,
    gate_enabled,
    is_dev_exempt,
    resolve_flow_selections,
)


def _byom_notice() -> None:
    if os.environ.get("ORCHESTRATOR_SUPPRESS_BYOM_NOTICE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return
    print(
        "note: orchestrator does not include AI model subscriptions — "
        "use your own Grok/Copilot/Claude/Gemini accounts."
    )


def run_check(key: str | None = None) -> int:
    from pathlib import Path

    k = key or os.environ.get("ORCHESTRATOR_LICENSE_KEY")
    gate = LicenseGate(key=k)

    if is_dev_exempt():
        print("license: dev exempt (template checkout or ORCHESTRATOR_LICENSE_DEV=1)")
        _byom_notice()
        return 0

    if not gate_enabled():
        print("license: Light (free) — no validate URL configured")
        print("  deploy selections capped to free Light unless first-party/dev.")
        print(
            "  Pro (£99/mo per company; annual = 10× monthly = 2 months free): "
            "set ORCHESTRATOR_LICENSE_URL + ORCHESTRATOR_LICENSE_KEY"
        )
        _byom_notice()
        return 0

    # No key → Light without calling the network
    if not (k or "").strip():
        ent = evaluate(Path.cwd(), gate=gate)
        sel = resolve_flow_selections(None, ent) or "(light)"
        print("license: Light (free) — no ORCHESTRATOR_LICENSE_KEY")
        print(f"  deploy_selections={sel}")
        print(
            "  Pro (£99/mo per company; annual = 10× monthly = 2 months free): "
            "set ORCHESTRATOR_LICENSE_KEY after subscribe"
        )
        _byom_notice()
        return 0

    try:
        lease = gate.validate()
        if lease:
            tier = lease.tier
            ent = evaluate(Path.cwd(), gate=gate)
            sel = resolve_flow_selections(None, ent) or "(bundle default)"
            label = "Pro" if tier == "pro" or lease.is_first_party else "Light"
            print(f"license: valid ✓ ({label}, wire_tier={tier}, deploy_selections={sel})")
            if lease.allowed_selections:
                print(f"  allowed_selections: {', '.join(lease.allowed_selections)}")
            _byom_notice()
        else:
            print("license: valid (gate disabled)")
        return 0
    except LicenseError as exc:
        print(f"license: INVALID — {exc}", file=sys.stderr)
        print("  Free Light still works without a key; remove ORCHESTRATOR_LICENSE_KEY to use Light.", file=sys.stderr)
        return 1


def run() -> int:
    return run_check(None)
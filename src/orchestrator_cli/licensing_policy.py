"""Unified licensing policy for CLI init/upgrade (Phase 1).

Single module for entitlement evaluation, selection caps, and gate URL resolution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from . import defaults
from .first_party import is_first_party
from .license import LicenseError, LicenseGate, get_license_gate
from .template_root import dev_repo_root

if TYPE_CHECKING:
    from .license import Lease


class EntitlementKind(str, Enum):
    DEV_OPEN = "dev_open"
    FIRST_PARTY = "first_party"
    TRIAL_LITE = "trial_lite"
    PRO_FULL = "pro_full"
    DENIED = "denied"


@dataclass(frozen=True)
class Entitlement:
    kind: EntitlementKind
    """Deploy selections string, or None to use CLI/bundle default."""

    selections: str | None = None
    lease: Lease | None = None

    def to_dict(self) -> dict:
        out: dict = {
            "kind": self.kind.value,
            "selections": self.selections,
        }
        if self.lease is not None:
            out["tier"] = self.lease.tier
            out["expires_at"] = self.lease.expires_at
            if self.lease.allowed_selections is not None:
                out["allowed_selections"] = list(self.lease.allowed_selections)
        return out


def is_dev_exempt() -> bool:
    """True when license enforcement is disabled for template development."""
    if os.environ.get("ORCHESTRATOR_LICENSE_DEV", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return True
    return dev_repo_root() is not None


def effective_license_url() -> str | None:
    """Resolved validate endpoint, or None when gate is off."""
    if is_dev_exempt():
        return None
    explicit = (os.environ.get("ORCHESTRATOR_LICENSE_URL") or "").strip()
    if explicit:
        return explicit
    if defaults.DEFAULT_LICENSE_URL:
        return defaults.DEFAULT_LICENSE_URL
    return None


def gate_enabled() -> bool:
    return effective_license_url() is not None


def light_entitlement(*, lease: Lease | None = None) -> Entitlement:
    """Free Light tier — capped deploy selections (no MCP/wiki/full mirrors)."""
    return Entitlement(
        kind=EntitlementKind.TRIAL_LITE,
        selections=defaults.LIGHT_SELECTIONS,
        lease=lease,
    )


def _lease_to_entitlement(lease: Lease) -> Entitlement:
    if lease.is_first_party or lease.tier == "pro":
        return Entitlement(kind=EntitlementKind.PRO_FULL, lease=lease)
    selections = defaults.LIGHT_SELECTIONS
    if lease.allowed_selections:
        selections = ",".join(lease.allowed_selections)
    return Entitlement(
        kind=EntitlementKind.TRIAL_LITE,
        selections=selections,
        lease=lease,
    )


def evaluate(target: Path, *, gate: LicenseGate | None = None) -> Entitlement:
    """Determine entitlement for deploying into ``target`` (no deny — use enforce)."""
    if is_dev_exempt():
        return Entitlement(kind=EntitlementKind.DEV_OPEN)
    if is_first_party(target):
        return Entitlement(kind=EntitlementKind.FIRST_PARTY)
    g = gate or get_license_gate()
    if not g.enabled:
        # Gate off: free Light defaults for third-party (Pro needs URL + key)
        return light_entitlement()

    # Gate on, no key → Light without network (anonymous free tier)
    key = getattr(g, "_key", None) or os.environ.get("ORCHESTRATOR_LICENSE_KEY")
    if not (key or "").strip():
        return light_entitlement()

    try:
        lease = g.validate()
    except LicenseError:
        return Entitlement(kind=EntitlementKind.DENIED)
    if lease is None:
        return light_entitlement()
    return _lease_to_entitlement(lease)


def enforce_for_flow(target: Path, *, gate: LicenseGate | None = None) -> Entitlement:
    """Like evaluate but raises ``LicenseError`` when a provided key is invalid.

    Missing key with gate on → Light (free). Invalid/revoked key → denied.
    """
    if is_dev_exempt():
        return Entitlement(kind=EntitlementKind.DEV_OPEN)
    if is_first_party(target):
        return Entitlement(kind=EntitlementKind.FIRST_PARTY)
    g = gate or get_license_gate()
    if not g.enabled:
        return light_entitlement()

    key = getattr(g, "_key", None) or os.environ.get("ORCHESTRATOR_LICENSE_KEY")
    if not (key or "").strip():
        return light_entitlement()

    lease = g.validate()
    if lease is None:
        raise LicenseError("license gate enabled but validation returned no lease")
    return _lease_to_entitlement(lease)


def resolve_flow_selections(
    user_selections: str | None,
    entitlement: Entitlement,
) -> str | None:
    """Apply tier caps to user ``--selections`` for init/upgrade."""
    if entitlement.kind in (
        EntitlementKind.DEV_OPEN,
        EntitlementKind.FIRST_PARTY,
        EntitlementKind.PRO_FULL,
    ):
        return user_selections
    # Light / trial: force free bundle regardless of --selections all
    return entitlement.selections or defaults.LIGHT_SELECTIONS


def entitlement_summary(target: Path) -> dict:
    """JSON-friendly summary for status and license commands."""
    return {
        "dev_exempt": is_dev_exempt(),
        "gate_enabled": gate_enabled(),
        "license_url": effective_license_url(),
        "target_first_party": is_first_party(target),
        "entitlement": evaluate(target).to_dict(),
    }
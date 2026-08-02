"""Build-time and release defaults for the orchestrator CLI.

``DEFAULT_LICENSE_URL`` is empty in the source tree so local dev stays open
unless ``ORCHESTRATOR_LICENSE_URL`` is set. Release wheels may set
``ORCHESTRATOR_BUILD_DEFAULT_LICENSE_URL`` at build time.
"""

from __future__ import annotations

import os

DEFAULT_LICENSE_URL = os.environ.get(
    "ORCHESTRATOR_BUILD_DEFAULT_LICENSE_URL",
    "",
).strip()

# Free Orchestrator Light deploy caps (comma-separated bundle selection names).
# Pro (paid company subscription) unlocks any selection / "all".
# See docs/internal/FREEMIUM-LICENSE-AND-SERVER-PLAN.md and freemium freeze.
LIGHT_SELECTIONS = "grok,chains,loops,scripts,cache-spine"

# Back-compat alias used by older leases / tests
TRIAL_SELECTION_NAME = LIGHT_SELECTIONS

# Product freeze (v1 commercial): one license key per *company* (organization),
# not per human seat. Seats/devices can share the same key.
LICENSE_SCOPE = "company"  # company | seat (seat reserved for a later SKU)

# Pro pricing: £99 / month; annual = 12 months for 10× monthly (2 months free)
LICENSE_PRICE_GBP_MONTHLY = 99
LICENSE_PRICE_GBP = LICENSE_PRICE_GBP_MONTHLY  # alias used in issue responses
LICENSE_BILLING_INTERVAL_DEFAULT = "month"  # month | year
LICENSE_ANNUAL_MONTHS_CHARGED = 10  # pay for 10, get 12
LICENSE_ANNUAL_MONTHS_INCLUDED = 12
LICENSE_PRICE_GBP_ANNUAL = LICENSE_PRICE_GBP_MONTHLY * LICENSE_ANNUAL_MONTHS_CHARGED  # £990
LICENSE_ANNUAL_SAVINGS_MONTHS = (
    LICENSE_ANNUAL_MONTHS_INCLUDED - LICENSE_ANNUAL_MONTHS_CHARGED
)  # 2

LICENSE_SKU_PRO = "orchestrator-pro-company"
LICENSE_SKU_PRO_MONTHLY = "orchestrator-pro-company-monthly"
LICENSE_SKU_PRO_ANNUAL = "orchestrator-pro-company-annual"
LICENSE_SKU_LIGHT = "orchestrator-light-free"


def pro_price_summary() -> dict:
    """JSON-friendly Pro pricing for license-server issue responses / status."""
    return {
        "scope": LICENSE_SCOPE,
        "currency": "GBP",
        "monthly_gbp": LICENSE_PRICE_GBP_MONTHLY,
        "annual_gbp": LICENSE_PRICE_GBP_ANNUAL,
        "annual_months_charged": LICENSE_ANNUAL_MONTHS_CHARGED,
        "annual_months_included": LICENSE_ANNUAL_MONTHS_INCLUDED,
        "annual_free_months": LICENSE_ANNUAL_SAVINGS_MONTHS,
        "note": (
            f"£{LICENSE_PRICE_GBP_MONTHLY}/month per company; "
            f"annual = {LICENSE_ANNUAL_MONTHS_CHARGED}× monthly "
            f"(£{LICENSE_PRICE_GBP_ANNUAL}) for {LICENSE_ANNUAL_MONTHS_INCLUDED} months "
            f"({LICENSE_ANNUAL_SAVINGS_MONTHS} months free)"
        ),
    }


# Pro-only bundle selections (marketing + server allowed_selections null = all)
PRO_ONLY_SELECTIONS = (
    "mcp",
    "wiki",
    "claude",
    "copilot",
    "github",
    "gemini",
    "loops-starter",
)

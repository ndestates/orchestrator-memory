"""License gate for the orchestrator installer CLI (Phase 3.5).

Modeled on the MCP server gate but independent (CLI does not depend on mcp-server).

Flow: validate (if ORCHESTRATOR_LICENSE_URL set) -> lease in-memory ->
check returns cached until TTL -> failure raises LicenseError (deny).

Fail-open when no URL configured (local/dev use remains free until a
license server is live).

Uses only stdlib urllib. Injectable for tests.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Literal


class LicenseError(RuntimeError):
    """Raised when a license cannot be validated (deny access)."""


@dataclass
class Lease:
    """An in-memory license lease with an absolute expiry (epoch seconds).

    is_first_party: True for ndestates org keys (allowlist, no trial limit).
    False for third-party (24h trial; server controls renewal after trial).
    """

    token: str
    expires_at: float
    is_first_party: bool = False
    tier: Literal["trial", "pro"] = "trial"
    allowed_selections: list[str] | None = field(default=None)

    def is_valid(self, now: float) -> bool:
        return now < self.expires_at

    @property
    def is_trial(self) -> bool:
        return self.tier == "trial" and not self.is_first_party


class LicenseGate:
    """Optional license gate for CLI operations (init/upgrade)."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        lease_ttl: int = 86400,  # 24h default for trial
        *,
        urlopen: Callable[..., object] = urllib.request.urlopen,
        now: Callable[[], float] = time.time,
        timeout: float = 10.0,
    ) -> None:
        if url is not None:
            self._url = url or None
        else:
            from .licensing_policy import effective_license_url

            self._url = effective_license_url()
        self._key = key or os.environ.get("ORCHESTRATOR_LICENSE_KEY")
        self._lease_ttl = max(60, int(lease_ttl))
        self._urlopen = urlopen
        self._now = now
        self._timeout = timeout
        self._lease: Lease | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    def validate(self) -> Lease | None:
        """Contact server (if configured) and obtain/refresh lease.

        Returns None when disabled (allow). Raises LicenseError on failure.
        """
        if not self.enabled:
            return None

        body = json.dumps({"license_key": self._key}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"

        req = urllib.request.Request(
            self._url, data=body, headers=headers, method="POST"
        )
        try:
            with self._urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise LicenseError(f"license validation failed: {exc}") from exc

        if not isinstance(payload, dict) or not payload.get("valid"):
            raise LicenseError("license rejected by server")

        token = str(payload.get("lease_token") or "")
        server_ttl = payload.get("ttl")
        ttl = self._lease_ttl
        if isinstance(server_ttl, (int, float)) and server_ttl > 0:
            ttl = min(self._lease_ttl, int(server_ttl))
        is_first_party = bool(payload.get("is_first_party", False))
        raw_tier = str(payload.get("tier") or "").lower()
        tier: Literal["trial", "pro"] = "pro" if raw_tier == "pro" or is_first_party else "trial"
        allowed_raw = payload.get("allowed_selections")
        allowed: list[str] | None = None
        if isinstance(allowed_raw, list):
            allowed = [str(x) for x in allowed_raw if x]

        self._lease = Lease(
            token=token,
            expires_at=self._now() + ttl,
            is_first_party=is_first_party,
            tier=tier,
            allowed_selections=allowed,
        )
        return self._lease

    def check(self) -> bool:
        """Return True if allowed (or gate disabled). Revalidates if needed."""
        if not self.enabled:
            return True
        if self._lease is not None and self._lease.is_valid(self._now()):
            return True
        self.validate()
        return True


# Global default gate (reads env at import time, like MCP)
_default_gate: LicenseGate | None = None


def get_license_gate() -> LicenseGate:
    global _default_gate
    if _default_gate is None:
        _default_gate = LicenseGate()
    return _default_gate


def check_license() -> bool:
    """Convenience: check the default gate. Raises LicenseError on deny."""
    return get_license_gate().check()

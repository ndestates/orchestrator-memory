"""License gate for the orchestrator MCP server (Phase 2 scaffold).

Flow: ``validate`` POSTs to ``ORCHESTRATOR_LICENSE_URL`` -> on success stores a
short-lived in-memory **lease** -> ``check`` returns the cached lease until its
TTL expires, then revalidates -> any validation failure raises ``LicenseError``
(deny).

Fail-open by design: when ``ORCHESTRATOR_LICENSE_URL`` is unset the gate is
disabled and ``check`` always allows, mirroring how an unset
``ORCHESTRATOR_MCP_API_KEY`` leaves HTTP auth off. This keeps local/stdio use
working until a license server exists (CONCERNS §7).

Network uses the stdlib ``urllib`` only — no new dependency. ``urlopen`` and the
clock are injectable so tests run without a network or real time.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable


class LicenseError(RuntimeError):
    """Raised when a license cannot be validated (deny)."""


@dataclass
class Lease:
    """An in-memory license lease with an absolute expiry (epoch seconds).

    is_first_party: True for ndestates org keys (allowlist). False for third-party
    (subject to 24h trial; server will stop returning valid after trial unless paid).
    """

    token: str
    expires_at: float
    is_first_party: bool = False

    def is_valid(self, now: float) -> bool:
        return now < self.expires_at

    @property
    def is_trial(self) -> bool:
        return not self.is_first_party


class LicenseGate:
    """Validate a license, lease the result in memory, and deny on expiry/failure."""

    def __init__(
        self,
        url: str | None,
        key: str | None,
        lease_ttl: int,
        *,
        urlopen: Callable[..., object] = urllib.request.urlopen,
        now: Callable[[], float] = time.time,
        timeout: float = 10.0,
    ) -> None:
        self._url = url or None
        self._key = key or None
        self._lease_ttl = max(1, int(lease_ttl))
        self._urlopen = urlopen
        self._now = now
        self._timeout = timeout
        self._lease: Lease | None = None

    @property
    def enabled(self) -> bool:
        """True only when a license URL is configured."""
        return self._url is not None

    def validate(self) -> Lease | None:
        """Contact the license server and store a fresh lease.

        Returns ``None`` (allow) when the gate is disabled. Raises
        ``LicenseError`` on any transport, decode, or rejection failure.
        """
        if not self.enabled:
            return None

        body = json.dumps({"license_key": self._key}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        request = urllib.request.Request(
            self._url, data=body, headers=headers, method="POST"
        )
        try:
            with self._urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except LicenseError:
            raise
        except Exception as exc:  # network, HTTP, decode — all deny
            raise LicenseError(f"license validation failed: {exc}") from exc

        if not isinstance(payload, dict) or not payload.get("valid"):
            raise LicenseError("license rejected by server")

        token = str(payload.get("lease_token") or "")
        server_ttl = payload.get("ttl")
        ttl = self._lease_ttl
        if isinstance(server_ttl, (int, float)) and server_ttl > 0:
            ttl = min(self._lease_ttl, int(server_ttl))
        is_first_party = bool(payload.get("is_first_party", False))
        self._lease = Lease(
            token=token,
            expires_at=self._now() + ttl,
            is_first_party=is_first_party,
        )
        return self._lease

    def check(self) -> bool:
        """Return True if licensed, revalidating an expired/absent lease.

        Allows unconditionally when the gate is disabled. Propagates
        ``LicenseError`` (deny) if revalidation fails.
        """
        if not self.enabled:
            return True
        if self._lease is not None and self._lease.is_valid(self._now()):
            return True
        self.validate()
        return True

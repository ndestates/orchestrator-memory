"""Bearer token verification for HTTP transport."""

from __future__ import annotations

import hmac
from typing import Callable


def make_bearer_verifier(expected_key: str | None) -> Callable[[str | None], bool]:
    """Return a verifier compatible with FastMCP auth hooks."""

    def verify(token: str | None) -> bool:
        if not expected_key:
            return True
        if not token:
            return False
        return hmac.compare_digest(token, expected_key)

    return verify
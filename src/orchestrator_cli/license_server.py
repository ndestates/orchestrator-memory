"""License validate + issue/revoke HTTP server (POST /api/licenses/*).

Implements the contract expected by ``orchestrator_cli.license.LicenseGate``
and ``orchestrator_mcp.license.LicenseGate`` using **stdlib only**.

MVP for DigitalOcean / self-host:
  - ``POST /api/licenses/validate`` (public)
  - ``POST /api/licenses/issue`` (admin token)
  - ``POST /api/licenses/revoke`` (admin token)
  - ``GET /healthz``

Storage: SQLite (hashed keys only) when ``ORCHESTRATOR_LICENSE_DB`` is set;
otherwise in-memory allowlist env (local e2e). Never commit real keys.

Environment
-----------
ORCHESTRATOR_LICENSE_ALLOWLIST / FIRST_PARTY / ALLOWLIST_FILE / DEV_ACCEPT_ANY
    Legacy allowlist mode (plaintext keys in env — local only).
ORCHESTRATOR_LICENSE_DB
    Path to SQLite file (production MVP). Keys stored as SHA-256 hex.
ORCHESTRATOR_LICENSE_ADMIN_TOKEN
    Bearer token required for issue/revoke.
ORCHESTRATOR_LICENSE_SERVER_HOST / PORT / LEASE_TTL
    Bind + default lease ttl (default 86400; Pro often 2592000 = 30d).
ORCHESTRATOR_LICENSE_PRO_TTL
    Optional longer ttl for pro tier (default 2592000).
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from . import defaults

VALIDATE_PATH = "/api/licenses/validate"
ISSUE_PATH = "/api/licenses/issue"
REVOKE_PATH = "/api/licenses/revoke"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_TTL = 86400
DEFAULT_PRO_TTL = 2592000  # 30 days

LIGHT_SELECTIONS = [
    s.strip() for s in defaults.LIGHT_SELECTIONS.split(",") if s.strip()
]


def _split_csv(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def _load_file_keys(path: str | None) -> set[str]:
    if not path:
        return set()
    try:
        with open(path, encoding="utf-8") as fh:
            keys: set[str] = set()
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                keys.add(line)
            return keys
    except OSError as exc:
        print(f"license-server: cannot read allowlist file {path}: {exc}", file=sys.stderr)
        return set()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def fingerprint(key: str) -> str:
    return hash_key(key)[:12]


def generate_license_key(*, prefix: str = "orch") -> str:
    """Issue a high-entropy key (shown once to admin/customer)."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"


class SqliteLicenseDb:
    """Hash-only license table."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS licenses (
                    key_hash TEXT PRIMARY KEY,
                    tier TEXT NOT NULL,
                    email TEXT,
                    issued_at REAL NOT NULL,
                    revoked_at REAL,
                    is_first_party INTEGER NOT NULL DEFAULT 0,
                    note TEXT,
                    scope TEXT NOT NULL DEFAULT 'company'
                )
                """
            )
            conn.commit()

    def issue(
        self,
        *,
        tier: str = "pro",
        email: str | None = None,
        note: str | None = None,
        is_first_party: bool = False,
        scope: str = "company",
        raw_key: str | None = None,
    ) -> str:
        key = raw_key or generate_license_key()
        kh = hash_key(key)
        tier_n = "pro" if tier.lower() == "pro" else "trial"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO licenses
                (key_hash, tier, email, issued_at, revoked_at, is_first_party, note, scope)
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    kh,
                    tier_n,
                    email,
                    time.time(),
                    1 if is_first_party else 0,
                    note,
                    scope or defaults.LICENSE_SCOPE,
                ),
            )
            conn.commit()
        return key

    def revoke(self, *, key: str | None = None, key_hash: str | None = None) -> bool:
        kh = key_hash or (hash_key(key) if key else None)
        if not kh:
            return False
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE licenses SET revoked_at = ? WHERE key_hash = ? AND revoked_at IS NULL",
                (time.time(), kh),
            )
            conn.commit()
            return cur.rowcount > 0

    def lookup(self, key: str) -> dict | None:
        kh = hash_key(key)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM licenses WHERE key_hash = ?", (kh,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)


@dataclass
class LicenseStore:
    """Allowlist (env) + optional SQLite store."""

    allowlist: set[str] = field(default_factory=set)
    first_party: set[str] = field(default_factory=set)
    dev_accept_any: bool = False
    lease_ttl: int = DEFAULT_TTL
    pro_ttl: int = DEFAULT_PRO_TTL
    db: SqliteLicenseDb | None = None
    admin_token: str | None = None

    @classmethod
    def from_environ(cls, env: dict[str, str] | None = None) -> LicenseStore:
        e = env if env is not None else os.environ
        allow = _split_csv(e.get("ORCHESTRATOR_LICENSE_ALLOWLIST"))
        allow |= _load_file_keys(e.get("ORCHESTRATOR_LICENSE_ALLOWLIST_FILE"))
        first = _split_csv(e.get("ORCHESTRATOR_LICENSE_FIRST_PARTY"))
        allow |= first
        ttl_raw = e.get("ORCHESTRATOR_LICENSE_LEASE_TTL", str(DEFAULT_TTL))
        pro_ttl_raw = e.get("ORCHESTRATOR_LICENSE_PRO_TTL", str(DEFAULT_PRO_TTL))
        try:
            ttl = max(60, int(ttl_raw))
        except ValueError:
            ttl = DEFAULT_TTL
        try:
            pro_ttl = max(ttl, int(pro_ttl_raw))
        except ValueError:
            pro_ttl = DEFAULT_PRO_TTL
        db_path = (e.get("ORCHESTRATOR_LICENSE_DB") or "").strip()
        db = SqliteLicenseDb(db_path) if db_path else None
        admin = (e.get("ORCHESTRATOR_LICENSE_ADMIN_TOKEN") or "").strip() or None
        return cls(
            allowlist=allow,
            first_party=first,
            dev_accept_any=e.get("ORCHESTRATOR_LICENSE_DEV_ACCEPT_ANY", "") == "1",
            lease_ttl=ttl,
            pro_ttl=pro_ttl,
            db=db,
            admin_token=admin,
        )

    def _success(
        self,
        *,
        key: str,
        is_first_party: bool,
        tier: str,
        allowed: list[str] | None,
    ) -> dict:
        is_pro = is_first_party or tier == "pro"
        ttl = self.pro_ttl if is_pro else self.lease_ttl
        body: dict = {
            "valid": True,
            "lease_token": secrets.token_urlsafe(16),
            "ttl": ttl,
            "is_first_party": is_first_party,
            "tier": "pro" if is_pro else "trial",
            "key_fingerprint": fingerprint(key),
            "scope": defaults.LICENSE_SCOPE,
        }
        if not is_pro:
            body["allowed_selections"] = allowed or list(LIGHT_SELECTIONS)
        else:
            body["allowed_selections"] = None
        return body

    def validate_key(self, key: str | None) -> dict:
        """Return response body dict for a key (always includes ``valid``)."""
        # Anonymous Light: no key → free tier (optional product path)
        if not key:
            return {
                "valid": True,
                "lease_token": secrets.token_urlsafe(16),
                "ttl": self.lease_ttl,
                "is_first_party": False,
                "tier": "trial",
                "allowed_selections": list(LIGHT_SELECTIONS),
                "anonymous_light": True,
                "scope": defaults.LICENSE_SCOPE,
            }

        if self.db is not None:
            row = self.db.lookup(key)
            if row is None:
                # fall through to env allowlist
                pass
            elif row.get("revoked_at") is not None:
                return {"valid": False, "error": "revoked_key"}
            else:
                return self._success(
                    key=key,
                    is_first_party=bool(row.get("is_first_party")),
                    tier=str(row.get("tier") or "trial"),
                    allowed=list(LIGHT_SELECTIONS),
                )

        if key in self.allowlist or (self.dev_accept_any and key):
            is_fp = key in self.first_party
            return self._success(
                key=key,
                is_first_party=is_fp,
                tier="pro" if is_fp else "trial",
                allowed=list(LIGHT_SELECTIONS),
            )

        return {"valid": False, "error": "unknown_or_revoked_key"}

    def issue(
        self,
        *,
        tier: str = "pro",
        email: str | None = None,
        note: str | None = None,
        is_first_party: bool = False,
        scope: str | None = None,
    ) -> dict:
        if self.db is None:
            return {
                "ok": False,
                "error": "sqlite_required",
                "hint": "Set ORCHESTRATOR_LICENSE_DB to issue durable keys",
            }
        key = self.db.issue(
            tier=tier,
            email=email,
            note=note,
            is_first_party=is_first_party,
            scope=scope or defaults.LICENSE_SCOPE,
        )
        is_pro = tier.lower() == "pro"
        out: dict = {
            "ok": True,
            "license_key": key,
            "tier": "pro" if is_pro else "trial",
            "scope": scope or defaults.LICENSE_SCOPE,
            "email": email,
            "key_fingerprint": fingerprint(key),
            "note": "Store the license_key now; only the hash is retained server-side.",
        }
        if is_pro:
            out["pricing"] = defaults.pro_price_summary()
            out["price_gbp_monthly"] = defaults.LICENSE_PRICE_GBP_MONTHLY
            out["price_gbp_annual"] = defaults.LICENSE_PRICE_GBP_ANNUAL
            # Back-compat field: list monthly list price
            out["price_gbp"] = defaults.LICENSE_PRICE_GBP_MONTHLY
        else:
            out["price_gbp"] = 0
        return out

    def revoke(self, *, key: str | None = None, key_hash: str | None = None) -> dict:
        if self.db is None:
            return {"ok": False, "error": "sqlite_required"}
        ok = self.db.revoke(key=key, key_hash=key_hash)
        return {"ok": ok, "revoked": ok}


def extract_key_from_request(
    *,
    headers: dict[str, str],
    body: bytes,
) -> str | None:
    """Pull key from Authorization Bearer and/or JSON body."""
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        bearer = auth[7:].strip()
        if bearer:
            return bearer

    if not body:
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    key = payload.get("license_key") or payload.get("key")
    return str(key) if key else None


def _json_body(body: bytes) -> dict:
    if not body:
        return {}
    try:
        data = json.loads(body.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def make_handler(store: LicenseStore):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # quieter default
            sys.stderr.write("[license-server] " + (fmt % args) + "\n")

        def _send(self, code: int, payload: dict) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def _admin_ok(self, headers: dict[str, str]) -> bool:
            if not store.admin_token:
                return False
            auth = headers.get("Authorization") or headers.get("authorization") or ""
            if auth.lower().startswith("bearer "):
                return auth[7:].strip() == store.admin_token
            return headers.get("X-Admin-Token") == store.admin_token

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in ("/", "/health", "/healthz"):
                self._send(
                    200,
                    {
                        "ok": True,
                        "service": "orchestrator-license-api",
                        "sqlite": store.db is not None,
                        "scope": defaults.LICENSE_SCOPE,
                    },
                )
                return
            self._send(404, {"valid": False, "error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length > 0 else b""
            headers = {k: v for k, v in self.headers.items()}

            if path == VALIDATE_PATH:
                key = extract_key_from_request(headers=headers, body=body)
                result = store.validate_key(key)
                # Anonymous light is 200; unknown key 401
                if result.get("valid"):
                    code = 200
                else:
                    code = 401
                self._send(code, result)
                return

            if path == ISSUE_PATH:
                if not self._admin_ok(headers):
                    self._send(403, {"ok": False, "error": "admin_required"})
                    return
                data = _json_body(body)
                result = store.issue(
                    tier=str(data.get("tier") or "pro"),
                    email=data.get("email"),
                    note=data.get("note"),
                    is_first_party=bool(data.get("is_first_party")),
                    scope=data.get("scope"),
                )
                code = 200 if result.get("ok") else 400
                self._send(code, result)
                return

            if path == REVOKE_PATH:
                if not self._admin_ok(headers):
                    self._send(403, {"ok": False, "error": "admin_required"})
                    return
                data = _json_body(body)
                result = store.revoke(
                    key=data.get("license_key") or data.get("key"),
                    key_hash=data.get("key_hash"),
                )
                code = 200 if result.get("ok") else 404
                self._send(code, result)
                return

            self._send(404, {"valid": False, "error": "not_found"})

    return Handler


def serve(
    host: str | None = None,
    port: int | None = None,
    *,
    store: LicenseStore | None = None,
) -> ThreadingHTTPServer:
    h = host or os.environ.get("ORCHESTRATOR_LICENSE_SERVER_HOST", DEFAULT_HOST)
    p = port if port is not None else int(
        os.environ.get("ORCHESTRATOR_LICENSE_SERVER_PORT", DEFAULT_PORT)
    )
    s = store or LicenseStore.from_environ()
    httpd = ThreadingHTTPServer((h, p), make_handler(s))
    return httpd


def main(argv: Iterable[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    host = os.environ.get("ORCHESTRATOR_LICENSE_SERVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("ORCHESTRATOR_LICENSE_SERVER_PORT", DEFAULT_PORT))
    if "--help" in args or "-h" in args:
        print(__doc__)
        print(
            f"\nUsage: orchestrator license-server  "
            f"(or python -m orchestrator_cli.license_server)"
        )
        print(f"  validate: POST http://{host}:{port}{VALIDATE_PATH}")
        print(f"  issue:    POST http://{host}:{port}{ISSUE_PATH}  (admin)")
        print(f"  revoke:   POST http://{host}:{port}{REVOKE_PATH} (admin)")
        return 0

    store = LicenseStore.from_environ()
    if not store.allowlist and not store.dev_accept_any and store.db is None:
        print(
            "license-server: WARNING — no allowlist, no SQLite DB, DEV_ACCEPT_ANY!=1; "
            "only anonymous Light validates. Set ORCHESTRATOR_LICENSE_DB + "
            "ORCHESTRATOR_LICENSE_ADMIN_TOKEN for issue/revoke.",
            file=sys.stderr,
        )

    httpd = serve(host, port, store=store)
    print(
        f"license-server: listening on http://{host}:{port}\n"
        f"  validate {VALIDATE_PATH} | issue {ISSUE_PATH} | revoke {REVOKE_PATH}\n"
        f"  allowlist={len(store.allowlist)} first-party={len(store.first_party)} "
        f"sqlite={store.db is not None} dev_accept_any={store.dev_accept_any} "
        f"scope={defaults.LICENSE_SCOPE}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nlicense-server: stopped", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

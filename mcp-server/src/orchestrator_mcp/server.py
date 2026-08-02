"""Orchestrator enterprise MCP server entrypoint."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from orchestrator_mcp.audit import AuditLogger, timed_audit
from orchestrator_mcp.auth import make_bearer_verifier
from orchestrator_mcp.config import (
    find_manifest_path,
    is_loopback_host,
    load_server_config,
    resolve_project_root,
)
from orchestrator_mcp.helpers import (
    extract_open_todo_items,
    latest_todo_file,
    get_chain_by_id,
    load_chains_registry,
    match_chains_by_intent,
    read_cache_freshness,
    summarize_manifest,
)
from orchestrator_mcp.license import LicenseError, LicenseGate
from orchestrator_mcp.sandbox import SandboxError, read_bounded, resolve_audit_script

mcp = FastMCP(
    "orchestrator",
    instructions=(
        "Manifest-first, cache-first MCP server for the orchestrator template. "
        "Load manifest and cache before reading application source. "
        "Respect agent_policy approval gates for medium/high risk operations."
    ),
)

_config = load_server_config()
_audit = AuditLogger(_config.audit_dir)
_root = _config.project_root
_license = LicenseGate(_config.license_url, _config.license_key, _config.lease_ttl)


def _rel(path: str) -> str:
    return path.lstrip("/")


def _enforce_license() -> None:
    """Deny a tool call when a configured license is invalid.

    Fail-open: a no-op when ORCHESTRATOR_LICENSE_URL is unset (local/stdio dev),
    so this only bites once the gate is configured against a license server.
    """
    try:
        _license.check()
    except LicenseError as exc:
        raise ValueError(f"license check failed: {exc}") from exc


class BearerASGIMiddleware:
    """Raw ASGI middleware enforcing a bearer token on HTTP requests.

    Implemented at the ASGI layer (not Starlette ``BaseHTTPMiddleware``) so it does
    not buffer streaming/SSE responses used by the streamable-http transport.
    Non-HTTP scopes (lifespan, websocket) pass straight through to preserve the
    wrapped app's lifespan/session manager.
    """

    def __init__(self, app, verify) -> None:
        self.app = app
        self.verify = verify

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        raw = headers.get(b"authorization", b"").decode("latin-1")
        token = raw[7:] if raw[:7].lower() == "bearer " else None
        if not self.verify(token):
            await self._unauthorized(send)
            return
        await self.app(scope, receive, send)

    @staticmethod
    async def _unauthorized(send) -> None:
        body = b'{"error":"unauthorized"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b"Bearer"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return server health and project root."""
    with timed_audit(_audit, "health_check"):
        manifest = find_manifest_path(_root)
        return {
            "status": "ok",
            "project_root": str(_root),
            "manifest": str(manifest.relative_to(_root)) if manifest else "missing",
            "transport_note": "stdio=local; HTTP requires ORCHESTRATOR_MCP_API_KEY when set",
        }


@mcp.tool()
def get_project_manifest() -> dict[str, Any]:
    """Load project manifest summary (stack, paths, token/chain/loop policy).

    Always includes ``identity`` — check that the manifest describes *this* repo
    and is not stock orchestrator template residue. When identity.status is
    template_residue or warn, surface identity_briefing and do not trust
    framework/runtime assumptions until the operator customizes the manifest.
    """
    with timed_audit(_audit, "get_project_manifest"):
        _enforce_license()
        return summarize_manifest(_root)


@mcp.tool()
def get_cache_freshness() -> dict[str, str]:
    """Read lean docs/codebase/.codebase-freshness.txt (fallback: bounded scan header)."""
    with timed_audit(_audit, "get_cache_freshness"):
        _enforce_license()
        return read_cache_freshness(_root, _config.max_read_bytes)


@mcp.tool()
def read_cache_file(relative_path: str, max_bytes: int | None = None) -> str:
    """Read an allowlisted cache or registry file under PROJECT_ROOT (bounded)."""
    limit = min(max_bytes or _config.max_read_bytes, _config.max_read_bytes)
    with timed_audit(_audit, "read_cache_file") as timer:
        _enforce_license()
        timer.details["path"] = relative_path
        try:
            return read_bounded(_root, _rel(relative_path), limit)
        except SandboxError as exc:
            raise ValueError(str(exc)) from exc


@mcp.tool()
def get_latest_todo(max_items: int = 5) -> dict[str, Any]:
    """Return latest TODO file path and open checklist items."""
    max_items = max(1, min(max_items, 20))
    with timed_audit(_audit, "get_latest_todo"):
        _enforce_license()
        todo = latest_todo_file(_root)
        if todo is None:
            return {"path": None, "open_items": []}
        text = todo.read_text(encoding="utf-8", errors="replace")
        return {
            "path": str(todo.relative_to(_root)),
            "open_items": extract_open_todo_items(text, max_items),
        }


@mcp.tool()
def get_loop_state() -> dict[str, Any]:
    """Read STATE.md if present."""
    with timed_audit(_audit, "get_loop_state"):
        _enforce_license()
        rel = "STATE.md"
        try:
            content = read_bounded(_root, rel, _config.max_read_bytes)
        except FileNotFoundError:
            return {"path": rel, "content": None, "status": "missing"}
        return {"path": rel, "content": content, "status": "ok"}


@mcp.tool()
def list_chains(intent: str | None = None) -> list[dict[str, Any]]:
    """List chains from chains/registry.yaml; optional intent keyword filter."""
    with timed_audit(_audit, "list_chains") as timer:
        _enforce_license()
        registry = load_chains_registry(_root)
        chains = registry.get("chains") or []
        if intent:
            timer.details["intent"] = intent
            return match_chains_by_intent(registry, intent)
        return [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "description": c.get("description"),
                "steps": len(c.get("steps") or []),
                "token_tier": c.get("token_tier"),
            }
            for c in chains
            if isinstance(c, dict)
        ]


@mcp.tool()
def get_chain_detail(chain_id: str) -> dict[str, Any]:
    """Return full chain definition including steps and cache_files_required."""
    with timed_audit(_audit, "get_chain_detail") as timer:
        _enforce_license()
        timer.details["chain_id"] = chain_id
        chain = get_chain_by_id(_root, chain_id)
        if chain is not None:
            return chain
        raise ValueError(f"Chain not found: {chain_id}")


@mcp.tool()
def list_skills(tier: str | None = None) -> list[dict[str, Any]]:
    """List skills from chains/registry.yaml skills inventory."""
    with timed_audit(_audit, "list_skills") as timer:
        _enforce_license()
        if tier:
            timer.details["tier"] = tier
        registry = load_chains_registry(_root)
        skills = []
        for skill in registry.get("skills") or []:
            if not isinstance(skill, dict):
                continue
            if tier and skill.get("tier") != tier:
                continue
            skills.append(
                {
                    "id": skill.get("id"),
                    "slash": skill.get("slash"),
                    "tier": skill.get("tier"),
                    "description": skill.get("description"),
                }
            )
        return skills


@mcp.tool()
def get_skill_summary(skill_id: str) -> dict[str, Any]:
    """Return skill registry entry and first 80 lines of SKILL.md if present."""
    with timed_audit(_audit, "get_skill_summary") as timer:
        _enforce_license()
        timer.details["skill_id"] = skill_id
        registry = load_chains_registry(_root)
        entry: dict[str, Any] | None = None
        for skill in registry.get("skills") or []:
            if isinstance(skill, dict) and skill.get("id") == skill_id:
                entry = dict(skill)
                break
        if entry is None:
            raise ValueError(f"Skill not found: {skill_id}")

        skill_path = entry.get("path")
        preview = None
        if skill_path:
            try:
                full = read_bounded(_root, _rel(str(skill_path)), _config.max_read_bytes)
                lines = full.splitlines()[:80]
                preview = "\n".join(lines)
            except (SandboxError, FileNotFoundError):
                preview = None
        entry["preview"] = preview
        return entry


@mcp.tool()
def wiki_status() -> dict[str, Any]:
    """Lean LLM wiki status (mode, index sections, log tail, open questions)."""
    with timed_audit(_audit, "wiki_status"):
        _enforce_license()
        script = _root / "scripts" / "session-wiki-brief.py"
        if not script.is_file():
            return {"status": "missing_script", "message": "session-wiki-brief.py not deployed"}
        try:
            completed = subprocess.run(
                [sys.executable, str(script), "--json"],
                cwd=_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if completed.returncode != 0 and not completed.stdout.strip():
                return {
                    "status": "error",
                    "stderr": (completed.stderr or "")[:500],
                }
            import json as _json

            return _json.loads(completed.stdout or "{}")
        except Exception as exc:  # noqa: BLE001 — surface to MCP client
            return {"status": "error", "message": str(exc)[:300]}


@mcp.tool()
def wiki_search_index(query: str = "", max_hits: int = 10) -> dict[str, Any]:
    """Search wiki/index.md (and optional grep under wiki/) for query terms. Read-only."""
    with timed_audit(_audit, "wiki_search_index") as timer:
        _enforce_license()
        timer.details["query"] = (query or "")[:80]
        max_hits = max(1, min(max_hits, 30))
        index_rel = "wiki/index.md"
        hits: list[dict[str, str]] = []
        try:
            text = read_bounded(_root, index_rel, _config.max_read_bytes)
        except (SandboxError, FileNotFoundError) as exc:
            return {"status": "missing", "hits": [], "message": str(exc)}
        q = (query or "").strip().lower()
        if not q:
            # return section headers
            for ln in text.splitlines():
                if ln.startswith("## ") or ln.startswith("| ["):
                    hits.append({"file": index_rel, "line": ln.strip()[:200]})
                if len(hits) >= max_hits:
                    break
            return {"status": "ok", "hits": hits, "source": "index_outline"}
        for i, ln in enumerate(text.splitlines(), 1):
            if q in ln.lower():
                hits.append({"file": index_rel, "line_no": str(i), "line": ln.strip()[:200]})
            if len(hits) >= max_hits:
                break
        # light walk of wiki md filenames + first-line titles
        wiki_dir = _root / "wiki"
        if wiki_dir.is_dir() and len(hits) < max_hits:
            for path in sorted(wiki_dir.rglob("*.md")):
                rel = path.relative_to(_root).as_posix()
                if q in rel.lower() or q in path.stem.lower():
                    hits.append({"file": rel, "line": path.stem})
                if len(hits) >= max_hits:
                    break
        return {"status": "ok", "hits": hits, "source": "index+paths"}


@mcp.tool()
def wiki_read_page(relative_path: str, max_bytes: int | None = None) -> str:
    """Read one allowlisted wiki/ or raw/ page (bounded). Prefer index-first via wiki_search_index."""
    limit = min(max_bytes or _config.max_read_bytes, _config.max_read_bytes)
    with timed_audit(_audit, "wiki_read_page") as timer:
        _enforce_license()
        rel = _rel(relative_path)
        timer.details["path"] = rel
        if not (rel.startswith("wiki/") or rel.startswith("raw/")):
            raise ValueError("wiki_read_page only allows paths under wiki/ or raw/")
        try:
            return read_bounded(_root, rel, limit)
        except SandboxError as exc:
            raise ValueError(str(exc)) from exc


@mcp.tool()
def run_readonly_audit(audit: str) -> dict[str, Any]:
    """Run allowlisted read-only audit: chain, loop, alignment, or wiki."""
    with timed_audit(_audit, "run_readonly_audit") as timer:
        _enforce_license()
        timer.details["audit"] = audit
        script = resolve_audit_script(_root, audit)
        if script.suffix == ".py":
            cmd = [sys.executable, str(script)]
        else:
            cmd = ["bash", str(script)]

        try:
            completed = subprocess.run(
                cmd,
                cwd=_root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Audit timed out: {audit}") from exc

        return {
            "audit": audit,
            "script": str(script.relative_to(_root)),
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-4000:],
        }


@mcp.resource("orchestrator://manifest")
def resource_manifest() -> str:
    """Project manifest YAML."""
    path = find_manifest_path(_root)
    if path is None:
        return "# manifest missing"
    return path.read_text(encoding="utf-8", errors="replace")


@mcp.resource("orchestrator://cache/index")
def resource_cache_index() -> str:
    """docs/codebase/README.md cache index."""
    return read_bounded(_root, "docs/codebase/README.md", _config.max_read_bytes)


@mcp.resource("orchestrator://chains/registry")
def resource_chains_registry() -> str:
    """chains/registry.yaml."""
    return read_bounded(_root, "chains/registry.yaml", _config.max_read_bytes)


@mcp.resource("orchestrator://todo/latest")
def resource_todo_latest() -> str:
    """Latest TODO file contents."""
    todo = latest_todo_file(_root)
    if todo is None:
        return "# no TODO file"
    return todo.read_text(encoding="utf-8", errors="replace")[: _config.max_read_bytes]


@mcp.resource("orchestrator://state")
def resource_loop_state() -> str:
    """STATE.md loop spine."""
    try:
        return read_bounded(_root, "STATE.md", _config.max_read_bytes)
    except FileNotFoundError:
        return "# STATE.md missing"


@mcp.prompt()
def session_start_hint() -> str:
    """Cache-first session opener aligned with /chain session-start."""
    return (
        "Start session cache-first: read manifest, docs/codebase/README.md, "
        "CONCERNS.md, latest TODO, chains/registry.yaml. "
        "Do not read application source until direction is confirmed. "
        "Offer chain opt-out (no chain)."
    )


def _run_http(host: str, port: int, allow_insecure: bool) -> None:
    """Run the streamable-http transport, failing closed on weak configurations.

    Guarantees enforced here (independent of the FastMCP version):
      * No API key + non-loopback host -> refuse to start.
      * No API key + loopback host     -> refuse unless --allow-insecure-http.
      * API key set                    -> verify it on every request, or refuse
                                          to start if enforcement cannot be wired
                                          (never run pretending to be authed).
    """
    if not _config.api_key:
        if not is_loopback_host(host):
            raise SystemExit(
                f"Refusing HTTP on non-loopback host {host!r} without "
                "ORCHESTRATOR_MCP_API_KEY. Set a key or bind to 127.0.0.1."
            )
        if not allow_insecure:
            raise SystemExit(
                "HTTP transport requires ORCHESTRATOR_MCP_API_KEY. For local-only "
                "dev without auth, re-run with --allow-insecure-http."
            )
        print(
            "WARNING: starting UNAUTHENTICATED HTTP on "
            f"{host}:{port} (loopback dev only).",
            file=sys.stderr,
        )

    mcp.settings.host = host
    mcp.settings.port = port

    # Wire request-time bearer verification at the ASGI layer. If this FastMCP
    # build cannot expose the app and a key is required, fail closed rather than
    # fall back to an unenforced transport.
    try:
        app = mcp.streamable_http_app()
    except AttributeError as exc:
        if _config.api_key:
            raise SystemExit(
                "This FastMCP version cannot expose streamable_http_app(); "
                "refusing to serve HTTP with an API key it cannot enforce."
            ) from exc
        mcp.run(transport="streamable-http")
        return

    import uvicorn

    verifier = make_bearer_verifier(_config.api_key)
    uvicorn.run(BearerASGIMiddleware(app, verifier), host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrator MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--project-root", default=None)
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="Permit unauthenticated HTTP on a loopback host (local dev only).",
    )
    args = parser.parse_args()

    global _config, _audit, _root
    _root = resolve_project_root(args.project_root)
    _config = load_server_config(_root)
    _audit = AuditLogger(_config.audit_dir)

    if args.transport == "stdio":
        print(
            "orchestrator-mcp: stdio transport is unauthenticated and local-only; "
            "reads are confined to the PROJECT_ROOT allowlist.",
            file=sys.stderr,
        )
        mcp.run(transport="stdio")
    else:
        _run_http(args.host, args.port, args.allow_insecure_http)


if __name__ == "__main__":
    main()
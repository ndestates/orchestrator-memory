"""Project configuration loaded from manifest and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


MANIFEST_CANDIDATES = (
    ".grok/project-manifest.yaml",  # Grok preference for wave/fleet
    ".github/project-manifest.yaml",
    ".claude/project-manifest.yaml",
    ".gemini/project-manifest.yaml",
    ".copilot/project-manifest.yaml",
    ".cursor/project-manifest.yaml",
)

# Hosts confined to the local machine. HTTP without an API key is only ever
# tolerated when bound to one of these (and only with an explicit opt-in).
# Note: ``0.0.0.0`` binds all interfaces and is deliberately NOT loopback.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def is_loopback_host(host: str) -> bool:
    """True only for hosts confined to the local machine."""
    return host in LOOPBACK_HOSTS


@dataclass(frozen=True)
class ServerConfig:
    project_root: Path
    audit_dir: Path
    max_read_bytes: int
    api_key: str | None
    require_auth_http: bool
    license_url: str | None
    license_key: str | None
    lease_ttl: int


def resolve_project_root(explicit: str | None = None) -> Path:
    root = Path(explicit or os.environ.get("PROJECT_ROOT", ".")).resolve()
    if not root.is_dir():
        raise ValueError(f"PROJECT_ROOT is not a directory: {root}")
    return root


def load_server_config(project_root: Path | None = None) -> ServerConfig:
    root = project_root or resolve_project_root()
    api_key = os.environ.get("ORCHESTRATOR_MCP_API_KEY") or None
    audit_dir = root / os.environ.get("ORCHESTRATOR_MCP_AUDIT_DIR", "reports/mcp")
    max_read = int(os.environ.get("ORCHESTRATOR_MCP_MAX_READ_BYTES", "65536"))
    license_url = os.environ.get("ORCHESTRATOR_LICENSE_URL") or None
    license_key = os.environ.get("ORCHESTRATOR_LICENSE_KEY") or None
    lease_ttl = int(os.environ.get("ORCHESTRATOR_LICENSE_LEASE_TTL", "86400"))
    return ServerConfig(
        project_root=root,
        audit_dir=audit_dir,
        max_read_bytes=max_read,
        api_key=api_key,
        require_auth_http=bool(api_key),
        license_url=license_url,
        license_key=license_key,
        lease_ttl=lease_ttl,
    )


def find_manifest_path(root: Path) -> Path | None:
    for rel in MANIFEST_CANDIDATES:
        path = root / rel
        if path.is_file():
            return path
    return None


def load_manifest(root: Path) -> dict[str, Any]:
    path = find_manifest_path(root)
    if path is None:
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a mapping: {path}")
    return data


def manifest_paths(root: Path) -> dict[str, str]:
    manifest = load_manifest(root)
    paths = manifest.get("paths") or {}
    if not isinstance(paths, dict):
        return {}
    return {str(k): str(v) for k, v in paths.items()}
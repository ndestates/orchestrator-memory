"""Shared helpers for cache, chains, and TODO resolution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from orchestrator_mcp.config import load_manifest, manifest_paths
from orchestrator_mcp.sandbox import read_bounded

# Process-local registry cache: root -> (signature, data, by_id)
# signature = (composed mtime/size, template mtime/size, app mtime/size)
_registry_cache: dict[str, tuple[tuple[Any, ...], dict[str, Any], dict[str, dict[str, Any]]]] = {}


def _file_sig(path: Path) -> tuple[int, int] | None:
    try:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def clear_registry_cache(root: Path | None = None) -> None:
    """Drop MCP registry cache (tests / after compose)."""
    if root is None:
        _registry_cache.clear()
        return
    _registry_cache.pop(str(root.resolve()), None)


def latest_todo_file(root: Path, todo_dir: str = "TODO") -> Path | None:
    todo_path = root / todo_dir
    if not todo_path.is_dir():
        return None
    candidates = sorted(todo_path.glob("*_TODO.md"), reverse=True)
    if candidates:
        return candidates[0]
    md_files = sorted(todo_path.glob("*.md"), reverse=True)
    return md_files[0] if md_files else None


def extract_open_todo_items(text: str, max_items: int = 5) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            items.append(stripped[5:].strip())
        if len(items) >= max_items:
            break
    return items


def _index_chains_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for chain in data.get("chains") or []:
        if isinstance(chain, dict) and chain.get("id"):
            by_id[str(chain["id"])] = chain
    return by_id


def load_chains_registry(root: Path) -> dict[str, Any]:
    """Load composed registry (template + app overlay when split files exist).

    Caches by source file mtime/size so repeated MCP tool calls do not re-parse
    ~2.8k-line YAML each time (Phase B BH-003).
    """
    root = root.resolve()
    template = root / "chains" / "registry.template.yaml"
    app = root / "chains" / "registry.app.yaml"
    composed = root / "chains" / "registry.yaml"
    sig = (_file_sig(composed), _file_sig(template), _file_sig(app))
    cache_key = str(root)
    cached = _registry_cache.get(cache_key)
    if cached is not None and cached[0] == sig:
        return cached[1]

    data: dict[str, Any] | None = None
    if template.is_file() and app.is_file():
        try:
            import sys

            scripts = root / "scripts"
            if scripts.is_dir() and str(scripts) not in sys.path:
                sys.path.insert(0, str(scripts))
            from _engine.registry_compose import compose_registry, load_yaml

            composed_data = compose_registry(load_yaml(template), load_yaml(app))
            if isinstance(composed_data, dict):
                data = composed_data
        except Exception:
            data = None

    if data is None:
        if composed.is_file():
            with composed.open(encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
            data = loaded if isinstance(loaded, dict) else {"chains": [], "skills": []}
        else:
            data = {"chains": [], "skills": []}

    by_id = _index_chains_by_id(data)
    _registry_cache[cache_key] = (sig, data, by_id)
    return data


def get_chain_by_id(root: Path, chain_id: str) -> dict[str, Any] | None:
    """O(1) chain lookup using the registry id index (Phase B BH-003)."""
    root = root.resolve()
    load_chains_registry(root)  # ensure cache warm
    cached = _registry_cache.get(str(root))
    if not cached:
        return None
    return cached[2].get(chain_id)


def match_chains_by_intent(registry: dict[str, Any], intent: str) -> list[dict[str, Any]]:
    intent_lower = intent.lower()
    intent_tokens = set(re.findall(r"[a-z0-9]+", intent_lower))
    scored: list[tuple[int, dict[str, Any]]] = []

    for chain in registry.get("chains") or []:
        if not isinstance(chain, dict):
            continue
        hits = 0
        for phrase in chain.get("intents") or []:
            phrase_lower = str(phrase).lower()
            if phrase_lower in intent_lower or intent_lower in phrase_lower:
                hits += 2
            else:
                phrase_tokens = set(re.findall(r"[a-z0-9]+", phrase_lower))
                hits += len(intent_tokens & phrase_tokens)
        if hits:
            scored.append((hits, chain))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chain for _, chain in scored[:5]]


def read_cache_freshness(root: Path, max_bytes: int) -> dict[str, str]:
    freshness_rel = "docs/codebase/.codebase-freshness.txt"
    scan_rel = "docs/codebase/.codebase-scan.txt"
    rel = freshness_rel if (root / freshness_rel).is_file() else scan_rel
    try:
        text = read_bounded(root, rel, min(max_bytes, 4096))
    except FileNotFoundError:
        return {"status": "missing", "path": rel}
    info: dict[str, str] = {"status": "ok", "path": rel, "source": "freshness" if rel == freshness_rel else "scan"}
    for line in text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            info[key.strip().lower().replace(" ", "_")] = value.strip()
    return info


def _manifest_identity(root: Path) -> dict[str, Any]:
    """Identity check so any consumer of get_project_manifest sees template residue."""
    try:
        import sys

        scripts = root / "scripts"
        if scripts.is_dir() and str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from _engine.manifest_identity import check_manifest_identity

        return check_manifest_identity(root)
    except Exception as exc:  # pragma: no cover - soft failure for MCP
        return {
            "status": "error",
            "ok": False,
            "briefing_line": f"Manifest identity: ERROR — {exc}",
            "issues": [str(exc)],
            "recommendations": [],
        }


def summarize_manifest(root: Path) -> dict[str, Any]:
    manifest = load_manifest(root)
    paths = manifest_paths(root)
    identity = _manifest_identity(root)
    return {
        "project": manifest.get("project", {}),
        "stack": manifest.get("stack", {}),
        "paths": paths,
        "token_policy": manifest.get("token_policy", {}),
        "chain_policy": manifest.get("chain_policy", {}),
        "loop_policy": manifest.get("loop_policy", {}),
        # Always present: models must honor status != ok as a workflow gate
        "identity": identity,
        "identity_briefing": identity.get("briefing_line") or "",
    }
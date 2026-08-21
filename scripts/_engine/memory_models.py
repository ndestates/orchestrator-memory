"""Route always-on memory LLM work across *all* project model catalog entries.

Uses scripts/model-route/catalog.yaml (oss_models + free_cloud) plus host frontier
surfaces. Never silent-switches interactive hosts; daemon uses Ollama when ready.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

# Host frontier / interactive surfaces (project multi-AI)
HOST_FRONTIER_SURFACES: list[dict[str, Any]] = [
    {"id": "frontier:grok", "surface": "grok", "kind": "frontier", "fits": ["high", "medium"]},
    {"id": "frontier:claude", "surface": "claude", "kind": "frontier", "fits": ["high", "medium"]},
    {"id": "frontier:cursor", "surface": "cursor", "kind": "frontier", "fits": ["high", "medium"]},
    {"id": "frontier:gemini", "surface": "gemini", "kind": "frontier", "fits": ["high", "medium"]},
    {"id": "frontier:copilot", "surface": "copilot", "kind": "frontier", "fits": ["high", "medium"]},
    {"id": "frontier:chatgpt", "surface": "chatgpt", "kind": "frontier", "fits": ["high", "medium"]},
]

# Role → demand tier for model-route
ROLE_DEMAND: dict[str, str] = {
    "ingest": "low",
    "consolidate": "medium",
    "query": "medium",
    "query_status": "low",
    "query_security": "high",
    "daemon": "low",
}


def load_catalog(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    # Prefer model-route-suggest loader (shared)
    try:
        import importlib.util

        path = root / "scripts" / "model-route-suggest.py"
        spec = importlib.util.spec_from_file_location("model_route_suggest", path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.load_catalog(root / "scripts" / "model-route" / "catalog.yaml")
    except Exception:
        pass
    return {
        "oss_models": [],
        "free_cloud": [],
        "low_keywords": [],
        "high_keywords": [],
    }


def list_all_models(catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every model the project knows about (OSS + free cloud + host frontiers)."""
    cat = catalog if catalog is not None else load_catalog()
    out: list[dict[str, Any]] = []
    for m in cat.get("oss_models") or []:
        if not isinstance(m, dict):
            continue
        out.append(
            {
                "id": str(m.get("id") or ""),
                "kind": "oss",
                "license": m.get("license"),
                "fits": list(m.get("fits") or ["low"]),
                "tags": list(m.get("tags") or []),
                "note": m.get("note") or "",
                "surface": "ollama",
            }
        )
    for m in cat.get("free_cloud") or []:
        if not isinstance(m, dict):
            continue
        out.append(
            {
                "id": str(m.get("id") or ""),
                "kind": "free_cloud",
                "license": "proprietary_free",
                "fits": ["low", "medium"],
                "tags": [],
                "note": m.get("label") or "",
                "surface": str(m.get("surface") or ""),
            }
        )
    out.extend(HOST_FRONTIER_SURFACES)
    return [m for m in out if m.get("id")]


def _ollama_installed_names(root: Path) -> list[str]:
    try:
        from _engine.ollama_detect import detect_api  # type: ignore
    except ImportError:
        from scripts._engine.ollama_detect import detect_api  # type: ignore

    report = detect_api()
    if report.get("ollama_api") != "reachable":
        return []
    return list(report.get("ollama_model_names") or [])


def _match_installed(tags: list[str], installed: list[str]) -> str | None:
    installed_l = [x.lower() for x in installed]
    for tag in tags:
        t = tag.lower()
        for inst in installed_l:
            if inst == t or inst.startswith(t + ":") or t in inst:
                # return original installed name
                for orig in installed:
                    if orig.lower() == inst:
                        return orig
    return None


def pick_model_for_role(
    role: str,
    *,
    root: Path | None = None,
    catalog: dict[str, Any] | None = None,
    force_model: str | None = None,
    prefer_kind: str | None = None,
) -> dict[str, Any]:
    """Pick a model id for ingest|consolidate|query using full catalog.

    Order:
      1. ORCHESTRATOR_MEMORY_MODEL or force_model if in catalog/all
      2. Installed Ollama matching OSS fits for demand tier
      3. First OSS catalog entry that fits (install needed)
      4. free_cloud entry matching surface
      5. frontier stay (interactive) for high demand
      6. heuristic (no LLM)
    """
    root = root or ROOT
    cat = catalog if catalog is not None else load_catalog()
    all_models = list_all_models(cat)
    demand = ROLE_DEMAND.get(role, "low")
    forced = (force_model or os.environ.get("ORCHESTRATOR_MEMORY_MODEL") or "").strip()
    if forced:
        for m in all_models:
            if m["id"] == forced or forced in (m.get("tags") or []):
                return {
                    **m,
                    "selected_for": role,
                    "demand": demand,
                    "backend": "ollama" if m.get("kind") == "oss" else m.get("kind"),
                    "status": "forced",
                }
        return {
            "id": forced,
            "kind": "custom",
            "fits": [demand],
            "selected_for": role,
            "demand": demand,
            "backend": "ollama",
            "status": "forced_unknown",
            "surface": "ollama",
        }

    installed = _ollama_installed_names(root)
    # Prefer installed OSS that fits demand
    for m in cat.get("oss_models") or []:
        if not isinstance(m, dict):
            continue
        fits = [str(x) for x in (m.get("fits") or [])]
        if demand not in fits and not (demand == "low" and "low" in fits):
            # allow medium models for low if no low-only match later
            if demand == "low" and "medium" in fits:
                pass
            elif demand == "medium" and ("medium" in fits or "low" in fits):
                pass
            elif demand == "high":
                continue
            else:
                continue
        tags = list(m.get("tags") or [m.get("id")])
        hit = _match_installed([str(t) for t in tags if t], installed)
        if hit:
            return {
                "id": str(m.get("id")),
                "kind": "oss",
                "ollama_name": hit,
                "fits": fits,
                "selected_for": role,
                "demand": demand,
                "backend": "ollama",
                "status": "ready",
                "surface": "ollama",
                "license": m.get("license"),
            }

    if demand == "high":
        # High → stay on frontier (interactive host agents)
        return {
            "id": "frontier:interactive",
            "kind": "frontier",
            "selected_for": role,
            "demand": demand,
            "backend": "host_agent",
            "status": "interactive",
            "surface": "all_hosts",
            "note": "Use host agent (Grok/Claude/Cursor/Gemini/Copilot/ChatGPT) — never free-route",
        }

    # No Ollama ready: offer first OSS install target, else free_cloud, else heuristic
    oss = [m for m in (cat.get("oss_models") or []) if isinstance(m, dict)]
    if oss:
        m0 = oss[0]
        return {
            "id": str(m0.get("id")),
            "kind": "oss",
            "fits": list(m0.get("fits") or []),
            "selected_for": role,
            "demand": demand,
            "backend": "heuristic",
            "status": "install_needed",
            "surface": "ollama",
            "note": f"Install Ollama model {m0.get('id')} for LLM path",
        }

    free = [m for m in (cat.get("free_cloud") or []) if isinstance(m, dict)]
    if free and prefer_kind != "oss":
        m0 = free[0]
        return {
            "id": str(m0.get("id")),
            "kind": "free_cloud",
            "selected_for": role,
            "demand": demand,
            "backend": "host_agent",
            "status": "interactive",
            "surface": str(m0.get("surface") or ""),
            "note": m0.get("label") or "",
        }

    return {
        "id": "heuristic",
        "kind": "heuristic",
        "selected_for": role,
        "demand": demand,
        "backend": "heuristic",
        "status": "fallback",
        "surface": "local",
    }


def models_inventory_brief(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    cat = load_catalog(root)
    all_m = list_all_models(cat)
    installed = _ollama_installed_names(root)
    return {
        "catalog_total": len(all_m),
        "oss_count": sum(1 for m in all_m if m.get("kind") == "oss"),
        "free_cloud_count": sum(1 for m in all_m if m.get("kind") == "free_cloud"),
        "frontier_count": sum(1 for m in all_m if m.get("kind") == "frontier"),
        "ollama_installed": installed,
        "models": all_m,
        "picks": {
            role: pick_model_for_role(role, root=root, catalog=cat)
            for role in ("ingest", "consolidate", "query", "query_status", "query_security")
        },
    }

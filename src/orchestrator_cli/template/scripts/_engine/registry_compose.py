"""Compose chains registry from template + app split files (Option B)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

TEMPLATE_NAME = "registry.template.yaml"
APP_NAME = "registry.app.yaml"
COMPOSED_NAME = "registry.yaml"

APP_SKILL_TIERS = frozenset({"app"})


def registry_paths(chains_dir: Path) -> dict[str, Path]:
    chains_dir = Path(chains_dir)
    return {
        "template": chains_dir / TEMPLATE_NAME,
        "app": chains_dir / APP_NAME,
        "composed": chains_dir / COMPOSED_NAME,
    }


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if item_id:
            out[str(item_id)] = item
    return out


def merge_skills(
    template_skills: list[dict[str, Any]],
    app_skills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = copy.deepcopy(_index_by_id(template_skills))
    for entry in app_skills:
        if isinstance(entry, dict) and entry.get("id"):
            merged[str(entry["id"])] = copy.deepcopy(entry)
    return sorted(merged.values(), key=lambda s: str(s.get("id", "")))


def merge_chains(
    template_chains: list[dict[str, Any]],
    app_chains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = copy.deepcopy(_index_by_id(template_chains))
    for entry in app_chains:
        if isinstance(entry, dict) and entry.get("id"):
            merged[str(entry["id"])] = copy.deepcopy(entry)
    return sorted(merged.values(), key=lambda c: str(c.get("id", "")))


def compose_registry(
    template: dict[str, Any],
    app: dict[str, Any],
    *,
    version: int = 2,
) -> dict[str, Any]:
    composed: dict[str, Any] = {"version": app.get("version") or template.get("version") or version}
    composed["skills"] = merge_skills(
        list(template.get("skills") or []),
        list(app.get("skills") or []),
    )
    composed["chains"] = merge_chains(
        list(template.get("chains") or []),
        list(app.get("chains") or []),
    )
    aliases = app.get("registry_aliases")
    if aliases:
        composed["registry_aliases"] = copy.deepcopy(aliases)
    return composed


def split_monolithic(
    monolithic: dict[str, Any],
    *,
    version: int = 2,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split a legacy registry.yaml into template + app documents."""
    template: dict[str, Any] = {"version": monolithic.get("version") or version}
    app: dict[str, Any] = {"version": monolithic.get("version") or version}

    template_skills: list[dict[str, Any]] = []
    app_skills: list[dict[str, Any]] = []
    for skill in monolithic.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        tier = skill.get("tier")
        if tier in APP_SKILL_TIERS:
            app_skills.append(copy.deepcopy(skill))
        else:
            template_skills.append(copy.deepcopy(skill))

    template["skills"] = template_skills
    template["chains"] = copy.deepcopy(list(monolithic.get("chains") or []))
    app["skills"] = app_skills
    app["chains"] = []

    aliases = monolithic.get("registry_aliases")
    if aliases:
        app["registry_aliases"] = copy.deepcopy(aliases)

    return template, app


def load_composed_registry(
    root: Path,
    *,
    chains_dir: Path | None = None,
    compose_if_missing: bool = True,
) -> dict[str, Any]:
    """Load composed registry — from split files when present, else legacy monolith."""
    chains = chains_dir or (Path(root) / "chains")
    paths = registry_paths(chains)

    if paths["template"].is_file() and paths["app"].is_file():
        return compose_registry(load_yaml(paths["template"]), load_yaml(paths["app"]))

    if paths["composed"].is_file():
        return load_yaml(paths["composed"])

    if compose_if_missing and paths["template"].is_file():
        return compose_registry(load_yaml(paths["template"]), {})

    return {"version": 2, "skills": [], "chains": []}


def write_composed(
    chains_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    paths = registry_paths(chains_dir)
    if not paths["template"].is_file():
        raise FileNotFoundError(f"Missing template registry: {paths['template']}")
    app = load_yaml(paths["app"]) if paths["app"].is_file() else {}
    composed = compose_registry(load_yaml(paths["template"]), app)
    if not dry_run:
        paths["composed"].write_text(dump_yaml(composed), encoding="utf-8")
    return composed


def extract_app_overlay(
    target_registry: dict[str, Any],
    template_registry: dict[str, Any],
) -> dict[str, Any]:
    """Build registry.app.yaml from a monolithic target vs orchestrator template."""
    template_skill_ids = {s["id"] for s in template_registry.get("skills", []) if s.get("id")}
    template_chains = _index_by_id(list(template_registry.get("chains") or []))

    app_skills: list[dict[str, Any]] = []
    for skill in target_registry.get("skills") or []:
        if not isinstance(skill, dict) or not skill.get("id"):
            continue
        sid = str(skill["id"])
        if skill.get("tier") == "app":
            app_skills.append(copy.deepcopy(skill))
            continue
        if sid not in template_skill_ids:
            entry = copy.deepcopy(skill)
            entry["tier"] = entry.get("tier") or "app"
            app_skills.append(entry)

    app_chains: list[dict[str, Any]] = []
    for chain in target_registry.get("chains") or []:
        if not isinstance(chain, dict) or not chain.get("id"):
            continue
        cid = str(chain["id"])
        template_chain = template_chains.get(cid)
        if template_chain is None:
            entry = copy.deepcopy(chain)
            entry["tier"] = entry.get("tier") or "app"
            app_chains.append(entry)
        elif chain != template_chain:
            entry = copy.deepcopy(chain)
            entry["tier"] = entry.get("tier") or "app"
            app_chains.append(entry)

    app_doc: dict[str, Any] = {
        "version": target_registry.get("version") or 2,
        "skills": app_skills,
        "chains": app_chains,
    }
    aliases = target_registry.get("registry_aliases")
    if aliases:
        app_doc["registry_aliases"] = copy.deepcopy(aliases)
    return app_doc
#!/usr/bin/env python3
"""
Register project-local .grok/skills in chains/registry.app.yaml (tier: app).

Run automatically after deploy-template-wave.sh. Project-only dirs are kept by
detect-project-skills.py before template sync; this script registers them in the
app registry overlay, then recomposes chains/registry.yaml. Idempotent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.registry_compose import APP_NAME, load_yaml, registry_paths, write_composed  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GROK_SKILLS = ROOT / ".grok/skills"
INVENTORY = Path(__file__).resolve().parent / "wave-inventory.yaml"

SKIP_DIRS = {"copilot-instructions", "README.md"}


def load_inventory() -> dict:
    if not INVENTORY.exists():
        return {"registry_aliases": {}}
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8")) or {}


def grok_skill_dirs() -> set[str]:
    dirs: set[str] = set()
    if not GROK_SKILLS.exists():
        return dirs
    for skill in GROK_SKILLS.rglob("SKILL.md"):
        rel = skill.parent.relative_to(GROK_SKILLS)
        name = str(rel).replace("\\", "/") if str(rel) != "." else skill.parent.name
        if name not in SKIP_DIRS:
            dirs.add(name)
    return dirs


def skill_dir_to_id(skill_dir: str) -> str:
    return skill_dir.replace("/", "-").replace("_", "-")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    block = text[4:end]
    data: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in block.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            data[key] = " ".join(buf).strip().strip("'\"")
            buf = []
            key = None
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v.startswith(">"):
                key = k
                buf = []
            elif v:
                data[k] = v.strip("'\"")
            else:
                key = k
                buf = []
    if key:
        data[key] = " ".join(buf).strip().strip("'\"")
    return data


def registry_skill_dirs(skills: list[dict]) -> dict[str, dict]:
    by_dir: dict[str, dict] = {}
    for entry in skills:
        path = entry.get("path", "")
        if not path.startswith(".grok/skills/"):
            continue
        rel = path.removeprefix(".grok/skills/").removesuffix("/SKILL.md")
        by_dir[rel] = entry
    return by_dir


def collapse(value: str) -> str:
    return " ".join(value.split())


def make_entry(
    skill_dir: str,
    meta: dict[str, str],
    *,
    tier: str = "app",
    force_id: str | None = None,
) -> dict:
    skill_id = force_id or skill_dir
    meta_name = (meta.get("name") or "").strip().strip("'\"")
    if not force_id and meta_name and meta_name == skill_dir:
        skill_id = meta_name
    description = collapse(meta.get("description", f"Project-local skill ({skill_dir})"))
    if len(description) > 160:
        description = description[:157] + "..."
    return {
        "id": skill_id,
        "slash": f"/{skill_id.lstrip('/')}",
        "path": f".grok/skills/{skill_dir}/SKILL.md",
        "tier": tier,
        "description": description,
    }


def dedupe_skills(skills: list[dict]) -> tuple[list[dict], list[str]]:
    """Drop duplicate ids; keep entry whose path matches its skill dir id best."""
    by_id: dict[str, dict] = {}
    removed: list[str] = []
    for entry in skills:
        eid = entry.get("id", "")
        path = entry.get("path", "")
        skill_dir = path.removeprefix(".grok/skills/").removesuffix("/SKILL.md")
        existing = by_id.get(eid)
        if not existing:
            by_id[eid] = entry
            continue
        existing_dir = existing.get("path", "").removeprefix(".grok/skills/").removesuffix("/SKILL.md")
        if skill_dir == eid and existing_dir != eid:
            removed.append(f"deduped {eid}: kept {path}")
            by_id[eid] = entry
        else:
            removed.append(f"deduped {eid}: kept {existing.get('path')}")
    return list(by_id.values()), removed


def fix_broken_entries(skills: list[dict], aliases: dict[str, str]) -> tuple[list[dict], list[str]]:
    fixed: list[str] = []
    kept: list[dict] = []
    for entry in skills:
        path = ROOT / entry.get("path", "")
        if path.exists():
            kept.append(entry)
            continue
        skill_id = entry.get("id", "")
        alias = aliases.get(skill_id)
        if alias:
            alias_path = GROK_SKILLS / alias / "SKILL.md"
            if alias_path.exists():
                entry = dict(entry)
                entry["path"] = f".grok/skills/{alias}/SKILL.md"
                entry["tier"] = "app"
                desc = entry.get("description", "")
                note = f" [app alias -> {alias}]"
                if note not in desc:
                    entry["description"] = (desc + note).strip()
                kept.append(entry)
                fixed.append(f"{skill_id} -> {alias} (missing file repaired)")
                continue
        fixed.append(f"removed stale registry entry: {skill_id} ({entry.get('path')})")
    return kept, fixed


def ensure_app_registry() -> Path:
    paths = registry_paths(ROOT / "chains")
    if paths["app"].is_file():
        return paths["app"]
    if paths["composed"].is_file() and not paths["template"].is_file():
        # Legacy monolith only — bootstrap minimal app file; compose will still work
        paths["app"].write_text(yaml.dump({"version": 2, "skills": [], "chains": []}, sort_keys=False), encoding="utf-8")
        return paths["app"]
    if not paths["template"].is_file() and paths["composed"].is_file():
        return paths["composed"]
    if not paths["app"].is_file():
        paths["app"].write_text(yaml.dump({"version": 2, "skills": [], "chains": []}, sort_keys=False), encoding="utf-8")
    return paths["app"]


def main() -> int:
    paths = registry_paths(ROOT / "chains")
    app_path = ensure_app_registry()

    if paths["template"].is_file():
        reg_path = app_path
        reg = load_yaml(app_path) or {"version": 2, "skills": [], "chains": []}
    elif paths["composed"].is_file():
        reg_path = paths["composed"]
        reg = yaml.safe_load(paths["composed"].read_text(encoding="utf-8")) or {}
        print("register-project-skills: legacy monolith mode (no split files)")
    else:
        print(f"register-project-skills: no registry at {paths['composed']}", file=sys.stderr)
        return 1

    inventory = load_inventory()
    aliases: dict[str, str] = inventory.get("registry_aliases") or {}

    skills: list[dict] = list(reg.get("skills") or [])
    # When writing the app overlay, also treat template skills as already registered
    # so we do not re-copy them as tier:app (would clobber shared/orchestrator tiers).
    if paths["template"].is_file() and reg_path == app_path:
        tpl = load_yaml(paths["template"]) or {}
        # Shadow into lookup sets only — do not write template rows into app file
        tpl_skills = [e for e in (tpl.get("skills") or []) if isinstance(e, dict)]
    else:
        tpl_skills = []

    by_dir = registry_skill_dirs(skills + tpl_skills)
    registered_ids = {e.get("id") for e in skills + tpl_skills}
    registered_paths = {e.get("path") for e in skills + tpl_skills}

    skills, repairs = fix_broken_entries(skills, aliases)
    by_dir = registry_skill_dirs(skills + tpl_skills)
    registered_ids = {e.get("id") for e in skills + tpl_skills}
    registered_paths = {e.get("path") for e in skills + tpl_skills}

    def register_missing(
        skill_list: list[dict],
        ids: set[str],
        paths_set: set[str],
        dirs: dict[str, dict],
    ) -> tuple[list[dict], set[str], set[str], dict[str, dict], list[str]]:
        new_added: list[str] = []
        for skill_dir in sorted(grok_skill_dirs()):
            if skill_dir in dirs:
                continue
            skill_path = GROK_SKILLS / skill_dir / "SKILL.md"
            meta = parse_frontmatter(skill_path)
            meta_name = (meta.get("name") or "").strip().strip("'\"")
            force_id: str | None = None
            if meta_name and meta_name != skill_dir:
                force_id = skill_dir
            if meta_name and meta_name in ids and meta_name != skill_dir:
                force_id = skill_dir
            entry = make_entry(skill_dir, meta, force_id=force_id)
            if entry["path"] in paths_set:
                continue
            if entry["id"] in ids:
                entry = make_entry(skill_dir, meta, force_id=skill_dir)
            if entry["id"] in ids:
                continue
            skill_list.append(entry)
            ids.add(entry["id"])
            paths_set.add(entry["path"])
            dirs[skill_dir] = entry
            new_added.append(f"{entry['id']} ({skill_dir})")
        return skill_list, ids, paths_set, dirs, new_added

    added: list[str] = []
    skills, registered_ids, registered_paths, by_dir, batch = register_missing(
        skills, registered_ids, registered_paths, by_dir
    )
    added.extend(batch)

    skills, deduped = dedupe_skills(skills)
    by_dir = registry_skill_dirs(skills + tpl_skills)
    registered_ids = {e.get("id") for e in skills + tpl_skills}
    registered_paths = {e.get("path") for e in skills + tpl_skills}
    skills, registered_ids, registered_paths, by_dir, batch = register_missing(
        skills, registered_ids, registered_paths, by_dir
    )
    added.extend(batch)
    reg["skills"] = skills
    reg_path.write_text(yaml.dump(reg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    if paths["template"].is_file():
        write_composed(ROOT / "chains")

    print("register-project-skills")
    if repairs:
        for r in repairs:
            print(f"  repair: {r}")
    for d in deduped:
        print(f"  dedupe: {d}")
    if added:
        for a in added:
            print(f"  registered (tier: app): {a}")
    if not repairs and not added and not deduped:
        print("  no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
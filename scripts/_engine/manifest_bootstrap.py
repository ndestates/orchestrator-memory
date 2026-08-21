"""Project-manifest install policy: never overwrite apps; seed/amend on new projects.

Hard rules
----------
1. ``project-manifest.yaml`` under any platform dir is **project-owned**.
   Deploy/upgrade must never replace an existing customized manifest with the
   template stock file.
2. On **new** projects (no manifest yet), seed from the template skeleton then
   **amend** identity + stack + runtime for *this* app (profile + file signals).
3. On **template residue** (still "Project Template" / generic stack after a
   prior deploy), amend identity/stack fields only — keep local policy sections.

Used by ``orchestrator init|upgrade`` (flow) after profile resolution.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from exc

from _engine.manifest_identity import (
    TEMPLATE_NAMES,
    detect_stack_signals,
    is_orchestrator_source_repo,
)
from _engine.manifest_sync import CANONICAL_REL, MANIFEST_TARGETS, sync_manifests
from _engine.roots import get_template_root

# Basename + platform dirs that hold project identity (never template-overwrite).
MANIFEST_BASENAME = "project-manifest.yaml"
PLATFORM_MANIFEST_RELS = tuple(rel for rel, _ in MANIFEST_TARGETS)

# Default stack fields per stack-profile id (override via profile.manifest_stack).
PROFILE_STACK_DEFAULTS: dict[str, dict[str, Any]] = {
    "laravel": {
        "framework": "laravel",
        "language": "php",
        "uses_database": True,
        "database_engine": "mysql",
    },
    "python-flask": {
        "framework": "flask",
        "language": "python",
        "uses_database": True,
        "database_engine": "sqlite",
    },
}

# Map detected repo signals → stack field sets (when profile defaults are generic).
SIGNAL_STACK: dict[str, dict[str, Any]] = {
    "laravel": {
        "framework": "laravel",
        "language": "php",
        "uses_database": True,
        "database_engine": "mysql",
    },
    "django": {
        "framework": "django",
        "language": "python",
        "uses_database": True,
        "database_engine": "postgres",
    },
    "fastapi": {
        "framework": "fastapi",
        "language": "python",
        "uses_database": True,
        "database_engine": "postgres",
    },
    "flask": {
        "framework": "flask",
        "language": "python",
        "uses_database": True,
        "database_engine": "sqlite",
    },
    "nextjs": {
        "framework": "nextjs",
        "language": "ts",
        "uses_database": False,
        "database_engine": "none",
    },
    "nuxt": {
        "framework": "nuxt",
        "language": "ts",
        "uses_database": False,
        "database_engine": "none",
    },
    "astro": {
        "framework": "astro",
        "language": "ts",
        "uses_database": False,
        "database_engine": "none",
    },
    "go": {
        "framework": "go",
        "language": "go",
        "uses_database": False,
        "database_engine": "none",
    },
}


def is_protected_manifest_rel(rel: str) -> bool:
    """True when *rel* is a per-platform project-manifest (never deploy overwrite).

    Protects exact platform paths and any ``*/project-manifest.yaml`` under a
    known platform root (``.github``, ``.grok``, …). Other filenames are not
    blocked (deploy allowlist still applies).
    """
    # Do NOT use str.lstrip("./") — it strips any leading '.' chars (".github" → "github")
    normalized = rel.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized in PLATFORM_MANIFEST_RELS:
        return True
    name = Path(normalized).name
    if name != MANIFEST_BASENAME:
        return False
    parts = Path(normalized).parts
    if not parts:
        return False
    platform_roots = {Path(r).parts[0] for r, _ in MANIFEST_TARGETS if Path(r).parts}
    return parts[0] in platform_roots


def find_existing_manifests(root: Path) -> list[Path]:
    found: list[Path] = []
    for rel, _ in MANIFEST_TARGETS:
        path = root / rel
        if path.is_file():
            found.append(path)
    return found


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )


def _template_manifest_body() -> dict[str, Any]:
    root = get_template_root()
    for rel in (CANONICAL_REL, ".grok/project-manifest.yaml", ".claude/project-manifest.yaml"):
        path = root / rel
        if path.is_file():
            data = _load_yaml(path)
            if data:
                return data
    # Minimal fallback if template tree incomplete
    return {
        "project": {
            "name": "Project Template",
            "description": "Reusable orchestrator template for fast start-to-beta delivery",
            "default_branch": "master",
        },
        "stack": {
            "framework": "generic",
            "language": "generic",
            "uses_database": False,
            "database_engine": "none",
        },
        "runtime": {
            "environment_manager": "local",
            "local_llm": "none",
            "ollama_runtime": "auto",
            "start_command": "",
            "test_command": "",
        },
        "token_policy": {"mode": "lean", "max_cache_files_default": 2},
    }


def _load_profile(profile_id: str) -> dict[str, Any]:
    path = get_template_root() / "scripts" / "stack-profiles" / f"{profile_id}.yaml"
    if not path.is_file():
        return {"id": profile_id}
    data = _load_yaml(path)
    data.setdefault("id", profile_id)
    return data


def _project_title(root: Path, profile: dict[str, Any]) -> str:
    """App identity title for seed/amend.

    Priority:
    1. profile ``project_titles_by_slug`` for this directory name
    2. humanized directory slug (real app name — not stack marketing title)
    3. profile ``project_title`` (only if slug is empty/unusable)
    """
    slug = root.name
    by_slug = profile.get("project_titles_by_slug") or {}
    if isinstance(by_slug, dict) and slug in by_slug:
        return str(by_slug[slug])
    # Prefer dir slug over profile project_title ("Python Flask App" is a stack
    # label, not the app identity — residue amend uses directory title).
    if slug and slug not in (".", ".."):
        return slug.replace("-", " ").replace("_", " ").title()
    title = profile.get("project_title")
    if title and str(title).strip() and str(title) != "Project Template":
        return str(title)
    return "Application"


def _project_description(title: str, profile_id: str, stack: dict[str, Any]) -> str:
    fw = stack.get("framework") or profile_id
    lang = stack.get("language") or "generic"
    return (
        f"{title} — {fw}/{lang} application with orchestrator "
        f"manifest-first, cache-first AI scaffolding (profile={profile_id})"
    )


def detect_runtime_manager(root: Path) -> str:
    if (root / ".ddev").is_dir():
        return "ddev"
    for name in (
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    ):
        if (root / name).is_file():
            return "docker-compose"
    return "local"


def resolve_stack_fields(
    root: Path,
    profile_id: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge profile defaults → profile.manifest_stack → repo file signals."""
    profile = profile or _load_profile(profile_id)
    stack: dict[str, Any] = {
        "framework": "generic",
        "language": "generic",
        "uses_database": False,
        "database_engine": "none",
        "profile": profile_id,
    }
    # 1) code defaults for known profiles
    stack.update(PROFILE_STACK_DEFAULTS.get(profile_id, {}))
    # 2) optional profile YAML block (authoritative for that profile)
    ms = profile.get("manifest_stack") or {}
    if isinstance(ms, dict):
        for key in ("framework", "language", "uses_database", "database_engine"):
            if key in ms and ms[key] is not None:
                stack[key] = ms[key]
    # 3) repo file signals override when they contradict "generic" or prove Laravel/etc.
    signals = detect_stack_signals(root)
    if signals:
        primary = signals[0]
        if primary in SIGNAL_STACK:
            if stack.get("framework") in (None, "", "generic") or primary in (
                "laravel",
                "django",
                "fastapi",
                "nextjs",
                "go",
            ):
                # Strong framework signals always win (e.g. artisan → laravel)
                if primary in ("laravel", "django", "fastapi", "nextjs", "nuxt", "astro", "go"):
                    stack.update(SIGNAL_STACK[primary])
                elif stack.get("framework") in (None, "", "generic"):
                    stack.update(SIGNAL_STACK[primary])
    stack["profile"] = profile_id
    return stack


def is_template_residue_manifest(data: dict[str, Any], root: Path) -> bool:
    """True when manifest still looks like stock orchestrator template (app repos)."""
    if is_orchestrator_source_repo(root):
        return False
    project = data.get("project") or {}
    name = str(project.get("name") or "").strip().lower()
    if name in TEMPLATE_NAMES or name == "project template":
        return True
    desc = str(project.get("description") or "").lower()
    if "reusable orchestrator template" in desc or "fast start-to-beta delivery" in desc:
        # Only residue if stack also still generic
        stack = data.get("stack") or {}
        if str(stack.get("framework") or "generic") == "generic":
            return True
    return False


def amend_manifest_for_project(
    data: dict[str, Any],
    root: Path,
    *,
    profile_id: str,
    force_identity: bool = False,
) -> dict[str, Any]:
    """Return a deep-copied manifest with project/stack/runtime amended."""
    out = deepcopy(data)
    profile = _load_profile(profile_id)
    title = _project_title(root, profile)
    stack = resolve_stack_fields(root, profile_id, profile)
    runtime_mgr = detect_runtime_manager(root)

    project = out.setdefault("project", {})
    if force_identity or is_template_residue_manifest(out, root):
        project["name"] = title
        project["description"] = _project_description(title, profile_id, stack)
    else:
        # New seed path always sets identity
        if not project.get("name") or str(project.get("name")).strip().lower() in TEMPLATE_NAMES:
            project["name"] = title
        if not project.get("description") or "orchestrator template" in str(
            project.get("description") or ""
        ).lower():
            project["description"] = _project_description(title, profile_id, stack)

    stack_node = out.setdefault("stack", {})
    for key, val in stack.items():
        # On residue amend or empty fields: write; preserve real app choices
        existing = stack_node.get(key)
        if key == "profile":
            stack_node[key] = profile_id
            continue
        if force_identity:
            # Residue path: apply resolved stack, but do not drop a True DB flag
            if key == "uses_database" and existing is True and val is False:
                continue
            if (
                key == "database_engine"
                and existing not in (None, "", "none", "generic")
                and val in (None, "", "none", "generic")
            ):
                continue
            stack_node[key] = val
            continue
        if existing in (None, "", "generic", "none"):
            stack_node[key] = val
    stack_node["profile"] = profile_id

    runtime = out.setdefault("runtime", {})
    existing_rt = runtime.get("environment_manager")
    if force_identity:
        # Prefer detected non-local; keep existing ddev/compose if detector says local
        if runtime_mgr != "local" or existing_rt in (None, "", "local"):
            runtime["environment_manager"] = runtime_mgr
    elif existing_rt in (None, "", "local") and runtime_mgr != "local":
        runtime["environment_manager"] = runtime_mgr

    return out


def write_canonical_and_sync(
    root: Path,
    data: dict[str, Any],
    *,
    dry_run: bool = False,
) -> list[str]:
    """Write canonical .github manifest body and sync all platform copies."""
    body = _dump_yaml(data)
    header = (
        "# Project Manifest v1\n"
        "# Purpose: make prompts/agents portable across repositories and reduce token cost.\n"
        "# Platform: GitHub Copilot (canonical — edit here)\n"
        "# Sync copies: python3 scripts/sync_manifests.py\n"
        "# Identity: customized for this project by orchestrator install "
        "(never overwritten by template deploy)\n"
    )
    canonical = root / CANONICAL_REL
    if dry_run:
        return [CANONICAL_REL, *[r for r, _ in MANIFEST_TARGETS if r != CANONICAL_REL]]
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(header + "\n" + body, encoding="utf-8")
    return sync_manifests(root, dry_run=False)


def ensure_project_manifest(
    root: Path,
    *,
    profile_id: str,
    mode: str = "init",
    dry_run: bool = False,
    amend_residue: bool = True,
) -> dict[str, Any]:
    """Ensure target has a stack-aware project-manifest; never clobber customized apps.

    Returns a result dict:
      action: preserved | seeded | amended | skipped_source
      path: primary manifest path (relative)
      profile: profile id
      stack: resolved stack fields
    """
    root = root.resolve()
    result: dict[str, Any] = {
        "action": "unknown",
        "path": CANONICAL_REL,
        "profile": profile_id,
        "stack": {},
        "paths_touched": [],
        "dry_run": dry_run,
        "mode": mode,
    }

    if is_orchestrator_source_repo(root):
        result["action"] = "skipped_source"
        result["note"] = "orchestrator template source keeps stock manifest"
        return result

    existing = find_existing_manifests(root)
    stack_preview = resolve_stack_fields(root, profile_id)
    result["stack"] = stack_preview

    if existing:
        primary = existing[0]
        data = _load_yaml(primary)
        result["path"] = str(primary.relative_to(root))
        if not is_template_residue_manifest(data, root):
            # Customized app identity — never overwrite with template
            result["action"] = "preserved"
            result["note"] = (
                f"existing project-manifest kept ({result['path']}); "
                "template deploy never overwrites"
            )
            # Ensure all platform copies exist (sync from existing body only)
            if not dry_run:
                try:
                    touched = sync_manifests(root, dry_run=False)
                    result["paths_touched"] = touched
                except FileNotFoundError:
                    pass
            return result

        if not amend_residue:
            result["action"] = "preserved"
            result["note"] = "template residue left unchanged (amend_residue=false)"
            return result

        amended = amend_manifest_for_project(
            data, root, profile_id=profile_id, force_identity=True
        )
        result["stack"] = amended.get("stack") or stack_preview
        if dry_run:
            result["action"] = "amended"
            result["note"] = "would amend template-residue identity/stack"
            return result
        touched = write_canonical_and_sync(root, amended, dry_run=False)
        result["action"] = "amended"
        result["paths_touched"] = touched
        result["path"] = CANONICAL_REL
        result["note"] = "amended template residue with project stack/identity"
        return result

    # No manifest — seed from template skeleton + amend for this project
    seed = amend_manifest_for_project(
        _template_manifest_body(),
        root,
        profile_id=profile_id,
        force_identity=True,
    )
    result["stack"] = seed.get("stack") or stack_preview
    if dry_run:
        result["action"] = "seeded"
        result["note"] = "would seed new project-manifest from template + stack amend"
        return result
    touched = write_canonical_and_sync(root, seed, dry_run=False)
    result["action"] = "seeded"
    result["paths_touched"] = touched
    result["path"] = CANONICAL_REL
    result["note"] = "seeded project-manifest for new project (stack-aware)"
    return result

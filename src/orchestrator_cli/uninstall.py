"""Uninstall orchestrator surfaces from a project and/or host CLI packages.

Project uninstall removes paths that deploy-bundle would install (default or
chosen selections), plus the ``.orchestrator-version`` lock. It never deletes
``.git``, app source heuristics, env files, or ``never_deploy`` paths unless
explicitly opted in for specific categories.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .lock import LOCK_NAME, read_lock
from .template_root import template_root

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

# Paths never removed by project uninstall (safety).
PROTECTED_PREFIXES = (
    ".git/",
    ".git",
    "node_modules/",
    "vendor/",
    ".env",
    "storage/",
    "bootstrap/",
    "database/",
    "app/",
    "resources/",
    "public/",
    "tests/Feature/",
    "tests/Unit/",
)

# Extra always-remove markers of an orchestrator install (beyond bundle file list).
ALWAYS_PROJECT_PATHS = (
    LOCK_NAME,  # .orchestrator-version
    "scripts/orchestrator-template-version",
    "mcp-server",
)

# Optional categories
OPTIONAL_CACHE = (
    "docs/codebase",
)
OPTIONAL_TODO = (
    "TODO",
)
OPTIONAL_STATE = (
    "STATE.md",
    "VISION.md",
    "loop-run-log.md",
)
KEEP_BY_DEFAULT = (
    ".grok/memories/who-i-am.md",
    "chains/registry.app.yaml",
)


@dataclass
class UninstallPlan:
    target: Path
    paths: list[str] = field(default_factory=list)
    skipped_protected: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    lock: dict | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": str(self.target),
            "paths": list(self.paths),
            "skipped_protected": list(self.skipped_protected),
            "missing": list(self.missing),
            "lock": self.lock,
            "errors": list(self.errors),
            "count": len(self.paths),
        }


def _is_template_source(path: Path) -> bool:
    return (path / "scripts" / "deploy_grok_to_project.py").is_file() and (
        path / "scripts" / "deploy-bundle.yaml"
    ).is_file() and path.name == "orchestrator"


def _load_bundle(root: Path | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required for project uninstall")
    tr = root or template_root()
    path = tr / "scripts" / "deploy-bundle.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"deploy-bundle.yaml not found at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("deploy-bundle.yaml must be a mapping")
    return data


def _selection_names(bundle: dict[str, Any], selections: str | None) -> list[str]:
    all_sel = bundle.get("selections") or {}
    if not isinstance(all_sel, dict):
        return []
    if selections is None or selections.strip() == "":
        defaults = bundle.get("default_selections") or list(all_sel.keys())
        return [s for s in defaults if s in all_sel]
    if selections.strip().lower() == "all":
        return list(all_sel.keys())
    names = []
    for part in selections.split(","):
        name = part.strip()
        if name and name in all_sel:
            names.append(name)
    return names


def _paths_from_selection(sel: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for d in sel.get("directories") or []:
        out.append(str(d).rstrip("/") + "/")
    for f in sel.get("files") or []:
        out.append(str(f))
    for item in sel.get("remap_files") or []:
        if isinstance(item, dict) and item.get("dest"):
            out.append(str(item["dest"]))
    return out


def _normalize_rel(rel: str) -> str:
    """Normalize relative path; keep leading dots (e.g. ``.grok/skills``)."""
    r = rel.replace("\\", "/")
    while r.startswith("./"):
        r = r[2:]
    return r.lstrip("/")  # strip only slashes, never '.'


def _is_protected(rel: str) -> bool:
    r = _normalize_rel(rel)
    if r in {p.rstrip("/") for p in PROTECTED_PREFIXES}:
        return True
    for pref in PROTECTED_PREFIXES:
        p = pref.rstrip("/")
        if r == p or r.startswith(p + "/"):
            return True
    if r.startswith(".env"):
        return True
    return False


def collect_project_paths(
    target: Path,
    *,
    selections: str | None = None,
    remove_cache: bool = False,
    remove_todo: bool = False,
    remove_state: bool = False,
    remove_memories: bool = False,
    remove_manifests: bool = False,
    force_template_source: bool = False,
) -> UninstallPlan:
    """Build list of relative paths to remove under ``target``."""
    target = target.resolve()
    plan = UninstallPlan(target=target, lock=read_lock(target))
    if not target.is_dir():
        plan.errors.append(f"not a directory: {target}")
        return plan
    if _is_template_source(target) and not force_template_source:
        plan.errors.append(
            "refusing to uninstall the orchestrator template source repo "
            "(use --force-template-source only if intentional)"
        )
        return plan

    try:
        bundle = _load_bundle()
    except Exception as exc:
        plan.errors.append(str(exc))
        return plan

    never = {_normalize_rel(str(x)) for x in (bundle.get("never_deploy") or [])}
    # never_deploy includes manifests and TODO/docs/codebase — respect unless opted in
    candidates: list[str] = []
    for name in _selection_names(bundle, selections):
        sel = (bundle.get("selections") or {}).get(name) or {}
        if isinstance(sel, dict):
            candidates.extend(_paths_from_selection(sel))

    for extra in ALWAYS_PROJECT_PATHS:
        candidates.append(extra)

    # Platform AI surfaces often fully from template
    for extra in (
        ".grok/skills",
        ".grok/prompts",
        ".grok/agents",
        ".grok/references",
        ".claude/commands",
        ".claude/agents",
        ".copilot/skills",
        ".github/skills",
        ".github/agents",
        ".github/prompts",
        ".gemini/prompts",
        ".cursor/rules",
    ):
        candidates.append(extra)

    if remove_cache:
        candidates.extend(OPTIONAL_CACHE)
    if remove_todo:
        candidates.extend(OPTIONAL_TODO)
    if remove_state:
        candidates.extend(OPTIONAL_STATE)
    if remove_manifests:
        candidates.extend(
            [
                ".github/project-manifest.yaml",
                ".claude/project-manifest.yaml",
                ".grok/project-manifest.yaml",
                ".copilot/project-manifest.yaml",
                ".gemini/project-manifest.yaml",
                ".cursor/project-manifest.yaml",
            ]
        )
    if remove_memories:
        candidates.append(".grok/memories")

    # Dedupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in candidates:
        rel = _normalize_rel(raw)
        if not rel or rel in seen:
            continue
        seen.add(rel)
        ordered.append(rel)

    keep = {_normalize_rel(k) for k in KEEP_BY_DEFAULT}
    if not remove_memories:
        keep.add(".grok/memories/who-i-am.md")

    for rel in ordered:
        if _is_protected(rel):
            plan.skipped_protected.append(rel)
            continue
        # never_deploy without opt-in
        base = rel.rstrip("/")
        if base in never or any(base == n.rstrip("/") or base.startswith(n.rstrip("/") + "/") for n in never):
            # allow if user opted into that category
            if base.startswith("docs/codebase") and remove_cache:
                pass
            elif base == "TODO" or base.startswith("TODO/") and remove_todo:
                pass
            elif base in OPTIONAL_STATE and remove_state:
                pass
            elif "project-manifest.yaml" in base and remove_manifests:
                pass
            else:
                plan.skipped_protected.append(rel)
                continue
        if rel in keep or any(rel.startswith(k.rstrip("/") + "/") for k in keep if k.endswith("/")):
            if not remove_memories and "who-i-am" in rel:
                plan.skipped_protected.append(rel)
                continue
        if rel in keep and not remove_memories:
            plan.skipped_protected.append(rel)
            continue

        path = target / rel.rstrip("/")
        if path.exists() or path.is_symlink():
            plan.paths.append(rel)
        else:
            plan.missing.append(rel)

    # Prefer removing deepest paths first when applying
    plan.paths.sort(key=lambda p: p.count("/"), reverse=True)
    return plan


def apply_project_uninstall(plan: UninstallPlan, *, dry_run: bool = True) -> list[str]:
    """Delete plan.paths under plan.target. Returns list of removed rel paths."""
    removed: list[str] = []
    if plan.errors:
        return removed
    for rel in plan.paths:
        path = plan.target / rel.rstrip("/")
        if dry_run:
            removed.append(rel)
            continue
        try:
            if path.is_symlink() or path.is_file():
                path.unlink(missing_ok=True)
                removed.append(rel)
            elif path.is_dir():
                shutil.rmtree(path)
                removed.append(rel)
        except OSError as exc:
            plan.errors.append(f"{rel}: {exc}")
    if not dry_run:
        _prune_empty_parents(plan.target, removed)
    return removed


def _prune_empty_parents(root: Path, removed: Iterable[str]) -> None:
    parents: set[Path] = set()
    root = root.resolve()
    for rel in removed:
        p = (root / rel.rstrip("/")).parent.resolve()
        while p != root and root in p.parents:
            parents.add(p)
            p = p.parent
    for p in sorted(parents, key=lambda x: len(x.parts), reverse=True):
        try:
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass


@dataclass
class HostUninstallResult:
    actions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "actions": self.actions,
            "errors": self.errors,
            "dry_run": self.dry_run,
        }


def uninstall_host_cli(*, dry_run: bool = True, npm: bool = True, pip: bool = True) -> HostUninstallResult:
    """Remove global npm package and/or pip package from this machine."""
    result = HostUninstallResult(dry_run=dry_run)
    if npm:
        cmd = ["npm", "uninstall", "-g", "@ndestates/orchestrator"]
        result.actions.append(" ".join(cmd))
        if not dry_run:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 and "not found" not in (r.stderr or "").lower():
                # also try without scope legacy
                r2 = subprocess.run(
                    ["npm", "uninstall", "-g", "orchestrator"],
                    capture_output=True,
                    text=True,
                )
                if r2.returncode != 0:
                    result.errors.append(
                        f"npm uninstall: {(r.stderr or r.stdout or r2.stderr or '')[:200]}"
                    )
    if pip:
        for py in ("python3", "python", "py"):
            # try uninstall; ignore if not installed
            cmd = [py, "-m", "pip", "uninstall", "-y", "orchestrator"]
            if py == "py":
                cmd = ["py", "-3", "-m", "pip", "uninstall", "-y", "orchestrator"]
            result.actions.append(" ".join(cmd))
            if not dry_run:
                r = subprocess.run(cmd, capture_output=True, text=True)
                # 0 or "not installed" is fine
                if r.returncode != 0 and "not installed" not in (r.stderr or "").lower() and "WARNING" not in (r.stderr or ""):
                    continue  # try next python
            break
    return result

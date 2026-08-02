"""Customize deployed skills for a target project (engine module)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from exc

from _engine.roots import get_template_root


def profiles_dir() -> Path:
    return get_template_root() / "scripts" / "stack-profiles"


def map_file() -> Path:
    return profiles_dir() / "manifest-map.yaml"


TEXT_SUFFIXES = {
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".sh",
    ".py",
    ".txt",
    ".cloud-config",
}

# Self-referential skills that legitimately name the template (repo slug,
# "Project Template", scan patterns). Must mirror the exclude list in
# scan-template-contamination.sh so customize and the gate stay consistent —
# rewriting these would corrupt their own documentation.
EXCLUDE_SKILLS = {"orchestrator-deploy", "template-decontaminate"}


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def manifest_paths(root: Path) -> list[Path]:
    from _engine import manifest_sync as _manifest_sync

    return _manifest_sync.manifest_search_paths(root)


def read_manifest(root: Path) -> dict:
    for path in manifest_paths(root):
        if path.is_file():
            return load_yaml(path)
    return {}


def resolve_profile(root: Path, explicit: str | None, auto: bool) -> str | None:
    if explicit:
        return explicit

    manifest = read_manifest(root)
    stack = manifest.get("stack") or {}
    profile_key = load_yaml(map_file()).get("manifest_profile_key", "stack.profile")
    if stack.get("profile"):
        return str(stack["profile"])
    # dotted key support (stack.profile)
    if "." in profile_key:
        node = manifest
        for part in profile_key.split("."):
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)
        if node:
            return str(node)

    if auto:
        mapping = load_yaml(map_file()).get("by_dirname") or {}
        slug = root.name
        if slug in mapping:
            return str(mapping[slug])
    return None


def profile_path(profile_id: str) -> Path:
    return profiles_dir() / f"{profile_id}.yaml"


def should_process(path: Path) -> bool:
    if not path.is_file():
        return False
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".cloud-config.yml")


def profile_context(root: Path, profile: dict) -> dict[str, str]:
    manifest = read_manifest(root)
    project = manifest.get("project") or {}
    slug = profile.get("project_slug") or root.name
    # Per-app titles from stack profile (laravel fleet shares one profile id).
    by_slug = profile.get("project_titles_by_slug") or {}
    slug_title = by_slug.get(slug) if isinstance(by_slug, dict) else None
    # A real (customized) manifest project name wins over the generic stack-profile
    # title: shared profiles like python-flask carry placeholder titles ("Python
    # Flask App"), so prefer the project's own identity when it has been set.
    manifest_name = project.get("name")
    if slug_title:
        title = str(slug_title)
    elif manifest_name and manifest_name != "Project Template":
        title = manifest_name
    else:
        title = profile.get("project_title") or slug
    if not profile.get("project_slug"):
        slug = root.name
    return {"slug": slug, "title": title}


# Template identifiers neutralized in every customized project, regardless of
# stack profile. The template's placeholder project name must become the real
# project title so the contamination gate (scan-template-contamination.sh) passes.
UNIVERSAL_REPLACEMENTS = [
    ["Project Template", "{title}"],
    ["ndestates/orchestrator", "{slug}"],
]


def expand_placeholders(value: str, ctx: dict[str, str]) -> str:
    for key, val in ctx.items():
        value = value.replace("{" + key + "}", val)
    return value


def apply_pairs(
    text: str, pairs: list[list[str]], ctx: dict[str, str] | None = None
) -> tuple[str, int]:
    total = 0
    for pair in pairs:
        if not pair or len(pair) != 2:
            continue
        old = expand_placeholders(pair[0], ctx or {})
        new = expand_placeholders(pair[1], ctx or {})
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            total += count
    return text, total


def cleanup_duplicates(text: str) -> str:
    for old, new in [
        ("facebook-stats/facebook-stats", "facebook-stats"),
        ("e.g. facebook-stats, facebook-stats", "e.g. facebook-stats"),
    ]:
        text = text.replace(old, new)
    return text


# Mirrors scan-template-contamination.sh scan_dirs (+ key root files).
SURFACE_REL_PATHS = (
    ".grok/skills",
    ".grok/prompts",
    ".grok/agents",
    ".grok/memories",
    ".github/skills",
    ".github/prompts",
    ".github/agents",
    ".github/copilot-instructions.md",
    ".copilot/skills",
    ".claude/commands",
    ".claude/agents",
    "CLAUDE.md",
)


def collect_surface_files(root: Path) -> list[Path]:
    """All text surfaces that must pass the contamination gate after sync."""
    files: list[Path] = []
    for rel in SURFACE_REL_PATHS:
        path = root / rel
        if path.is_file() and should_process(path):
            files.append(path)
            continue
        if not path.is_dir():
            continue
        for candidate in sorted(path.rglob("*")):
            if not should_process(candidate):
                continue
            rel_parts = candidate.relative_to(path).parts
            if rel_parts and rel_parts[0] in EXCLUDE_SKILLS:
                continue
            files.append(candidate)
    return files


def sweep_surfaces(root: Path, profile_id: str, *, dry_run: bool = False) -> int:
    """Apply profile replacements across all AI surfaces (post-sync decontaminate)."""
    profile = load_yaml(profile_path(profile_id))
    ctx = profile_context(root, profile)
    total = 0
    for path in collect_surface_files(root):
        if dry_run:
            continue
        total += apply_profile_to_file(path, profile, ctx)
    return total


def collect_skill_files(skills_dir: Path) -> list[Path]:
    files: list[Path] = []
    if not skills_dir.is_dir():
        return files
    for path in sorted(skills_dir.rglob("*")):
        if not should_process(path):
            continue
        rel_parts = path.relative_to(skills_dir).parts
        if rel_parts and rel_parts[0] in EXCLUDE_SKILLS:
            continue
        files.append(path)
    return files


def apply_profile_to_file(path: Path, profile: dict, ctx: dict[str, str]) -> int:
    original = path.read_text(encoding="utf-8")
    text = original
    count = 0

    for key in ("name_replacements", "stack_replacements"):
        text, n = apply_pairs(text, profile.get(key) or [], ctx)
        count += n

    text, n = apply_pairs(text, UNIVERSAL_REPLACEMENTS, ctx)
    count += n

    text = cleanup_duplicates(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
    return count


def apply_overrides(root: Path, profile: dict, profile_id: str, dry_run: bool) -> list[str]:
    applied: list[str] = []
    override_dir = profiles_dir() / profile_id / "overrides"
    for entry in profile.get("file_overrides") or []:
        source_name = entry.get("source")
        target_rel = entry.get("target")
        if not source_name or not target_rel:
            continue
        source = override_dir / source_name
        target = root / target_rel
        if not source.is_file():
            print(f"WARN missing override source: {source}", file=sys.stderr)
            continue
        content = source.read_text(encoding="utf-8")
        ctx = profile_context(root, profile)
        content = expand_placeholders(content, ctx)
        if dry_run:
            applied.append(str(target_rel))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        applied.append(str(target_rel))
    return applied


def run_customize(
    root: Path,
    profile_id: str,
    *,
    dry_run: bool = False,
    sync: bool = False,
) -> dict:
    profile_file = profile_path(profile_id)
    if not profile_file.is_file():
        raise SystemExit(f"Profile not found: {profile_file}")

    profile = load_yaml(profile_file)
    ctx = profile_context(root, profile)
    skills_dir = root / ".grok" / "skills"
    changed: list[dict] = []
    total_replacements = 0

    for path in collect_skill_files(skills_dir):
        rel = str(path.relative_to(root))
        if dry_run:
            original = path.read_text(encoding="utf-8")
            text = original
            for key in ("name_replacements", "stack_replacements"):
                text, _ = apply_pairs(text, profile.get(key) or [], ctx)
            text, _ = apply_pairs(text, UNIVERSAL_REPLACEMENTS, ctx)
            text = cleanup_duplicates(text)
            if text != original:
                changed.append({"file": rel, "replacements": "would-change"})
            continue
        n = apply_profile_to_file(path, profile, ctx)
        if n:
            changed.append({"file": rel, "replacements": n})
            total_replacements += n

    overrides = apply_overrides(root, profile, profile_id, dry_run)

    result = {
        "project_root": str(root),
        "profile": profile_id,
        "files_text_changed": changed,
        "file_overrides": overrides,
        "total_replacements": total_replacements,
        "dry_run": dry_run,
    }

    if sync and not dry_run:
        sync_script = root / "scripts" / "sync_grok_to_github_claude.py"
        if sync_script.is_file():
            # Prefer the target app's scripts/ on PYTHONPATH; drop other
            # orchestrator checkouts so sync_grok does not bind ROOT to the wrong tree.
            env = dict(**__import__("os").environ)
            env["PYTHONPATH"] = str(root / "scripts")
            subprocess.run(
                [sys.executable, str(sync_script)],
                cwd=root,
                check=True,
                env=env,
            )
            result["synced"] = True
            # Re-apply overrides after sync (sync regenerates .github/copilot-instructions.md)
            post_overrides = apply_overrides(root, profile, profile_id, dry_run=False)
            if post_overrides:
                result["file_overrides_post_sync"] = post_overrides
            swept = sweep_surfaces(root, profile_id, dry_run=False)
            if swept:
                result["surface_sweep_replacements"] = swept
        else:
            result["synced"] = False
            print(f"WARN sync script missing: {sync_script}", file=sys.stderr)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Customize skills for target project stack")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Target project root (default: cwd)",
    )
    parser.add_argument("--profile", help="Stack profile id (e.g. facebook-stats, laravel)")
    parser.add_argument(
        "--auto-profile",
        action="store_true",
        help="Resolve profile from manifest stack.profile or manifest-map by_dirname",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Run sync_grok_to_github_claude.py after customization",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary")
    args = parser.parse_args()

    root = args.project_root.resolve()
    profile_id = resolve_profile(root, args.profile, args.auto_profile or not args.profile)
    if not profile_id:
        raise SystemExit(
            "Could not resolve profile. Pass --profile <id> or set stack.profile in manifest "
            "or add dirname to stack-profiles/manifest-map.yaml"
        )

    result = run_customize(root, profile_id, dry_run=args.dry_run, sync=args.sync)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        mode = "DRY-RUN" if args.dry_run else "APPLIED"
        print(f"{mode} profile={profile_id} root={root}")
        print(f"  text files changed: {len(result['files_text_changed'])}")
        print(f"  replacements: {result['total_replacements']}")
        if result["file_overrides"]:
            print(f"  overrides: {', '.join(result['file_overrides'])}")
        if result.get("synced"):
            print("  synced: .github/ + .claude/ + .copilot/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
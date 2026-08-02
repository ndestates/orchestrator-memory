"""Deploy orchestrator surfaces to a target project (engine module)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from _engine.roots import get_template_root

STATE_NAME = "deploy-state.json"
REPORT_DIR_NAME = "deploy-reports"
BACKUP_DIR_NAME = "deploy-backups"
MANIFEST_NAME = "manifest.json"

# When True, suppress per-file NEW/UPDATE/CONFLICT/SCAFFOLD chatter (agent-safe).
# Errors still go to stderr via explicit file=sys.stderr prints.
_QUIET = False


def _deploy_print(msg: str, *, force: bool = False, file=None) -> None:
    """Stdout deploy chatter; skipped when quiet unless force or stderr."""
    if file is sys.stderr or force or not _QUIET:
        print(msg, file=file if file is not None else sys.stdout, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def bundle_path() -> Path:
    return get_template_root() / "scripts" / "deploy-bundle.yaml"


def load_bundle() -> dict:
    if yaml is None:
        sys.exit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(bundle_path().read_text(encoding="utf-8"))


def resolve_selections(bundle: dict, selections_arg: str | None) -> list[str]:
    available = set(bundle.get("selections", {}).keys())
    if not available:
        # Legacy v1 bundle fallback
        return ["legacy"]

    if selections_arg is None:
        return list(bundle.get("default_selections", sorted(available)))

    raw = selections_arg.strip().lower()
    if raw == "all":
        return sorted(available)

    # Free Light / trial aliases → fixed free selection set (freemium freeze)
    if raw in ("light", "trial", "free"):
        light = "grok,chains,loops,scripts,cache-spine"
        return resolve_selections(bundle, light)

    names = [s.strip() for s in selections_arg.split(",") if s.strip()]
    # Expand light/trial tokens inside a comma list
    expanded: list[str] = []
    for n in names:
        if n in ("light", "trial", "free"):
            expanded.extend(
                resolve_selections(bundle, "grok,chains,loops,scripts,cache-spine")
            )
        else:
            expanded.append(n)
    names = list(dict.fromkeys(expanded))  # preserve order, unique
    unknown = [n for n in names if n not in available]
    if unknown:
        opts = ", ".join(sorted(available))
        sys.exit(f"Unknown selection(s): {', '.join(unknown)}. Available: {opts}, all")
    return names


def collect_paths_from_spec(spec: dict) -> list[Path]:
    paths: list[Path] = []
    for rel in spec.get("files", []):
        p = get_template_root() / rel
        if p.exists():
            paths.append(p)
    for rel in spec.get("directories", []):
        base = get_template_root() / rel
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and not _skip_hidden_segment(f, rel) and not _skip_artifact(f):
                paths.append(f)
    return paths


def _skip_artifact(path: Path) -> bool:
    """Skip build artifacts that must never ship in the bundle.

    The walk reads every file as UTF-8, so compiled bytecode under
    ``__pycache__`` would crash the deploy (UnicodeDecodeError). These are
    gitignored/untracked but still present on disk.
    """
    if path.suffix in {".pyc", ".pyo"}:
        return True
    return "__pycache__" in path.parts


def _skip_hidden_segment(path: Path, root_rel: str) -> bool:
    """Skip dotfiles except under known trees (.grok, .claude, .copilot, .github)."""
    rel = str(path.relative_to(get_template_root())).replace("\\", "/")
    parts = rel.split("/")
    if parts[0] in {".grok", ".claude", ".copilot", ".github"}:
        return False
    return any(part.startswith(".") for part in parts[1:])


def collect_source_files(bundle: dict, selections: list[str]) -> list[Path]:
    if "legacy" in selections:
        return _collect_legacy(bundle)

    paths: list[Path] = []
    for name in selections:
        spec = bundle.get("selections", {}).get(name, {})
        paths.extend(collect_paths_from_spec(spec))

    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return sorted(out, key=lambda p: str(p.relative_to(get_template_root())))


def _collect_legacy(bundle: dict) -> list[Path]:
    spec = {
        "files": bundle.get("files", []),
        "directories": bundle.get("directories", []),
    }
    paths = collect_paths_from_spec(spec)
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def rel_from_root(path: Path) -> str:
    return str(path.relative_to(get_template_root())).replace("\\", "/")


def load_state(target: Path) -> dict:
    state_path = target / ".grok" / STATE_NAME
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "source_label": "",
        "source_commit": "",
        "last_deploy": None,
        "files": {},
    }


def save_state(target: Path, state: dict) -> None:
    grok = target / ".grok"
    grok.mkdir(parents=True, exist_ok=True)
    (grok / STATE_NAME).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def git_commit_short(path: Path) -> str:
    import subprocess

    try:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _cache_spine_allowed(rel: str, bundle: dict, selections: list[str]) -> bool:
    if "cache-spine" not in selections:
        return False
    overrides = bundle.get("selection_overrides", {}).get("cache-spine", {})
    for prefix in overrides.get("allow_deploy_prefixes", ["docs/codebase/"]):
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            return True
    return False


def is_never_deploy(rel: str, bundle: dict, selections: list[str] | None = None) -> bool:
    """Return True when *rel* must not be copied from the template.

    Hard rule: every ``project-manifest.yaml`` is project-owned and is **never**
    overwritten by deploy (even with --yes / init overwrite). New projects seed
    a stack-aware manifest via ``manifest_bootstrap.ensure_project_manifest``
    after deploy, not by copying the template stock file.
    """
    # Absolute protection — cannot be bypassed by cache-spine allowlist or selections
    try:
        from _engine.manifest_bootstrap import is_protected_manifest_rel
    except ImportError:  # pragma: no cover
        from pathlib import Path as _P

        def is_protected_manifest_rel(r: str) -> bool:  # type: ignore
            return _P(r).name == "project-manifest.yaml"

    if is_protected_manifest_rel(rel):
        return True
    if selections and _cache_spine_allowed(rel, bundle, selections):
        return False
    for prefix in bundle.get("never_deploy", []):
        if rel == prefix or rel.startswith(prefix + "/"):
            return True
    return False


def is_orchestrator_only(rel: str, bundle: dict) -> bool:
    """Fleet/operator paths that must not be copied onto app project targets."""
    for prefix in bundle.get("orchestrator_only", []):
        if rel == prefix or rel.startswith(prefix + "/"):
            return True
    return False


def _require_fleet_commit_approval() -> None:
    """No-op: fleet wave is deleted. Per-app --commit-push is allowed.

    Kept as a hook so call sites do not need a mass rename; never gates on
    ORCHESTRATOR_WAVE_DEPLOY_APPROVED (that env is obsolete).
    """
    return


def collect_remap_pairs(bundle: dict, selections: list[str]) -> list[tuple[Path, str]]:
    pairs: list[tuple[Path, str]] = []
    for name in selections:
        spec = bundle.get("selections", {}).get(name, {})
        for item in spec.get("remap_files", []):
            src = get_template_root() / item["source"]
            dest = item["dest"]
            if src.exists():
                pairs.append((src, dest))
    return pairs


def is_customized(state: dict, rel: str, target_file: Path) -> bool:
    entry = state.get("files", {}).get(rel)
    if not entry:
        return False
    if entry.get("customized"):
        return True
    deployed = entry.get("deployed_sha256")
    if not deployed or not target_file.exists():
        return False
    return sha256_file(target_file) != deployed


def merge_contents(local: str, template: str, rel: str) -> str:
    return (
        f"# MERGE CONFLICT — resolve manually then remove markers\n"
        f"# File: {rel}\n\n"
        f"<<<<<<< project (local)\n{local.rstrip()}\n=======\n"
        f"{template.rstrip()}\n>>>>>>> orchestrator (template)\n"
    )


def prompt_action(rel: str, default: str) -> str:
    opts = "[o]verwrite  [s]kip  [m]erge  [d]iff"
    if default:
        print(f"  Default: {default}")
    while True:
        choice = input(f"  {opts} > ").strip().lower() or default
        if choice in {"o", "overwrite"}:
            return "overwrite"
        if choice in {"s", "skip", ""} and not default:
            return "skip"
        if choice in {"s", "skip"}:
            return "skip"
        if choice in {"m", "merge"}:
            return "merge"
        if choice in {"d", "diff"}:
            return "diff"
        print("  Invalid choice.")


def show_diff(local: str, template: str, rel: str) -> None:
    import difflib

    diff = difflib.unified_diff(
        local.splitlines(keepends=True),
        template.splitlines(keepends=True),
        fromfile=f"{rel} (project)",
        tofile=f"{rel} (template)",
    )
    sys.stdout.writelines(diff)


class BackupSession:
    """Pre-deploy snapshot for rollback."""

    def __init__(self, target: Path, *, backup_id: str, selections: list[str], source_commit: str):
        self.target = target
        self.backup_id = backup_id
        self.backup_root = target / ".grok" / BACKUP_DIR_NAME / backup_id
        self.manifest: dict = {
            "backup_id": backup_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": str(get_template_root()),
            "source_commit": source_commit,
            "selections": selections,
            "files": {},
        }
        self._seen: set[str] = set()

    def ensure(self, rel: str) -> None:
        if rel in self._seen:
            return
        self._seen.add(rel)
        tgt_file = self.target / rel
        entry: dict = {"rel": rel}
        if tgt_file.exists():
            dest = self.backup_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tgt_file, dest)
            entry["type"] = "existing"
            entry["sha256"] = sha256_file(tgt_file)
        else:
            entry["type"] = "missing"
        self.manifest["files"][rel] = entry

    def mark_created(self, rel: str) -> None:
        entry = self.manifest["files"].setdefault(rel, {"rel": rel, "type": "missing"})
        entry["created_during_deploy"] = True

    def finalize(self, state: dict) -> None:
        self.backup_root.mkdir(parents=True, exist_ok=True)
        state_path = self.target / ".grok" / STATE_NAME
        if state_path.exists():
            shutil.copy2(state_path, self.backup_root / STATE_NAME)
        (self.backup_root / MANIFEST_NAME).write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )


def list_backups(target: Path) -> list[Path]:
    root = target / ".grok" / BACKUP_DIR_NAME
    if not root.exists():
        return []
    backups = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / MANIFEST_NAME).exists():
            backups.append(d)
    return backups


def cmd_list_backups(target: Path) -> int:
    backups = list_backups(target)
    if not backups:
        print(f"No backups in {target / '.grok' / BACKUP_DIR_NAME}")
        return 0
    print(f"Backups for {target}:")
    for d in backups:
        manifest = json.loads((d / MANIFEST_NAME).read_text(encoding="utf-8"))
        n_files = len(manifest.get("files", {}))
        selections = ",".join(manifest.get("selections", []))
        print(
            f"  {manifest.get('backup_id', d.name)}  "
            f"files={n_files}  selections={selections}  "
            f"commit={manifest.get('source_commit', '?')}"
        )
    print(f"\nRollback latest: python3 scripts/deploy_grok_to_project.py {target} --rollback")
    print(f"Rollback specific: python3 scripts/deploy_grok_to_project.py {target} --rollback --backup-id <id>")
    return 0


def cmd_list_selections(bundle: dict) -> int:
    selections = bundle.get("selections", {})
    defaults = bundle.get("default_selections", [])
    print("Available selections (--selections name,name or all):")
    for name in sorted(selections):
        spec = selections[name]
        desc = spec.get("description", "")
        default = " [default]" if name in defaults else ""
        print(f"  {name}{default}: {desc}")
    return 0


def cmd_rollback(target: Path, backup_id: str | None, *, dry_run: bool) -> int:
    backups = list_backups(target)
    if not backups:
        print(f"ERROR: no backups found in {target / '.grok' / BACKUP_DIR_NAME}", file=sys.stderr)
        return 1

    if backup_id:
        backup_dir = target / ".grok" / BACKUP_DIR_NAME / backup_id
        if not (backup_dir / MANIFEST_NAME).exists():
            print(f"ERROR: backup not found: {backup_id}", file=sys.stderr)
            return 1
    else:
        backup_dir = backups[-1]
        backup_id = backup_dir.name

    manifest = json.loads((backup_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    print(f"Rollback target: {target}")
    print(f"Backup: {backup_id} ({manifest.get('timestamp', '')})")
    print(f"Selections: {','.join(manifest.get('selections', []))}")
    print("---")

    restored = 0
    removed = 0
    for rel, info in sorted(manifest.get("files", {}).items()):
        tgt = target / rel
        if info.get("created_during_deploy"):
            if tgt.exists():
                print(f"REMOVE {rel} (created during deploy)")
                if not dry_run:
                    tgt.unlink()
                removed += 1
            continue
        if info.get("type") == "existing":
            src = backup_dir / rel
            if src.exists():
                print(f"RESTORE {rel}")
                if not dry_run:
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, tgt)
                restored += 1

    state_backup = backup_dir / STATE_NAME
    if state_backup.exists():
        print(f"RESTORE {'.grok/' + STATE_NAME}")
        if not dry_run:
            save_state(target, json.loads(state_backup.read_text(encoding="utf-8")))

    print("---")
    print(f"Done: restored={restored} removed={removed}" + (" (dry-run)" if dry_run else ""))
    if not dry_run:
        print("Next: cd target && python3 scripts/sync_grok_to_github_claude.py")
    return 0


def deploy_file(
    rel: str,
    src: Path,
    target: Path,
    state: dict,
    *,
    dry_run: bool,
    default_action: str,
    interactive: bool,
    stats: dict,
    backup: BackupSession | None,
) -> None:
    tgt_file = target / rel
    src_hash = sha256_file(src)
    template_text = src.read_text(encoding="utf-8")

    def maybe_backup() -> None:
        if backup and not dry_run:
            backup.ensure(rel)

    if not tgt_file.exists():
        stats["new"] += 1
        _deploy_print(f"NEW  {rel}")
        if not dry_run:
            maybe_backup()
            tgt_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, tgt_file)
            if backup:
                backup.mark_created(rel)
            state.setdefault("files", {})[rel] = {
                "template_sha256": src_hash,
                "deployed_sha256": src_hash,
                "customized": False,
                "last_action": "new",
            }
        return

    entry = state.get("files", {}).get(rel)
    tgt_hash = sha256_file(tgt_file)
    first_seen_conflict = entry is None and tgt_hash != src_hash

    if first_seen_conflict or is_customized(state, rel, tgt_file):
        local_text = tgt_file.read_text(encoding="utf-8")
        local_hash = tgt_hash
        if local_hash == src_hash:
            stats["unchanged"] += 1
            _deploy_print(f"OK   {rel} (customized flag but matches template)")
            if not dry_run:
                state["files"][rel]["customized"] = False
                state["files"][rel]["template_sha256"] = src_hash
                state["files"][rel]["deployed_sha256"] = src_hash
            return

        stats["conflict"] += 1
        reason = "no prior deploy-state" if first_seen_conflict else "project-customized"
        _deploy_print(f"CONFLICT {rel} ({reason})")
        action = default_action
        if interactive and not dry_run:
            while True:
                action = prompt_action(rel, default_action)
                if action == "diff":
                    show_diff(local_text, template_text, rel)
                    action = prompt_action(rel, default_action)
                else:
                    break
        elif dry_run:
            action = "skip"
            _deploy_print(f"  dry-run: would prompt ({default_action} default)")

        if action == "skip":
            stats["skipped"] += 1
            if not dry_run:
                state["files"].setdefault(rel, {})["customized"] = True
            return

        if action == "merge":
            stats["merged"] += 1
            merged = merge_contents(local_text, template_text, rel)
            merge_path = tgt_file.with_suffix(tgt_file.suffix + ".merged")
            _deploy_print(f"  merge → {merge_path.relative_to(target)}")
            if not dry_run:
                maybe_backup()
                merge_path.write_text(merged, encoding="utf-8")
                state["files"][rel] = {
                    "template_sha256": src_hash,
                    "deployed_sha256": local_hash,
                    "customized": True,
                    "last_action": "merge",
                    "merge_artifact": str(merge_path.relative_to(target)),
                }
            return

        stats["overwritten"] += 1
        _deploy_print(f"  overwrite {rel}")
        if not dry_run:
            maybe_backup()
            shutil.copy2(src, tgt_file)
            state["files"][rel] = {
                "template_sha256": src_hash,
                "deployed_sha256": src_hash,
                "customized": False,
                "last_action": "overwrite",
            }
        return

    if tgt_hash == src_hash:
        stats["unchanged"] += 1
        return

    stats["updated"] += 1
    _deploy_print(f"UPDATE {rel}")
    if not dry_run:
        maybe_backup()
        shutil.copy2(src, tgt_file)
        state["files"][rel] = {
            "template_sha256": src_hash,
            "deployed_sha256": src_hash,
            "customized": False,
            "last_action": "update",
        }


def scaffold_missing(target: Path, bundle: dict, dry_run: bool) -> None:
    for rel in bundle.get("scaffold_if_missing", []):
        p = target / rel
        if p.exists():
            continue
        _deploy_print(f"SCAFFOLD {rel}")
        if not dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()


def write_report(target: Path, stats: dict, state: dict, dry_run: bool, *, backup_id: str | None, selections: list[str]) -> Path:
    report_dir = target / ".grok" / REPORT_DIR_NAME
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report_path = report_dir / f"{ts}-deploy.json"
    payload = {
        "dry_run": dry_run,
        "source": str(get_template_root()),
        "target": str(target),
        "selections": selections,
        "backup_id": backup_id,
        "stats": stats,
        "source_commit": state.get("source_commit"),
        "timestamp": ts,
    }
    if not dry_run:
        report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return report_path


def run_deploy(
    target: Path,
    *,
    dry_run: bool = False,
    selections: str | None = None,
    default_action: str = "skip",
    non_interactive: bool = True,
    yes: bool = False,
    no_backup: bool = False,
    quiet: bool = False,
) -> dict:
    """Programmatic deploy entry (Phase 3 clean-deploy flow).

    Returns a summary dict including stats, backup_id, and report_path.
    ``quiet``: suppress per-file NEW/UPDATE/CONFLICT lines (agent-safe).
    """
    global _QUIET
    target = target.resolve()
    if target == get_template_root().resolve():
        raise ValueError("target cannot be the orchestrator template source repo")

    prev_quiet = _QUIET
    _QUIET = bool(quiet)
    try:
        bundle = load_bundle()
        selected = resolve_selections(bundle, selections)
        state = load_state(target)
        state["source_label"] = bundle.get("source_label", "orchestrator")
        state["source_commit"] = git_commit_short(get_template_root())
        state["last_deploy"] = datetime.now(timezone.utc).isoformat()

        interactive = not non_interactive and not yes and sys.stdin.isatty()
        action = "overwrite" if yes else default_action

        stats = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "conflict": 0,
            "skipped": 0,
            "overwritten": 0,
            "merged": 0,
        }

        backup_id: str | None = None
        backup_session: BackupSession | None = None
        if not dry_run and not no_backup:
            backup_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            backup_session = BackupSession(
                target,
                backup_id=backup_id,
                selections=selected,
                source_commit=state["source_commit"],
            )

        for src, dest_rel in collect_remap_pairs(bundle, selected):
            if is_orchestrator_only(dest_rel, bundle):
                continue
            if is_never_deploy(dest_rel, bundle, selected):
                continue
            deploy_file(
                dest_rel,
                src,
                target,
                state,
                dry_run=dry_run,
                default_action=action,
                interactive=interactive,
                stats=stats,
                backup=backup_session,
            )

        for src in collect_source_files(bundle, selected):
            rel = rel_from_root(src)
            if is_orchestrator_only(rel, bundle):
                continue
            if is_never_deploy(rel, bundle, selected):
                continue
            deploy_file(
                rel,
                src,
                target,
                state,
                dry_run=dry_run,
                default_action=action,
                interactive=interactive,
                stats=stats,
                backup=backup_session,
            )

        scaffold_missing(target, bundle, dry_run)

        if not dry_run:
            if backup_session:
                backup_session.finalize(state)
            save_state(target, state)

        report = write_report(
            target, stats, state, dry_run, backup_id=backup_id, selections=selected
        )
        return {
            "target": str(target),
            "selections": selected,
            "stats": stats,
            "backup_id": backup_id,
            "report_path": str(report),
            "dry_run": dry_run,
            "source_commit": state.get(
                "source_commit", git_commit_short(get_template_root())
            ),
            "quiet": quiet,
        }
    finally:
        _QUIET = prev_quiet


def selection_rel_paths(bundle: dict, selections: list[str]) -> list[str]:
    rels = [rel_from_root(src) for src in collect_source_files(bundle, selections)]
    for rel in bundle.get("scaffold_if_missing", []):
        rels.append(rel)
    return sorted(set(rels))


def _is_gitignored(target: Path, rel: str) -> bool:
    return _git(target, "check-ignore", "-q", "--", rel, check=False).returncode == 0


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def commit_wave_deploy(
    target: Path,
    selections: list[str],
    *,
    source_commit: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Stage deployed bundle paths on a wave app, commit, and push to origin.

    Policy: wave deploys must not leave copied files uncommitted on the target.
    Excludes deploy-state, backups, and reports under .grok/.
    """
    target = target.resolve()
    if target == get_template_root().resolve():
        raise ValueError("cannot commit-push on orchestrator source repo")

    bundle = load_bundle()
    sha = source_commit or git_commit_short(get_template_root())
    branch = _git(target, "branch", "--show-current").stdout.strip()
    if not branch:
        raise RuntimeError(f"detached HEAD on {target} — checkout a branch before commit-push")

    rels = selection_rel_paths(bundle, selections)
    staged: list[str] = []
    for rel in rels:
        path = target / rel
        if not path.exists():
            continue
        if _is_gitignored(target, rel):
            print(f"COMMIT-SKIP (gitignored) {rel}")
            continue
        if dry_run:
            print(f"COMMIT-STAGE {rel}")
            staged.append(rel)
            continue
        add = _git(target, "add", "--", rel, check=False)
        if add.returncode != 0:
            force = _git(target, "add", "-f", "--", rel, check=False)
            if force.returncode != 0:
                print(f"COMMIT-SKIP (git add failed) {rel}", file=sys.stderr)
                continue
        staged.append(rel)

    for rel in ("STATE.md", "loop-run-log.md", "reports/loops/lessons-state.json"):
        path = target / rel
        if not path.exists() or _is_gitignored(target, rel):
            if path.exists():
                _git(target, "add", "-f", "--", rel, check=False)
                staged.append(rel)
            continue

    if dry_run:
        print(f"commit-push dry-run: would commit on {branch} ({len(staged)} path(s))")
        return {"committed": False, "pushed": False, "branch": branch, "staged": staged, "dry_run": True}

    if _git(target, "diff", "--cached", "--quiet", check=False).returncode != 0:
        guard = target / "scripts" / "git-push-secrets-guard.py"
        if guard.is_file():
            subprocess.run(["python3", str(guard), "--staged"], cwd=target, check=True)

        selection_label = ",".join(selections)
        message = (
            f"chore(orchestrator): deploy {selection_label} from ndestates/orchestrator @ {sha}\n\n"
            f"Per-app deploy on current working branch ({branch}).\n"
            "Committed deployed bundle paths only (excludes .grok deploy-state/backups)."
        )
        _git(target, "commit", "-m", message)
        print(f"COMMITTED {branch} @ {_git(target, 'rev-parse', '--short', 'HEAD').stdout.strip()}")

        push = _git(target, "push", "-u", "origin", branch, check=False)
        if push.returncode != 0:
            push = _git(target, "push", "origin", branch)
        print(f"PUSHED origin/{branch}")
        return {"committed": True, "pushed": True, "branch": branch, "staged": rels}

    print("commit-push: nothing to commit (working tree clean for selection paths)")
    return {"committed": False, "pushed": False, "branch": branch, "staged": []}


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy orchestrator .grok bundle to a target project")
    parser.add_argument("target", type=Path, nargs="?", help="Target project root (absolute path recommended)")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing")
    parser.add_argument(
        "--default-action",
        choices=["skip", "overwrite", "merge"],
        default="skip",
        help="Default for customized files when non-interactive (default: skip)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Never prompt; use --default-action (default: skip)",
    )
    parser.add_argument("--yes", action="store_true", help="Overwrite all conflicts without prompting")
    parser.add_argument(
        "--selections",
        metavar="NAMES",
        help="Comma-separated bundle selections (grok,chains,loops,scripts,claude,copilot,github) or 'all'",
    )
    parser.add_argument(
        "--list-selections",
        action="store_true",
        help="List available bundle selections and exit",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore target from latest deploy backup (or --backup-id)",
    )
    parser.add_argument(
        "--backup-id",
        metavar="ID",
        help="Specific backup timestamp for --rollback (e.g. 2026-06-17T143022Z)",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List deploy backups on target and exit",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip pre-deploy backup (not recommended)",
    )
    parser.add_argument(
        "--commit-push",
        action="store_true",
        help="After deploy, commit and push selection paths on the target (per-app)",
    )
    parser.add_argument(
        "--commit-push-only",
        action="store_true",
        help="Skip deploy; only commit and push selection paths already on the target",
    )
    args = parser.parse_args()

    bundle = load_bundle()

    if args.list_selections:
        return cmd_list_selections(bundle)

    if not args.target:
        parser.error("target is required unless using --list-selections")

    target = args.target.resolve()
    if not target.is_dir():
        print(f"ERROR: target not a directory: {target}", file=sys.stderr)
        return 1

    if args.list_backups:
        return cmd_list_backups(target)

    if args.rollback:
        if target == get_template_root().resolve():
            print("ERROR: cannot rollback the orchestrator source repo", file=sys.stderr)
            return 1
        return cmd_rollback(target, args.backup_id, dry_run=args.dry_run)

    if target == get_template_root().resolve():
        print("ERROR: target cannot be the orchestrator source repo itself", file=sys.stderr)
        return 1

    print(f"Source: {get_template_root()}")
    print(f"Target: {target}")
    selections = resolve_selections(bundle, args.selections)
    print(f"Selections: {','.join(selections)}")
    if args.commit_push_only:
        print("Mode: commit-push-only")
    else:
        print(
            f"Mode: {'dry-run' if args.dry_run else 'deploy'} | "
            f"interactive={not args.non_interactive and not args.yes and sys.stdin.isatty()}"
        )
    if args.commit_push or args.commit_push_only:
        _require_fleet_commit_approval()
        print("Commit-push: enabled (per-app)")
    print("---")

    source_commit = git_commit_short(get_template_root())
    if args.commit_push_only:
        if args.dry_run:
            commit_wave_deploy(
                target, selections, source_commit=source_commit, dry_run=True
            )
            return 0
        commit_wave_deploy(target, selections, source_commit=source_commit)
        return 0

    result = run_deploy(
        target,
        dry_run=args.dry_run,
        selections=args.selections,
        default_action=args.default_action,
        non_interactive=args.non_interactive,
        yes=args.yes,
        no_backup=args.no_backup,
    )
    stats = result["stats"]
    backup_id = result["backup_id"]
    report = Path(result["report_path"])
    source_commit = result.get("source_commit") or source_commit
    # Project-manifest: never copied above; seed/amend stack-aware file when needed
    try:
        from _engine.manifest_bootstrap import ensure_project_manifest
        from _engine import customize as _customize

        profile = _customize.resolve_profile(target, None, auto=True)
        if not profile:
            if (target / "artisan").is_file() and (target / "composer.json").is_file():
                profile = "laravel"
            elif (target / "requirements.txt").is_file() or (
                target / "pyproject.toml"
            ).is_file():
                profile = "python-flask"
        if profile:
            mres = ensure_project_manifest(
                target,
                profile_id=profile,
                mode="init",
                dry_run=args.dry_run,
            )
            print(
                f"project-manifest: {mres.get('action')} "
                f"(profile={profile}) — {mres.get('note') or 'ok'}"
            )
        else:
            print(
                "project-manifest: skipped seed (could not resolve stack profile; "
                "pass via orchestrator init --profile …)"
            )
    except Exception as exc:  # noqa: BLE001 — non-fatal for legacy deploy path
        print(f"project-manifest: ensure skipped ({exc})", file=sys.stderr)
    if backup_id and not args.dry_run:
        print(f"Backup: {target / '.grok' / BACKUP_DIR_NAME / backup_id}")
    print("---")
    print(
        f"Done: new={stats['new']} updated={stats['updated']} unchanged={stats['unchanged']} "
        f"conflicts={stats['conflict']} skipped={stats['skipped']} "
        f"overwritten={stats['overwritten']} merged={stats['merged']}"
    )
    if not args.dry_run:
        print(f"State: {target / '.grok' / STATE_NAME}")
        print(f"Report: {report}")
        if backup_id:
            print(f"Rollback: python3 scripts/deploy_grok_to_project.py {target} --rollback --backup-id {backup_id}")
        if not args.commit_push:
            print("Next: cd target && python3 scripts/sync_grok_to_github_claude.py")
            print("Next: re-run with --commit-push to commit and push on the target app")

    if args.commit_push and not args.dry_run:
        print("---")
        commit_wave_deploy(target, selections, source_commit=source_commit)
    elif args.commit_push and args.dry_run:
        print("---")
        commit_wave_deploy(target, selections, source_commit=source_commit, dry_run=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Pre-fix backup and rollback for bug-hunter fix mode.

Backups: reports/bugs/backups/<backup_id>/
Critical security fixes can be marked rollback-exempt (kept on rollback).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKUP_ROOT_NAME = "backups"
MANIFEST_NAME = "manifest.json"


def project_root(start: Path) -> Path:
    return start.resolve()


def backup_root(root: Path) -> Path:
    return root / "reports" / "bugs" / BACKUP_ROOT_NAME


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(backup_dir: Path) -> dict:
    return json.loads((backup_dir / MANIFEST_NAME).read_text(encoding="utf-8"))


def save_manifest(backup_dir: Path, manifest: dict) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


class BackupSession:
    def __init__(self, root: Path, *, backup_id: str, scope: str, mode: str):
        self.root = root
        self.backup_id = backup_id
        self.backup_dir = backup_root(root) / backup_id
        self.manifest: dict = {
            "backup_id": backup_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scope": scope,
            "mode": mode,
            "files": {},
            "rollback_exempt": [],
            "created_during_fix": [],
        }
        self._seen: set[str] = set()

    def backup_file(self, rel: str) -> None:
        if rel in self._seen:
            return
        self._seen.add(rel)
        src = self.root / rel
        entry: dict = {"rel": rel}
        if src.exists():
            dest = self.backup_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            entry["type"] = "existing"
            entry["sha256"] = sha256_file(src)
        else:
            entry["type"] = "missing"
        self.manifest["files"][rel] = entry

    def mark_created(self, rel: str) -> None:
        if rel not in self.manifest["created_during_fix"]:
            self.manifest["created_during_fix"].append(rel)
        entry = self.manifest["files"].setdefault(rel, {"rel": rel, "type": "missing"})
        entry["created_during_fix"] = True

    def mark_rollback_exempt(self, rel: str, *, finding_id: str, reason: str) -> None:
        self.manifest["rollback_exempt"].append(
            {"rel": rel, "finding_id": finding_id, "reason": reason}
        )
        entry = self.manifest["files"].get(rel, {"rel": rel})
        entry["rollback_exempt"] = True
        entry["exempt_reason"] = reason
        entry["finding_id"] = finding_id
        self.manifest["files"][rel] = entry

    def finalize(self, report_path: str | None = None) -> Path:
        if report_path:
            self.manifest["report_path"] = report_path
        save_manifest(self.backup_dir, self.manifest)
        return self.backup_dir


def list_backups(root: Path) -> list[Path]:
    br = backup_root(root)
    if not br.exists():
        return []
    out = []
    for d in sorted(br.iterdir()):
        if d.is_dir() and (d / MANIFEST_NAME).exists():
            out.append(d)
    return out


def cmd_init(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backup_id = args.backup_id or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    session = BackupSession(root, backup_id=backup_id, scope=args.scope, mode=args.mode)
    session.finalize()
    print(backup_id)
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backup_dir = backup_root(root) / args.backup_id
    if not (backup_dir / MANIFEST_NAME).exists():
        print(f"ERROR: backup session not found: {args.backup_id}", file=sys.stderr)
        return 1
    manifest = load_manifest(backup_dir)
    session = BackupSession(root, backup_id=args.backup_id, scope=manifest.get("scope", ""), mode=manifest.get("mode", "fix"))
    session.manifest = manifest
    session.backup_dir = backup_dir
    session._seen = set(manifest.get("files", {}).keys())
    for rel in args.files:
        session.backup_file(rel)
    save_manifest(backup_dir, session.manifest)
    print(f"backed up: {', '.join(args.files)}")
    return 0


def cmd_mark_exempt(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backup_dir = backup_root(root) / args.backup_id
    manifest = load_manifest(backup_dir)
    exempt = manifest.setdefault("rollback_exempt", [])
    exempt.append({"rel": args.rel, "finding_id": args.finding_id, "reason": args.reason})
    entry = manifest.setdefault("files", {}).setdefault(args.rel, {"rel": args.rel})
    entry["rollback_exempt"] = True
    entry["exempt_reason"] = args.reason
    entry["finding_id"] = args.finding_id
    save_manifest(backup_dir, manifest)
    print(f"exempt: {args.rel} ({args.finding_id})")
    return 0


def cmd_mark_created(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backup_dir = backup_root(root) / args.backup_id
    manifest = load_manifest(backup_dir)
    created = manifest.setdefault("created_during_fix", [])
    if args.rel not in created:
        created.append(args.rel)
    save_manifest(backup_dir, manifest)
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backup_dir = backup_root(root) / args.backup_id
    manifest = load_manifest(backup_dir)
    if args.report:
        manifest["report_path"] = args.report
    save_manifest(backup_dir, manifest)
    print(f"Backup ready: {backup_dir}")
    print(f"Rollback: python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id {args.backup_id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backups = list_backups(root)
    if not backups:
        print(f"No backups in {backup_root(root)}")
        return 0
    print(f"Bug-hunt backups ({root}):")
    for d in backups:
        m = load_manifest(d)
        n_exempt = len(m.get("rollback_exempt", []))
        print(
            f"  {m.get('backup_id', d.name)}  scope={m.get('scope', '?')}  "
            f"files={len(m.get('files', {}))}  exempt={n_exempt}  "
            f"mode={m.get('mode', '?')}"
        )
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    root = project_root(Path(args.root))
    backups = list_backups(root)
    if not backups:
        print("ERROR: no backups found", file=sys.stderr)
        return 1

    if args.backup_id:
        backup_dir = backup_root(root) / args.backup_id
        if not (backup_dir / MANIFEST_NAME).exists():
            print(f"ERROR: backup not found: {args.backup_id}", file=sys.stderr)
            return 1
    else:
        backup_dir = backups[-1]
        args.backup_id = backup_dir.name

    manifest = load_manifest(backup_dir)
    exempt_rels = {e["rel"] for e in manifest.get("rollback_exempt", [])}
    for _rel, info in manifest.get("files", {}).items():
        if info.get("rollback_exempt"):
            exempt_rels.add(_rel)

    restored = 0
    removed = 0
    kept = 0

    print(f"Rollback: {args.backup_id}")
    if exempt_rels:
        print(f"Keeping critical security fixes: {', '.join(sorted(exempt_rels))}")

    for rel in manifest.get("created_during_fix", []):
        if rel in exempt_rels:
            print(f"KEEP (exempt) {rel}")
            kept += 1
            continue
        tgt = root / rel
        if tgt.exists() and not args.dry_run:
            tgt.unlink()
        print(f"REMOVE {rel} (created during fix)")
        removed += 1

    for rel, info in sorted(manifest.get("files", {}).items()):
        if info.get("created_during_fix"):
            continue
        if rel in exempt_rels:
            print(f"KEEP (critical security) {rel}")
            kept += 1
            continue
        if info.get("type") == "existing":
            src = backup_dir / rel
            if src.exists():
                print(f"RESTORE {rel}")
                if not args.dry_run:
                    tgt = root / rel
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, tgt)
                restored += 1

    print(f"Done: restored={restored} removed={removed} kept_exempt={kept}" + (" (dry-run)" if args.dry_run else ""))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bug-hunter fix backup and rollback")
    parser.add_argument("--root", default=".", help="Project root")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Start backup session")
    p_init.add_argument("--scope", default="")
    p_init.add_argument("--mode", default="fix")
    p_init.add_argument("--backup-id", default=None)

    p_backup = sub.add_parser("backup", help="Backup files before patch")
    p_backup.add_argument("--backup-id", required=True)
    p_backup.add_argument("files", nargs="+")

    p_exempt = sub.add_parser("mark-exempt", help="Mark critical security fix as rollback-exempt")
    p_exempt.add_argument("--backup-id", required=True)
    p_exempt.add_argument("--finding-id", required=True)
    p_exempt.add_argument("--reason", default="critical_security_fix")
    p_exempt.add_argument("rel")

    p_created = sub.add_parser("mark-created", help="Mark file created during fix")
    p_created.add_argument("--backup-id", required=True)
    p_created.add_argument("rel")

    p_fin = sub.add_parser("finalize", help="Finalize backup manifest")
    p_fin.add_argument("--backup-id", required=True)
    p_fin.add_argument("--report", default=None)

    sub.add_parser("list", help="List backups")

    p_rb = sub.add_parser("rollback", help="Rollback fix (keeps critical security exempt)")
    p_rb.add_argument("--backup-id", default=None)
    p_rb.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    handlers = {
        "init": cmd_init,
        "backup": cmd_backup,
        "mark-exempt": cmd_mark_exempt,
        "mark-created": cmd_mark_created,
        "finalize": cmd_finalize,
        "list": cmd_list,
        "rollback": cmd_rollback,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
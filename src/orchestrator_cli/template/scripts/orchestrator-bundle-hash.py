#!/usr/bin/env python3
"""Bundle hash stamp generate/verify for orchestrator template (v1.6.1 Phase 2).

Creates a content-addressed manifest of high-risk paths so apps can verify
upgrades with ``orchestrator upgrade --verify-bundle`` (or this script).

Usage:
  python3 scripts/orchestrator-bundle-hash.py generate
  python3 scripts/orchestrator-bundle-hash.py verify
  python3 scripts/orchestrator-bundle-hash.py verify --stamp reports/security/bundle-hashes.json
  python3 scripts/orchestrator-bundle-hash.py generate --json
  python3 scripts/orchestrator-bundle-hash.py pre-commit   # hook: regen+stage if needed

Exit 0 on success; 1 on verify mismatch or missing files (unless --warn-only).
Bypass pre-commit auto-heal: ORCHESTRATOR_BUNDLE_HASH_SKIP=1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = ROOT_DEFAULT / "scripts/security/bundle-paths.txt"
DEFAULT_STAMP = ROOT_DEFAULT / "reports/security/bundle-hashes.json"
STAMP_REL = "reports/security/bundle-hashes.json"
PATHS_REL = "scripts/security/bundle-paths.txt"


def load_path_specs(paths_file: Path) -> list[str]:
    if not paths_file.is_file():
        return []
    specs: list[str] = []
    for line in paths_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        specs.append(line)
    return specs


def resolve_files(root: Path, specs: list[str]) -> list[Path]:
    files: set[Path] = set()
    for spec in specs:
        if any(ch in spec for ch in "*?[]"):
            for p in root.glob(spec):
                if p.is_file():
                    files.add(p.resolve())
        else:
            p = (root / spec).resolve()
            if p.is_file():
                files.add(p)
    return sorted(files, key=lambda p: str(p.relative_to(root)).replace("\\", "/"))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    root: Path,
    specs: list[str],
    *,
    version: str | None = None,
) -> dict[str, Any]:
    files = resolve_files(root, specs)
    entries: dict[str, str] = {}
    missing: list[str] = []
    for spec in specs:
        if any(ch in spec for ch in "*?[]"):
            continue
        if not (root / spec).is_file():
            missing.append(spec)
    for path in files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        entries[rel] = file_sha256(path)
    # Stable root of all file hashes
    material = "\n".join(f"{k}:{v}" for k, v in sorted(entries.items()))
    bundle_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
    ver = version
    if ver is None:
        vpath = root / "VERSION"
        ver = vpath.read_text(encoding="utf-8").strip() if vpath.is_file() else "0.0.0"
    return {
        "version": ver.lstrip("v"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "sha256",
        "paths_file": "scripts/security/bundle-paths.txt",
        "file_count": len(entries),
        "bundle_hash": bundle_hash,
        "files": entries,
        "missing_specs": missing,
    }


def write_stamp(manifest: dict[str, Any], stamp_path: Path) -> None:
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify(
    root: Path,
    stamp_path: Path,
    specs: list[str],
) -> tuple[bool, list[str], dict[str, Any]]:
    if not stamp_path.is_file():
        return False, [f"stamp missing: {stamp_path}"], {}
    try:
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"invalid stamp JSON: {exc}"], {}

    current = build_manifest(root, specs, version=stamp.get("version"))
    issues: list[str] = []
    stamp_files: dict[str, str] = stamp.get("files") or {}
    cur_files: dict[str, str] = current.get("files") or {}

    for rel, expected in sorted(stamp_files.items()):
        actual = cur_files.get(rel)
        if actual is None:
            issues.append(f"missing file: {rel}")
        elif actual != expected:
            issues.append(f"hash mismatch: {rel}")

    for rel in sorted(set(cur_files) - set(stamp_files)):
        # Extra files listed in paths but not in stamp — warn as issue
        issues.append(f"unexpected file not in stamp: {rel}")

    if stamp.get("bundle_hash") and stamp["bundle_hash"] != current["bundle_hash"]:
        if not any(i.startswith("hash mismatch") or i.startswith("missing") for i in issues):
            issues.append(
                f"bundle_hash mismatch: stamp={stamp['bundle_hash'][:16]}… "
                f"current={current['bundle_hash'][:16]}…"
            )

    return len(issues) == 0, issues, {"stamp": stamp, "current": current}


def _staged_files(root: Path) -> list[str]:
    """Relative paths staged for commit (ACMR only)."""
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if r.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in r.stdout.splitlines() if line.strip()]


def high_risk_relpaths(root: Path, specs: list[str]) -> set[str]:
    files = resolve_files(root, specs)
    rels = {str(p.relative_to(root)).replace("\\", "/") for p in files}
    rels.add(PATHS_REL)
    rels.add(STAMP_REL)
    # Also treat exact non-glob specs as high-risk even if missing on disk
    for spec in specs:
        if not any(ch in spec for ch in "*?[]"):
            rels.add(spec.replace("\\", "/"))
    return rels


def staged_touches_high_risk(staged: list[str], high_risk: set[str]) -> list[str]:
    hits: list[str] = []
    for rel in staged:
        if rel in high_risk:
            hits.append(rel)
            continue
        # staged under a high-risk directory prefix (future globs)
        for hr in high_risk:
            if rel.startswith(hr.rstrip("/") + "/"):
                hits.append(rel)
                break
    return hits


def run_pre_commit(
    root: Path,
    specs: list[str],
    stamp_path: Path,
    *,
    quiet: bool = False,
) -> int:
    """Regenerate + stage stamp when high-risk files are staged or stamp is stale.

    Prevents CI malware-lint / tooling-tests failures from forgotten stamp updates.
    Skip with ORCHESTRATOR_BUNDLE_HASH_SKIP=1.
    """
    if os.environ.get("ORCHESTRATOR_BUNDLE_HASH_SKIP", "").strip() in (
        "1",
        "true",
        "yes",
    ):
        if not quiet:
            print("orchestrator-bundle-hash: pre-commit skipped (ORCHESTRATOR_BUNDLE_HASH_SKIP)")
        return 0

    staged = _staged_files(root)
    if not staged:
        return 0

    high_risk = high_risk_relpaths(root, specs)
    hits = staged_touches_high_risk(staged, high_risk)
    ok, issues, _ = verify(root, stamp_path, specs)

    if not hits and ok:
        return 0

    reason = (
        f"staged high-risk: {', '.join(hits[:8])}"
        if hits
        else f"stamp stale ({len(issues)} issue(s))"
    )
    if not quiet:
        print(f"orchestrator-bundle-hash: pre-commit regenerating stamp ({reason})")

    manifest = build_manifest(root, specs)
    write_stamp(manifest, stamp_path)

    try:
        subprocess.run(
            ["git", "add", "--", STAMP_REL],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        print(f"orchestrator-bundle-hash: failed to stage {STAMP_REL}: {exc}", file=sys.stderr)
        return 1

    ok2, issues2, _ = verify(root, stamp_path, specs)
    if not ok2:
        print("orchestrator-bundle-hash: pre-commit verify still FAIL after generate:", file=sys.stderr)
        for i in issues2:
            print(f"  - {i}", file=sys.stderr)
        return 1

    if not quiet:
        print(
            f"orchestrator-bundle-hash: staged {STAMP_REL} "
            f"bundle={manifest['bundle_hash'][:16]}… v{manifest['version']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "command",
        choices=("generate", "verify", "print-hash", "pre-commit"),
    )
    ap.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    ap.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    ap.add_argument("--stamp", type=Path, default=DEFAULT_STAMP)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--warn-only", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="less noise for pre-commit")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    specs = load_path_specs(args.paths if args.paths.is_absolute() else root / args.paths)
    if not specs:
        print("orchestrator-bundle-hash: no path specs loaded", file=sys.stderr)
        return 1

    stamp_path = args.stamp if args.stamp.is_absolute() else root / args.stamp

    if args.command == "pre-commit":
        return run_pre_commit(root, specs, stamp_path, quiet=args.quiet)

    if args.command == "generate":
        manifest = build_manifest(root, specs)
        write_stamp(manifest, stamp_path)
        if args.json:
            print(json.dumps(manifest, indent=2))
        else:
            print(
                f"orchestrator-bundle-hash: wrote {stamp_path} "
                f"files={manifest['file_count']} "
                f"bundle={manifest['bundle_hash'][:16]}… "
                f"v{manifest['version']}"
            )
            if manifest.get("missing_specs"):
                print(f"  missing specs (skipped): {', '.join(manifest['missing_specs'])}")
        return 0

    if args.command == "print-hash":
        manifest = build_manifest(root, specs)
        print(manifest["bundle_hash"])
        return 0

    # verify
    ok, issues, detail = verify(root, stamp_path, specs)
    if args.json:
        print(
            json.dumps(
                {"ok": ok, "issues": issues, "bundle_hash": (detail.get("current") or {}).get("bundle_hash")},
                indent=2,
            )
        )
    else:
        print(f"orchestrator-bundle-hash: verify {'OK' if ok else 'FAIL'} issues={len(issues)}")
        for i in issues:
            print(f"  - {i}")
    if not ok and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

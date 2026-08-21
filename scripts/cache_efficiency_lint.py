#!/usr/bin/env python3
"""L1 report-only lint: cache/token anti-patterns in agent artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_READS = [
    r"docs/codebase/\.codebase-scan\.txt",
    r"Read\([^)]*\.codebase-scan",
]
WARN_PATTERNS = [
    (r"chains/registry\.yaml", "full registry read — grep chain id + offset/limit or MCP get_chain_detail"),
    (r"Glob\(\*\*", "broad glob — scope path"),
]


def scan_text(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for pat in FORBIDDEN_READS:
        if re.search(pat, text, re.I):
            issues.append(f"FORBIDDEN: lean-mode read of .codebase-scan.txt in {path}")
    for pat, msg in WARN_PATTERNS:
        if re.search(pat, text):
            issues.append(f"WARN: {msg} ({path})")
    return issues


def scan_dir(directory: Path, glob: str) -> list[str]:
    issues: list[str] = []
    if not directory.is_dir():
        return issues
    for path in directory.rglob(glob):
        try:
            issues.extend(scan_text(path, path.read_text(encoding="utf-8", errors="replace")))
        except OSError as e:
            issues.append(f"SKIP: {path}: {e}")
    return issues


def check_manifest_caps() -> list[str]:
    issues: list[str] = []
    manifest = ROOT / ".github" / "project-manifest.yaml"
    if not manifest.exists():
        return ["WARN: missing .github/project-manifest.yaml"]
    text = manifest.read_text(encoding="utf-8")
    m = re.search(r"max_cache_files_default:\s*(\d+)", text)
    if m and int(m.group(1)) > 2:
        issues.append(f"WARN: max_cache_files_default={m.group(1)} (expected ≤2 for lean)")
    return issues


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--paths", nargs="*", default=[], help="extra files to scan")
    args = p.parse_args()

    issues: list[str] = []
    issues.extend(check_manifest_caps())
    issues.extend(scan_dir(ROOT / "reports" / "chains", "*.md"))
    issues.extend(scan_dir(ROOT / "reports" / "loops", "*.md"))
    for rel in args.paths:
        path = Path(rel)
        if path.is_file():
            issues.extend(scan_text(path, path.read_text(encoding="utf-8", errors="replace")))

    payload = {"issues": issues, "count": len(issues), "status": "PASS" if not issues else "WARN"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for i in issues:
            print(i)
        print(f"\nStatus: {payload['status']} ({payload['count']} findings)")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Align chain/loop max_cache_files with manifest token_policy (lean caps)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TIER_CAPS = {"low": 2, "medium": 3, "high": 4}
DEFAULT_CAP = 4
LOOP_CAP = 2


def cap_chains_registry(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?=\n- id: )", text)
    if not blocks:
        return 0

    changed = 0
    out: list[str] = []
    for block in blocks:
        if "max_cache_files:" not in block:
            out.append(block)
            continue
        tier_m = re.search(r"token_tier:\s*(\w+)", block)
        tier = tier_m.group(1) if tier_m else "medium"
        cap = min(TIER_CAPS.get(tier, DEFAULT_CAP), DEFAULT_CAP)
        old_m = re.search(r"max_cache_files:\s*(\d+)", block)
        if not old_m:
            out.append(block)
            continue
        old = int(old_m.group(1))
        if old <= cap:
            out.append(block)
            continue
        new_block = re.sub(r"max_cache_files:\s*\d+", f"max_cache_files: {cap}", block, count=1)
        out.append(new_block)
        changed += 1
        cid = re.search(r"- id:\s*(\S+)", block)
        print(f"  chain {cid.group(1) if cid else '?'}: {old} -> {cap} ({tier})")

    new_text = "".join(out)
    if changed and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return changed


def cap_patterns_registry(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    changed = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal changed
        old = int(m.group(1))
        if old <= LOOP_CAP:
            return m.group(0)
        changed += 1
        return f"max_cache_files: {LOOP_CAP}"

    new_text = re.sub(r"max_cache_files:\s*(\d+)", repl, text)
    # Lean spine: freshness not full scan
    new_text = new_text.replace(
        "docs/codebase/.codebase-scan.txt",
        "docs/codebase/.codebase-freshness.txt",
    )
    if changed or new_text != text:
        if not dry_run:
            path.write_text(new_text, encoding="utf-8")
    return changed


def patch_pattern_md_globs(root: Path, dry_run: bool) -> int:
    n = 0
    for md in (root / "patterns").glob("*.md"):
        text = md.read_text(encoding="utf-8")
        new = text.replace("(default 3)", f"(default {LOOP_CAP})")
        new = new.replace(".codebase-scan.txt", ".codebase-freshness.txt")
        if new != text:
            n += 1
            if not dry_run:
                md.write_text(new, encoding="utf-8")
            print(f"  pattern doc {md.name}")
    return n


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    chains = ROOT / "chains" / "registry.template.yaml"
    if not chains.is_file():
        chains = ROOT / "chains" / "registry.yaml"
    patterns = ROOT / "patterns" / "registry.yaml"

    print("Chains registry:")
    c = cap_chains_registry(chains, args.dry_run)
    print(f"Patterns registry: {cap_patterns_registry(patterns, args.dry_run)} blocks capped")
    print(f"Pattern markdown: {patch_pattern_md_globs(ROOT, args.dry_run)} files")
    print(f"Summary: {c} chain entries adjusted")
    if c and not args.dry_run and (ROOT / "chains" / "registry.template.yaml").is_file():
        import subprocess

        compose = ROOT / "scripts" / "compose-registry.py"
        if compose.is_file():
            subprocess.run([sys.executable, str(compose)], cwd=ROOT, check=False)
            print("Recomposed chains/registry.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
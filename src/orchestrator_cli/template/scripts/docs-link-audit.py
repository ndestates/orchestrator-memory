#!/usr/bin/env python3
"""
Full automated link audit for the documentation site.

Usage:
  python3 scripts/docs-link-audit.py
  python3 scripts/docs-link-audit.py --report reports/docs/audit-$(date +%Y-%m-%d).md

Scans all .md files under docs/ (and docs/codebase/) for internal relative links.
Resolves them relative to the source file, handles:
- Anchors (#foo)
- Directory links (→ index.md)
- Missing .md extensions
- Paths starting with /

Reports broken links. Exits non-zero if any broken found.

Part of the self-building vault / documentation process.
Persisted after full docs site update (2026-07-07).
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Automated docs link audit")
    parser.add_argument("--report", help="Optional path to write detailed report")
    args = parser.parse_args()

    project_root = Path(".").resolve()
    docs_root = project_root / "docs"

    md_files = list(docs_root.rglob("*.md"))
    print(f"Full Automated Link Audit")
    print(f"Scanned {len(md_files)} Markdown files under docs/\n")

    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken = []
    checked = 0
    external = 0
    skipped = 0

    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="ignore")
        for match in link_re.finditer(content):
            text, dest = match.groups()
            dest = dest.strip()

            if dest.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
                external += 1
                continue
            if dest.startswith("#"):
                skipped += 1
                continue

            # Resolve relative to the .md file
            if dest.startswith("/"):
                target = (project_root / dest.lstrip("/")).resolve()
            else:
                target = (md.parent / dest).resolve()

            # Strip anchors for file existence check
            if "#" in target.name:
                target = target.with_name(target.name.split("#", 1)[0])

            # Directory or no suffix → index.md
            if target.is_dir() or (not target.suffix and target != project_root):
                target = target / "index.md"

            # Try adding .md if it looks like a doc reference
            if not target.exists() and not target.suffix:
                md_target = target.with_suffix(".md")
                if md_target.exists():
                    target = md_target

            checked += 1
            if not target.exists():
                broken.append({
                    "source": str(md.relative_to(project_root)),
                    "link": dest,
                    "resolved": str(target)
                })

    print(f"Internal links checked: {checked}")
    print(f"External links skipped: {external}")
    print(f"Anchors/other skipped: {skipped}\n")

    if broken:
        print(f"❌ {len(broken)} BROKEN LINKS FOUND:")
        for b in broken:
            print(f"  {b['source']} → {b['link']}")
            print(f"      resolved to: {b['resolved']}")
        status = 1
    else:
        print("✅ ALL internal links resolve successfully.")
        status = 0

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w") as f:
            f.write(f"# Docs Link Audit Report\n\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n")
            f.write(f"**Files scanned:** {len(md_files)}\n")
            f.write(f"**Internal links checked:** {checked}\n")
            f.write(f"**Result:** {'PASSED' if status == 0 else 'FAILED'}\n\n")
            if broken:
                f.write("## Broken Links\n\n")
                for b in broken:
                    f.write(f"- `{b['source']}` → `{b['link']}`\n")
                    f.write(f"  Resolved: `{b['resolved']}`\n\n")
            else:
                f.write("No broken links.\n")
        print(f"\nReport written to {report_path}")

    sys.exit(status)

if __name__ == "__main__":
    main()

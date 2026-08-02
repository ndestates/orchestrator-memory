#!/usr/bin/env python3
"""L1 / CI wiki health check (report-only).

Checks:
  - required scaffold files when mode is lean|full
  - parseable log prefixes
  - relative markdown links under wiki/
  - frontmatter source: paths exist
  - open questions / contradictions present

Usage:
  python3 scripts/wiki_lint_check.py
  python3 scripts/wiki_lint_check.py --json
  python3 scripts/wiki_lint_check.py --strict   # exit 1 on any warn/fail

Exit 0 when mode=off or status ok/warn (unless --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

LOG_ENTRY = re.compile(
    r"^## \[(\d{4}-\d{2}-\d{2})\] (ingest|query|lint|scaffold|file-answer) \| .+"
)
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SOURCE_FM = re.compile(r"(?m)^source:\s*(.+)$")


def _mode(root: Path) -> str:
    for rel in (".github/project-manifest.yaml", ".claude/project-manifest.yaml"):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^wiki_policy:\s*$", text)
        if not m:
            continue
        block = text[m.end() :]
        end = re.search(r"(?m)^[a-zA-Z_]", block)
        if end:
            block = block[: end.start()]
        mm = re.search(r'(?m)^\s+mode:\s*["\']?([a-z]+)["\']?', block)
        if mm:
            return mm.group(1)
    return "off"


def lint(root: Path) -> dict[str, Any]:
    mode = _mode(root)
    findings: list[dict[str, str]] = []
    wiki = root / "wiki"

    if mode == "off":
        return {"status": "skip", "mode": mode, "findings": [], "summary": "wiki off"}

    required = [
        "index.md",
        "log.md",
        "contradictions.md",
        "open-questions.md",
    ]
    if not wiki.is_dir():
        findings.append({"level": "fail", "msg": "wiki/ directory missing"})
        return {
            "status": "fail",
            "mode": mode,
            "findings": findings,
            "summary": "wiki missing",
        }

    for rel in required:
        if not (wiki / rel).is_file():
            findings.append({"level": "fail", "msg": f"missing wiki/{rel}"})

    log = wiki / "log.md"
    if log.is_file():
        entries = [
            ln
            for ln in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.startswith("## [")
        ]
        if not entries:
            findings.append({"level": "warn", "msg": "wiki/log.md has no ## [date] entries"})
        for ln in entries:
            if not LOG_ENTRY.match(ln):
                findings.append({"level": "fail", "msg": f"bad log prefix: {ln[:80]}"})

    # Relative links
    for path in wiki.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in MD_LINK.finditer(text):
            href = m.group(2).strip()
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # strip anchors
            href_path = href.split("#", 1)[0]
            if not href_path:
                continue
            target = (path.parent / href_path).resolve()
            try:
                target.relative_to(wiki.resolve())
            except ValueError:
                # allow links outside wiki (e.g. docs/) if exist under root
                target = (path.parent / href_path).resolve()
                if not target.is_file():
                    findings.append(
                        {
                            "level": "warn",
                            "msg": f"broken link in {path.relative_to(root)}: {href}",
                        }
                    )
                continue
            if not target.is_file():
                findings.append(
                    {
                        "level": "warn",
                        "msg": f"broken link in {path.relative_to(root)}: {href}",
                    }
                )

        sm = SOURCE_FM.search(text)
        if sm:
            src = sm.group(1).strip().strip("\"'")
            if src and not (root / src).is_file():
                findings.append(
                    {
                        "level": "warn",
                        "msg": f"frontmatter source missing for {path.relative_to(root)}: {src}",
                    }
                )

    fails = sum(1 for f in findings if f["level"] == "fail")
    warns = sum(1 for f in findings if f["level"] == "warn")
    if fails:
        status = "fail"
    elif warns:
        status = "warn"
    else:
        status = "ok"
    return {
        "status": status,
        "mode": mode,
        "findings": findings,
        "fail_count": fails,
        "warn_count": warns,
        "summary": f"{status}: fails={fails} warns={warns}",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args(argv)
    result = lint(args.root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"wiki_lint: {result['summary']} (mode={result['mode']})")
        for f in result.get("findings") or []:
            print(f"  [{f['level']}] {f['msg']}")
    if args.strict and result["status"] in ("fail", "warn"):
        return 1
    if result["status"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

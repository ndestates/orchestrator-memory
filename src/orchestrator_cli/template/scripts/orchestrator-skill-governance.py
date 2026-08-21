#!/usr/bin/env python3
"""Skill tool-governance lint (v1.6.1 Phase 3).

Flags skills that grant broad shell execution without an explicit governance
marker. Complements malware-lint (content patterns) with frontmatter policy.

Exit 0 clean; 1 on critical findings (unless --warn-only).

Markers accepted in SKILL.md frontmatter or body:
  tool_governance: justified
  # tool-governance: justified
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[1]

SHELL_TOOL_RE = re.compile(
    r"\b(bash|shell|run_terminal_command|run_command|terminal)\b",
    re.I,
)
JUSTIFIED_RE = re.compile(
    r"tool[_ -]?governance\s*:\s*justified|#\s*tool-governance\s*:\s*justified",
    re.I,
)
# Tight patterns — avoid matching benign phrases like "any command that touches…"
UNRESTRICTED_RE = re.compile(
    r"\b("
    r"unrestricted\s+(?:shell|access|tools?|execution)|"
    r"arbitrary\s+commands?|"
    r"run\s+any\s+command|"
    r"full\s+shell\s+access|"
    r"no\s+tool\s+restrictions?"
    r")\b",
    re.I,
)

SKILL_GLOBS = [
    ".grok/skills/**/SKILL.md",
    ".github/skills/**/SKILL.md",
    ".claude/commands/**/*.md",
]


def load_allowlist(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def scan(root: Path, allow: list[str], *, include_info: bool = False) -> list[dict]:
    """Scan skills for governance issues.

    By default only **critical** findings are collected (Phase A: avoid ~200 info
    rows per run). Pass ``include_info=True`` (CLI ``--info``) for inventory.
    """
    findings: list[dict] = []
    seen: set[Path] = set()
    for pattern in SKILL_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            if any(a in rel for a in allow):
                continue
            # Only skills that mention shell-class tools
            if not SHELL_TOOL_RE.search(text):
                continue
            if JUSTIFIED_RE.search(text):
                continue
            # Critical only when unrestricted language present without justification
            if UNRESTRICTED_RE.search(text):
                findings.append(
                    {
                        "rule": "unrestricted-shell-without-governance",
                        "severity": "critical",
                        "file": rel,
                        "description": "Shell tools + unrestricted language without tool_governance: justified",
                    }
                )
            elif include_info:
                findings.append(
                    {
                        "rule": "shell-tools-unmarked",
                        "severity": "info",
                        "file": rel,
                        "description": "Mentions shell tools; add tool_governance: justified if intentional",
                    }
                )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    ap.add_argument(
        "--allowlist",
        type=Path,
        default=ROOT_DEFAULT / "scripts/security/skill-governance-allowlist.txt",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--warn-only", action="store_true")
    ap.add_argument(
        "--info",
        action="store_true",
        help="also collect/print info-severity shell-tool inventory (off by default)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    allow = load_allowlist(args.allowlist)
    findings = scan(root, allow, include_info=args.info)
    critical = [f for f in findings if f["severity"] == "critical"]
    info = [f for f in findings if f["severity"] == "info"]

    if args.json:
        print(
            json.dumps(
                {
                    "critical": len(critical),
                    "info": len(info),
                    "include_info": args.info,
                    "findings": findings,
                },
                indent=2,
            )
        )
    else:
        print(
            f"orchestrator-skill-governance: critical={len(critical)}"
            + (f" info={len(info)}" if args.info else " (info skipped; pass --info)")
        )
        for f in critical:
            print(f"  [critical] {f['file']} — {f['description']}")
        if args.info:
            for f in info[:20]:
                print(f"  [info] {f['file']}")
            if len(info) > 20:
                print(f"  … +{len(info) - 20} more info")
        if not critical:
            print("  no critical findings")

    if critical and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

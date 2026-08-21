#!/usr/bin/env python3
"""Session-start lean wiki brief (Karpathy LLM Wiki — Phase 2).

When wiki_policy.mode is lean|full and wiki/index.md exists, print a capped
brief: mode, last log lines, open questions. Never dumps full wiki.

Usage:
  python3 scripts/session-wiki-brief.py
  python3 scripts/session-wiki-brief.py --json
  python3 scripts/session-wiki-brief.py --log-lines 5 --questions 5

Exit 0 always (status=off|missing|ok). Non-zero only on crash.
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
    r"^## \[(\d{4}-\d{2}-\d{2})\] (ingest|query|lint|scaffold|file-answer) \| (.+)$"
)
OPEN_ITEM = re.compile(r"^- \[ \] (.+)$")


def _load_wiki_policy(root: Path) -> dict[str, Any]:
    """Parse wiki_policy from manifest without requiring PyYAML."""
    for rel in (
        ".github/project-manifest.yaml",
        ".claude/project-manifest.yaml",
        ".grok/project-manifest.yaml",
    ):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "wiki_policy:" not in text:
            continue
        mode = "off"
        m = re.search(r"(?m)^wiki_policy:\s*$", text)
        if not m:
            continue
        block = text[m.end() :]
        # next top-level key starts at column 0
        end = re.search(r"(?m)^[a-zA-Z_]", block)
        if end:
            block = block[: end.start()]
        mm = re.search(r'(?m)^\s+mode:\s*["\']?([a-z]+)["\']?', block)
        if mm:
            mode = mm.group(1)
        return {"mode": mode, "path": rel}
    return {"mode": "off", "path": None}


def _tail_log(log_path: Path, n: int) -> list[str]:
    if not log_path.is_file():
        return []
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    entries = [ln for ln in lines if LOG_ENTRY.match(ln)]
    return entries[-n:] if entries else []


def _open_questions(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = OPEN_ITEM.match(ln.strip())
        if m:
            out.append(m.group(1).strip())
        if len(out) >= n:
            break
    return out


def build_brief(
    root: Path,
    *,
    log_lines: int = 5,
    questions: int = 5,
) -> dict[str, Any]:
    policy = _load_wiki_policy(root)
    mode = policy.get("mode") or "off"
    wiki = root / "wiki"
    index = wiki / "index.md"
    log = wiki / "log.md"
    oq = wiki / "open-questions.md"

    if mode == "off":
        return {
            "status": "off",
            "mode": mode,
            "message": "wiki_policy.mode=off — skip wiki brief",
        }
    if not index.is_file():
        return {
            "status": "missing",
            "mode": mode,
            "message": "wiki/index.md missing — run Phase 1 scaffold or deploy selection wiki",
        }

    log_tail = _tail_log(log, log_lines)
    open_q = _open_questions(oq, questions)
    # Index section titles only (not full body)
    headings: list[str] = []
    for ln in index.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("## "):
            headings.append(ln[3:].strip())
        if len(headings) >= 8:
            break

    return {
        "status": "ok",
        "mode": mode,
        "wiki_dir": "wiki",
        "index_sections": headings,
        "log_tail": log_tail,
        "open_questions": open_q,
        "open_question_count": len(open_q),
        "hint": "Query via /chain wiki-query; ingest via /chain wiki-ingest; lint via /chain wiki-lint",
    }


def format_human(brief: dict[str, Any]) -> str:
    status = brief.get("status")
    if status == "off":
        return f"Wiki: off · {brief.get('message', '')}"
    if status == "missing":
        return f"Wiki: missing · mode={brief.get('mode')} · {brief.get('message', '')}"
    lines = [
        f"Wiki: ok · mode={brief.get('mode')} · sections={', '.join(brief.get('index_sections') or []) or '—'}",
    ]
    for e in brief.get("log_tail") or []:
        lines.append(f"  log {e}")
    oqs = brief.get("open_questions") or []
    if oqs:
        lines.append(f"  open questions ({brief.get('open_question_count', len(oqs))}):")
        for q in oqs:
            lines.append(f"    - {q}")
    else:
        lines.append("  open questions: (none listed)")
    lines.append(f"  → {brief.get('hint', '')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--log-lines", type=int, default=5)
    p.add_argument("--questions", type=int, default=5)
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args(argv)
    brief = build_brief(
        args.root,
        log_lines=max(1, min(args.log_lines, 20)),
        questions=max(1, min(args.questions, 20)),
    )
    if args.json:
        print(json.dumps(brief, indent=2, ensure_ascii=False))
    else:
        print(format_human(brief))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

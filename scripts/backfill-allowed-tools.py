#!/usr/bin/env python3
"""Backfill allowed-tools frontmatter in .grok/skills/*/SKILL.md (least privilege)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".grok" / "skills"

# read_file + bash only — report/audit/cache loaders
READONLY = ("read_file", "bash")

# + edit_file — implementation and delivery skills
EDIT = ("read_file", "bash", "edit_file")

# + write_file — multi-file doc/skill/deploy outputs
WRITE = ("read_file", "bash", "edit_file", "write_file")

# external research without default code edits
RESEARCH = ("read_file", "bash", "web_search")

TIER_BY_NAME: dict[str, tuple[str, ...]] = {
    # already set — skip via has allowed-tools
    # readonly / L1 report
    "loop-verifier": READONLY,
    "cache-efficient": READONLY,
    "token-usage-meter": READONLY,
    "branch-context-agent": READONLY,
    "schema-audit-agent": READONLY,
    "model-schema-check": READONLY,
    "filament-panel-review": READONLY,
    "repo-maintenance-watch": READONLY,
    "security-pipeline-watch": READONLY,
    "copilot-instructions": READONLY,
    "ai-engineering-maturity": READONLY,
    "test-safety-agent": READONLY,
    "qa-agent": READONLY,
    "cyber-security-essentials": READONLY,
    "maintenance-task": READONLY,
    # research
    "research-deep-dive": RESEARCH,
    "web-build-design": (*EDIT, "web_search"),
    "frontend-web-design-expert": EDIT,
    # heavy writers
    "skill-creator": WRITE,
    "docx": WRITE,
    "acquire-codebase-knowledge": WRITE,
    "read-codebase": WRITE,
    "documentation-specialist": WRITE,
    "readme-specialist": WRITE,
    "changelog-specialist": WRITE,
    "orchestrator-deploy": WRITE,
    "template-decontaminate": WRITE,
    "loop-compound": WRITE,
    "loop-engineering": WRITE,
    "ddev-cleanup": WRITE,
    "prompt-patterns": WRITE,
    "mysql-concurrency-test": WRITE,
    "webapp-testing": WRITE,
}


def format_allowed_tools(tools: tuple[str, ...]) -> str:
    lines = ["allowed-tools:"]
    for tool in tools:
        lines.append(f"  - {tool}")
    return "\n".join(lines)


def insert_allowed_tools(content: str, tools: tuple[str, ...]) -> str:
    if re.search(r"^allowed-tools:\s*$", content, re.MULTILINE):
        return content

    block = format_allowed_tools(tools)
    # Prefer after disable-model-invocation when present
    if re.search(r"^disable-model-invocation:", content, re.MULTILINE):
        return re.sub(
            r"(^disable-model-invocation:.*\n)",
            r"\1" + block + "\n",
            content,
            count=1,
            flags=re.MULTILINE,
        )
    # Else before closing frontmatter ---
    return re.sub(r"\n---\n", "\n" + block + "\n---\n", content, count=1)


def tier_for(skill_name: str) -> tuple[str, ...]:
    if skill_name in TIER_BY_NAME:
        return TIER_BY_NAME[skill_name]
    return EDIT


def process_skill(skill_md: Path, dry_run: bool) -> str | None:
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return f"skip (no frontmatter): {skill_md}"

    if re.search(r"^allowed-tools:\s*$", content, re.MULTILINE):
        return None

    rel = skill_md.relative_to(SKILLS_DIR)
    skill_name = rel.parent.as_posix() if rel.parent != Path(".") else skill_md.parent.name
    # Nested skills (e.g. eval/maintenance-task) — match by leaf dir for tier lookup
    tier_key = skill_md.parent.name
    tools = tier_for(tier_key)
    updated = insert_allowed_tools(content, tools)

    if dry_run:
        return f"would update {skill_name}: {', '.join(tools)}"

    skill_md.write_text(updated, encoding="utf-8")
    return f"updated {skill_name}: {', '.join(tools)}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SKILLS_DIR.is_dir():
        print(f"FAIL: skills dir missing: {SKILLS_DIR}", file=sys.stderr)
        return 1

    changed: list[str] = []
    skipped = 0
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        result = process_skill(skill_md, args.dry_run)
        if result is None:
            skipped += 1
        elif result.startswith("skip"):
            print(result)
        else:
            changed.append(result)
            print(result)

    print(f"\nSummary: {len(changed)} updated, {skipped} already had allowed-tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
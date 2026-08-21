#!/usr/bin/env python3
"""
Detect project-only and locally customized skills on a deploy target.

Used by deploy-template-wave.sh — operators do not maintain per-app preserve lists.

Project-only: .grok/skills/<name>/ exists on target but not in orchestrator template.
Customized: same skill name as template but SKILL.md content differs (keep target copy).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKIP = {"copilot-instructions", "README.md"}


def skill_dirs(root: Path) -> set[str]:
    base = root / ".grok/skills"
    found: set[str] = set()
    if not base.is_dir():
        return found
    for skill in base.rglob("SKILL.md"):
        rel = skill.parent.relative_to(base)
        name = str(rel).replace("\\", "/") if str(rel) != "." else skill.parent.name
        if name not in SKIP:
            found.add(name)
    return found


def skill_md(root: Path, skill_dir: str) -> Path | None:
    p = root / ".grok/skills" / skill_dir / "SKILL.md"
    return p if p.is_file() else None


def detect(orchestrator: Path, target: Path) -> dict:
    template = skill_dirs(orchestrator)
    on_target = skill_dirs(target)

    project_only = sorted(on_target - template)
    customized: list[str] = []
    for name in sorted(on_target & template):
        t_path = skill_md(target, name)
        o_path = skill_md(orchestrator, name)
        if not t_path or not o_path:
            continue
        try:
            if t_path.read_text(encoding="utf-8") != o_path.read_text(encoding="utf-8"):
                customized.append(name)
        except OSError:
            customized.append(name)

    preserve = sorted(set(project_only) | set(customized))
    return {
        "project_only": project_only,
        "customized": customized,
        "preserve": preserve,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect skills to preserve on wave deploy")
    parser.add_argument("--orchestrator", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument(
        "--format",
        choices=("preserve", "report", "json"),
        default="preserve",
        help="preserve: space-separated names for shell; report: human lines; json: machine",
    )
    args = parser.parse_args()

    result = detect(args.orchestrator.resolve(), args.target.resolve())

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "report":
        print("  project-skill scan:")
        if result["project_only"]:
            for s in result["project_only"]:
                print(f"    project-only: {s}")
        else:
            print("    project-only: (none)")
        if result["customized"]:
            for s in result["customized"]:
                print(f"    customized (keep local): {s}")
        else:
            print("    customized: (none)")
        if not result["preserve"]:
            print("    preserve: (template sync only)")
    else:
        print(" ".join(result["preserve"]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
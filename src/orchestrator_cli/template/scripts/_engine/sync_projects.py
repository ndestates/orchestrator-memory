"""Run sync-all-projects.sh with injectable template root (script location)."""

from __future__ import annotations

import sys
from pathlib import Path

from .roots import get_template_root, set_template_root


def script_path() -> Path:
    return get_template_root() / "scripts" / "sync-all-projects.sh"


def run(
    projects_root: Path | None = None,
    *,
    report_only: bool = False,
    strict: bool = False,
    template_root: Path | None = None,
) -> int:
    """Fleet sync is deleted. Always refuse."""
    del projects_root, report_only, strict
    if template_root is not None:
        set_template_root(template_root)
    print(
        "fleet sync removed — install with: npm install -g @ndestates/orchestrator",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    return run(template_root=None) if not (argv or sys.argv[1:]) else _main_args(argv or sys.argv[1:])


def _main_args(args: list[str]) -> int:
    projects_root: Path | None = None
    report_only = False
    strict = False
    for arg in args:
        if arg == "--report-only":
            report_only = True
        elif arg == "--strict":
            strict = True
        elif not arg.startswith("-"):
            projects_root = Path(arg)
    return run(projects_root, report_only=report_only, strict=strict)


if __name__ == "__main__":
    raise SystemExit(_main_args(sys.argv[1:]))
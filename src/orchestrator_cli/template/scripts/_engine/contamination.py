"""Run scan-template-contamination.sh with injectable template root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .roots import get_template_root, set_template_root


def script_path() -> Path:
    return get_template_root() / "scripts" / "scan-template-contamination.sh"


def run(
    target: Path,
    slug: str | None = None,
    *,
    template_root: Path | None = None,
    quiet: bool = False,
) -> int:
    import os

    if template_root is not None:
        set_template_root(template_root)
    cmd = ["bash", str(script_path()), str(target)]
    if slug:
        cmd.append(slug)
    quiet = quiet or os.environ.get("ORCHESTRATOR_QUIET", "").strip() in (
        "1",
        "true",
        "yes",
    )
    if quiet:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        # One-line outcome only (full scan is agent-hostile)
        tail = (proc.stdout or "").strip().splitlines()
        if tail:
            print(tail[-1])
        if proc.returncode != 0 and proc.stderr:
            print(proc.stderr.strip()[-500:], file=sys.stderr)
        return proc.returncode
    return subprocess.run(cmd, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: contamination.py TARGET [SLUG]", file=sys.stderr)
        return 2
    target = Path(args[0])
    slug = args[1] if len(args) > 1 else None
    return run(target, slug)


if __name__ == "__main__":
    raise SystemExit(main())
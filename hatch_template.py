"""Helpers for the Hatch public-pack hook (no hatchling import)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def template_is_vcs_tracked(root: Path, dest: Path) -> bool:
    """True when the public tree already commits the staged template.

    Factory checkouts gitignore ``src/orchestrator_cli/template/`` and need
    Hatch ``force-include``. This public product tree tracks that directory, so
    force-include would add the same paths twice and fail the wheel.
    """
    marker = dest / "VERSION"
    if not marker.is_file():
        return False
    try:
        rel = str(marker.relative_to(root))
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return r.returncode == 0

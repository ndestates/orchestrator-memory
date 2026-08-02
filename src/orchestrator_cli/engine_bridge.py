"""Load scripts/_engine modules against the active template_root."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .template_root import template_root


def load_engines() -> tuple[Any, Any, Any]:
    """Return (deploy, customize, contamination) engine modules."""
    root = template_root()
    scripts = root / "scripts"
    scripts_s = str(scripts)
    if scripts_s not in sys.path:
        sys.path.insert(0, scripts_s)

    from _engine.roots import set_template_root

    set_template_root(root)

    from _engine import contamination, customize, deploy

    return deploy, customize, contamination
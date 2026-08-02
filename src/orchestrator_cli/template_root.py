"""Resolve where the template surfaces live.

Two modes:
- **Installed wheel:** surfaces are bundled at `orchestrator_cli/template/`
  (see pyproject force-include). Use that.
- **Dev checkout:** running from the source repo (editable install or straight
  `python -m`); fall back to the repo root, detected by `scripts/deploy-bundle.yaml`.

This replaces the brittle `ROOT = Path(__file__).parents[1]` assumption the
standalone scripts use, so an installed CLI with no git checkout still works.
"""

from __future__ import annotations

import os
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
_BUNDLED = _PKG_DIR / "template"


def is_bundled() -> bool:
    """True when running from an installed wheel that carries the surfaces."""
    return (_BUNDLED / "scripts" / "deploy-bundle.yaml").is_file()


def dev_repo_root() -> Path | None:
    """Find the source repo root when running from a dev checkout."""
    for parent in (_PKG_DIR, *_PKG_DIR.parents):
        if (parent / "scripts" / "deploy-bundle.yaml").is_file():
            return parent
    return None


def template_root() -> Path:
    """Directory holding the deployable surfaces (.grok, scripts, chains, ...).

    Priority:
    1. ``ORCHESTRATOR_TEMPLATE_ROOT`` (explicit override / GitHub materialize)
    2. Bundled wheel template
    3. Dev monorepo checkout
    """
    env = (os.environ.get("ORCHESTRATOR_TEMPLATE_ROOT") or "").strip()
    if env:
        root = Path(env).expanduser().resolve()
        if (root / "scripts" / "deploy-bundle.yaml").is_file():
            return root
        raise RuntimeError(
            f"ORCHESTRATOR_TEMPLATE_ROOT={root} is not a valid template root "
            "(missing scripts/deploy-bundle.yaml)"
        )
    if is_bundled():
        return _BUNDLED
    root = dev_repo_root()
    if root is not None:
        return root
    raise RuntimeError(
        "Cannot locate template surfaces: not an installed wheel and no "
        "scripts/deploy-bundle.yaml found above the package. "
        "Use --from-github or set ORCHESTRATOR_TEMPLATE_ROOT."
    )


def bundle_path() -> Path:
    return template_root() / "scripts" / "deploy-bundle.yaml"

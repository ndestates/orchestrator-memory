"""Injectable template-root engine for orchestrator deploy/customize tooling.

Phase 2: scripts import from here; thin ``scripts/*.py`` shims keep ``__main__``
defaults (``Path(__file__).resolve().parents[1]``). The CLI sets the root via
``orchestrator_cli.template_root`` before calling engine entry points.
"""

from .roots import default_main_root, get_template_root, reset_template_root, set_template_root

__all__ = [
    "default_main_root",
    "get_template_root",
    "reset_template_root",
    "set_template_root",
]
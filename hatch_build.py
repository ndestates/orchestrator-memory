"""Hatch hook: stage a residue-free template tree into the wheel/sdist.

Factory ``scripts/`` and skill specializations stay in the private checkout.
Public artifacts only receive ``public_pack.stage_wheel_template`` output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

from hatch_template import template_is_vcs_tracked

_ROOT = Path(__file__).resolve().parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        del version
        root = Path(self.root)
        dest = root / "src" / "orchestrator_cli" / "template"
        factory_marker = root / "scripts" / "deploy-bundle.yaml"
        already = (dest / "scripts" / "deploy-bundle.yaml").is_file()
        if factory_marker.is_file():
            try:
                from _engine.public_pack import stage_wheel_template
            except ImportError:
                if not already:
                    raise RuntimeError(
                        "public_pack unavailable and template is not staged at "
                        f"{dest}"
                    ) from None
            else:
                n = stage_wheel_template(root, dest)
                self.app.display_info(f"public-pack staged {n} template files")
                already = True
        if not already:
            raise RuntimeError(
                "Cannot stage public template: missing scripts/deploy-bundle.yaml "
                f"and no bundled tree at {dest}"
            )
        # Factory: staged template is gitignored — force-include so it ships.
        # Public orchestrator-memory: template is committed under packages= —
        # force-include duplicates CHAIN.md and fails the wheel.
        if template_is_vcs_tracked(root, dest):
            self.app.display_info(
                "public-pack: template is VCS-tracked; skip force-include"
            )
            return
        build_data.setdefault("force_include", {})
        if self.target_name == "wheel":
            build_data["force_include"][str(dest)] = "orchestrator_cli/template"
        else:
            build_data["force_include"][str(dest)] = "src/orchestrator_cli/template"

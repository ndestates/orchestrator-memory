#!/usr/bin/env python3
"""
Customize .grok/skills (and optional root files) for a target project.

Thin shim over ``scripts/_engine/customize.py`` — see deploy shim for rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.roots import default_main_root, set_template_root
from _engine import customize as _customize

set_template_root(default_main_root(Path(__file__)))

expand_placeholders = _customize.expand_placeholders
apply_pairs = _customize.apply_pairs
profile_context = _customize.profile_context
apply_profile_to_file = _customize.apply_profile_to_file
collect_skill_files = _customize.collect_skill_files
run_customize = _customize.run_customize
sweep_surfaces = _customize.sweep_surfaces
main = _customize.main

if __name__ == "__main__":
    raise SystemExit(_customize.main())

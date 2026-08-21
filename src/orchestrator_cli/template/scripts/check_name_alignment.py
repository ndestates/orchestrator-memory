#!/usr/bin/env python3
"""Verify prompt/agent/skill name alignment across .grok, .github, .claude."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.roots import default_main_root, set_template_root
from _engine import check_alignment as _check

set_template_root(default_main_root(Path(__file__)))

main = _check.main

if __name__ == "__main__":
    raise SystemExit(_check.main())
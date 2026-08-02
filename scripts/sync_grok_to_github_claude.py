#!/usr/bin/env python3
"""Sync .grok/ skills, prompts, and agents to .github/ and .claude/."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

# Pin app/template root BEFORE importing sync_grok — that module binds
# GROK/GITHUB/… via lazy_root() at import time. If PYTHONPATH includes a
# different orchestrator checkout, get_template_root() would otherwise
# resolve to the wrong tree and dest.relative_to(ROOT) fails.
from _engine.roots import default_main_root, set_template_root

set_template_root(default_main_root(Path(__file__)))

from _engine import sync_grok as _sync  # noqa: E402

main = _sync.main

if __name__ == "__main__":
    raise SystemExit(_sync.main())

#!/usr/bin/env python3
"""Sync .github/project-manifest.yaml to all platform copies."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.roots import default_main_root, set_template_root
from _engine import manifest_sync as _ms

set_template_root(default_main_root(Path(__file__)))

if __name__ == "__main__":
    raise SystemExit(_ms.main())
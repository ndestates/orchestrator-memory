#!/usr/bin/env python3
"""
Deploy orchestrator .grok skills, prompts, agents, and root chains to a target project.

Thin shim: implementation lives in ``scripts/_engine/deploy.py`` so the CLI can
inject ``template_root`` from an installed wheel. ``__main__`` keeps the legacy
default (repo root = parent of ``scripts/``).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.roots import default_main_root, set_template_root
from _engine import deploy as _deploy

set_template_root(default_main_root(Path(__file__)))

# Re-export for tests and callers that import this module by path.
sha256_file = _deploy.sha256_file
_skip_artifact = _deploy._skip_artifact
load_state = _deploy.load_state
save_state = _deploy.save_state
deploy_file = _deploy.deploy_file
resolve_selections = _deploy.resolve_selections
is_orchestrator_only = _deploy.is_orchestrator_only
_require_fleet_commit_approval = _deploy._require_fleet_commit_approval
load_bundle = _deploy.load_bundle
collect_paths_from_spec = _deploy.collect_paths_from_spec
run_deploy = _deploy.run_deploy
commit_wave_deploy = _deploy.commit_wave_deploy
main = _deploy.main

if __name__ == "__main__":
    raise SystemExit(_deploy.main())

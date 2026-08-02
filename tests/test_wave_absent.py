"""Phase A: fleet wave tooling must stay deleted (plan §10 / APP-INSTALLABLE plan).

Hard-delete acceptance:
- No scripts/*wave* fleet entrypoints
- No orchestrator wave CLI subcommand
- No scripts-fleet bundle selection
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Plan §10 delete list + fleet compound companions (stop-wave parity).
FORBIDDEN_REL_PATHS = (
    "scripts/backfill-wave-vault.sh",
    "scripts/commit-cache-efficiency-wave.sh",
    "scripts/commit-template-wave-skip.sh",
    "scripts/commit-template-wave.sh",
    "scripts/commit-token-meter-wave.sh",
    "scripts/deploy-cache-efficiency-wave.sh",
    "scripts/deploy-loops-starter-wave.sh",
    "scripts/deploy-mcp-wave.sh",
    "scripts/deploy-registry-wave.py",
    "scripts/deploy-session-start-wave.sh",
    "scripts/deploy-skills-customize-wave.sh",
    "scripts/deploy-template-wave-skip.sh",
    "scripts/deploy-template-wave.sh",
    "scripts/deploy-token-meter-wave.sh",
    "scripts/fix-chain-audit-wave.sh",
    "scripts/fix-node24-wave.sh",
    "scripts/resolve-wave-app-path.py",
    "scripts/wave-app-branch.sh",
    "scripts/wave-app-prepare-branch.sh",
    "scripts/wave-apps.sh",
    "scripts/wave-deploy-guard.sh",
    "scripts/wave-deploy-policy.sh",
    "scripts/wave-inventory.yaml",
    "scripts/fleet-compound-audit.sh",
    "scripts/fleet_compound_ritual.py",
    "src/orchestrator_cli/commands/wave.py",
)

# Basename patterns that must not reappear under scripts/ (allow historical docs).
FORBIDDEN_SCRIPT_GLOBS = (
    "*-wave.sh",
    "*-wave.py",
    "wave-*.sh",
    "wave-*.py",
    "wave-*.yaml",
    "wave-*.yml",
    "fleet*compound*",
)


def test_forbidden_wave_paths_absent():
    missing_ok = []
    for rel in FORBIDDEN_REL_PATHS:
        path = REPO_ROOT / rel
        assert not path.exists(), f"fleet wave path must stay deleted: {rel}"
        missing_ok.append(rel)
    assert len(missing_ok) == len(FORBIDDEN_REL_PATHS)


def test_no_wave_scripts_under_scripts_dir():
    scripts = REPO_ROOT / "scripts"
    assert scripts.is_dir()
    found: list[str] = []
    for pattern in FORBIDDEN_SCRIPT_GLOBS:
        for p in scripts.glob(pattern):
            if p.is_file():
                found.append(str(p.relative_to(REPO_ROOT)))
        for p in scripts.glob(f"**/{pattern}"):
            if p.is_file():
                rel = str(p.relative_to(REPO_ROOT))
                if rel not in found:
                    found.append(rel)
    assert found == [], f"unexpected wave/fleet scripts: {found}"


def test_orchestrator_wave_cli_removed():
    from orchestrator_cli.__main__ import build_parser, main

    parser = build_parser()
    # argparse stores subparsers on the action; "wave" must not be registered
    sub_actions = [a for a in parser._actions if getattr(a, "dest", None) == "command"]
    assert sub_actions, "expected command subparsers"
    choices = getattr(sub_actions[0], "choices", None) or {}
    assert "wave" not in choices

    with pytest.raises(SystemExit) as exc:
        main(["wave"])
    # argparse unknown subcommand → exit 2
    assert exc.value.code == 2


def test_wave_command_module_not_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("orchestrator_cli.commands.wave")


def test_deploy_bundle_has_no_scripts_fleet():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from _engine import deploy as deploy_mod

    bundle = deploy_mod.load_bundle()
    selections = bundle.get("selections", {})
    assert "scripts-fleet" not in selections
    # orchestrator_only may be empty list after Phase A
    only = bundle.get("orchestrator_only") or []
    waveish = [p for p in only if "wave" in str(p)]
    assert waveish == [], f"orchestrator_only still lists wave paths: {waveish}"


def test_resolve_selections_all_excludes_nothing_fleetish():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from _engine import deploy as deploy_mod

    bundle = {
        "selections": {"grok": {}, "chains": {}, "scripts": {}},
    }
    assert deploy_mod.resolve_selections(bundle, "all") == ["chains", "grok", "scripts"]


def test_commit_push_no_longer_requires_wave_env(monkeypatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from _engine import deploy as deploy_mod

    monkeypatch.delenv("ORCHESTRATOR_WAVE_DEPLOY_APPROVED", raising=False)
    # must not raise / exit
    deploy_mod._require_fleet_commit_approval()


def test_help_does_not_advertise_wave_subcommand(capsys):
    from orchestrator_cli.__main__ import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    # Subcommand list uses {cmd,cmd,...} — wave must not appear as a token
    tokens = out.replace("{", " ").replace("}", " ").replace(",", " ").split()
    assert "wave" not in tokens

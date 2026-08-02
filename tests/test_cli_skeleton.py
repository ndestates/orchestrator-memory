"""Phase 1 tests for the orchestrator_cli package skeleton (version + status)."""

from __future__ import annotations

import json

from orchestrator_cli import version as ver
from orchestrator_cli import lock as lockmod
from orchestrator_cli.commands import status as status_cmd
from orchestrator_cli.template_root import template_root


def test_semver_parse_and_compare():
    assert ver.is_newer("1.3.0", "1.2.0")
    assert ver.is_newer("2.0.0", "1.9.9")
    assert not ver.is_newer("1.2.0", "1.2.0")
    assert not ver.is_newer("1.1.0", "1.2.0")
    assert ver.is_newer("v1.3.0", "1.2.9")  # tolerates leading v
    # Pre-release stamps (template VERSION) must compare, not collapse to core only
    assert ver.is_newer("1.9.0-pre.5", "1.9.0-pre.3")
    assert not ver.is_newer("1.9.0-pre.3", "1.9.0-pre.5")
    assert not ver.is_newer("1.9.0-pre.5", "1.9.0-pre.5")
    assert ver.is_newer("1.9.0", "1.9.0-pre.5")  # final > pre
    assert ver.is_newer("1.9.0-pre.1", "1.8.9")


def test_template_version_reads_VERSION_file():
    v = ver.template_version()
    assert v and v[0].isdigit()
    # matches the repo VERSION
    assert (template_root() / "VERSION").read_text(encoding="utf-8").strip() == v


def test_status_uninstalled_target(target):
    info = status_cmd.collect_status(target)
    assert info["uninstalled"] is True
    assert info["installed"] is None
    assert info["available"] == ver.template_version()


def test_status_installed_and_update_detection(target):
    lockmod.write_lock(
        target, version="1.0.0", release_tag="v1.0.0", profile="laravel",
        cli_version="1.0.0", installed_at="2026-06-24T00:00:00Z",
    )
    info = status_cmd.collect_status(target)
    assert info["installed"] == "1.0.0"
    assert info["uninstalled"] is False
    # repo VERSION (1.3.0) is newer than the locked 1.0.0
    assert info["update_available"] is True


def test_status_counts_customized_files(target):
    from orchestrator_cli.version import template_version

    ver = template_version()
    lockmod.write_lock(
        target, version=ver, release_tag=f"v{ver}", profile=None,
        cli_version=ver, installed_at="2026-06-24T00:00:00Z",
    )
    grok = target / ".grok"
    grok.mkdir()
    (grok / "deploy-state.json").write_text(json.dumps({
        "files": {
            "a": {"customized": True},
            "b": {"customized": False},
            "c": {"customized": True},
        }
    }), encoding="utf-8")
    info = status_cmd.collect_status(target)
    assert info["customized_files"] == 2
    assert info["update_available"] is False


def test_cli_main_version_and_status(capsys, target):
    from orchestrator_cli.__main__ import main
    assert main(["version"]) == 0
    out = capsys.readouterr().out
    assert "orchestrator" in out

    assert main(["status", str(target), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["uninstalled"] is True

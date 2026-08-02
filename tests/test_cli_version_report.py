"""CLI version identity: VERSION SSOT; host/template/app matrix."""

from __future__ import annotations

import json
from pathlib import Path

from orchestrator_cli import version as ver
from orchestrator_cli.commands import version as version_cmd


def test_cli_version_prefers_template_in_dev_when_metadata_stale(monkeypatch):
    """Bug: orchestrator 1.9.1 (template 1.9.2, dev checkout) after VERSION bump."""
    monkeypatch.setattr(ver, "is_bundled", lambda: False)
    monkeypatch.setattr(ver, "dev_repo_root", lambda: Path("/fake/orch"))
    monkeypatch.setattr(ver, "template_version", lambda: "1.9.2")
    monkeypatch.setattr(ver, "package_metadata_version", lambda: "1.9.1")
    assert ver.cli_version() == "1.9.2"


def test_cli_version_prefers_full_version_when_bundled(monkeypatch):
    monkeypatch.setattr(ver, "is_bundled", lambda: True)
    monkeypatch.setattr(ver, "dev_repo_root", lambda: None)
    monkeypatch.setattr(ver, "template_version", lambda: "1.9.0-pre.5")
    monkeypatch.setattr(ver, "package_metadata_version", lambda: "1.9.0")
    assert ver.cli_version() == "1.9.0-pre.5"


def test_versions_equal_core_and_pre():
    assert ver.versions_equal("1.9.5", "1.9.5")
    assert ver.versions_equal("v1.9.5", "1.9.5")
    assert not ver.versions_equal("1.9.0", "1.9.0-pre.5")
    assert not ver.versions_equal("1.9.0-pre.5", "1.9.0")
    assert ver.versions_equal("1.9.5", "1.9.5", core_ok=True)


def test_is_template_source_tree(tmp_path):
    # Consumer-like
    assert ver.is_template_source_tree(tmp_path) is False
    # Fingerprint monorepo
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy-bundle.yaml").write_text("v: 1\n", encoding="utf-8")
    (tmp_path / "src" / "orchestrator_cli").mkdir(parents=True)
    assert ver.is_template_source_tree(tmp_path) is True


def test_version_report_app_behind(tmp_path, monkeypatch):
    lock = {
        "version": "1.9.1",
        "release_tag": "v1.9.1",
        "profile": "laravel",
        "cli_version": "1.9.1",
        "installed_at": "2026-07-24T00:00:00Z",
    }
    (tmp_path / ".orchestrator-version").write_text(
        json.dumps(lock) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(ver, "is_bundled", lambda: True)
    monkeypatch.setattr(ver, "dev_repo_root", lambda: None)
    monkeypatch.setattr(ver, "template_version", lambda: "1.9.5")
    monkeypatch.setattr(ver, "package_metadata_version", lambda: "1.9.5")
    monkeypatch.setattr(ver, "is_template_source_tree", lambda t=None: False)
    rep = ver.version_report(tmp_path)
    assert rep["cli"] == "1.9.5"
    assert rep["template"] == "1.9.5"
    assert rep["app_lock"] == "1.9.1"
    assert rep["app_status"] == "behind"
    assert any("upgrade" in a for a in rep["actions"])
    assert any("behind" in n for n in rep["notes"])


def test_version_command_prints_matrix(capsys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        version_cmd,
        "version_report",
        lambda target=None: {
            "cli": "1.9.5",
            "template": "1.9.5",
            "mode": "installed",
            "package_metadata": "1.9.5",
            "app_lock": "1.9.1",
            "app_cli_at_install": "1.9.1",
            "app_status": "behind",
            "host_aligned": True,
            "is_template_source": False,
            "target": str(tmp_path),
            "notes": ["app lock 1.9.1 is behind template 1.9.5"],
            "actions": ["orchestrator upgrade . --from-github v1.9.5 --yes --no-pr"],
            "aligned": False,
        },
    )
    assert version_cmd.run() == 0
    out = capsys.readouterr().out
    assert "orchestrator 1.9.5" in out
    assert "host:" in out
    assert "app:" in out
    assert "1.9.1" in out

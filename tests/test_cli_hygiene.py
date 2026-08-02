"""Host CLI hygiene after upgrade."""

from __future__ import annotations

from unittest.mock import patch

from orchestrator_cli import cli_hygiene


def test_hygiene_suppressed(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_SKIP_CLI_HYGIENE", "1")
    r = cli_hygiene.refresh_host_cli(version="1.9.3")
    assert r["skipped"] is True
    assert r["ran"] is False


def test_hygiene_editable_success(monkeypatch, tmp_path):
    monkeypatch.delenv("ORCHESTRATOR_SKIP_CLI_HYGIENE", raising=False)
    root = tmp_path / "orch"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='orchestrator'\n", encoding="utf-8")
    (root / ".git").mkdir()

    monkeypatch.setattr(cli_hygiene, "template_root", lambda: root)
    monkeypatch.setattr(cli_hygiene, "template_version", lambda: "1.9.3")
    monkeypatch.setattr(cli_hygiene, "package_metadata_version", lambda: "1.9.3")

    with patch.object(cli_hygiene, "_pip_install", return_value=(0, "ok")) as pip:
        r = cli_hygiene.refresh_host_cli(version="1.9.3")
    assert r["ok"] is True
    assert r["method"] == "pip_editable_template_root"
    pip.assert_called()
    args = pip.call_args[0][0]
    assert "-e" in args
    assert str(root) in args


def test_hygiene_pypi_fallback_when_no_pyproject(monkeypatch, tmp_path):
    monkeypatch.delenv("ORCHESTRATOR_SKIP_CLI_HYGIENE", raising=False)
    root = tmp_path / "cache-release"
    root.mkdir()
    monkeypatch.setattr(cli_hygiene, "template_root", lambda: root)
    monkeypatch.setattr(cli_hygiene, "package_metadata_version", lambda: "1.9.3")

    with patch.object(cli_hygiene, "_pip_install", return_value=(0, "ok")) as pip:
        r = cli_hygiene.refresh_host_cli(version="1.9.3")
    assert r["ok"] is True
    assert r["method"] == "pip_pypi"
    args = pip.call_args[0][0]
    assert any("orchestrator==1.9.3" in a for a in args)

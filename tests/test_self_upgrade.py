"""Host CLI self-upgrade plan + apply (mocked channels)."""

from __future__ import annotations

import json
from unittest.mock import patch

from orchestrator_cli import self_upgrade
from orchestrator_cli.__main__ import main


def test_plan_already_current(monkeypatch):
    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.9.5")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.9.5")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "local_template"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "uv_tool")
    plan = self_upgrade.plan_self_upgrade()
    assert plan["already_current"] is True
    assert plan["ok"] is True
    code, result = self_upgrade.run_self_upgrade(yes=True)
    assert code == 0
    assert result["applied"] is False


def test_plan_uv_from_path(monkeypatch, tmp_path):
    root = tmp_path / "orch"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='orchestrator'\n", encoding="utf-8")
    (root / ".git").mkdir()

    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.9.0")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.9.0")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "flag:to"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "uv_tool")
    monkeypatch.setattr(self_upgrade, "find_uv", lambda: "/usr/bin/uv")
    monkeypatch.setattr(self_upgrade, "_template_root_for_install", lambda: root)

    plan = self_upgrade.plan_self_upgrade(to_version="1.9.5", method="uv_tool")
    assert plan["needs_upgrade"] is True
    assert plan["method"] == "uv_tool_from_path"
    assert plan["commands"][0][0] == "/usr/bin/uv"
    assert "--from" in plan["commands"][0]
    assert str(root) in plan["commands"][0]


def test_plan_pip_pypi(monkeypatch, tmp_path):
    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.8.0")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.8.0")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "flag:to"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "pip")
    monkeypatch.setattr(self_upgrade, "_template_root_for_install", lambda: None)

    plan = self_upgrade.plan_self_upgrade(to_version="1.9.5", method="pip")
    assert plan["method"] == "pip_hygiene"
    flat = " ".join(plan["commands"][0])
    assert "orchestrator==1.9.5" in flat


def test_apply_uv_success(monkeypatch, tmp_path):
    root = tmp_path / "orch"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='orchestrator'\n", encoding="utf-8")

    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.9.0")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.9.5")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "flag:to"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "uv_tool")
    monkeypatch.setattr(self_upgrade, "find_uv", lambda: "/usr/bin/uv")
    monkeypatch.setattr(self_upgrade, "_template_root_for_install", lambda: root)

    with patch.object(self_upgrade, "_run", return_value=(0, "installed")) as run:
        code, result = self_upgrade.run_self_upgrade(
            to_version="1.9.5", method="uv_tool", yes=True
        )
    assert code == 0
    assert result["applied"] is True
    run.assert_called_once()


def test_dry_run_default_no_apply(monkeypatch):
    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.9.0")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.9.0")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "local_template"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "pip")
    monkeypatch.setattr(self_upgrade, "_template_root_for_install", lambda: None)

    with patch.object(self_upgrade, "apply_self_upgrade") as apply:
        code, result = self_upgrade.run_self_upgrade(yes=False)
    assert code == 0
    assert result.get("dry_run") is True
    apply.assert_not_called()


def test_cli_self_upgrade_json(capsys, monkeypatch):
    monkeypatch.setattr(self_upgrade, "cli_version", lambda: "1.9.5")
    monkeypatch.setattr(self_upgrade, "package_metadata_version", lambda: "1.9.5")
    monkeypatch.setattr(
        self_upgrade,
        "resolve_target_version",
        lambda **kw: ("1.9.5", "local_template"),
    )
    monkeypatch.setattr(self_upgrade, "detect_channel", lambda: "uv_tool")
    monkeypatch.setattr(self_upgrade, "find_uv", lambda: "/usr/bin/uv")

    assert main(["self-upgrade", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "self-upgrade"
    assert payload["already_current"] is True

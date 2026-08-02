"""Tests for local Ollama detection (host, DDEV, docker-compose)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.ollama_detect import (  # noqa: E402
    detect_api,
    detect_binary,
    evaluate,
    install_hint,
    parse_environment_manager,
    parse_local_llm,
    parse_ollama_runtime,
    resolve_ollama_host,
    resolve_ollama_target,
    runtime_signals,
)


def test_parse_local_llm_none_default():
    text = 'runtime:\n  environment_manager: "local"\n'
    assert parse_local_llm(text) == "none"


def test_parse_local_llm_ollama():
    text = (
        'runtime:\n'
        '  environment_manager: "local"\n'
        '  local_llm: "ollama"\n'
    )
    assert parse_local_llm(text) == "ollama"


def test_parse_ollama_runtime_auto_default():
    text = 'runtime:\n  environment_manager: "local"\n'
    assert parse_ollama_runtime(text) == "auto"


def test_parse_ollama_runtime_explicit_ddev():
    text = 'runtime:\n  ollama_runtime: "ddev"\n'
    assert parse_ollama_runtime(text) == "ddev"


def test_parse_environment_manager():
    text = 'runtime:\n  environment_manager: "docker-compose"\n'
    assert parse_environment_manager(text) == "docker-compose"


def test_resolve_ollama_target_auto_prefers_ddev(tmp_path):
    (tmp_path / ".ddev").mkdir()
    (tmp_path / ".ddev" / "config.yaml").write_text("name: test\n", encoding="utf-8")
    signals = runtime_signals(tmp_path)
    assert resolve_ollama_target(
        requested="auto", environment_manager="local", signals=signals
    ) == "ddev"


def test_resolve_ollama_target_auto_compose_without_ddev(tmp_path):
    (tmp_path / "docker-compose.yml").write_text("services:\n  app:\n    image: app\n", encoding="utf-8")
    signals = runtime_signals(tmp_path)
    assert resolve_ollama_target(
        requested="auto", environment_manager="local", signals=signals
    ) == "docker-compose"


def test_resolve_ollama_target_explicit_host():
    signals = {"has_ddev": True, "has_compose": True}
    assert resolve_ollama_target(
        requested="host", environment_manager="ddev", signals=signals
    ) == "host"


def test_install_hint_ddev_and_compose():
    assert "install-ollama-ddev" in install_hint("ddev", configured=False)
    assert "install-ollama-compose" in install_hint("docker-compose", configured=False)


def test_resolve_ollama_host_default():
    with patch.dict("os.environ", {}, clear=True):
        assert resolve_ollama_host() == "http://127.0.0.1:11434"


def test_detect_binary_when_missing():
    with patch("shutil.which", return_value=None):
        report = detect_binary()
    assert report["ollama_binary"] == "no"


def test_detect_api_reachable():
    payload = json.dumps({"models": [{"name": "llama3.2"}]}).encode()

    class FakeResp:
        status = 200

        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("urllib.request.urlopen", return_value=FakeResp()):
        report = detect_api(host="http://127.0.0.1:11434")
    assert report["ollama_api"] == "reachable"
    assert report["ollama_models_count"] == 1


def test_evaluate_manifest_ollama_host_not_ready(tmp_path):
    manifest = tmp_path / ".github" / "project-manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        'runtime:\n  environment_manager: "local"\n  local_llm: "ollama"\n  ollama_runtime: "host"\n',
        encoding="utf-8",
    )
    with patch("shutil.which", return_value=None):
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            report = evaluate(tmp_path)
    assert report["ollama_runtime"] == "host"
    assert report["local_llm_ready"] == "no"
    assert "install-ollama.sh" in report["ollama_note"]


def test_evaluate_manifest_ollama_ddev_not_configured(tmp_path):
    manifest = tmp_path / ".github" / "project-manifest.yaml"
    manifest.parent.mkdir(parents=True)
    (tmp_path / ".ddev").mkdir()
    (tmp_path / ".ddev" / "config.yaml").write_text("name: app\n", encoding="utf-8")
    manifest.write_text(
        'runtime:\n  environment_manager: "ddev"\n  local_llm: "ollama"\n',
        encoding="utf-8",
    )
    with patch("shutil.which", return_value="/usr/bin/ddev"):
        with patch(
            "subprocess.run",
            return_value=type("P", (), {"returncode": 1, "stdout": "", "stderr": ""})(),
        ):
            with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
                report = evaluate(tmp_path)
    assert report["ollama_runtime"] == "ddev"
    assert report["local_llm_ready"] == "no"
    assert "install-ollama-ddev" in report["ollama_note"]


def test_evaluate_compose_auto_target(tmp_path):
    manifest = tmp_path / ".github" / "project-manifest.yaml"
    manifest.parent.mkdir(parents=True)
    (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    image: web\n", encoding="utf-8")
    manifest.write_text(
        'runtime:\n  environment_manager: "docker-compose"\n  local_llm: "none"\n',
        encoding="utf-8",
    )
    with patch("shutil.which", return_value=None):
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            report = evaluate(tmp_path)
    assert report["ollama_runtime"] == "docker-compose"
    assert report["has_compose"] == "yes"


def test_evaluate_manifest_ollama_ready_host(tmp_path):
    manifest = tmp_path / ".github" / "project-manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        'runtime:\n  local_llm: "ollama"\n  ollama_runtime: "host"\n',
        encoding="utf-8",
    )
    payload = json.dumps({"models": []}).encode()

    class FakeResp:
        status = 200

        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("shutil.which", return_value="/usr/bin/ollama"):
        with patch("subprocess.run") as run:
            run.return_value.stdout = "ollama version 0.5.0\n"
            run.return_value.stderr = ""
            run.return_value.returncode = 0
            with patch("urllib.request.urlopen", return_value=FakeResp()):
                report = evaluate(tmp_path)
    assert report["local_llm_ready"] == "yes"


def test_template_manifest_has_local_llm_field():
    text = (REPO_ROOT / ".github" / "project-manifest.yaml").read_text(encoding="utf-8")
    assert parse_local_llm(text) == "none"
    assert parse_ollama_runtime(text) == "auto"
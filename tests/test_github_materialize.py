"""Tests for GitHub release materialize + template_root override."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator_cli.github_materialize import (
    MaterializedRelease,
    cache_root,
    resolve_release,
)
from orchestrator_cli.remote_version import RemoteVersion
from orchestrator_cli.template_root import template_root


def test_template_root_env_override(tmp_path: Path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy-bundle.yaml").write_text("selections: {}\n", encoding="utf-8")
    (tmp_path / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    monkeypatch.setenv("ORCHESTRATOR_TEMPLATE_ROOT", str(tmp_path))
    assert template_root() == tmp_path.resolve()


def test_template_root_env_invalid(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_TEMPLATE_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError, match="not a valid template root"):
        template_root()


def test_resolve_release_latest(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_NO_REMOTE_VERSION", raising=False)
    fake = RemoteVersion(version="1.8.5", source="github:test", tag="v1.8.5")
    with patch(
        "orchestrator_cli.github_materialize.fetch_latest_release_version",
        return_value=fake,
    ):
        r = resolve_release(None)
    assert r.version == "1.8.5"
    assert r.tag == "v1.8.5"


def test_resolve_release_explicit_tag_no_api():
    # When API fails, still returns a ref-based RemoteVersion
    with patch(
        "orchestrator_cli.github_materialize.urllib.request.urlopen",
        side_effect=TimeoutError("x"),
    ):
        r = resolve_release("v1.8.5")
    assert r.version == "1.8.5"
    assert r.tag == "v1.8.5"


def test_cache_root_respects_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ORCHESTRATOR_CACHE", str(tmp_path / "c"))
    assert cache_root() == (tmp_path / "c" / "releases").resolve()


def test_materialize_uses_cache(monkeypatch, tmp_path: Path):
    from orchestrator_cli import github_materialize as gm

    monkeypatch.setenv("ORCHESTRATOR_CACHE", str(tmp_path))
    ver_dir = tmp_path / "releases" / "1.8.5"
    ver_dir.mkdir(parents=True)
    (ver_dir / "scripts").mkdir()
    (ver_dir / "scripts" / "deploy-bundle.yaml").write_text("x: 1\n", encoding="utf-8")
    (ver_dir / "VERSION").write_text("1.8.5\n", encoding="utf-8")

    with patch.object(
        gm,
        "resolve_release",
        return_value=RemoteVersion(version="1.8.5", source="t", tag="v1.8.5"),
    ):
        mat = gm.materialize_github_release("v1.8.5")
    assert mat.path == ver_dir.resolve()
    assert mat.source.startswith("cache:")

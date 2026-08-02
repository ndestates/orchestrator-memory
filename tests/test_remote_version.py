"""Tests for GitHub remote version probe and best_available."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from orchestrator_cli.remote_version import (
    RemoteVersion,
    best_available,
    fetch_latest_release_version,
    remote_version_suppressed,
)


def test_suppressed(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_NO_REMOTE_VERSION", "1")
    assert remote_version_suppressed() is True
    assert fetch_latest_release_version() is None


def test_fetch_latest_ok(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_NO_REMOTE_VERSION", raising=False)
    payload = json.dumps({"tag_name": "v9.9.9"}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    with patch("urllib.request.urlopen", return_value=mock_resp):
        r = fetch_latest_release_version()
    assert r is not None
    assert r.version == "9.9.9"
    assert "github:" in r.source


def test_fetch_latest_failure(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_NO_REMOTE_VERSION", raising=False)
    with patch("urllib.request.urlopen", side_effect=TimeoutError("nope")):
        assert fetch_latest_release_version() is None


def test_best_available_prefers_newer_remote():
    remote = RemoteVersion(version="2.0.0", source="github:x/y")
    ver, src = best_available("1.0.0", remote)
    assert ver == "2.0.0"
    assert src.startswith("github:")


def test_best_available_keeps_local_when_newer():
    remote = RemoteVersion(version="1.0.0", source="github:x/y")
    ver, src = best_available("1.8.5", remote)
    assert ver == "1.8.5"
    assert src == "local_template"

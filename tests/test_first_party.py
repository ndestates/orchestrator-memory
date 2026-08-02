"""Tests for first-party org detection (license bypass)."""

from __future__ import annotations

import subprocess

from orchestrator_cli.first_party import _parse_org, is_first_party


def test_parse_org_ssh_and_https():
    assert _parse_org("git@github.com:ndestates/orchestrator.git") == "ndestates"
    assert _parse_org("https://github.com/acme-corp/my-app.git") == "acme-corp"
    assert _parse_org("git@github.com:Acme-Corp/repo") == "Acme-Corp"


def test_is_first_party_allowlisted(tmp_path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/ndestates/demo.git"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.delenv("ORCHESTRATOR_FIRST_PARTY_ORGS", raising=False)
    assert is_first_party(tmp_path) is True


def test_is_first_party_third_party(tmp_path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/other-org/demo.git"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.delenv("ORCHESTRATOR_FIRST_PARTY_ORGS", raising=False)
    assert is_first_party(tmp_path) is False


def test_is_first_party_custom_orgs(tmp_path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/my-org/app.git"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("ORCHESTRATOR_FIRST_PARTY_ORGS", "my-org,partner")
    assert is_first_party(tmp_path) is True
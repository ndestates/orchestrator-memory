"""Tests for scripts/workstream_guard.py — integrity safeguards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from conftest import load_script  # noqa: E402

guard = load_script("workstream_guard.py")


def _write_reg(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _run_guard(monkeypatch, reg: Path, repo: Path, *extra: str) -> tuple[int, str]:
    monkeypatch.setattr(guard, "ROOT", repo)
    monkeypatch.setattr(guard, "REGISTRY", reg)
    # avoid dirty-main noise from the real tree; run git in fake repo
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = guard.main(list(extra))
    return code, buf.getvalue()


@pytest.fixture
def bare_repo(tmp_path):
    """Minimal git repo so dirty check is clean."""
    import os
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.test",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.test"}
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "i"], cwd=repo, check=True, env=env)
    return repo


class TestProtectedHelper:
    def test_protected(self):
        assert guard._protected("main") is True
        assert guard._protected("develop") is True
        assert guard._protected("release/1.0") is True
        assert guard._protected("feature/x") is False


class TestGuardFindings:
    def test_missing_registry_fail(self, bare_repo, monkeypatch, tmp_path):
        missing = tmp_path / "nope.yaml"
        code, out = _run_guard(monkeypatch, missing, bare_repo, "--json")
        assert code == 2
        payload = json.loads(out)
        assert payload["level"] == "FAIL"
        codes = {f["code"] for f in payload["findings"]}
        assert "no_registry" in codes

    def test_primary_held_fail(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "lic",
                "workstreams": [
                    {
                        "id": "lic",
                        "status": "held_ready",
                        "branch": "feature/lic",
                        "title": "license stuff",
                    }
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        assert code == 2
        payload = json.loads(out)
        codes = {f["code"] for f in payload["findings"]}
        assert "primary_not_active" in codes

    def test_protected_branch_fail(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "a",
                "workstreams": [
                    {"id": "a", "status": "active", "branch": "develop", "title": "ok"},
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        assert code == 2
        payload = json.loads(out)
        codes = {f["code"] for f in payload["findings"]}
        assert "protected_branch" in codes

    def test_high_risk_active_warn(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "pay",
                "workstreams": [
                    {
                        "id": "pay",
                        "status": "active",
                        "branch": "feature/pay",
                        "title": "PayPal production billing",
                        "open": "live paypal",
                    }
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        # WARN or FAIL depending on dirty; high_risk is WARN
        payload = json.loads(out)
        codes = {f["code"] for f in payload["findings"]}
        assert "high_risk_active" in codes
        assert code in (0, 1)  # PASS or WARN (not FAIL from this alone)

    def test_worktree_missing_warn(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        missing_wt = tmp_path / "gone-wt"
        _write_reg(
            reg,
            {
                "primary": "a",
                "workstreams": [
                    {
                        "id": "a",
                        "status": "active",
                        "branch": "feature/a",
                        "title": "A",
                        "worktree": str(missing_wt),
                    }
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        payload = json.loads(out)
        codes = {f["code"] for f in payload["findings"]}
        assert "worktree_missing" in codes

    def test_healthy_pass(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "a",
                "workstreams": [
                    {
                        "id": "a",
                        "status": "active",
                        "branch": "feature/multi",
                        "title": "Multi stream docs",
                    },
                    {
                        "id": "b",
                        "status": "held",
                        "branch": "feature/held",
                        "title": "Held track",
                    },
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        payload = json.loads(out)
        assert payload["level"] in ("PASS", "WARN")  # dirty may warn
        codes = {f["code"] for f in payload["findings"]}
        assert "primary_not_active" not in codes
        assert "protected_branch" not in codes
        assert "no_auto_merge" in codes

    def test_primary_missing_fail(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "ghost",
                "workstreams": [
                    {"id": "a", "status": "active", "branch": "feature/a", "title": "A"},
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo, "--json")
        assert code == 2
        payload = json.loads(out)
        assert any(f["code"] == "primary_missing" for f in payload["findings"])

    def test_text_output(self, bare_repo, monkeypatch, tmp_path):
        reg = tmp_path / "ws.yaml"
        _write_reg(
            reg,
            {
                "primary": "a",
                "workstreams": [
                    {"id": "a", "status": "active", "branch": "feature/a", "title": "A"},
                ],
            },
        )
        code, out = _run_guard(monkeypatch, reg, bare_repo)
        assert "workstream_guard:" in out
        assert "safeguards:" in out

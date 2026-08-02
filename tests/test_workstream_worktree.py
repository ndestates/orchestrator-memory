"""Tests for scripts/workstream_worktree.py — git worktree isolation + safeguards.

All git operations use an isolated temp repo with monkeypatched ROOT so the
real orchestrator checkout is never modified.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from conftest import load_script  # noqa: E402

wtw = load_script("workstream_worktree.py")


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "tester", "GIT_AUTHOR_EMAIL": "t@t.test",
             "GIT_COMMITTER_NAME": "tester", "GIT_COMMITTER_EMAIL": "t@t.test"},
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.test")
    _git(repo, "config", "user.name", "tester")
    # Prefer "main" as default; create develop for base patterns
    _git(repo, "checkout", "-b", "main")
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "develop")
    # Feature branches not checked out (so worktree add can claim them)
    _git(repo, "branch", "feature/alpha-ws")
    _git(repo, "branch", "feature/beta-ws")
    _git(repo, "branch", "release/1.0")


def _registry(
    *,
    status: str = "active",
    branch: str = "feature/alpha-ws",
    worktree: str | None = None,
    wid: str = "alpha",
) -> dict:
    entry: dict = {
        "id": wid,
        "title": "Alpha",
        "status": status,
        "branch": branch,
        "next": "do work",
        "updated": "2026-07-22",
    }
    if worktree is not None:
        entry["worktree"] = worktree
    return {
        "version": 1,
        "primary": wid,
        "updated": "2026-07-22",
        "workstreams": [
            entry,
            {
                "id": "beta",
                "title": "Beta",
                "status": "held",
                "branch": "feature/beta-ws",
                "next": "wait",
                "updated": "2026-07-22",
            },
        ],
    }


def _write_reg(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def iso_repo(tmp_path, monkeypatch):
    """Isolated git repo as fake ROOT for workstream_worktree."""
    parent = tmp_path / "projects"
    parent.mkdir()
    repo = parent / "app"
    _init_repo(repo)
    monkeypatch.setattr(wtw, "ROOT", repo)
    reg = _write_reg(repo / "reports" / "sessions" / "workstreams.yaml", _registry())
    return {"repo": repo, "parent": parent, "reg": reg}


# ── pure helpers ───────────────────────────────────────────────────────────


class TestProtectedBranch:
    def test_empty_is_protected(self):
        assert wtw._is_protected_branch("") is True
        assert wtw._is_protected_branch("   ") is True

    def test_named_protected(self):
        for b in ("master", "main", "develop", "staging", "production", "prod"):
            assert wtw._is_protected_branch(b) is True

    def test_prefixes(self):
        assert wtw._is_protected_branch("release/1.9.0") is True
        assert wtw._is_protected_branch("hotfix/urgent") is True

    def test_feature_ok(self):
        assert wtw._is_protected_branch("feature/alpha-ws") is False
        assert wtw._is_protected_branch("bugfix/x") is False


class TestSlugAndDefaultPath:
    def test_slug(self):
        assert wtw._slug("Hello World!") == "hello-world"
        assert wtw._slug("a" * 100)[:48] == "a" * 48

    def test_default_path_under_parent(self, iso_repo, monkeypatch):
        repo = iso_repo["repo"]
        monkeypatch.setattr(wtw, "ROOT", repo)
        p = wtw._default_worktree_path("alpha")
        assert p.parent == repo.parent
        assert p.name == f"{repo.name}-ws-alpha"


class TestPathAllowed:
    def test_under_parent(self, iso_repo, monkeypatch):
        repo = iso_repo["repo"]
        parent = iso_repo["parent"]
        monkeypatch.setattr(wtw, "ROOT", repo)
        assert wtw._path_allowed(parent / "app-ws-alpha") is True
        assert wtw._path_allowed(repo) is True  # main itself allowed by check

    def test_outside_jail(self, iso_repo, monkeypatch, tmp_path):
        repo = iso_repo["repo"]
        monkeypatch.setattr(wtw, "ROOT", repo)
        outsider = tmp_path / "elsewhere" / "evil"
        outsider.parent.mkdir(parents=True, exist_ok=True)
        # path does not need to exist for resolve in some cases — use parent.resolve
        assert wtw._path_allowed(outsider) is False


class TestAssertSafeWs:
    def test_held_refused(self):
        with pytest.raises(SystemExit, match="refusing worktree for status=held"):
            wtw._assert_safe_ws({"id": "x", "status": "held", "branch": "feature/x"}, force=False)

    def test_parked_refused(self):
        with pytest.raises(SystemExit, match="parked"):
            wtw._assert_safe_ws({"id": "x", "status": "parked", "branch": "feature/x"}, force=False)

    def test_held_force_ok_if_feature(self):
        wtw._assert_safe_ws({"id": "x", "status": "held", "branch": "feature/x"}, force=True)

    def test_protected_branch_always_refused(self):
        with pytest.raises(SystemExit, match="protected"):
            wtw._assert_safe_ws(
                {"id": "x", "status": "active", "branch": "develop"}, force=True
            )
        with pytest.raises(SystemExit, match="protected"):
            wtw._assert_safe_ws(
                {"id": "x", "status": "active", "branch": "main"}, force=False
            )
        with pytest.raises(SystemExit, match="protected"):
            wtw._assert_safe_ws(
                {"id": "x", "status": "active", "branch": ""}, force=False
            )


# ── git worktree integration ───────────────────────────────────────────────


class TestWorktreeAddRemove:
    def test_add_list_remove_happy_path(self, iso_repo, capsys):
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))

        # Main stays on main; feature/alpha-ws free for worktree
        assert _git(repo, "branch", "--show-current").stdout.strip() == "main"

        rc = wtw.cmd_add(data, reg_path, "alpha", force=False)
        assert rc == 0, capsys.readouterr()
        out = capsys.readouterr().out
        assert "worktree added:" in out
        assert "SAFEGUARD" in out

        loaded = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        wt_path = Path(loaded["workstreams"][0]["worktree"])
        assert wt_path.is_dir()
        assert (wt_path / "README.md").is_file()
        # worktree should be on feature branch
        br = _git(wt_path, "branch", "--show-current").stdout.strip()
        assert br == "feature/alpha-ws"

        # list
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        assert wtw.cmd_list(data) == 0
        list_out = capsys.readouterr().out
        assert "alpha" in list_out
        assert "feature/alpha-ws" in list_out

        # status json
        assert wtw.cmd_status_json(data) == 0
        json_out = capsys.readouterr().out
        assert "worktrees" in json_out
        assert "registered" in json_out

        # remove
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        rc = wtw.cmd_remove(data, reg_path, "alpha", force=False)
        assert rc == 0
        assert "worktree removed" in capsys.readouterr().out
        loaded = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        assert "worktree" not in loaded["workstreams"][0]
        assert not wt_path.exists()

    def test_add_idempotent_when_exists(self, iso_repo, capsys):
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        assert wtw.cmd_add(data, reg_path, "alpha", force=False) == 0
        capsys.readouterr()
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        rc = wtw.cmd_add(data, reg_path, "alpha", force=False)
        assert rc == 0
        assert "worktree exists" in capsys.readouterr().out

    def test_add_refuses_held_without_force(self, iso_repo):
        reg_path = iso_repo["reg"]
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="status=held"):
            wtw.cmd_add(data, reg_path, "beta", force=False)

    def test_add_held_with_force(self, iso_repo, capsys):
        reg_path = iso_repo["reg"]
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        rc = wtw.cmd_add(data, reg_path, "beta", force=True)
        assert rc == 0
        assert "worktree added" in capsys.readouterr().out
        # cleanup
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        wtw.cmd_remove(data, reg_path, "beta", force=True)

    def test_add_refuses_protected_branch(self, iso_repo, tmp_path):
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        data = _registry(status="active", branch="develop", wid="prot")
        data["workstreams"] = [data["workstreams"][0]]
        data["workstreams"][0]["id"] = "prot"
        reg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="protected"):
            wtw.cmd_add(data, reg_path, "prot", force=False)

    def test_add_refuses_main_as_dest(self, iso_repo):
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        data = _registry(worktree=str(repo))
        reg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="main repo path"):
            wtw.cmd_add(data, reg_path, "alpha", force=False)

    def test_add_refuses_path_outside_jail(self, iso_repo, tmp_path):
        reg_path = iso_repo["reg"]
        outsider = tmp_path / "jailbreak" / "wt"
        data = _registry(worktree=str(outsider))
        reg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="not allowed"):
            wtw.cmd_add(data, reg_path, "alpha", force=False)

    def test_add_missing_branch(self, iso_repo):
        reg_path = iso_repo["reg"]
        data = _registry(branch="feature/does-not-exist")
        reg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="branch not found"):
            wtw.cmd_add(data, reg_path, "alpha", force=False)

    def test_remove_no_worktree_registered(self, iso_repo, capsys):
        reg_path = iso_repo["reg"]
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        rc = wtw.cmd_remove(data, reg_path, "alpha", force=False)
        assert rc == 0
        assert "no worktree registered" in capsys.readouterr().out

    def test_remove_refuses_main(self, iso_repo):
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        data = _registry(worktree=str(repo))
        reg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        with pytest.raises(SystemExit, match="refusing to remove main"):
            wtw.cmd_remove(data, reg_path, "alpha", force=False)

    def test_branch_already_checked_out_fails_clearly(self, iso_repo, capsys):
        """If main is already on the feature branch, worktree add must fail (git rule)."""
        repo = iso_repo["repo"]
        reg_path = iso_repo["reg"]
        _git(repo, "checkout", "feature/alpha-ws")
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        rc = wtw.cmd_add(data, reg_path, "alpha", force=False)
        # git worktree add returns non-zero when branch already checked out
        assert rc != 0
        err = capsys.readouterr()
        combined = (err.err or "") + (err.out or "")
        assert "already checked out" in combined.lower() or "hint:" in combined.lower()

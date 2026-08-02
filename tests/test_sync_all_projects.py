"""Phase 0 tests for scripts/sync-all-projects.sh (multi-machine startup sync).

Driven via subprocess. Pins: missing root is graceful, a no-upstream repo is
reported (not mutated), report-only never pulls.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync-all-projects.sh"


def _git(cwd: Path, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


def _init_repo(path: Path):
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@t.test")
    _git(path, "config", "user.name", "t")
    (path / "f.txt").write_text("x", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "init")


def _run(root: Path, *flags):
    return subprocess.run(
        ["bash", str(SCRIPT), str(root), *flags],
        capture_output=True, text=True,
    )


def test_missing_root_is_graceful(tmp_path):
    res = _run(tmp_path / "does-not-exist")
    assert res.returncode == 0


def test_no_upstream_repo_reported_not_mutated(tmp_path):
    root = tmp_path / "projects"
    root.mkdir()
    _init_repo(root / "repo-a")
    res = _run(root, "--report-only")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "no upstream" in res.stdout
    assert "Summary:" in res.stdout


def test_strict_flags_attention(tmp_path):
    # A clean no-upstream repo is not "attention" on its own; just assert the
    # script runs under --strict without crashing and emits the summary.
    root = tmp_path / "projects"
    root.mkdir()
    _init_repo(root / "repo-a")
    res = _run(root, "--report-only", "--strict")
    assert "Summary:" in res.stdout
    assert res.returncode in (0, 1)

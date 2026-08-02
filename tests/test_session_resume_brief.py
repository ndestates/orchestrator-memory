"""Smoke tests for scripts/session-resume-brief.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "session-resume-brief.py"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@t.test")
    _git(path, "config", "user.name", "tester")
    _git(path, "checkout", "-b", "feature/resume-brief-test")
    (path / "README.md").write_text("init\n", encoding="utf-8")
    todo = path / "TODO"
    todo.mkdir()
    (todo / "2026-07-16_TODO.md").write_text(
        "# TODO\n\n## Priority next\n\n- [ ] P0 ship feature\n- [ ] P1 write tests\n",
        encoding="utf-8",
    )
    manifest_dir = path / ".github"
    manifest_dir.mkdir()
    (manifest_dir / "project-manifest.yaml").write_text(
        'project:\n  name: "Lightstone"\nstack:\n  framework: "laravel"\n',
        encoding="utf-8",
    )
    docs = path / "docs" / "codebase"
    docs.mkdir(parents=True)
    (docs / "ARCHITECTURE.md").write_text(
        "Laravel Filament app architecture.\n", encoding="utf-8"
    )


def test_write_and_read_resume_card() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        (repo / "wip.txt").write_text("dirty\n", encoding="utf-8")

        write = _run(
            [
                "write",
                "--date",
                "2026-07-16",
                "--summary",
                "customized manifest",
                "--done",
                "fixed token meter docs",
                "--json",
            ],
            repo,
        )
        assert write.returncode == 0, write.stderr
        data = json.loads(write.stdout)
        assert data["project"] == "Lightstone"
        assert data["branch"] == "feature/resume-brief-test"
        assert data["dirty"] is True
        assert "resume-2026-07-16.md" in data["path"]
        assert "Lightstone — resume 2026-07-16" in data["card"]
        assert "P0 ship feature" in data["card"]
        assert "customized manifest" in data["card"]

        read = _run(["read", "--json"], repo)
        assert read.returncode == 0, read.stderr
        found = json.loads(read.stdout)
        assert found["status"] == "found"
        assert found["kind"] == "resume"
        assert "Start with /chain session-start" in found["card"]
        assert "remote_last" in found["card"].lower() or "Next start" in found["card"]


def test_check_resume_first_yes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        write = _run(
            ["write", "--date", "2026-07-16", "--summary", "wip", "--rich", "--json"],
            repo,
        )
        assert write.returncode == 0
        wdata = json.loads(write.stdout)
        assert wdata.get("next_start_reminder")
        assert "remote_last first" in wdata["next_start_reminder"].lower()
        assert "Next start order" in wdata.get("card", "") or "fetch" in wdata.get(
            "card", ""
        )
        check = _run(["check", "--json"], repo)
        assert check.returncode == 0, check.stderr
        data = json.loads(check.stdout)
        assert data["resume_first"] == "yes"
        assert data["max_cache_files"] == 0
        assert "todo_full_read" in data["skip"]
        assert data["card"]
        assert data.get("card_present") == "yes"
        assert data.get("surface_card") == "always"
        assert data.get("card_branch_match") in ("yes", "unknown")
        assert data.get("startup_order")


def test_check_resume_first_no_without_card() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        check = _run(["check", "--json"], repo)
        assert check.returncode == 0
        data = json.loads(check.stdout)
        assert data["resume_first"] == "no"
        assert data.get("card_present") == "no"


def test_write_rich_includes_head_and_details() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        write = _run(
            [
                "write",
                "--date",
                "2026-07-16",
                "--summary",
                "eod close",
                "--rich",
                "--source",
                "eod-shutdown",
                "--json",
            ],
            repo,
        )
        assert write.returncode == 0, write.stderr
        data = json.loads(write.stdout)
        assert data["rich"] is True
        assert data["source"] == "eod-shutdown"
        assert "HEAD:" in data["card"] or "Branch:" in data["card"]
        body = (repo / data["path"]).read_text(encoding="utf-8")
        assert "Source | eod-shutdown" in body or "eod-shutdown" in body
        assert "## Open (full)" in body


def test_read_missing_returns_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _init_repo(repo)
        read = _run(["read"], repo)
        assert read.returncode == 2


def main() -> None:
    test_write_and_read_resume_card()
    test_check_resume_first_yes()
    test_check_resume_first_no_without_card()
    test_write_rich_includes_head_and_details()
    test_read_missing_returns_2()
    print("All session-resume-brief smoke tests passed.")


if __name__ == "__main__":
    main()
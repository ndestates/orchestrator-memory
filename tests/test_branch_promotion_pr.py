"""Tests for scripts/branch-promotion-pr.sh head ref handling.

Regression: find-existing must locate same-repo open PRs (branch name only, not owner:branch).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "branch-promotion-pr.sh"


def _run_find_existing(tmp_path: Path, gh_script: str) -> str:
    gh_bin = tmp_path / "gh"
    gh_bin.write_text(gh_script, encoding="utf-8")
    gh_bin.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}"}
    res = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "find-existing",
            "ndestates/orchestrator",
            "ndestates",
            "feature/work-2026-07-08",
            "develop",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return res.stdout.strip()


def test_find_existing_uses_branch_name_for_head(tmp_path: Path) -> None:
    captured: list[str] = []

    gh_script = textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        if [[ "$1" == "pr" && "$2" == "list" ]]; then
          while [[ $# -gt 0 ]]; do
            case "$1" in
              --head) echo "HEAD=$2" >> "{tmp_path}/captured.txt" ;;
            esac
            shift
          done
          echo '[{{"url":"https://github.com/ndestates/orchestrator/pull/111"}}]'
        fi
        exit 0
        """
    )
    _run_find_existing(tmp_path, gh_script)
    captured_text = (tmp_path / "captured.txt").read_text(encoding="utf-8")
    assert "HEAD=feature/work-2026-07-08" in captured_text
    assert "HEAD=ndestates:feature/work-2026-07-08" not in captured_text


def test_find_existing_returns_url(tmp_path: Path) -> None:
    gh_script = textwrap.dedent(
        """\
        #!/usr/bin/env bash
        if [[ "$1" == "pr" && "$2" == "list" ]]; then
          for arg in "$@"; do
            if [[ "$arg" == "--jq" ]]; then
              echo "https://github.com/ndestates/orchestrator/pull/111"
              exit 0
            fi
          done
        fi
        exit 0
        """
    )
    url = _run_find_existing(tmp_path, gh_script)
    assert url == "https://github.com/ndestates/orchestrator/pull/111"


def test_find_existing_live_when_gh_available() -> None:
    """Optional local smoke test — skipped in CI when gh is unauthenticated."""
    if not shutil.which("gh"):
        return
    res = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "find-existing",
            "ndestates/orchestrator",
            "ndestates",
            "feature/work-2026-07-08",
            "develop",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return
    url = res.stdout.strip()
    # Closed/missing PRs may yield empty stdout with exit 0 — treat as skip.
    if not url:
        return
    assert "github.com" in url and "/pull/" in url
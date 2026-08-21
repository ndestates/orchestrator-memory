#!/usr/bin/env python3
"""Block commits/pushes that would expose secrets or live .env files.

Used by .githooks/pre-commit (--staged) and .githooks/pre-push (--range).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ENV_NAMES = frozenset(
    {
        ".env.example",
        ".env.production.example",
        ".env.develop",
    }
)

BLOCKED_ENV_NAMES = frozenset(
    {
        ".env",
        ".env.backup",
        ".env.production",
        ".env.testing",
        ".env.dusk",
        ".env.local",
    }
)

BINARY_SUFFIXES = frozenset(
    {
        ".gz",
        ".zip",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".mp4",
        ".mp3",
        ".sqlite",
    }
)

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("GitHub personal access token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("GitHub fine-grained token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("OpenAI API key", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    (
        "JSON password literal",
        re.compile(r'"password"\s*:\s*"(?!\$\{)[^"\s]{4,}"'),
    ),
    (
        "Private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
]

DATED_BACKUP = re.compile(r"^backup/20\d{12,}-.+\.sql\.gz$")
MAX_SCAN_BYTES = 512_000


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def env_block_reason(path: str) -> str | None:
    name = Path(path).name
    if name in ALLOWED_ENV_NAMES:
        return None
    if name in BLOCKED_ENV_NAMES:
        return "live .env file (secrets must stay local)"
    if name == ".env" or (
        name.startswith(".env.")
        and not name.endswith(".example")
        and name not in ALLOWED_ENV_NAMES
    ):
        return "unapproved .env variant (only .env.example, .env.production.example, .env.develop are allowed)"
    return None


def path_block_reason(path: str) -> str | None:
    normalized = path.replace("\\", "/")

    env_reason = env_block_reason(normalized)
    if env_reason:
        return env_reason

    if DATED_BACKUP.match(normalized):
        return (
            "dated database backup export (contains live credentials; "
            "commit only backup/latest-*.sql.gz symlinks/archives)"
        )

    if normalized.startswith("reports/flare-incidents/") and normalized.endswith(".log"):
        return "flare incident log (may contain generated 2FA secrets or tokens)"

    if normalized.startswith("reports/vault/") and normalized.endswith(".jsonl"):
        # Vault events are scrubbed at write time by secure vault lib, but guard as defense-in-depth.
        # Any unredacted secret here is a serious policy violation.
        pass

    return None


def files_from_range(commit_range: str) -> list[str]:
    output = run_git("diff", "--name-only", "--diff-filter=ACMR", commit_range)
    return [line.strip() for line in output.splitlines() if line.strip()]


def files_from_staged() -> list[str]:
    output = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [line.strip() for line in output.splitlines() if line.strip()]


def scan_file_content(path: str) -> list[str]:
    full = ROOT / path
    if not full.is_file():
        return []

    if full.suffix.lower() in BINARY_SUFFIXES:
        return []

    try:
        if full.stat().st_size > MAX_SCAN_BYTES:
            return []
    except OSError:
        return []

    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    hits: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(label)
    return hits


def check_files(paths: list[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for path in paths:
        if path in seen:
            continue
        seen.add(path)

        reason = path_block_reason(path)
        if reason:
            errors.append(f"{path}: {reason}")
            continue

        for hit in scan_file_content(path):
            errors.append(f"{path}: possible secret ({hit})")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--staged",
        action="store_true",
        help="Scan files staged for commit (pre-commit).",
    )
    group.add_argument(
        "--range",
        metavar="REV_RANGE",
        help="Scan files changed in REV_RANGE (pre-push), e.g. origin/main..HEAD.",
    )
    group.add_argument(
        "--files",
        nargs="+",
        metavar="PATH",
        help="Scan explicit file paths (manual/CI check).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.staged:
            paths = files_from_staged()
        elif args.range:
            paths = files_from_range(args.range)
        else:
            paths = list(args.files)
    except RuntimeError as exc:
        print(f"git-push-secrets-guard: {exc}", file=sys.stderr)
        return 1

    if not paths:
        print("OK: no files to scan for secrets/env violations.")
        return 0

    errors = check_files(paths)
    if errors:
        print("BLOCKED: push/commit would expose secrets or forbidden env files:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            "\nRemediate: git reset/unstage offending paths, rotate any exposed secrets, "
            "and re-run. Emergency bypass (audited): GIT_PUSH_SECRETS_BYPASS=1 git push",
            file=sys.stderr,
        )
        return 1

    print(f"OK: scanned {len(paths)} file(s); no secrets or blocked env paths detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
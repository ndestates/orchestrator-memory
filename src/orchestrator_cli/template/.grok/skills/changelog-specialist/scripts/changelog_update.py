#!/usr/bin/env python3
"""Incremental changelog: session log, CHANGELOG.md [Unreleased], PR body."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = (
    "added",
    "changed",
    "fixed",
    "removed",
    "security",
    "tests",
    "infrastructure",
)

CATEGORY_HEADINGS = {c: c.capitalize() for c in CATEGORIES}
CATEGORY_HEADINGS["tests"] = "Tests"
CATEGORY_HEADINGS["infrastructure"] = "Infrastructure"


def project_root() -> Path:
    env = Path.cwd()
    for candidate in (env, *env.parents):
        if (candidate / "CHANGELOG.md").is_file():
            return candidate
    return env


def run_git(args: list[str], root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            return ""
        return (proc.stdout or "").strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def current_branch(root: Path) -> str:
    return run_git(["branch", "--show-current"], root) or "unknown"


def reports_dir(root: Path) -> Path:
    path = root / "reports" / "changelog"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_path(root: Path) -> Path:
    return reports_dir(root) / "state.json"


def session_path(root: Path, date: str) -> Path:
    return reports_dir(root) / f"session-{date}.md"


def load_state(root: Path) -> dict:
    path = state_path(root)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(root: Path, state: dict) -> None:
    state_path(root).write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_summary(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def ensure_changelog(root: Path) -> Path:
    path = root / "CHANGELOG.md"
    if path.is_file():
        return path
    body = (
        "# Changelog\n\n"
        "All notable changes to this project are documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
        "## [Unreleased]\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def parse_unreleased_sections(text: str) -> dict[str, list[str]]:
    match = re.search(r"^## \[Unreleased\]\s*$", text, re.MULTILINE)
    if not match:
        return {}
    rest = text[match.end() :]
    next_version = re.search(r"^## \[[^\]]+\]", rest, re.MULTILINE)
    block = rest[: next_version.start()] if next_version else rest
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        heading = re.match(r"^### (Added|Changed|Fixed|Removed|Security|Tests|Infrastructure)\s*$", line)
        if heading:
            current = heading.group(1).lower()
            sections.setdefault(current, [])
            continue
        if current and line.startswith("- "):
            sections[current].append(line[2:].strip())
    return sections


def unreleased_counts(root: Path) -> dict[str, int]:
    text = ensure_changelog(root).read_text(encoding="utf-8")
    sections = parse_unreleased_sections(text)
    return {k: len(v) for k, v in sections.items()}


def write_session_header(path: Path, date: str, branch: str, started_at: str) -> None:
    if path.is_file():
        return
    path.write_text(
        f"# Session changelog — {date}\n\n"
        f"**Branch:** `{branch}`  \n"
        f"**Started:** {started_at}\n\n"
        "## Entries\n\n",
        encoding="utf-8",
    )


def append_session_markdown(
    path: Path,
    ts: str,
    category: str,
    summary: str,
    commits: list[str],
    files: list[str],
) -> None:
    time_short = ts.split("T")[-1].replace("Z", "")[:5] if "T" in ts else ts[:5]
    block = f"### {time_short} — {CATEGORY_HEADINGS[category]}\n\n- {summary}\n"
    if commits:
        block += f"  - commits: {', '.join(commits)}\n"
    if files:
        block += f"  - files: {', '.join(files)}\n"
    block += "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(block)


def cmd_init(root: Path, date: str | None, branch: str | None) -> int:
    date = date or datetime.now().strftime("%Y-%m-%d")
    branch = branch or current_branch(root)
    started_at = now_iso()
    session = session_path(root, date)
    write_session_header(session, date, branch, started_at)

    state = load_state(root)
    if state.get("session_date") != date or not state.get("entries"):
        state = {
            "session_date": date,
            "branch": branch,
            "started_at": started_at,
            "session_file": str(session.relative_to(root)),
            "entries": [],
            "consolidated": False,
        }
        save_state(root, state)

    counts = unreleased_counts(root)
    total = sum(counts.values())
    payload = {
        "status": "ready",
        "session_date": date,
        "branch": branch,
        "session_file": str(session.relative_to(root)),
        "unreleased_total": total,
        "unreleased_by_category": counts,
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_append(
    root: Path,
    category: str,
    summary: str,
    commits: list[str],
    files: list[str],
    date: str | None,
) -> int:
    category = category.lower()
    if category not in CATEGORIES:
        print(f"error: invalid category {category}", file=sys.stderr)
        return 1
    summary = summary.strip()
    if not summary:
        print("error: --summary required", file=sys.stderr)
        return 1

    date = date or datetime.now().strftime("%Y-%m-%d")
    branch = current_branch(root)
    ts = now_iso()
    session = session_path(root, date)
    write_session_header(session, date, branch, ts)

    state = load_state(root)
    if state.get("session_date") != date:
        state = {
            "session_date": date,
            "branch": branch,
            "started_at": ts,
            "session_file": str(session.relative_to(root)),
            "entries": [],
            "consolidated": False,
        }

    entry = {
        "ts": ts,
        "category": category,
        "summary": summary,
        "commits": commits,
        "files": files,
    }
    state.setdefault("entries", []).append(entry)
    state["branch"] = branch
    state["consolidated"] = False
    save_state(root, state)
    append_session_markdown(session, ts, category, summary, commits, files)

    print(
        json.dumps(
            {
                "status": "appended",
                "category": category,
                "summary": summary,
                "session_entries": len(state["entries"]),
            },
            indent=2,
        )
    )
    return 0


def cmd_status(root: Path, as_json: bool) -> int:
    state = load_state(root)
    counts = unreleased_counts(root)
    payload = {
        "session_date": state.get("session_date"),
        "branch": state.get("branch") or current_branch(root),
        "session_entries": len(state.get("entries", [])),
        "consolidated": state.get("consolidated", False),
        "unreleased_by_category": counts,
        "unreleased_total": sum(counts.values()),
    }
    if as_json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Branch: {payload['branch']}")
    print(f"Session: {payload['session_date']} ({payload['session_entries']} entries)")
    print(f"Unreleased in CHANGELOG.md: {payload['unreleased_total']}")
    for cat, n in counts.items():
        if n:
            print(f"  {CATEGORY_HEADINGS[cat]}: {n}")
    return 0


def insert_into_unreleased(changelog_text: str, category: str, bullet: str) -> str:
    heading = f"### {CATEGORY_HEADINGS[category]}"
    norm_bullet = normalize_summary(bullet)
    sections = parse_unreleased_sections(changelog_text)
    existing = {normalize_summary(x) for x in sections.get(category, [])}
    if norm_bullet in existing:
        return changelog_text

    match = re.search(r"^## \[Unreleased\]\s*$", changelog_text, re.MULTILINE)
    if not match:
        changelog_text = changelog_text.rstrip() + "\n\n## [Unreleased]\n"
        match = re.search(r"^## \[Unreleased\]\s*$", changelog_text, re.MULTILINE)
    assert match is not None

    rest = changelog_text[match.end() :]
    next_version = re.search(r"^## \[[^\]]+\]", rest, re.MULTILINE)
    unreleased_block = rest[: next_version.start()] if next_version else rest
    tail = rest[next_version.start() :] if next_version else ""

    if re.search(rf"^{re.escape(heading)}\s*$", unreleased_block, re.MULTILINE):
        updated_block = re.sub(
            rf"(^{re.escape(heading)}\s*$)",
            rf"\1\n\n- {bullet}",
            unreleased_block,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        section = f"\n{heading}\n\n- {bullet}\n"
        updated_block = unreleased_block.rstrip() + section

    return changelog_text[: match.end()] + updated_block + tail


def cmd_consolidate(root: Path, dry_run: bool) -> int:
    state = load_state(root)
    entries = state.get("entries", [])
    if not entries:
        print(json.dumps({"status": "noop", "reason": "no session entries"}, indent=2))
        return 0

    changelog = ensure_changelog(root)
    text = changelog.read_text(encoding="utf-8")
    added = 0
    skipped = 0
    for entry in entries:
        bullet = entry["summary"]
        before = text
        text = insert_into_unreleased(text, entry["category"], bullet)
        if text == before:
            skipped += 1
        else:
            added += 1

    if not dry_run and added:
        changelog.write_text(text, encoding="utf-8")
        state["consolidated"] = True
        state["consolidated_at"] = now_iso()
        save_state(root, state)

    print(
        json.dumps(
            {
                "status": "dry_run" if dry_run else "consolidated",
                "added": added,
                "skipped_duplicates": skipped,
                "session_entries": len(entries),
            },
            indent=2,
        )
    )
    return 0


def slugify_branch(branch: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", branch).strip("-").lower()
    return slug[:80] or "branch"


def cmd_pr_body(root: Path, output: str | None) -> int:
    state = load_state(root)
    branch = state.get("branch") or current_branch(root)
    date = state.get("session_date") or datetime.now().strftime("%Y-%m-%d")
    entries = state.get("entries", [])

    by_cat: dict[str, list[str]] = {}
    for entry in entries:
        by_cat.setdefault(entry["category"], []).append(entry["summary"])

    lines = [
        f"# {branch}",
        "",
        f"**Date:** {date}  ",
        f"**Branch:** `{branch}` → `develop`",
        "",
        "## Summary",
        "",
    ]
    if entries:
        lines.append(
            f"Session delivered {len(entries)} changelog entries across "
            f"{len(by_cat)} categories."
        )
    else:
        lines.append("No session changelog entries recorded.")
    lines.append("")

    for category in CATEGORIES:
        items = by_cat.get(category, [])
        if not items:
            continue
        lines.append(f"### {CATEGORY_HEADINGS[category]}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    counts = unreleased_counts(root)
    if sum(counts.values()):
        lines.extend(["## Unreleased (CHANGELOG.md)", ""])
        for category in CATEGORIES:
            n = counts.get(category, 0)
            if n:
                lines.append(f"- **{CATEGORY_HEADINGS[category]}:** {n} item(s)")
        lines.append("")

    body = "\n".join(lines).rstrip() + "\n"
    out_path = (
        Path(output)
        if output
        else reports_dir(root) / f"pr-{slugify_branch(branch)}.md"
    )
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    print(json.dumps({"status": "written", "path": str(out_path.relative_to(root))}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Session start: open today's session log")
    init_p.add_argument("--date", help="YYYY-MM-DD (default: today)")
    init_p.add_argument("--branch", help="Override git branch")

    append_p = sub.add_parser("append", help="Record one changelog entry after an action")
    append_p.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help="Keep a Changelog category",
    )
    append_p.add_argument("--summary", required=True, help="One-line change description")
    append_p.add_argument("--commit", action="append", default=[], help="Commit hash (repeatable)")
    append_p.add_argument("--files", default="", help="Comma-separated file paths")
    append_p.add_argument("--date", help="Session date override")

    status_p = sub.add_parser("status", help="Session + unreleased summary")
    status_p.add_argument("--json", action="store_true")

    cons_p = sub.add_parser("consolidate", help="EOD: merge session into CHANGELOG.md [Unreleased]")
    cons_p.add_argument("--dry-run", action="store_true")

    pr_p = sub.add_parser("pr-body", help="EOD: write PR description from session")
    pr_p.add_argument("--output", help="Output path (default: reports/changelog/pr-<branch>.md)")

    args = parser.parse_args()
    root = project_root()

    if args.command == "init":
        return cmd_init(root, args.date, args.branch)
    if args.command == "append":
        files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
        return cmd_append(root, args.category, args.summary, args.commit, files, args.date)
    if args.command == "status":
        return cmd_status(root, args.json)
    if args.command == "consolidate":
        return cmd_consolidate(root, args.dry_run)
    if args.command == "pr-body":
        return cmd_pr_body(root, args.output)
    return 1


if __name__ == "__main__":
    sys.exit(main())
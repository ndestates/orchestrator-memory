#!/usr/bin/env python3
"""Check docs/codebase cache freshness vs manifest policy and git/TODO context."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


_MANIFEST_MARKERS = (
    ".grok/project-manifest.yaml",  # Grok first (wave/fleet Grok users)
    ".github/project-manifest.yaml",
    ".claude/project-manifest.yaml",
    ".gemini/project-manifest.yaml",
    ".copilot/project-manifest.yaml",
    ".cursor/project-manifest.yaml",
)


def project_root() -> Path:
    env = Path.cwd()
    for candidate in (env, *env.parents):
        for marker in _MANIFEST_MARKERS:
            if (candidate / marker).exists():
                return candidate
    return env


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_cache_stale_days(manifest_text: str) -> int:
    match = re.search(r"cache_stale_days:\s*(\d+)", manifest_text)
    return int(match.group(1)) if match else 14


def parse_iso_dates(text: str) -> list[date]:
    dates: list[date] = []
    for match in re.finditer(r"\[UPDATED\s+(\d{4}-\d{2}-\d{2})\]", text, re.I):
        dates.append(date.fromisoformat(match.group(1)))
    for match in re.finditer(r"\[CACHED\s+(\d{4}-\d{2}-\d{2})\]", text, re.I):
        dates.append(date.fromisoformat(match.group(1)))
    for match in re.finditer(r"##\s+(\d{4}-\d{2}-\d{2})\b", text):
        dates.append(date.fromisoformat(match.group(1)))
    for match in re.finditer(r"Generated:\s+(\d{4}-\d{2}-\d{2})", text):
        dates.append(date.fromisoformat(match.group(1)))
    return dates


def latest_date(dates: list[date]) -> date | None:
    return max(dates) if dates else None


def git_current_branch(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.stdout or "").strip() or "unknown"
    except OSError:
        return "unknown"


def latest_todo_file(root: Path) -> Path | None:
    todo_dir = root / "TODO"
    if not todo_dir.is_dir():
        return None
    dated: list[tuple[date, Path]] = []
    for path in todo_dir.glob("*_TODO.md"):
        if not path.is_file():
            continue
        match = re.match(r"(\d{4}-\d{2}-\d{2})_TODO\.md$", path.name)
        if match:
            dated.append((date.fromisoformat(match.group(1)), path))
    if dated:
        dated.sort(key=lambda item: item[0], reverse=True)
        return dated[0][1]
    fallback = sorted(todo_dir.glob("*_TODO.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return fallback[0] if fallback else None


def todo_branch(todo_text: str) -> str | None:
    match = re.search(r"\*\*Branch:\*\*\s*`([^`]+)`", todo_text)
    if match:
        return match.group(1)
    match = re.search(r"^Branch:\s*`([^`]+)`", todo_text, re.M)
    return match.group(1) if match else None


def scan_branch_reference(scan_text: str) -> str | None:
    for pattern in (
        r"HEAD:\s*`([^`]+)`",
        r"on\s+`([^`]+)`",
        r"branch\s+`([^`]+)`",
    ):
        match = re.search(pattern, scan_text, re.I)
        if match:
            return match.group(1)
    return None


def classify_age(days: int, stale_days: int) -> str:
    if days > stale_days:
        return "stale"
    if days > max(stale_days // 2, 3):
        return "aging"
    return "fresh"


def recommend(status: str, branch_drift: bool) -> list[str]:
    recs: list[str] = []
    if status == "stale":
        recs.append("/read-codebase")
        recs.append("/chain cache-rebuild")
    elif status == "aging":
        recs.append("/read-codebase (targeted delta on current branch)")
    if branch_drift:
        recs.append("/chain cache-rebuild or targeted /read-codebase on current branch")
        recs.append("/branch-context-agent")
    if status == "fresh" and not branch_drift:
        recs.append("No refresh required — continue with /load-project-cache-first")
    return recs


def main() -> int:
    root = project_root()
    today = date.today()

    try:
        from _engine import manifest_sync as _ms
    except ImportError:
        _scripts = root / "scripts"
        if str(_scripts) not in sys.path:
            sys.path.insert(0, str(_scripts))
        from _engine import manifest_sync as _ms

    manifest_text = ""
    manifest_path = None
    # Prefer .grok copy for Grok sessions (wave/fleet apps often have
    # .github + .grok; Grok prompts expect the .grok one).
    found = getattr(_ms, "find_grok_manifest_path", _ms.find_manifest_path)(root)
    if found is not None:
        manifest_text = read_text(found)
        manifest_path = str(found.relative_to(root))

    stale_days = parse_cache_stale_days(manifest_text)
    freshness_path = root / "docs" / "codebase" / ".codebase-freshness.txt"
    scan_path = root / "docs" / "codebase" / ".codebase-scan.txt"
    readme_path = root / "docs" / "codebase" / "README.md"
    scan_text = read_text(freshness_path) if freshness_path.is_file() else read_text(scan_path)
    readme_text = read_text(readme_path)

    scan_dates = parse_iso_dates(scan_text)
    readme_dates = parse_iso_dates(readme_text)
    last_scan = latest_date(scan_dates)
    last_readme = latest_date(readme_dates)
    last_cache = max(d for d in (last_scan, last_readme) if d is not None) if (last_scan or last_readme) else None

    age_days = (today - last_cache).days if last_cache else None
    status = "unknown" if age_days is None else classify_age(age_days, stale_days)

    current_branch = git_current_branch(root)
    todo_file = latest_todo_file(root)
    todo_text = read_text(todo_file) if todo_file else ""
    todo_branch_name = todo_branch(todo_text)
    scan_branch = scan_branch_reference(scan_text)

    branch_drift = False
    drift_reasons: list[str] = []
    if todo_branch_name and current_branch != todo_branch_name:
        branch_drift = True
        drift_reasons.append(f"git={current_branch} vs TODO={todo_branch_name}")
    if scan_branch and current_branch != scan_branch:
        branch_drift = True
        drift_reasons.append(f"git={current_branch} vs scan={scan_branch}")

    payload = {
        "checked_at": today.isoformat(),
        "manifest": manifest_path,
        "cache_stale_days": stale_days,
        "last_scan_date": last_scan.isoformat() if last_scan else None,
        "last_readme_updated": last_readme.isoformat() if last_readme else None,
        "last_cache_activity": last_cache.isoformat() if last_cache else None,
        "age_days": age_days,
        "status": status,
        "branch_drift": branch_drift,
        "drift_reasons": drift_reasons,
        "current_branch": current_branch,
        "todo_branch": todo_branch_name,
        "scan_branch": scan_branch,
        "todo_file": str(todo_file.relative_to(root)) if todo_file else None,
        "recommendations": recommend(status, branch_drift),
        "files_checked": [
            str(scan_path.relative_to(root)),
            str(readme_path.relative_to(root)),
        ],
    }

    try:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from scripts import skill_health as _skill_health

        skill_scan = _skill_health.scan_skills(root)
        payload["skill_stale"] = skill_scan.get("stale_count", 0)
        payload["skill_missing_verified_at"] = skill_scan.get("missing_verified_at", [])
        if payload["skill_stale"]:
            payload["recommendations"].append("/skill-health (stale verified_at/covers)")
    except Exception:
        payload["skill_stale"] = None

    if "--json" in sys.argv:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Cache freshness: {status.upper()}")
        print(f"Policy: cache_stale_days={stale_days} ({manifest_path or 'default'})")
        if last_cache:
            print(f"Last cache activity: {last_cache.isoformat()} ({age_days} days ago)")
        else:
            print("Last cache activity: unknown (no dates in scan/README)")
        print(f"Branch: {current_branch}")
        if todo_branch_name:
            print(f"TODO branch: {todo_branch_name}")
        if scan_branch:
            print(f"Scan branch: {scan_branch}")
        if branch_drift:
            print(f"Branch drift: YES — {'; '.join(drift_reasons)}")
        else:
            print("Branch drift: no")
        print("Recommend:")
        for item in payload["recommendations"]:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Per-app compound learning gate — assess spine and close incomplete loops."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

REQUIRED_SPINE = [
    "STATE.md",
    "VISION.md",
    "reports/loops/lessons-state.json",
    "scripts/loop-compound.sh",
    "scripts/loop_compound.py",
    ".grok/skills/loop-compound/SKILL.md",
    "patterns/compound-learning.md",
]

TEMPLATE_LESSON_MARKER = "Full `.codebase-scan.txt` can lag README"

LESSONS_HEADING = re.compile(r"^##\s+Lessons\b", re.I)
LESSON_BULLET = re.compile(r"^[-*]\s+(.+)$")
NONE_NEW = re.compile(r"none\s+new|no\s+new\s+lesson", re.I)


def loop_enabled(root: Path) -> bool:
    return (root / "LOOP.md").is_file()


def checker_script(root: Path) -> Path | None:
    local = root / ".grok/skills/cache-freshness-check/scripts/cache_freshness_check.py"
    if local.is_file():
        return local
    orch = Path(__file__).resolve().parent.parent.parent
    shared = orch / ".grok/skills/cache-freshness-check/scripts/cache_freshness_check.py"
    return shared if shared.is_file() else None


def run_cache_checker(root: Path) -> dict:
    script = checker_script(root)
    if not script:
        return {"status": "unknown", "error": "cache_freshness_check.py missing"}
    proc = subprocess.run(
        ["python3", str(script), "--json"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {"status": "unknown", "error": (proc.stderr or proc.stdout or "").strip()[:500]}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "unknown", "error": "invalid checker json"}


def load_lessons_state(root: Path) -> tuple[dict, int, int, int]:
    path = root / "reports/loops/lessons-state.json"
    if not path.is_file():
        return {}, 0, 0, 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, 0, 0, 0
    items = data.get("lessons_learned", [])
    app_lessons = sum(
        1 for x in items if TEMPLATE_LESSON_MARKER not in x.get("text", "")
    )
    gates = len(data.get("gate_history", []))
    return data, len(items), app_lessons, gates


def extract_report_lessons(text: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    lessons: list[str] = []
    for line in lines:
        if LESSONS_HEADING.match(line.strip()):
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("## "):
                break
            if not stripped:
                continue
            m = LESSON_BULLET.match(stripped)
            if m:
                body = m.group(1).strip()
                if NONE_NEW.search(body):
                    continue
                lessons.append(body)
    return lessons


def lesson_recorded(data: dict, lesson: str) -> bool:
    key = re.sub(r"\s+", " ", lesson.strip().lower())
    for item in data.get("lessons_learned", []):
        if re.sub(r"\s+", " ", item.get("text", "").strip().lower()) == key:
            return True
    return False


# Cap how many loop reports we open at session-start compound gate (Phase B BH-009).
UNCLOSED_REPORT_SCAN_LIMIT = 20


def find_unclosed_report(
    root: Path,
    lessons_data: dict,
    *,
    max_reports: int = UNCLOSED_REPORT_SCAN_LIMIT,
) -> Path | None:
    loops = root / "reports/loops"
    if not loops.is_dir():
        return None
    reports = sorted(loops.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    scanned = 0
    for report in reports:
        if report.name.endswith("-host.md"):
            continue
        scanned += 1
        if scanned > max_reports:
            break
        lessons = extract_report_lessons(report.read_text(encoding="utf-8", errors="replace"))
        if not lessons:
            continue
        if any(not lesson_recorded(lessons_data, lesson) for lesson in lessons):
            return report
    return None


def read_state_lessons(root: Path, limit: int = 3) -> list[str]:
    state = root / "STATE.md"
    if not state.is_file():
        return []
    text = state.read_text(encoding="utf-8")
    marker = "## Lessons → skills"
    if marker not in text:
        return []
    _, rest = text.split(marker, 1)
    block = rest.split("## ", 1)[0]
    out: list[str] = []
    for line in block.splitlines():
        m = LESSON_BULLET.match(line.strip())
        if m:
            body = m.group(1).strip()
            if body and not body.startswith("("):
                out.append(body)
    return out[:limit]


def build_app_lesson(root: Path, checker: dict, *, trigger: str) -> str:
    name = root.name
    status = checker.get("status", "unknown")
    branch = checker.get("current_branch") or checker.get("branch") or "unknown"
    last_scan = checker.get("last_scan_date") or "unknown"
    return (
        f"{name}: session-start compound gate ({trigger}) — cache {status} on `{branch}` "
        f"(scan {last_scan}); durable lessons in STATE prevent loop context drift."
    )


def assess(root: Path) -> dict:
    root = root.resolve()
    if not loop_enabled(root):
        return {
            "status": "skip",
            "loop_enabled": False,
            "reason": "no LOOP.md — compound gate not applicable",
            "action": "none",
        }

    missing = [p for p in REQUIRED_SPINE if not (root / p).exists()]
    spine_ok = len(REQUIRED_SPINE) - len(missing)
    lessons_data, lessons_total, app_lessons, gates = load_lessons_state(root)
    unclosed = find_unclosed_report(root, lessons_data)
    checker = run_cache_checker(root)
    cache_status = checker.get("status", "unknown")

    if spine_ok == len(REQUIRED_SPINE) and app_lessons >= 1 and gates >= 1:
        compound_status = "ready"
    elif spine_ok == len(REQUIRED_SPINE) and gates >= 1:
        compound_status = "scaffold"
    elif spine_ok >= 4:
        compound_status = "partial"
    else:
        compound_status = "gap"

    if compound_status == "ready" and unclosed:
        compound_status = "unclosed_report"

    if compound_status == "gap":
        action = "offer_scaffold"
    elif compound_status == "partial":
        action = "offer_loops_starter"
    elif compound_status == "scaffold":
        action = "close_compound"
    elif compound_status == "unclosed_report":
        action = "close_compound"
    else:
        action = "load_state"

    return {
        "status": compound_status,
        "loop_enabled": True,
        "spine": f"{spine_ok}/{len(REQUIRED_SPINE)}",
        "missing_spine": missing,
        "lessons_total": lessons_total,
        "app_lessons": app_lessons,
        "gates": gates,
        "cache_status": cache_status,
        "unclosed_report": str(unclosed.relative_to(root)) if unclosed else None,
        "state_lessons": read_state_lessons(root),
        "action": action,
        "checker_error": checker.get("error"),
    }


def update_state_after_close(root: Path, checker: dict, report_rel: str) -> None:
    state = root / "STATE.md"
    if not state.is_file():
        return
    text = state.read_text(encoding="utf-8")
    status = checker.get("status", "unknown")
    branch = checker.get("current_branch") or checker.get("branch") or "unknown"
    today = date.today().isoformat()
    cache_block = "\n".join(
        [
            "- `.github/project-manifest.yaml` — cache_stale_days",
            "- `docs/codebase/README.md` or scan artifact",
            "- `STATE.md`, `LOOP.md`, `VISION.md`",
            f"- Gate report: `{report_rel}`",
        ]
    )
    replacements = {
        "## Cache used (last run)\n\n- (populated by loops)": (
            f"## Cache used (last run)\n\n{cache_block}"
        ),
    }
    stale_marker = "## Stale flags\n\n"
    if stale_marker in text:
        parts = text.split(stale_marker, 1)
        rest = parts[1].split("## ", 1)
        text = (
            parts[0]
            + stale_marker
            + f"- **{status}** — app-compound-gate {today} (branch `{branch}`)\n\n"
            + ("## " + rest[1] if len(rest) > 1 else "")
        )
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
    state.write_text(text, encoding="utf-8")


def append_run_log(root: Path, report_rel: str) -> None:
    log = root / "loop-run-log.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = (
        f"| {ts} | app-compound-gate | session-start | STATE,VISION,lessons-state | "
        f"PASS | {report_rel} |\n"
    )
    if log.is_file():
        text = log.read_text(encoding="utf-8")
        if "| Timestamp |" not in text and "| Timestamp (UTC) |" not in text:
            if not text.endswith("\n"):
                text += "\n"
            text += (
                "\n| Timestamp | Loop | Type | Cache | Outcome | Artifact |\n"
                "|-----------|------|------|-------|---------|----------|\n"
            )
        text += row
    else:
        text = (
            "# Loop run log (append-only)\n\n"
            "| Timestamp | Loop | Type | Cache | Outcome | Artifact |\n"
            "|-----------|------|------|-------|---------|----------|\n"
            + row
        )
    log.write_text(text, encoding="utf-8")


def write_compound_report(root: Path, checker: dict, *, trigger: str) -> Path:
    today = date.today().isoformat()
    report_name = f"{today}-session-compound-gate.md"
    path = root / "reports/loops" / report_name
    path.parent.mkdir(parents=True, exist_ok=True)
    status = checker.get("status", "unknown")
    branch = checker.get("current_branch") or checker.get("branch") or "unknown"
    todo_branch = checker.get("todo_branch") or "—"
    last_scan = checker.get("last_scan_date") or "unknown"
    drift = "yes" if checker.get("branch_drift") else "no"
    recs = checker.get("recommendations") or ["Continue with `/load-project-cache-first`."]
    lesson = build_app_lesson(root, checker, trigger=trigger)
    summary = (
        f"Per-app compound gate on session-start: cache **{status}** on `{branch}`. "
        f"Last scan {last_scan}; drift {drift}. L1 — closes learning loop in this repo only."
    )
    body = f"""# App Compound Gate — {today}

**Level:** L1 report-only
**Trigger:** session-start `app-compound-gate`
**Repo:** `{root.name}`

## Cache cited

- `STATE.md`, `VISION.md`, `LOOP.md`
- `reports/loops/lessons-state.json`
- `cache_freshness_check.py --json`

## Executive summary

{summary}

## Checker results

| Field | Value |
|-------|-------|
| Status | `{status}` |
| Branch | `{branch}` |
| TODO branch | `{todo_branch}` |
| Last scan | `{last_scan}` |
| Branch drift | {drift} |

**Recommendations:**
{chr(10).join(f"- {r}" for r in recs)}

## L1 compliance

- Per-app only — no fleet audit
- No auto `/read-codebase` without user approval

## Lessons

- {lesson}

## Next

1. Cite `STATE.md` lessons each session-start when status is READY
2. Run weekly `/chain cache-freshness-watch scheduled` when cache work resumes
"""
    path.write_text(body, encoding="utf-8")
    return path


def run_compound(root: Path, report: Path) -> tuple[int, str]:
    script = root / "scripts/loop-compound.sh"
    if not script.is_file():
        return 1, "missing loop-compound.sh"
    proc = subprocess.run(
        ["bash", str(script), "--report", str(report.relative_to(root))],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout or proc.stderr or "").strip()


def close(root: Path) -> dict:
    root = root.resolve()
    assessment = assess(root)
    if assessment["status"] == "skip":
        return {**assessment, "closed": False, "reason": assessment.get("reason")}

    action = assessment["action"]
    if action not in ("close_compound",):
        return {
            **assessment,
            "closed": False,
            "reason": f"action={action} — no auto-close at L1",
        }

    checker = run_cache_checker(root)
    unclosed_rel = assessment.get("unclosed_report")
    if unclosed_rel:
        report = root / unclosed_rel
        trigger = "unclosed_report"
    else:
        report = write_compound_report(root, checker, trigger="scaffold")
        trigger = "scaffold"

    report_rel = str(report.relative_to(root))
    if trigger == "scaffold":
        update_state_after_close(root, checker, report_rel)
        append_run_log(root, report_rel)

    code, compound_out = run_compound(root, report)
    post = assess(root)
    return {
        **assessment,
        "closed": code == 0,
        "compound_exit": code,
        "report": report_rel,
        "trigger": trigger,
        "post_status": post.get("status"),
        "compound_tail": compound_out.splitlines()[-2:] if compound_out else [],
    }
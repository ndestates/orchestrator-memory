#!/usr/bin/env python3
"""Compound learning (steps 10–14): promote loop lessons into STATE + lessons-state.json."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Secure vault graph (hash-chained, scrubbed, verifiable).
# Repo root is parents[1] for scripts/*.py (parents[2] is wrong — lands in projects/).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
try:
    from scripts._engine import vault as vault_mod
except ImportError:  # app deploy with scripts/ on path only
    from _engine import vault as vault_mod  # type: ignore


LESSONS_HEADING = re.compile(r"^##\s+Lessons\b", re.I)
LESSON_BULLET = re.compile(r"^[-*]\s+(.+)$")
NONE_NEW = re.compile(r"none\s+new|no\s+new\s+lesson", re.I)


def extract_lessons(report_text: str) -> list[str]:
    lines = report_text.splitlines()
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
                text = m.group(1).strip()
                if NONE_NEW.search(text):
                    continue
                lessons.append(text)
    return lessons


def normalize_lesson(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _lessons_from_state_text(text: str) -> list[str]:
    marker = "## Lessons → skills"
    if marker not in text:
        return []
    _, rest = text.split(marker, 1)
    block = rest.split("## ", 1)[0]
    out: list[str] = []
    for line in block.splitlines():
        m = LESSON_BULLET.match(line.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def read_state_lessons(state_path: Path) -> list[str]:
    if not state_path.exists():
        return []
    return _lessons_from_state_text(state_path.read_text(encoding="utf-8"))


def append_state_lessons(state_path: Path, new_lessons: list[str]) -> int:
    """Append new lesson bullets under ## Lessons → skills (single STATE read)."""
    if state_path.exists():
        text = state_path.read_text(encoding="utf-8")
    else:
        template = Path(__file__).resolve().parent.parent / "starters/loop-state/STATE.template.md"
        text = (
            template.read_text(encoding="utf-8")
            if template.exists()
            else "# Loop State\n\n## Lessons → skills\n\n"
        )

    existing = {normalize_lesson(x) for x in _lessons_from_state_text(text)}
    to_add = [l for l in new_lessons if normalize_lesson(l) not in existing]
    if not to_add:
        return 0

    marker = "## Lessons → skills"
    bullets = "\n".join(f"- {l}" for l in to_add)
    if marker in text:
        text = text.replace(marker, f"{marker}\n\n{bullets}", 1)
    else:
        text = text.rstrip() + f"\n\n{marker}\n\n{bullets}\n"
    state_path.write_text(text, encoding="utf-8")
    return len(to_add)


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "lessons_learned": [], "promotions": [], "gate_history": []}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def merge_lessons_json(data: dict, lessons: list[str], *, source: str) -> int:
    existing = {normalize_lesson(x.get("text", "")) for x in data.get("lessons_learned", [])}
    added = 0
    ts = datetime.now(timezone.utc).isoformat()
    for lesson in lessons:
        key = normalize_lesson(lesson)
        if key in existing:
            continue
        data.setdefault("lessons_learned", []).append(
            {"text": lesson, "source": source, "recorded_at": ts}
        )
        existing.add(key)
        added += 1
    data["updated"] = ts
    return added


def run_gate(script: Path, root: Path) -> dict:
    if not script.is_file():
        return {"script": str(script), "exit_code": -1, "ok": False, "summary": "missing"}
    proc = subprocess.run(
        ["bash", str(script)] if script.suffix == ".sh" else ["python3", str(script)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    tail = (proc.stdout or proc.stderr or "").strip().splitlines()
    summary = tail[-1] if tail else ""
    ok = proc.returncode == 0
    return {
        "script": script.name,
        "exit_code": proc.returncode,
        "ok": ok,
        "summary": summary[:200],
    }


def suggest_promotions(lessons: list[str]) -> list[dict]:
    suggestions: list[dict] = []
    for lesson in lessons:
        low = lesson.lower()
        if any(k in low for k in ("concern", "security", "blast radius", "drift", "secret")):
            suggestions.append({"target": "CONCERNS", "lesson": lesson, "status": "pending"})
        elif any(k in low for k in ("skill", "chain", "loop", "deploy", "wave")):
            suggestions.append({"target": "skill", "lesson": lesson, "status": "pending"})
        elif any(k in low for k in ("cache", "memory", "index", "docs/codebase")):
            suggestions.append({"target": "memory", "lesson": lesson, "status": "pending"})
        else:
            suggestions.append({"target": "STATE", "lesson": lesson, "status": "recorded"})
    return suggestions


def update_compound_queue(state_path: Path, suggestions: list[dict]) -> None:
    pending = [s for s in suggestions if s["target"] != "STATE" and s["status"] == "pending"]
    if not pending or not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    marker = "## Compound queue"
    if marker not in text:
        return
    rows = ["| Target | Lesson | Status |", "|--------|--------|--------|"]
    for s in pending[:5]:
        lesson = s["lesson"].replace("|", "/")[:80]
        rows.append(f"| {s['target']} | {lesson} | pending |")
    table = "\n".join(rows)
    before, rest = text.split(marker, 1)
    rest_lines = rest.splitlines()
    end = len(rest_lines)
    for i, line in enumerate(rest_lines[1:], start=1):
        if line.startswith("## ") and i > 0:
            end = i
            break
    text = before + marker + "\n\n" + table + "\n\n" + "\n".join(rest_lines[end:]).lstrip()
    state_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote loop lessons into durable project memory")
    parser.add_argument("--report", type=Path, help="Loop report markdown (requires ## Lessons)")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--gates-only", action="store_true", help="Run objective gates only")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary")
    args = parser.parse_args()

    root = args.root.resolve()
    state_path = root / "STATE.md"
    lessons_json_path = root / "reports/loops/lessons-state.json"

    gate_results = [
        run_gate(root / "scripts/loop-audit.sh", root),
        run_gate(root / "scripts/chain-audit.sh", root),
    ]
    data = load_json(lessons_json_path)
    ts = datetime.now(timezone.utc).isoformat()
    data.setdefault("gate_history", []).append({"at": ts, "gates": gate_results})

    lessons: list[str] = []
    if args.report:
        report_path = args.report if args.report.is_absolute() else root / args.report
        if not report_path.is_file():
            print(f"ERROR: report not found: {report_path}", file=sys.stderr)
            return 1
        lessons = extract_lessons(report_path.read_text(encoding="utf-8"))
        if not lessons and not args.gates_only:
            print(f"WARN: no lessons in {report_path} — add '## Lessons' or '- none new'", file=sys.stderr)

    try:
        from scripts import skill_health as skill_health_mod
    except ImportError:
        try:
            import skill_health as skill_health_mod  # type: ignore
        except ImportError:
            skill_health_mod = None
    if skill_health_mod is not None and not args.gates_only:
        existing = {normalize_lesson(x) for x in read_state_lessons(state_path)}
        existing.update(normalize_lesson(x) for x in lessons)
        lessons.extend(skill_health_mod.pending_lessons(root, existing=existing))

    added_state = append_state_lessons(state_path, lessons) if lessons else 0
    added_json = merge_lessons_json(data, lessons, source=str(args.report or "gates-only")) if lessons else 0
    suggestions = suggest_promotions(lessons) if lessons else []
    if suggestions:
        data.setdefault("promotions", []).extend(suggestions)
        update_compound_queue(state_path, suggestions)

    # === Secure self-building vault graph (strong integrity + provenance) ===
    # Post-compound step: ALWAYS emit lessons to the graph (and verify) for self-building vault.
    vault_ledger = root / "reports/vault/events.jsonl"
    vault_events_added = 0
    vault_verify_ok = True
    vault_issues: list[str] = []
    last_head = None

    # Load previous head for hash chain (last event's content_hash if any)
    prev_events = vault_mod.load_events(vault_ledger)
    if prev_events:
        last = prev_events[-1]
        last_head = last.get("content_hash")

    for lesson in lessons:
        ev = vault_mod.secure_compound_emit(
            lesson=lesson,
            report_source=str(args.report or "gates-only"),
            ledger_path=vault_ledger,
            previous_head=last_head,
            root=root,
            area="learning",
        )
        if ev:
            vault_events_added += 1
            last_head = ev.get("content_hash")

    # Always verify the ledger for tamper-evidence as post-compound step
    vault_verify_ok, vault_issues = vault_mod.verify_ledger(vault_ledger)

    save_json(lessons_json_path, data)

    summary = {
        "lessons_extracted": len(lessons),
        "state_added": added_state,
        "json_added": added_json,
        "vault_events_added": vault_events_added,
        "vault_verify_ok": vault_verify_ok,
        "vault_issues_count": len(vault_issues),
        "gates": gate_results,
        "promotions_pending": len([s for s in suggestions if s.get("status") == "pending"]),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Compound: lessons={len(lessons)} state+={added_state} json+={added_json} vault+={vault_events_added}")
        for g in gate_results:
            status = "PASS" if g["ok"] else "FAIL"
            print(f"Gate {g['script']}: {status} — {g['summary']}")
        if not vault_verify_ok:
            print("VAULT INTEGRITY WARNING (hash chain):")
            for issue in vault_issues[:5]:
                print(f"  - {issue}")
        if suggestions:
            print("Promotion queue (human approves at L1):")
            for s in suggestions:
                if s["target"] != "STATE":
                    print(f"  → {s['target']}: {s['lesson'][:100]}")
    return 0 if (all(g["ok"] for g in gate_results) and vault_verify_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
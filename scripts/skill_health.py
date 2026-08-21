#!/usr/bin/env python3
"""Skill-health log, week-over-week scores, and verified_at/covers drift scan.

No secrets in notes. Scores live in reports/skill-health/scores.jsonl (gitignored).
Significant events (score < 0.7, --corrected, or new stale/drop flags) emit to
the vault ledger the same way loop-compound lessons do.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)
DROP_THRESHOLD = 0.15
LOW_SCORE = 0.7
COHORT = (
    "skill-creator",
    "loop-compound",
    "project-drift-guardian",
    "cache-freshness-check",
    "security-audit-agent",
    "ai-content-guardrails",
    "jersey-data-protection-expert",
    "jersey-aml-compliance-expert",
    "didit-identity-integration",
    "documentation-specialist",
    "code-review",
    "skill-health",
)

SECRETISH = re.compile(
    r"(?i)(ghp_|github_pat_|sk-|AKIA[0-9A-Z]{16}|-----BEGIN |"
    r"(api[_-]?key|secret|password|token)\s*[:=]\s*\S+)"
)


def scores_path(root: Path) -> Path:
    return root / "reports" / "skill-health" / "scores.jsonl"


def normalize_lesson(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def scrub_notes(notes: str) -> str:
    cleaned = SECRETISH.sub("[REDACTED]", notes or "")
    cleaned = re.sub(r"[A-Za-z0-9/+=]{40,}", "[REDACTED:long-token]", cleaned)
    return cleaned.strip()[:240]


def parse_skill_frontmatter(text: str) -> dict[str, Any]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    out: dict[str, Any] = {}
    key: str | None = None
    covers: list[str] = []
    for raw in match.group(1).splitlines():
        if key == "covers" and re.match(r"^[ \t]+-\s+", raw):
            covers.append(raw.split("-", 1)[1].strip().strip("'\""))
            continue
        if key == "covers":
            key = None
        if ":" not in raw or raw.startswith(" ") or raw.startswith("\t"):
            continue
        name, _, rest = raw.partition(":")
        name, rest = name.strip(), rest.strip()
        if name == "name":
            out["name"] = rest.strip("'\"")
        elif name == "verified_at":
            date = re.search(r"(\d{4}-\d{2}-\d{2})", rest)
            if date:
                out["verified_at"] = date.group(1)
        elif name == "self_regulating" and rest.lower() in {"true", "yes"}:
            out["self_regulating"] = True
        elif name == "learnings" and rest.lower() in {"true", "yes"}:
            out["learnings"] = True
        elif name == "covers":
            key = "covers"
            inline = re.match(r"\[(.*)\]", rest)
            if inline:
                covers.extend(
                    part.strip().strip("'\"")
                    for part in inline.group(1).split(",")
                    if part.strip()
                )
                key = None
    if covers:
        out["covers"] = covers
    return out


def iter_skills(root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    skills_root = root / ".grok" / "skills"
    found: list[tuple[str, Path, dict[str, Any]]] = []
    if not skills_root.is_dir():
        return found
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        meta = parse_skill_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        name = meta.get("name") or skill_md.parent.name
        found.append((name, skill_md, meta))
    return found


def load_scores(root: Path) -> list[dict[str, Any]]:
    path = scores_path(root)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _avg(rows: list[dict[str, Any]]) -> float | None:
    scores = []
    for row in rows:
        try:
            scores.append(float(row["score"]))
        except (KeyError, TypeError, ValueError):
            continue
    if not scores:
        return None
    return sum(scores) / len(scores)


def summary_for(rows: list[dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_skill.setdefault(str(row.get("skill") or "unknown"), []).append(row)

    skills: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    for name, skill_rows in sorted(by_skill.items()):
        dated: list[tuple[datetime, dict[str, Any]]] = []
        for row in skill_rows:
            ts = parse_ts(str(row.get("ts") or ""))
            if ts is not None:
                dated.append((ts, row))
        this_week = [row for ts, row in dated if now - ts <= timedelta(days=7)]
        prev_week = [
            row for ts, row in dated if timedelta(days=7) < now - ts <= timedelta(days=14)
        ]
        this_avg = _avg(this_week)
        prev_avg = _avg(prev_week)
        rec = {
            "skill": name,
            "n_this_week": len(this_week),
            "n_prev_week": len(prev_week),
            "avg_this_week": this_avg,
            "avg_prev_week": prev_avg,
            "drop": None,
            "drift": False,
        }
        if this_avg is not None and prev_avg is not None and len(this_week) >= 2 and len(prev_week) >= 2:
            drop = prev_avg - this_avg
            rec["drop"] = round(drop, 4)
            if drop > DROP_THRESHOLD:
                rec["drift"] = True
                flags.append(
                    {
                        "skill": name,
                        "kind": "score_drop",
                        "lesson": (
                            f"skill-health: {name} score drop "
                            f"{prev_avg:.2f} → {this_avg:.2f} (>{DROP_THRESHOLD:.0%})"
                        ),
                    }
                )
        skills.append(rec)
    return {"skills": skills, "flags": flags, "threshold": DROP_THRESHOLD}


def git_commits_after(root: Path, verified_at: str, paths: list[str]) -> list[str]:
    if not paths:
        return []
    cmd = [
        "git",
        "-C",
        str(root),
        "log",
        "--pretty=format:%h",
        f"--since={verified_at}",
        "--",
        *paths,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def scan_skills(root: Path) -> dict[str, Any]:
    stale: list[dict[str, Any]] = []
    missing: list[str] = []
    checked: list[dict[str, Any]] = []
    present: set[str] = set()
    for name, skill_md, meta in iter_skills(root):
        present.add(name)
        if not meta.get("verified_at"):
            if name in COHORT:
                missing.append(name)
            continue
        covers = meta.get("covers") or [str(skill_md.parent.relative_to(root))]
        commits = git_commits_after(root, meta["verified_at"], covers)
        rec = {
            "skill": name,
            "verified_at": meta["verified_at"],
            "covers": covers,
            "commits_since": commits[:8],
            "stale": bool(commits),
        }
        checked.append(rec)
        if commits:
            stale.append(rec)
    for name in COHORT:
        if name not in present:
            missing.append(name)
    flags = [
        {
            "skill": rec["skill"],
            "kind": "stale",
            "lesson": (
                f"skill-health: {rec['skill']} stale vs verified_at={rec['verified_at']} "
                f"({len(rec['commits_since'])} commits on covers)"
            ),
        }
        for rec in stale
    ]
    return {
        "checked": len(checked),
        "stale_count": len(stale),
        "stale": stale,
        "missing_verified_at": missing,
        "flags": flags,
    }


def _emit_vault(root: Path, lesson: str, source: str) -> bool:
    try:
        from scripts._engine import vault as vault_mod
    except ImportError:
        try:
            from _engine import vault as vault_mod  # type: ignore
        except ImportError:
            return False
    ledger = root / "reports" / "vault" / "events.jsonl"
    last_head = None
    events = vault_mod.load_events(ledger)
    if events:
        last_head = events[-1].get("content_hash")
    ev = vault_mod.secure_compound_emit(
        lesson=lesson,
        report_source=source,
        ledger_path=ledger,
        previous_head=last_head,
        root=root,
        area="learning",
    )
    return ev is not None


def log_score(
    root: Path,
    *,
    skill: str,
    score: float,
    notes: str = "",
    corrected: bool = False,
    vault: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be between 0.0 and 1.0")
    now = now or datetime.now(timezone.utc)
    row = {
        "ts": now.isoformat(),
        "skill": skill,
        "score": round(float(score), 4),
        "notes": scrub_notes(notes),
        "corrected": bool(corrected),
    }
    path = scores_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    vaulted = False
    if vault or corrected or score < LOW_SCORE:
        lesson = f"skill-health: {skill} score={score:.2f}"
        if corrected:
            lesson += " corrected"
        if row["notes"]:
            lesson += f" — {row['notes']}"
        vaulted = _emit_vault(root, lesson, source=f"skill-health:{skill}")
    row["vaulted"] = vaulted
    return row


def pending_lessons(root: Path, existing: set[str] | None = None) -> list[str]:
    existing = existing or set()
    lessons: list[str] = []
    for flag in summary_for(load_scores(root))["flags"] + scan_skills(root)["flags"]:
        text = flag["lesson"]
        key = normalize_lesson(text)
        if key in existing:
            continue
        existing.add(key)
        lessons.append(text)
    return lessons


def cmd_log(args: argparse.Namespace) -> int:
    row = log_score(
        args.root,
        skill=args.skill,
        score=args.score,
        notes=args.notes or "",
        corrected=args.corrected,
        vault=args.vault,
    )
    print(json.dumps(row, indent=2) if args.json else f"logged {row['skill']} {row['score']}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    payload = summary_for(load_scores(args.root))
    if args.skill:
        payload["skills"] = [s for s in payload["skills"] if s["skill"] == args.skill]
        payload["flags"] = [f for f in payload["flags"] if f["skill"] == args.skill]
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"skill-health summary: flags={len(payload['flags'])}")
        for rec in payload["skills"]:
            this_avg = rec["avg_this_week"]
            prev_avg = rec["avg_prev_week"]
            mark = " DRIFT" if rec["drift"] else ""
            print(
                f"  {rec['skill']}: this={this_avg} prev={prev_avg} "
                f"n={rec['n_this_week']}/{rec['n_prev_week']}{mark}"
            )
        for flag in payload["flags"]:
            print(f"  FLAG {flag['lesson']}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    payload = scan_skills(args.root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"skill-health scan: checked={payload['checked']} "
            f"stale={payload['stale_count']} missing_verified_at={len(payload['missing_verified_at'])}"
        )
        for rec in payload["stale"]:
            print(f"  STALE {rec['skill']} since {rec['verified_at']} commits={rec['commits_since']}")
        for name in payload["missing_verified_at"]:
            print(f"  MISSING verified_at: {name}")
    return 1 if payload["stale_count"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill-health scores and drift scan")
    parser.add_argument("--root", type=Path, default=_ROOT)
    sub = parser.add_subparsers(dest="cmd", required=True)

    log_p = sub.add_parser("log", help="Append a run score")
    log_p.add_argument("--skill", required=True)
    log_p.add_argument("--score", type=float, required=True)
    log_p.add_argument("--notes", default="")
    log_p.add_argument("--corrected", action="store_true")
    log_p.add_argument("--vault", action="store_true")
    log_p.add_argument("--json", action="store_true")

    sum_p = sub.add_parser("summary", help="Week-over-week averages")
    sum_p.add_argument("--skill", default="")
    sum_p.add_argument("--json", action="store_true")

    scan_p = sub.add_parser("scan", help="Git verified_at + covers staleness")
    scan_p.add_argument("--json", action="store_true")

    args = parser.parse_args()
    args.root = args.root.resolve()
    if args.cmd == "log":
        return cmd_log(args)
    if args.cmd == "summary":
        return cmd_summary(args)
    return cmd_scan(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
EOD Vault Emit (integration hook) — **guaranteed** brain contribution (v1.5.0+).

Always appends a learning signal at end-of-day so app vaults do not stay empty.
When the day had substantive activity, emits a richer synthesis + lesson pair.

Usage:
  python3 scripts/eod-vault-emit.py
  python3 scripts/eod-vault-emit.py --summary "…" --area process
  python3 scripts/eod-vault-emit.py --dry-run
  python3 scripts/eod-vault-emit.py --skip-if-empty   # legacy: only emit if useful

Called from eod-shutdown / ddev-cleanup (mandatory).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from scripts._engine import vault as vmod
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts._engine import vault as vmod

DEFAULT_LEDGER = Path("reports/vault/events.jsonl")


def ensure_ledger(ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if not ledger.is_file():
        ledger.write_text("", encoding="utf-8")


def get_recent_changelog_summary() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    log = Path(f"reports/changelog/session-{today}.md")
    if not log.exists():
        return ""
    try:
        text = log.read_text(encoding="utf-8")
        lines = [l.strip() for l in text.splitlines() if l.strip()][-8:]
        return " | ".join(lines)[:400]
    except Exception:
        return ""


def todays_commits(limit: int = 8) -> list[str]:
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        res = subprocess.run(
            ["git", "log", "--since", today, "--oneline", f"-{limit}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return [l for l in res.stdout.strip().splitlines() if l.strip()]
    except Exception:
        return []


def is_useful_activity() -> bool:
    """True when changelog or git activity today is substantive."""
    cl = get_recent_changelog_summary()
    if len(cl) > 80:
        return True
    return len(todays_commits()) >= 1


def build_auto_summary() -> tuple[str, bool]:
    """Return (summary, rich_mode)."""
    cl = get_recent_changelog_summary()
    commits = todays_commits()
    branch = ""
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = (r.stdout or "").strip()
    except Exception:
        pass

    useful = is_useful_activity()
    parts: list[str] = []
    if branch:
        parts.append(f"branch={branch}")
    if commits:
        parts.append(f"commits={len(commits)}: " + "; ".join(commits[:5]))
    if cl:
        parts.append(f"changelog: {cl[:200]}")
    if useful:
        summary = "EOD (active day): " + " | ".join(parts) if parts else "EOD active day"
        return summary[:500], True

    # Guaranteed minimal heartbeat so vaults grow on quiet days too
    summary = (
        f"EOD heartbeat {datetime.now().strftime('%Y-%m-%d')}"
        + (f" on {branch}" if branch else "")
        + " — session closed; no large changelog/commits detected"
    )
    return summary[:500], False


def emit_eod_summary(
    summary: str | None = None,
    area: str = "process",
    source: str = "eod-shutdown",
    *,
    skip_if_empty: bool = False,
) -> dict | None:
    ensure_ledger(DEFAULT_LEDGER)
    root = Path(".")
    ledger = DEFAULT_LEDGER

    rich = True
    if not summary:
        summary, rich = build_auto_summary()
    else:
        summary = summary.strip()
        rich = is_useful_activity() or len(summary) > 40

    if skip_if_empty and not is_useful_activity() and len(summary) < 40:
        print("EOD vault emit: --skip-if-empty and no useful activity — skipping.")
        return None

    if len(summary) < 8:
        summary = f"EOD heartbeat {datetime.now().strftime('%Y-%m-%d')}"

    events = vmod.load_events(ledger)
    previous_head = events[-1].get("content_hash") if events else None

    if rich:
        ev = vmod.emit_synthesis_event(
            summary=summary,
            proposals=[
                "Review vault precedents for similar work tomorrow",
                "Promote durable patterns to STATE or skills after human review",
                "Query vault before re-planning work already recorded as done",
            ],
            source=source,
            area=area,
            root=root,
            parents=[previous_head] if previous_head else None,
            date=datetime.now().strftime("%Y-%m-%d"),
            activity_type="eod-shutdown",
        )
        # append synthesis
        vmod.append_event(ledger, ev)
        lesson_text = f"EOD shutdown: {summary[:200]}"
        mode = "rich"
    else:
        # Minimal guaranteed lesson only
        lesson_text = summary
        mode = "heartbeat"
        ev = None

    lesson_ev = vmod.secure_compound_emit(
        lesson=lesson_text,
        report_source=source,
        ledger_path=ledger,
        previous_head=previous_head or (ev.get("content_hash") if ev else None),
        root=root,
        area="learning" if rich else "process",
    )

    print(f"EOD vault emit: guaranteed write ({mode}, area={area}).")
    if ev:
        print(f"  synthesis id: {ev.get('content_hash', ev.get('id', ''))[:16]}")
    if lesson_ev:
        print(f"  lesson id:    {(lesson_ev.get('content_hash') or '')[:16]}")

    # Workspace pointer for multi-machine resume (embeds startup_policy for next start)
    try:
        wp = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parent / "vault-workspace-pointer.py"),
                "--emit",
                "--source",
                source,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if wp.returncode == 0:
            for line in (wp.stdout or "").strip().splitlines():
                print(line)
        else:
            err = (wp.stderr or "").strip() or "no branch"
            print(f"EOD vault emit: workspace pointer skipped ({err})")
    except Exception as exc:
        print(f"EOD vault emit: workspace pointer skipped ({exc})")

    # Rich resume card — mandatory for next /chain session-start (check + card)
    resume_data: dict | None = None
    resume_script = Path(__file__).resolve().parent / "session-resume-brief.py"
    if resume_script.is_file():
        try:
            cmd = [
                sys.executable,
                str(resume_script),
                "write",
                "--rich",
                "--source",
                "eod-shutdown",
                "--json",
            ]
            if summary:
                cmd.extend(["--summary", summary[:280]])
            rc = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=90,
            )
            if rc.returncode == 0 and (rc.stdout or "").strip():
                try:
                    data = json.loads(rc.stdout)
                    resume_data = data
                    print(f"EOD resume card: {data.get('path')} (rich)")
                    card = (data.get("card") or "").strip()
                    if card:
                        print("--- resume card ---")
                        print(card)
                        print("--- end resume card ---")
                    # Mandatory: next session-start is remote_last-first (order matters)
                    reminder = (data.get("next_start_reminder") or "").strip()
                    if reminder:
                        print(reminder)
                    else:
                        tip = (data.get("remote_last") or "").strip() or "remote_last"
                        print("=== NEXT SESSION-START (remote_last first) ===")
                        print("Chronological order — do not skip steps:")
                        print("  1. git fetch origin --prune")
                        print(
                            "  2. Auto-switch to remote_last (team tip) when tree clean "
                            "+ pull --ff-only"
                        )
                        print(
                            "  3. Load resume card from THAT tip "
                            "(not from pre-switch branch)"
                        )
                        print("  4. Security sweep → lean cache / work")
                        print(f"  Team tip at write: {tip}")
                        print("  Command: /chain session-start")
                        print("=== end next-start reminder ===")
                    if data.get("on_team_tip") is False:
                        print(
                            "EOD note: you shut down off team tip — next session-start "
                            "still prefers remote_last; commit this EOD branch before leave."
                        )
                except json.JSONDecodeError:
                    print("EOD resume card: written (unparsed json)")
            else:
                err = (rc.stderr or rc.stdout or "").strip() or f"exit {rc.returncode}"
                print(f"EOD resume card: FAILED — {err}", file=sys.stderr)
        except Exception as exc:
            print(f"EOD resume card: FAILED — {exc}", file=sys.stderr)
    else:
        print("EOD resume card: script missing (session-resume-brief.py)")

    # Vault double-check: session_startup event for next remote_last-first start
    try:
        branch_now = ""
        try:
            br = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if br.returncode == 0:
                branch_now = (br.stdout or "").strip()
        except Exception:
            pass
        remote_last = (resume_data or {}).get("remote_last") or None
        on_tip = (resume_data or {}).get("on_team_tip")
        on_rl = None
        if on_tip is True:
            on_rl = "yes"
        elif on_tip is False:
            on_rl = "no"
        sev = vmod.emit_session_startup(
            branch=branch_now or str((resume_data or {}).get("branch") or ""),
            remote_last=remote_last,
            on_remote_last=on_rl,
            resume_first=None,
            card_path=(resume_data or {}).get("path"),
            card_branch=(resume_data or {}).get("branch"),
            phase="eod-shutdown",
            source=source,
            ledger_path=ledger,
            root=root,
            extra={
                "summary": (summary or "")[:200],
                "next_action": "/chain session-start",
                "mode": mode,
            },
        )
        print(
            f"EOD vault emit: session_startup recorded "
            f"({(sev.get('content_hash') or '')[:16]}) "
            f"policy={vmod.SESSION_STARTUP_POLICY}"
        )
    except Exception as exc:
        print(f"EOD vault emit: session_startup skipped ({exc})")

    # Vault + resume card often touch tracked files after the "clean git" gate.
    # Preserve that WIP for tomorrow (commit on feature/*). Never ask the operator to stash.
    try:
        drain = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parent / "eod-commit-dirty.py"),
                "--message",
                "chore(eod): vault and resume-card artifacts",
                "--root",
                str(root.resolve()),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        note = (drain.stdout or drain.stderr or "").strip()
        if note:
            print(f"EOD vault emit: {note.splitlines()[0]}")
        if drain.returncode != 0:
            print(
                "EOD vault emit: preserve-wip did not finish clean — "
                "EOD incomplete while dirty"
            )
    except Exception as exc:
        print(f"EOD vault emit: preserve-wip skipped ({exc})")

    return lesson_ev or ev


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guaranteed EOD vault emit (rich when active, heartbeat otherwise)"
    )
    parser.add_argument("--summary", type=str, default=None)
    parser.add_argument("--area", type=str, default="process")
    parser.add_argument("--source", type=str, default="eod-shutdown")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-if-empty",
        action="store_true",
        help="Legacy behaviour: skip emit when no useful activity",
    )
    args = parser.parse_args()

    if args.dry_run:
        summary, rich = (
            (args.summary, True) if args.summary else build_auto_summary()
        )
        print("DRY RUN - would emit:")
        print(f"  mode: {'rich' if rich else 'heartbeat'}")
        print(f"  summary: {(summary or '')[:240]}")
        print(f"  area: {args.area}")
        print(f"  skip_if_empty: {args.skip_if_empty}")
        return 0

    try:
        emit_eod_summary(
            summary=args.summary,
            area=args.area,
            source=args.source,
            skip_if_empty=args.skip_if_empty,
        )
    except Exception as exc:
        print(f"EOD vault emit: FAILED — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

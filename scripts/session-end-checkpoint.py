#!/usr/bin/env python3
"""Mid-day session end checkpoint (v1.5.1+) — NOT full EOD.

Use when the user is leaving temporarily and will return later the same day
(or after a break). Differs from eod-shutdown:

  session-end                         eod-shutdown
  ─────────────────────────────────   ────────────────────────────────
  Dirty git OK (records WIP)          Clean git mandatory
  No ddev stop                        ddev stop
  No tomorrow TODO / reposition       Tomorrow TODO + leave feature/*
  Light vault pause + pointer         Guaranteed full EOD vault emit
  Resume note for same-day return     Day closed

Usage:
  python3 scripts/session-end-checkpoint.py
  python3 scripts/session-end-checkpoint.py --summary "Paused after PR review"
  python3 scripts/session-end-checkpoint.py --json

Exit 0 on success, 1 on hard failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def git_snapshot() -> dict:
    code_b, branch, _ = _run(["git", "branch", "--show-current"])
    code_s, status, _ = _run(["git", "status", "--porcelain"])
    code_l, log1, _ = _run(["git", "log", "-1", "--oneline"])
    dirty = bool(status) if code_s == 0 else True
    lines = status.splitlines() if status else []
    return {
        "branch": branch if code_b == 0 else "(unknown)",
        "dirty": dirty,
        "porcelain_lines": len(lines),
        "porcelain_sample": lines[:12],
        "head": log1 if code_l == 0 else "",
    }


def latest_todo() -> Path | None:
    todo_dir = ROOT / "TODO"
    if not todo_dir.is_dir():
        return None
    files = sorted(todo_dir.glob("*.md"), key=lambda p: p.name, reverse=True)
    dated = [p for p in files if any(c.isdigit() for c in p.name[:10])]
    pool = dated or files
    return pool[0] if pool else None


def append_todo_resume(todo: Path, branch: str, when: str, summary: str) -> None:
    block = (
        f"\n## Session pause ({when})\n\n"
        f"**Resume later today on:** `{branch}`\n\n"
        f"- [ ] Resume: {summary or 'continue in-progress work'}\n"
        f"- Run `/chain session-resume` (same-day return — not session-start)\n"
    )
    try:
        text = todo.read_text(encoding="utf-8")
        if f"## Session pause ({when[:10]})" in text and branch in text[-800:]:
            # still append with full timestamp uniqueness
            pass
        todo.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    except OSError:
        pass


def vault_pause_emit(summary: str, branch: str, dirty: bool) -> dict:
    """Light vault write: pause lesson + workspace pointer. Never fails the chain hard."""
    out: dict = {"lesson": None, "pointer": None, "errors": []}
    try:
        from scripts._engine import vault as vmod
    except ImportError:
        try:
            from _engine import vault as vmod  # type: ignore
        except ImportError:
            out["errors"].append("vault engine not importable")
            return out

    ledger = ROOT / "reports" / "vault" / "events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if not ledger.is_file():
        ledger.write_text("", encoding="utf-8")

    lesson = (
        f"Session pause on {branch}"
        + (" (dirty WIP)" if dirty else " (clean tree)")
        + (f": {summary}" if summary else "")
        + " — next: /chain session-resume on this branch (prior session, not remote_last)"
    )
    try:
        events = vmod.load_events(ledger)
        prev = events[-1].get("content_hash") if events else None
        ev = vmod.secure_compound_emit(
            lesson=lesson[:280],
            report_source="session-end",
            ledger_path=ledger,
            previous_head=prev,
            root=ROOT,
            area="process",
        )
        out["lesson"] = (ev or {}).get("content_hash")
    except Exception as exc:
        out["errors"].append(f"lesson: {exc}")

    # workspace pointer for multi-machine / later session-start (includes startup_policy)
    try:
        wp = ROOT / "scripts" / "vault-workspace-pointer.py"
        if wp.is_file():
            code, stdout, stderr = _run(
                [
                    sys.executable,
                    str(wp),
                    "--emit",
                    "--source",
                    "session-end",
                    "--branch",
                    branch,
                ],
                timeout=30,
            )
            out["pointer"] = "ok" if code == 0 else (stderr or stdout or f"exit {code}")
        else:
            out["pointer"] = "script missing"
    except Exception as exc:
        out["errors"].append(f"pointer: {exc}")

    # Explicit session_startup vault event for double-check of next-start order
    try:
        remote_last = ""
        try:
            code, rb_out, _ = _run(
                ["bash", str(ROOT / "scripts" / "resume-branch.sh")], timeout=60
            )
            if code == 0:
                for line in (rb_out or "").splitlines():
                    if line.startswith("remote_last="):
                        remote_last = line.split("=", 1)[1].strip()
        except Exception:
            pass
        on_tip = bool(remote_last and branch == remote_last)
        sev = vmod.emit_session_startup(
            branch=branch,
            remote_last=remote_last or None,
            on_remote_last="yes" if on_tip else "no",
            phase="session-end",
            source="session-end",
            ledger_path=ledger,
            root=ROOT,
            extra={
                "dirty": dirty,
                "summary": (summary or "")[:200],
                "next_action": "/chain session-start",
            },
        )
        out["session_startup"] = (sev or {}).get("content_hash")
    except Exception as exc:
        out["errors"].append(f"session_startup: {exc}")

    return out


def write_checkpoint(summary: str, snap: dict, when: str) -> Path:
    d = ROOT / "reports" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    # filename-safe
    stamp = when.replace(":", "").replace("+00:00", "Z")
    path = d / f"pause-{stamp}.md"
    body = f"""# Session pause — {when}

**Not EOD.** Mid-session checkpoint for later resume the same day (or after a break).

| Field | Value |
|-------|--------|
| Branch | `{snap.get("branch")}` |
| Dirty WIP | {"yes" if snap.get("dirty") else "no"} ({snap.get("porcelain_lines")} paths) |
| HEAD | `{snap.get("head")}` |
| Summary | {summary or "—"} |

## Resume

```text
/chain session-start
```

Stay on branch `{snap.get("branch")}` unless the briefing offers a better resume branch.

## WIP sample (if dirty)

```
"""
    for line in snap.get("porcelain_sample") or []:
        body += line + "\n"
    if not snap.get("porcelain_sample"):
        body += "(clean)\n"
    body += "```\n"
    path.write_text(body, encoding="utf-8")
    return path


def publish_pause_to_github(when_date: str, branch: str) -> dict:
    """Commit pause card + vault pointer and push so other machines can resume.

    Remaining dirty WIP stays local (stash is machine-only). Unpushed branch
    means GitHub has no prior session for the other laptop.
    """
    out: dict = {"committed": False, "pushed": False, "error": None, "paths": []}
    paths = [
        f"reports/sessions/resume-{when_date}.md",
        "reports/sessions/resume-latest.md",
        "reports/sessions/resume-session-end-latest.md",
        "reports/vault/events.jsonl",
    ]
    existing = [p for p in paths if (ROOT / p).is_file()]
    out["paths"] = existing
    if existing:
        _run(["git", "add", "--", *existing])
        code, cout, err = _run(
            [
                "git",
                "commit",
                "-m",
                "chore(session-end): pause card for other machines",
            ]
        )
        blob = f"{cout}\n{err}".lower()
        if code == 0:
            out["committed"] = True
        elif "nothing to commit" not in blob:
            out["error"] = (err or cout)[:240]
    code, outp, err = _run(["git", "push", "-u", "origin", "HEAD"])
    if code == 0:
        out["pushed"] = True
    else:
        msg = (err or outp or "git push failed")[:240]
        out["error"] = ((out.get("error") or "") + " " + msg).strip()
        out["unpushed"] = True
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", default="", help="What you were doing / next step")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-vault", action="store_true", help="Skip vault pointer/lesson")
    ap.add_argument("--no-todo", action="store_true", help="Skip TODO resume block")
    ap.add_argument(
        "--no-push",
        action="store_true",
        help="Do not commit/push pause card (other machines will not see this session)",
    )
    args = ap.parse_args()

    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    snap = git_snapshot()
    summary = (args.summary or "").strip()

    checkpoint = write_checkpoint(summary, snap, when)
    resume_card: dict | None = None
    resume_script = ROOT / "scripts" / "session-resume-brief.py"
    if resume_script.is_file():
        when_date = when[:10] if len(when) >= 10 else when
        cmd = [
            sys.executable,
            str(resume_script),
            "write",
            "--date",
            when_date,
            "--rich",
            "--source",
            "session-end",
            "--json",
        ]
        if summary:
            cmd.extend(["--summary", summary])
        code, stdout, _ = _run(cmd, timeout=90)
        if code == 0 and stdout:
            try:
                resume_card = json.loads(stdout)
            except json.JSONDecodeError:
                resume_card = {"error": "invalid json from session-resume-brief"}
    todo = None if args.no_todo else latest_todo()
    if todo and not args.no_todo:
        append_todo_resume(todo, snap["branch"], when, summary)

    vault = {"skipped": True}
    if not args.no_vault:
        vault = vault_pause_emit(summary, snap["branch"], bool(snap["dirty"]))

    github = {"skipped": True}
    if not args.no_push:
        github = publish_pause_to_github(when[:10] if len(when) >= 10 else when, snap["branch"])

    result = {
        "status": "paused",
        "when": when,
        "checkpoint": str(checkpoint.relative_to(ROOT)),
        "branch": snap["branch"],
        "dirty": snap["dirty"],
        "porcelain_lines": snap["porcelain_lines"],
        "todo_updated": str(todo) if todo and not args.no_todo else None,
        "vault": vault,
        "resume": "/chain session-resume",
        "resume_card": resume_card,
        "github": github,
        "note": "This is NOT eod-shutdown — no clean-git force, no ddev stop, no tomorrow TODO.",
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Session end (mid-day pause) — NOT full EOD")
        print(f"  branch:     {snap['branch']}")
        print(
            f"  WIP:        {'DIRTY — left as-is (' + str(snap['porcelain_lines']) + ' paths)' if snap['dirty'] else 'clean'}"
        )
        print(f"  checkpoint: {result['checkpoint']}")
        if resume_card and resume_card.get("path"):
            print(f"  resume:     {resume_card['path']}")
            print()
            print(resume_card.get("card") or "")
            print()
        if result["todo_updated"]:
            print(f"  TODO:       resume note appended → {Path(result['todo_updated']).name}")
        if not args.no_vault:
            if vault.get("lesson"):
                print(f"  vault:      pause lesson {(vault.get('lesson') or '')[:16]}")
            if vault.get("pointer"):
                print(f"  pointer:    {vault.get('pointer')}")
            for e in vault.get("errors") or []:
                print(f"  vault note: {e}")
        print()
        # Same-day return: /chain session-resume (not full session-start)
        reminder = (resume_card or {}).get("next_start_reminder") if resume_card else None
        if reminder:
            print(reminder)
        else:
            print("=== NEXT: SESSION-RESUME (same day, prior session) ===")
            print("Chronological order — do not skip steps:")
            print("  1. git fetch origin --prune")
            print("  2. Checkout this pause Branch (the session you just left)")
            print("  3. Load this session-end card")
            print("  4. Security sweep → lean work")
            print("  Command: /chain session-resume")
            print("  Do NOT switch to remote_last. Do NOT run /chain session-start.")
            print("=== end next-open reminder ===")
        print()
        print("Resume later (same day):")
        print("  /chain session-resume  (lands on this Branch — prior session)")
        print("  /chain session-start only after eod-shutdown or a new calendar day")
        print("  (do not run eod-shutdown unless you are done for the day)")
        gh = result.get("github") or {}
        if gh.get("pushed"):
            print("  github:     pause card pushed — other machines can session-resume this Branch")
        elif not args.no_push:
            print(
                "  github:     NOT pushed — other machines cannot see this pause "
                f"({gh.get('error') or 'no origin'})"
            )
        if snap["dirty"]:
            print(
                "  WIP:        uncommitted files stay on THIS machine only "
                "(stash/dirty never reach GitHub)."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

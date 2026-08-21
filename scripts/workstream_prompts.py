#!/usr/bin/env python3
"""Operator prompts + recommendations for multi-workstream (merge-ready, next steps).

Surfaces what is going on without merging. Never push/merge/force-push.

Slash:
  /multi-workstream prompts
  /multi-workstream ready
  /multi-workstream status

Exit: 0 always (report-only) unless --strict and a FAIL-level integrity issue.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports" / "sessions" / "workstreams.yaml"
PROTECTED = frozenset({"master", "main", "develop", "staging", "production", "prod"})


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    r = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def _streams(data: dict) -> list[dict]:
    return list(data.get("workstreams") or [])


def _cwd_for_ws(ws: dict) -> Path:
    wtp = ws.get("worktree")
    if wtp and Path(str(wtp)).is_dir():
        return Path(str(wtp))
    return ROOT


def _branch_ahead_behind(branch: str, base: str = "origin/develop") -> dict:
    if not branch:
        return {"ok": False, "ahead": 0, "behind": 0, "note": "no branch"}
    code, _, _ = _run(["git", "rev-parse", "--verify", branch])
    if code != 0:
        code2, _, _ = _run(["git", "rev-parse", "--verify", f"origin/{branch}"])
        if code2 != 0:
            return {"ok": False, "ahead": 0, "behind": 0, "note": "branch missing"}
        branch_ref = f"origin/{branch}"
    else:
        branch_ref = branch
    code_b, _, _ = _run(["git", "rev-parse", "--verify", base])
    if code_b != 0:
        base = "origin/master"
        code_b, _, _ = _run(["git", "rev-parse", "--verify", base])
        if code_b != 0:
            return {"ok": True, "ahead": 0, "behind": 0, "note": "no develop/master base"}
    code, out, _ = _run(["git", "rev-list", "--left-right", "--count", f"{base}...{branch_ref}"])
    if code != 0 or not out:
        return {"ok": False, "ahead": 0, "behind": 0, "note": "rev-list failed"}
    parts = out.split()
    if len(parts) != 2:
        return {"ok": False, "ahead": 0, "behind": 0, "note": f"bad rev-list: {out}"}
    # left = commits on base not in branch (behind), right = commits on branch not in base (ahead)
    behind, ahead = int(parts[0]), int(parts[1])
    return {"ok": True, "ahead": ahead, "behind": behind, "base": base, "note": "ok"}


def _dirty(cwd: Path) -> bool:
    code, out, _ = _run(["git", "status", "--porcelain"], cwd=cwd)
    return bool(out.strip()) if code == 0 else False


def _gh_pr(branch: str) -> dict | None:
    if not branch:
        return None
    code, out, _ = _run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--json",
            "number,url,state,title,mergeable,statusCheckRollup",
            "--limit",
            "1",
        ]
    )
    if code != 0 or not out:
        return None
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        return None
    return rows[0] if rows else None


def _assess(ws: dict, *, index: int, primary: str) -> dict:
    wid = str(ws.get("id") or "")
    status = str(ws.get("status") or "")
    branch = str(ws.get("branch") or "")
    nxt = str(ws.get("next") or "")
    cwd = _cwd_for_ws(ws)
    dirty = _dirty(cwd)
    ab = _branch_ahead_behind(branch)
    pr = _gh_pr(branch) if branch and branch not in PROTECTED else None

    prompts: list[str] = []
    recs: list[str] = []
    merge_ready = False
    phase = "idle"

    if status in {"parked", "done"}:
        phase = status
        prompts.append(f"#{index} {wid} is {status} — not in active work set.")
        if status == "parked":
            recs.append(f"Unpark only if intentional: /multi-workstream activate {index}")
    elif status in {"held", "held_ready"}:
        phase = status
        prompts.append(f"#{index} {wid} is {status} — frozen until you unhold.")
        recs.append(f"To open: /multi-workstream activate {index}")
        recs.append("Do not merge held tracks.")
    elif status == "active":
        phase = "active"
        if wid == primary:
            prompts.append(f"#{index} {wid} is PRIMARY focus — do serial work here first.")
        else:
            prompts.append(f"#{index} {wid} is active but not primary.")
            recs.append(f"Focus when ready: /multi-workstream focus {index}")

        if not branch:
            prompts.append(f"#{index} has no branch — set branch before merge talk.")
            recs.append(f"/multi-workstream note {index} --next \"set feature branch\"")
        elif branch in PROTECTED:
            prompts.append(f"#{index} points at protected branch `{branch}` — STOP.")
            recs.append("Point workstream at a feature/* branch; never merge from multi-workstream.")
        elif dirty:
            phase = "wip"
            prompts.append(
                f"#{index} has **uncommitted work** in {cwd if cwd != ROOT else 'main tree'}."
            )
            recs.append("Commit or stash before PR/merge readiness.")
            if nxt:
                recs.append(f"Next note: {nxt}")
        elif ab.get("ok") and ab.get("ahead", 0) == 0:
            phase = "no_commits"
            prompts.append(f"#{index} branch `{branch}` has **0 commits** ahead of {ab.get('base', 'base')}.")
            recs.append("Do the work, commit, then re-run /multi-workstream prompts.")
        elif ab.get("ok") and ab.get("behind", 0) > 0:
            phase = "needs_rebase"
            prompts.append(
                f"#{index} is **{ab['behind']} behind** {ab.get('base')} "
                f"(and {ab.get('ahead', 0)} ahead)."
            )
            recs.append("Rebase/merge develop into the feature branch before PR (manual git).")
            recs.append("Then: /multi-workstream prompts")
        elif pr:
            st = pr.get("state") or ""
            url = pr.get("url") or ""
            mergeable = pr.get("mergeable")
            checks = pr.get("statusCheckRollup") or []
            failing = [
                c
                for c in checks
                if isinstance(c, dict) and (c.get("conclusion") or "").upper() in {"FAILURE", "CANCELLED", "TIMED_OUT"}
            ]
            pending = [
                c
                for c in checks
                if isinstance(c, dict) and (c.get("state") or "").upper() in {"PENDING", "QUEUED", "IN_PROGRESS"}
            ]
            if st == "MERGED":
                phase = "merged"
                prompts.append(f"#{index} PR already **MERGED**: {url}")
                recs.append(f"/multi-workstream hold {index} --ready  # or park when done")
                recs.append("Focus next active track: /multi-workstream list")
            elif st == "OPEN" and failing:
                phase = "pr_failing"
                prompts.append(f"#{index} PR **open but checks failing**: {url}")
                recs.append("Fix CI on the feature branch; do not merge.")
            elif st == "OPEN" and pending:
                phase = "pr_pending"
                prompts.append(f"#{index} PR **open, checks still running**: {url}")
                recs.append("Wait for green CI, then merge via GitHub UI/gh (not multi-workstream).")
            elif st == "OPEN" and (mergeable is True or mergeable == "MERGEABLE" or mergeable is None):
                phase = "merge_ready"
                merge_ready = True
                prompts.append(
                    f"#{index} **READY TO MERGE?** PR open and looks mergeable: {url}"
                )
                recs.append(
                    f"Review PR #{pr.get('number')}, then: gh pr merge {pr.get('number')} --merge"
                )
                recs.append("After merge: /multi-workstream hold {0} --ready && /multi-workstream focus <next>".format(index))
                recs.append("SAFEGUARD: multi-workstream will not merge for you.")
            elif st == "OPEN":
                phase = "pr_open"
                prompts.append(f"#{index} PR open (mergeable={mergeable}): {url}")
                recs.append("Resolve conflicts or wait for checks; merge only when green.")
            else:
                phase = "pr_other"
                prompts.append(f"#{index} PR state={st}: {url}")
        elif ab.get("ok") and ab.get("ahead", 0) > 0:
            phase = "ready_for_pr"
            merge_ready = False
            prompts.append(
                f"#{index} has **{ab['ahead']} commit(s)** ahead of {ab.get('base')} "
                f"and **no open PR** — ready to open a PR when you are."
            )
            recs.append(
                f"gh pr create --base develop --head {branch} --title \"…\" --body \"…\""
            )
            recs.append("Or promote via existing branch-promotion workflow.")
            recs.append("Then re-run: /multi-workstream prompts")
            recs.append("SAFEGUARD: do not push to develop/master directly.")
        else:
            phase = "unknown"
            prompts.append(f"#{index} {wid}: could not fully assess ({ab.get('note')}).")
            recs.append("Check branch exists and origin/develop is fetched.")

    return {
        "n": index,
        "id": wid,
        "status": status,
        "branch": branch,
        "primary": wid == primary,
        "phase": phase,
        "merge_ready": merge_ready,
        "dirty": dirty,
        "ahead": ab.get("ahead", 0),
        "behind": ab.get("behind", 0),
        "base": ab.get("base"),
        "worktree": str(cwd) if cwd != ROOT else None,
        "pr": (
            {
                "number": pr.get("number"),
                "url": pr.get("url"),
                "state": pr.get("state"),
                "mergeable": pr.get("mergeable"),
            }
            if pr
            else None
        ),
        "prompts": prompts,
        "recommendations": recs,
    }


def build_report(data: dict) -> dict:
    primary = str(data.get("primary") or "")
    rows = []
    for i, ws in enumerate(_streams(data), start=1):
        rows.append(_assess(ws, index=i, primary=primary))
    merge_ready = [r for r in rows if r.get("merge_ready")]
    ready_for_pr = [r for r in rows if r.get("phase") == "ready_for_pr"]
    wip = [r for r in rows if r.get("phase") == "wip"]
    frozen = [r for r in rows if r.get("status") in {"held", "held_ready", "parked"}]
    return {
        "primary": primary,
        "streams": rows,
        "summary": {
            "merge_ready": len(merge_ready),
            "ready_for_pr": len(ready_for_pr),
            "wip": len(wip),
            "frozen": len(frozen),
            "total": len(rows),
        },
        "headline_prompts": _headlines(rows, primary),
    }


def _headlines(rows: list[dict], primary: str) -> list[str]:
    lines = []
    for r in rows:
        if r.get("merge_ready"):
            lines.append(
                f"ACTION: #{r['n']} `{r['id']}` looks **merge-ready** — review PR then merge via gh/UI."
            )
        elif r.get("phase") == "ready_for_pr":
            lines.append(
                f"ACTION: #{r['n']} `{r['id']}` has commits and **no PR** — open PR when ready."
            )
        elif r.get("phase") == "pr_failing":
            lines.append(f"ACTION: #{r['n']} `{r['id']}` PR checks **failing** — fix CI.")
        elif r.get("phase") == "wip" and r.get("primary"):
            lines.append(f"FOCUS: #{r['n']} `{r['id']}` is primary with **uncommitted** work.")
        elif r.get("primary") and r.get("phase") == "active":
            lines.append(f"FOCUS: #{r['n']} `{r['id']}` is primary — continue work or prepare PR.")
    if not lines:
        lines.append("No merge prompts right now — continue primary or activate a held track.")
    lines.append("SAFEGUARD: multi-workstream never merges to develop/staging/master for you.")
    return lines


def format_text(report: dict) -> str:
    lines = [
        "MULTI-WORKSTREAM prompts · auto_merge=no · report-only",
        f"primary={report.get('primary') or 'none'}",
        (
            f"summary: merge_ready={report['summary']['merge_ready']} "
            f"ready_for_pr={report['summary']['ready_for_pr']} "
            f"wip={report['summary']['wip']} "
            f"frozen={report['summary']['frozen']} "
            f"total={report['summary']['total']}"
        ),
        "",
        "## What is going on",
    ]
    for h in report.get("headline_prompts") or []:
        lines.append(f"- {h}")
    lines.append("")
    lines.append("## Per stream")
    for r in report.get("streams") or []:
        star = "*" if r.get("primary") else " "
        lines.append(
            f"{star}#{r['n']} {r['id']}  status={r['status']}  phase={r['phase']}  "
            f"branch={r.get('branch') or '—'}  "
            f"ahead={r.get('ahead')} behind={r.get('behind')}"
        )
        for p in r.get("prompts") or []:
            lines.append(f"    prompt: {p}")
        for rec in r.get("recommendations") or []:
            lines.append(f"    → {rec}")
        if r.get("pr"):
            lines.append(f"    pr: {r['pr'].get('url')} ({r['pr'].get('state')})")
    lines.append("")
    lines.append("## Operator next")
    lines.append("1. Act on ACTION/FOCUS lines above")
    lines.append("2. Re-run /multi-workstream prompts after commits or PR changes")
    lines.append("3. Merge only via GitHub/gh when checks green — not via multi-workstream")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    try:
        import yaml
    except ImportError:
        print("PyYAML required", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description="Multi-workstream operator prompts")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY,
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "examples" / "agent-graphs" / "prompts-latest.md",
    )
    args = ap.parse_args(argv)

    if not args.registry.is_file():
        print(f"missing registry: {args.registry}", file=sys.stderr)
        return 2
    data = yaml.safe_load(args.registry.read_text(encoding="utf-8")) or {}
    report = build_report(data)
    text = format_text(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text + "\n", encoding="utf-8")
    (args.out.with_suffix(".json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(text)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

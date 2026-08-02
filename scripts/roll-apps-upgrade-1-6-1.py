#!/usr/bin/env python3
"""Per-app orchestrator upgrade to template 1.6.1 (no fleet wave).

Usage (from orchestrator repo root):
  python3 scripts/roll-apps-upgrade-1-6-1.py --dry-run
  python3 scripts/roll-apps-upgrade-1-6-1.py --apply

Policy:
  - One app at a time via orchestrator_cli upgrade (skip customized).
  - Dirty trees skipped (except lightstone single .grok/config.toml → stash/pop).
  - Apps with .grok but no lock get a temporary lock at 1.5.0 so upgrade (skip)
    can run instead of destructive init overwrite.
  - Never sets ORCHESTRATOR_WAVE_DEPLOY_APPROVED.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ORCH = Path(__file__).resolve().parents[1]
PROJECTS = Path.home() / "projects"
APPS = [
    "ndestates-io",
    "e-ndsign",
    "jerseyhouseprices",
    "lightstone",
    "mailchimp",
    "facebook-stats",
    "google-stats",
    "ndestates",
]
# lightstone only: known single-file dirty allowed for stash
STASHABLE = {
    "lightstone": [".grok/config.toml"],
}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or ORCH),
        capture_output=True,
        text=True,
        check=False,
    )


def git_porcelain(app: Path) -> list[str]:
    p = run(["git", "status", "--porcelain"], cwd=app)
    return [ln for ln in (p.stdout or "").splitlines() if ln.strip()]


def git_branch(app: Path) -> str:
    p = run(["git", "branch", "--show-current"], cwd=app)
    return (p.stdout or "").strip() or "?"


def read_lock(app: Path) -> dict | None:
    p = app / ".orchestrator-version"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def backfill_lock(app: Path) -> None:
    """Write a skip-safe lock so upgrade path is used (not init overwrite)."""
    data = {
        "version": "1.5.0",
        "release_tag": "v1.5.0",
        "profile": None,
        "cli_version": "lock-backfill",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "note": "backfilled so orchestrator upgrade (skip) can run; was .grok without lock",
    }
    (app / ".orchestrator-version").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


def porcelain_paths(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        # " M path" or "?? path" or "M  path"
        path = ln[3:].strip() if len(ln) > 3 else ln.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[-1]
        out.append(path)
    return out


def try_stash(app: Path, slug: str) -> str | None:
    allowed = STASHABLE.get(slug)
    if not allowed:
        return None
    dirty = porcelain_paths(git_porcelain(app))
    if not dirty:
        return None
    if set(dirty) - set(allowed):
        return None
    msg = f"orchestrator-roll-1.6.1 auto-stash {slug}"
    p = run(["git", "stash", "push", "-u", "-m", msg, "--"] + allowed, cwd=app)
    if p.returncode != 0:
        return None
    return msg


def stash_pop(app: Path) -> None:
    run(["git", "stash", "pop"], cwd=app)


def upgrade(app: Path, *, dry_run: bool, verify_bundle: bool) -> tuple[int, str]:
    env_cmd = [
        sys.executable,
        "-m",
        "orchestrator_cli",
        "upgrade",
        str(app),
        "--no-pr",
    ]
    if dry_run:
        env_cmd.append("--dry-run")
    if verify_bundle:
        env_cmd.append("--verify-bundle")
    # Inherit PYTHONPATH via env
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ORCH / 'src'}:{ORCH / 'scripts'}:{env.get('PYTHONPATH', '')}"
    p = subprocess.run(
        env_cmd,
        cwd=str(ORCH),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return p.returncode, out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify-bundle", action="store_true")
    ap.add_argument("--only", nargs="*", help="subset of app slugs")
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run and/or --apply", file=sys.stderr)
        return 2

    apps = args.only or APPS
    results: list[dict] = []

    print(f"Source: {ORCH} @ {run(['git', 'rev-parse', '--short', 'HEAD']).stdout.strip()}")
    print(f"Template: {(ORCH / 'VERSION').read_text().strip()}")
    print(f"Mode: {'dry-run' if args.dry_run and not args.apply else 'apply'}")
    print()

    for slug in apps:
        app = PROJECTS / slug
        row: dict = {"app": slug, "path": str(app)}
        if not app.is_dir():
            row["status"] = "missing"
            results.append(row)
            print(f"SKIP {slug}: missing")
            continue

        branch = git_branch(app)
        dirty = git_porcelain(app)
        lock = read_lock(app)
        row["branch"] = branch
        row["dirty_count"] = len(dirty)
        row["lock"] = (lock or {}).get("version")

        stashed = False
        if dirty:
            msg = try_stash(app, slug)
            if msg:
                stashed = True
                dirty = git_porcelain(app)
                row["stashed"] = True
            else:
                row["status"] = "skip_dirty"
                row["dirty_sample"] = porcelain_paths(dirty)[:8]
                results.append(row)
                print(f"SKIP {slug}: dirty ({len(dirty)} paths) branch={branch}")
                continue

        if not (app / ".grok").is_dir() and lock is None:
            row["status"] = "skip_no_template"
            results.append(row)
            print(f"SKIP {slug}: no .grok and no lock")
            continue

        if lock is None:
            if args.apply or args.dry_run:
                # On dry-run still note; on apply write lock before real upgrade only
                if args.apply and not args.dry_run:
                    backfill_lock(app)
                    row["lock_backfill"] = "1.5.0"
                elif args.apply:
                    backfill_lock(app)
                    row["lock_backfill"] = "1.5.0"
                else:
                    row["lock_backfill_planned"] = "1.5.0"
            # For dry-run without lock, plant temp lock for accurate dry-run then restore?
            if args.dry_run and not args.apply:
                had = (app / ".orchestrator-version").is_file()
                if not had:
                    backfill_lock(app)
                    row["lock_backfill_temp"] = True

        # If only dry-run after temp backfill, or apply
        if args.dry_run:
            code, out = upgrade(app, dry_run=True, verify_bundle=args.verify_bundle)
            row["dry_run_exit"] = code
            row["dry_run_tail"] = out[-800:] if out else ""
            print(f"DRY  {slug}: exit={code} branch={branch} lock={row.get('lock')}")
            if code != 0:
                print(f"     {out[:400]}")
            # Remove temp lock if we added only for dry-run
            if row.get("lock_backfill_temp") and not args.apply:
                try:
                    (app / ".orchestrator-version").unlink(missing_ok=True)
                except OSError:
                    pass

        if args.apply:
            # Ensure lock for upgrade path
            if read_lock(app) is None:
                backfill_lock(app)
                row["lock_backfill"] = "1.5.0"
            code, out = upgrade(app, dry_run=False, verify_bundle=args.verify_bundle)
            row["apply_exit"] = code
            row["apply_tail"] = out[-1200:] if out else ""
            new_lock = read_lock(app)
            row["lock_after"] = (new_lock or {}).get("version")
            row["branch_after"] = git_branch(app)
            status = "ok" if code == 0 else "fail"
            row["status"] = status
            print(
                f"APPLY {slug}: exit={code} → lock={row.get('lock_after')} "
                f"branch={row.get('branch_after')}"
            )
            if code != 0:
                print(f"     {out[:600]}")
        else:
            row["status"] = row.get("status") or "dry_only"

        if stashed:
            stash_pop(app)
            row["stash_popped"] = True

        results.append(row)

    out_path = ORCH / "reports" / "deploys" / f"roll-1.6.1-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport: {out_path}")

    fails = [r for r in results if r.get("apply_exit") not in (None, 0)]
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

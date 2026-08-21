#!/usr/bin/env python3
"""Per-operator workspace branch pointer in the vault brain.

Emit at EOD (after clean push) so session-start on another machine can resume
*this user's* last branch — not just repo-wide remote-last.

Usage:
  python3 scripts/vault-workspace-pointer.py --emit
  python3 scripts/vault-workspace-pointer.py --read --format shell
  python3 scripts/vault-workspace-pointer.py --read --format json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts._engine import vault as vmod  # noqa: E402

DEFAULT_LEDGER = Path("reports/vault/events.jsonl")


def _git_branch(root: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def _parse_resume_branch_kv(stdout: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k] = v
    return data


def _remote_last_from_git(root: Path) -> tuple[str, str]:
    """Lightweight remote-last without calling resume-branch (avoid recursion)."""
    try:
        subprocess.run(["git", "fetch", "origin", "--prune"], cwd=root, capture_output=True, timeout=30)
        r = subprocess.run(
            [
                "git",
                "for-each-ref",
                "refs/remotes/origin/",
                "--sort=-committerdate",
                "--format=%(refname:short)|%(subject)",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in r.stdout.splitlines():
            if not line or "origin/HEAD" in line:
                continue
            if line.endswith("/develop") or line.endswith("/master"):
                continue
            ref, _, subject = line.partition("|")
            return ref.removeprefix("origin/"), subject
    except Exception:
        pass
    return "", ""


def _branch_on_origin(root: Path, branch: str) -> bool:
    if not branch:
        return False
    try:
        r = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
            cwd=root,
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def cmd_emit(args: argparse.Namespace) -> int:
    root = Path(args.root or ".").resolve()
    branch = args.branch or _git_branch(root)
    if not branch:
        print("vault-workspace-pointer: no current branch; skip emit.", file=sys.stderr)
        return 1

    remote_last, subject = _remote_last_from_git(root)
    on_tip = bool(remote_last and branch == remote_last)
    ev = vmod.emit_workspace_pointer(
        branch,
        operator=args.operator,
        remote_last=remote_last or None,
        subject=subject or args.subject,
        source=args.source,
        ledger_path=Path(args.ledger),
        root=root,
        startup_policy=vmod.SESSION_STARTUP_POLICY,
        next_start_order=vmod.SESSION_STARTUP_ORDER,
        on_team_tip=on_tip,
    )
    if args.json:
        print(json.dumps({"status": "emitted", "event": ev}, indent=2, default=str))
    else:
        print(f"vault-workspace-pointer: emitted for {ev['payload']['operator']} -> {branch}")
        print(f"  id: {ev.get('id')}")
        print(f"  startup_policy: {ev['payload'].get('startup_policy')}")
        print(f"  on_team_tip: {ev['payload'].get('on_team_tip_at_emit')}")
        print(f"  remote_last: {remote_last or 'none'}")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    root = Path(args.root or ".").resolve()
    ledger = Path(args.ledger)
    op = args.operator or vmod._git_operator_email(root)
    ptr = vmod.get_operator_workspace_pointer(ledger, operator=op, root=root)

    if not ptr:
        if args.format == "json":
            print(json.dumps({"status": "none", "operator": op}))
        else:
            print(f"operator={op}")
            print("operator_last_branch=")
            print("operator_pointer_found=no")
        return 0

    payload = ptr.get("payload") or {}
    branch = payload.get("branch", "")
    out = {
        "status": "ok",
        "operator": op,
        "operator_last_branch": branch,
        "operator_last_ts": ptr.get("ts", ""),
        "operator_pointer_found": "yes",
        "operator_branch_on_origin": "yes" if _branch_on_origin(root, branch) else "no",
        "operator_subject": payload.get("subject", ""),
        "startup_policy": payload.get("startup_policy") or vmod.SESSION_STARTUP_POLICY,
        "next_start_order": payload.get("next_start_order") or vmod.SESSION_STARTUP_ORDER,
        "on_team_tip_at_emit": payload.get("on_team_tip_at_emit"),
        "remote_last_at_emit": payload.get("remote_last_at_emit", ""),
    }

    if args.format == "json":
        print(json.dumps(out, indent=2, default=str))
        return 0

    for k, v in out.items():
        if k == "status":
            continue
        print(f"{k}={v}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-operator vault workspace branch pointer")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--root", default=".")
    parser.add_argument("--operator", help="Override git user.email")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--emit", action="store_true", help="Record current branch for this operator")
    parser.add_argument("--read", action="store_true", help="Read latest pointer for this operator")
    parser.add_argument("--format", choices=("shell", "json"), default="shell")
    parser.add_argument("--branch", help="Branch to emit (default: current)")
    parser.add_argument("--subject", help="Optional commit subject at emit time")
    parser.add_argument("--source", default="eod-shutdown")
    args = parser.parse_args()

    if args.emit and args.read:
        print("Use --emit or --read, not both.", file=sys.stderr)
        return 1
    if not args.emit and not args.read:
        parser.error("one of --emit or --read is required")

    if args.emit:
        return cmd_emit(args)
    return cmd_read(args)


if __name__ == "__main__":
    raise SystemExit(main())
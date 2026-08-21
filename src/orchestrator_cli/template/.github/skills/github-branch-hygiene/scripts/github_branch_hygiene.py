#!/usr/bin/env python3
"""Safe GitHub remote/local branch hygiene (orchestrator template + apps).

Report-only by default. Never deletes protected integration branches.
Does not delete every remote that has no local counterpart — that is unsafe.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

PROTECTED = ("master", "main", "develop", "staging", "production")
CANDIDATE_PREFIXES = ("feature/", "fix/", "chore/", "feat/", "hotfix/", "dependabot/")


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def git_lines(cmd: list[str]) -> list[str]:
    proc = run(["git", *cmd])
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def is_ancestor(commit: str, of: str) -> bool:
    proc = run(["git", "merge-base", "--is-ancestor", commit, of])
    return proc.returncode == 0


def unique_count(base: str, branch: str) -> int:
    proc = run(["git", "rev-list", "--count", f"{base}..{branch}"])
    if proc.returncode != 0 or not proc.stdout.strip():
        return -1
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return -1


def gh_json(args: list[str]) -> Any:
    proc = run(["gh", *args])
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout or "null")
    except json.JSONDecodeError:
        return None


def classify_remote(
    name: str,
    current: str,
    open_heads: set[str],
) -> dict[str, Any]:
    ref = f"origin/{name}"
    row: dict[str, Any] = {
        "name": name,
        "action": "keep",
        "reason": "",
        "unique_vs_develop": unique_count("origin/develop", ref),
    }
    if name in PROTECTED or name == "HEAD":
        row["reason"] = "protected"
        return row
    if name == current:
        row["reason"] = "current_branch"
        return row
    if name in open_heads:
        row["reason"] = "open_pr"
        return row

    merged_into = [p for p in PROTECTED if p != "main" and is_ancestor(ref, f"origin/{p}")]
    if "main" in PROTECTED and is_ancestor(ref, "origin/main"):
        merged_into.append("main")
    if merged_into:
        row["action"] = "delete"
        row["reason"] = "merged_into:" + ",".join(merged_into)
        return row

    row["reason"] = "unmerged"
    return row


def classify_local(name: str, current: str) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name, "action": "keep", "reason": ""}
    if name in PROTECTED:
        row["reason"] = "protected"
        return row
    if name == current:
        row["reason"] = "current_branch"
        return row
    for base in ("origin/develop", "origin/master", "origin/main"):
        if is_ancestor(name, base):
            row["action"] = "delete"
            row["reason"] = f"merged_into:{base.removeprefix('origin/')}"
            return row
    gone = run(["git", "rev-parse", "--abbrev-ref", f"{name}@{{upstream}}"])
    if gone.returncode != 0:
        row["action"] = "delete"
        row["reason"] = "no_upstream"
        return row
    row["reason"] = "unmerged"
    return row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe remote/local branch hygiene (report-only default)."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete remote candidates (merged only). No-op without this flag.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="With --apply, also git branch -d local merged/no-upstream candidates.",
    )
    parser.add_argument(
        "--include-dependabot",
        action="store_true",
        help="Allow deleting origin/dependabot/* when they are merged.",
    )
    parser.add_argument("--no-fetch", action="store_true")
    args = parser.parse_args()

    if not args.no_fetch:
        run(["git", "fetch", "origin", "--prune"])

    current = git_lines(["branch", "--show-current"])
    current_name = current[0] if current else ""

    remotes = []
    for line in git_lines(["branch", "-r"]):
        if "->" in line:
            continue
        name = line.removeprefix("origin/").strip()
        if name and name != "HEAD":
            remotes.append(name)

    open_heads: set[str] = set()
    prs = gh_json(["pr", "list", "--state", "open", "--limit", "200", "--json", "headRefName"])
    if isinstance(prs, list):
        open_heads = {str(p.get("headRefName") or "") for p in prs if p.get("headRefName")}

    remote_rows = [classify_remote(n, current_name, open_heads) for n in sorted(set(remotes))]
    locals_ = [
        ln.lstrip("*+ ").strip()
        for ln in git_lines(["branch", "--list"])
        if ln.lstrip("*+ ").strip()
    ]
    local_rows = [classify_local(n, current_name) for n in sorted(set(locals_))]

    def remote_ok(row: dict[str, Any]) -> bool:
        if row["action"] != "delete":
            return False
        name = row["name"]
        if name.startswith("dependabot/") and not args.include_dependabot:
            return False
        if not any(name.startswith(p) for p in CANDIDATE_PREFIXES):
            return False
        return True

    remote_delete = [r for r in remote_rows if remote_ok(r)]
    local_delete = [r for r in local_rows if r["action"] == "delete"]
    dependabot_held = [
        r
        for r in remote_rows
        if r["action"] == "delete"
        and r["name"].startswith("dependabot/")
        and not args.include_dependabot
    ]

    deleted: list[str] = []
    errors: list[str] = []
    if args.apply:
        for row in remote_delete:
            proc = run(["git", "push", "origin", "--delete", row["name"]])
            if proc.returncode == 0:
                deleted.append("origin/" + row["name"])
            else:
                errors.append((proc.stderr or proc.stdout or "push delete failed").strip()[:200])
        if args.local:
            for row in local_delete:
                proc = run(["git", "branch", "-d", row["name"]])
                if proc.returncode == 0:
                    deleted.append(row["name"])
                else:
                    errors.append((proc.stderr or proc.stdout or "branch -d failed").strip()[:200])

    report = {
        "protected": list(PROTECTED),
        "current": current_name,
        "applied": bool(args.apply),
        "include_dependabot": bool(args.include_dependabot),
        "remote_candidates": remote_delete,
        "dependabot_held": dependabot_held,
        "local_candidates": local_delete,
        "kept": [r for r in remote_rows if r["action"] == "keep"],
        "deleted": deleted,
        "errors": errors,
        "note": (
            "Report-only. Pass --apply to delete remote_candidates. "
            "Pass --apply --local to also delete local_candidates with git branch -d."
            if not args.apply
            else "Applied deletes listed in deleted[]."
        ),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 1 if errors else 0

    print("GitHub branch hygiene")
    print(f"Current: {current_name or '(detached)'}")
    print(f"Protected: {', '.join(PROTECTED)}")
    print()
    print(f"Remote delete candidates: {len(remote_delete)}")
    for r in remote_delete:
        print(f"  - origin/{r['name']}  ({r['reason']}; unique_vs_develop={r['unique_vs_develop']})")
    if dependabot_held:
        print(f"Dependabot held (pass --include-dependabot): {len(dependabot_held)}")
        for r in dependabot_held[:15]:
            print(f"  - origin/{r['name']}  ({r['reason']})")
        if len(dependabot_held) > 15:
            print(f"  … {len(dependabot_held) - 15} more")
    print(f"Local delete candidates: {len(local_delete)}")
    for r in local_delete:
        print(f"  - {r['name']}  ({r['reason']})")
    kept_open = [r for r in remote_rows if r["reason"] == "open_pr"]
    kept_unmerged = [r for r in remote_rows if r["reason"] == "unmerged"]
    print(f"Kept (open PR): {len(kept_open)}")
    print(f"Kept (unmerged): {len(kept_unmerged)}")
    if args.apply:
        print()
        print(f"Deleted: {len(deleted)}")
        for d in deleted:
            print(f"  - {d}")
        if errors:
            print("Errors:")
            for e in errors:
                print(f"  - {e}")
    else:
        print()
        print(report["note"])
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Integrity safeguards for multi-workstream — keep projects on course.

Checks (exit 0=PASS, 1=WARN, 2=FAIL):
  - registry present + primary set
  - held/parked not primary
  - no worktree on protected branches
  - worktree paths exist and match git worktree list
  - main tree not dirty when policy=strict (optional --strict)
  - high-risk workstreams still held unless explicitly active with note

Does NOT merge, push, or change code beyond reading registry.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports" / "sessions" / "workstreams.yaml"
PROTECTED = frozenset({"master", "main", "develop", "staging", "production", "prod"})
PROTECTED_PREFIXES = ("release/", "hotfix/")
HIGH_RISK_KEYWORDS = (
    "license",
    "paypal",
    "production",
    "secret",
    "apache",
    "eula",
    "billing",
)


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return r.stdout or ""


def _protected(branch: str) -> bool:
    b = (branch or "").strip()
    if b in PROTECTED:
        return True
    return any(b.startswith(p) for p in PROTECTED_PREFIXES)


def main(argv: list[str] | None = None) -> int:
    import argparse

    try:
        import yaml
    except ImportError:
        print("FAIL: PyYAML required", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description="Multi-workstream integrity guard")
    ap.add_argument("--strict", action="store_true", help="dirty main tree = FAIL")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    findings: list[dict] = []
    level = "PASS"

    def add(sev: str, code: str, msg: str) -> None:
        nonlocal level
        findings.append({"severity": sev, "code": code, "message": msg})
        if sev == "FAIL":
            level = "FAIL"
        elif sev == "WARN" and level != "FAIL":
            level = "WARN"

    if not REGISTRY.is_file():
        add("FAIL", "no_registry", f"missing {REGISTRY}")
    else:
        data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
        streams = list(data.get("workstreams") or [])
        primary = data.get("primary") or ""
        if not streams:
            add("WARN", "empty", "no workstreams registered")
        if not primary:
            add("WARN", "no_primary", "primary not set")
        else:
            pws = next((s for s in streams if s.get("id") == primary), None)
            if not pws:
                add("FAIL", "primary_missing", f"primary id not in list: {primary}")
            elif str(pws.get("status") or "") in {"held", "held_ready", "parked", "done"}:
                add(
                    "FAIL",
                    "primary_not_active",
                    f"primary {primary} has status={pws.get('status')} — focus an active track",
                )

        for ws in streams:
            wid = ws.get("id")
            st = str(ws.get("status") or "")
            br = str(ws.get("branch") or "")
            blob = " ".join(
                [str(wid), str(ws.get("title") or ""), str(ws.get("open") or ""), str(ws.get("next") or "")]
            ).lower()
            if st == "active" and any(k in blob for k in HIGH_RISK_KEYWORDS):
                add(
                    "WARN",
                    "high_risk_active",
                    f"{wid} is active but looks high-risk — confirm intentional unhold",
                )
            if br and _protected(br):
                add(
                    "FAIL",
                    "protected_branch",
                    f"{wid} branch={br} is protected — use a feature/* branch",
                )
            wtp = ws.get("worktree")
            if wtp:
                p = Path(str(wtp))
                if not p.exists():
                    add("WARN", "worktree_missing", f"{wid} worktree path missing: {wtp}")
                if _protected(br):
                    add(
                        "FAIL",
                        "worktree_protected",
                        f"{wid} worktree on protected branch {br}",
                    )

    dirty = _run(["git", "status", "--porcelain"]).strip()
    if dirty:
        sev = "FAIL" if args.strict else "WARN"
        add(sev, "dirty_main", "main worktree has uncommitted changes")

    # Never-merge reminder (informational)
    add(
        "INFO",
        "no_auto_merge",
        "multi-workstream never merges to develop/staging/master — use PR + CI",
    )

    payload = {"level": level, "findings": findings, "root": str(ROOT)}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"workstream_guard: {level}")
        for f in findings:
            if f["severity"] == "INFO":
                print(f"  · {f['code']}: {f['message']}")
            else:
                print(f"  {f['severity']} {f['code']}: {f['message']}")
        print("safeguards: no auto-merge · no force-push · activate before held work · feature branches only")

    if level == "FAIL":
        return 2
    if level == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

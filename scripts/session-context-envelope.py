#!/usr/bin/env python3
"""Session context envelope — one spin-up brief for every AI platform.

Replaces multi-script dumps (resume check + runtime + identity + vault narrative)
with a fixed-size status envelope. Print compact by default.

Usage:
  python3 scripts/session-context-envelope.py              # compact (default)
  python3 scripts/session-context-envelope.py --json
  python3 scripts/session-context-envelope.py --compact --write
  python3 scripts/session-context-envelope.py --expand     # include expand_payload
  python3 scripts/session-context-envelope.py --with-security-run
  python3 scripts/session-context-envelope.py --write --no-apply   # report only, no branch switch

Default: auto-switch to remote_last when the working tree is clean
(resume-branch.sh --apply). Dirty trees block switch (never discard WIP).

Platforms (same command):
  .grok / .claude / .copilot / .github / .gemini / .cursor
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.session_envelope import (  # noqa: E402
    build_envelope,
    format_compact,
    write_envelope_files,
)


def project_root() -> Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except Exception:
        pass
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="Full JSON envelope")
    ap.add_argument(
        "--compact",
        action="store_true",
        help="Force compact text (default when not --json)",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help=f"Write reports/sessions/context-latest.{{json,txt}}",
    )
    ap.add_argument(
        "--expand",
        action="store_true",
        help="After compact, print expand_payload if expand≠none",
    )
    ap.add_argument(
        "--with-security-run",
        action="store_true",
        help="Run session-security-sweep.sh before reading status (slower)",
    )
    ap.add_argument(
        "--no-apply",
        action="store_true",
        help="Do not auto-switch to remote_last (report-only resume-branch)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Force auto-switch to remote_last when clean (default unless --no-apply)",
    )
    ap.add_argument("--root", type=Path, default=None)
    args = ap.parse_args(argv)

    root = (args.root or project_root()).resolve()
    apply_remote_last = not args.no_apply
    env = build_envelope(
        root,
        with_security_run=args.with_security_run,
        apply_remote_last=apply_remote_last,
    )

    # Always persist latest for cross-tool reuse (Claude/Copilot/Gemini/Cursor/Grok)
    written = write_envelope_files(root, env)
    env["ptrs"] = {**(env.get("ptrs") or {}), **{f"wrote_{k}": v for k, v in written.items()}}
    _ = args.write  # --write accepted for CLI symmetry; write is always on

    if args.json:
        print(json.dumps(env, indent=2, ensure_ascii=False))
        return 0

    sys.stdout.write(env.get("briefing_compact") or format_compact(env))
    if args.expand and (env.get("expand") or []) and env.get("expand") != ["none"]:
        payload = env.get("expand_payload") or {}
        if payload:
            print("--- expand ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

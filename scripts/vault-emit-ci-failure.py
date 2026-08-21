#!/usr/bin/env python3
"""Emit a CI failure (and optional fix link) into the vault graph (v1.5.0+).

Use from GitHub Actions on failure, or manually after a red build, so the next
session can find "this failed before" via vault query.

Usage:
  python3 scripts/vault-emit-ci-failure.py \\
    --workflow tooling-tests --job unit --conclusion failure \\
    --url https://github.com/org/repo/actions/runs/123 \\
    --log-snippet "AssertionError: …"

  python3 scripts/vault-emit-ci-failure.py --from-github-env
    # reads GITHUB_* env vars when run inside Actions

  python3 scripts/vault-emit-ci-failure.py --fix-summary "…" --solves-hash <hash>
    # link a later fix to a prior error event

Exit 0 on success, 1 on emit failure, 2 if skipped (not a failure).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
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


def from_github_env() -> dict:
    return {
        "workflow": os.environ.get("GITHUB_WORKFLOW") or "",
        "job": os.environ.get("GITHUB_JOB") or "",
        "run_id": os.environ.get("GITHUB_RUN_ID") or "",
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT") or "",
        "repository": os.environ.get("GITHUB_REPOSITORY") or "",
        "ref": os.environ.get("GITHUB_REF_NAME") or os.environ.get("GITHUB_REF") or "",
        "sha": (os.environ.get("GITHUB_SHA") or "")[:12],
        "actor": os.environ.get("GITHUB_ACTOR") or "",
        "server": os.environ.get("GITHUB_SERVER_URL") or "https://github.com",
        "conclusion": os.environ.get("VAULT_CI_CONCLUSION")
        or os.environ.get("JOB_STATUS")
        or "failure",
    }


def build_url(meta: dict) -> str:
    if meta.get("url"):
        return str(meta["url"])
    repo = meta.get("repository") or ""
    run_id = meta.get("run_id") or ""
    server = (meta.get("server") or "https://github.com").rstrip("/")
    if repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return ""


def emit_failure(
    *,
    workflow: str,
    job: str,
    conclusion: str,
    url: str,
    log_snippet: str,
    ref: str,
    sha: str,
    repository: str,
    source: str,
    ledger: Path,
) -> dict:
    ensure_ledger(ledger)
    root = Path(".")
    events = vmod.load_events(ledger)
    previous_head = events[-1].get("content_hash") if events else None

    snippet = (log_snippet or "").strip()[:1200]
    title = f"CI {conclusion}: {workflow}" + (f" / {job}" if job else "")
    text = title
    if ref:
        text += f" ref={ref}"
    if sha:
        text += f" sha={sha}"
    if url:
        text += f" url={url}"
    if snippet:
        text += f"\n--- log ---\n{snippet}"

    error_data = {
        "text": text[:2000],
        "title": title,
        "workflow": workflow,
        "job": job,
        "conclusion": conclusion,
        "url": url,
        "ref": ref,
        "sha": sha,
        "repository": repository,
        "log_snippet": snippet[:800],
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    ev = vmod.emit_error_event(
        error_data,
        source=source,
        parents=[previous_head] if previous_head else None,
        root=root,
        area="ci",
    )
    vmod.append_event(ledger, ev)

    # Searchable lesson line for session-vault-brief
    lesson = (
        f"CI failure: {workflow}"
        + (f"/{job}" if job else "")
        + (f" — {snippet[:120]}" if snippet else "")
    )
    vmod.secure_compound_emit(
        lesson=lesson[:300],
        report_source=source,
        ledger_path=ledger,
        previous_head=ev.get("content_hash"),
        root=root,
        area="ci",
    )
    return ev


def emit_fix(
    *,
    summary: str,
    solves_hash: str | None,
    source: str,
    ledger: Path,
) -> dict:
    ensure_ledger(ledger)
    root = Path(".")
    events = vmod.load_events(ledger)
    previous_head = events[-1].get("content_hash") if events else None
    relations = []
    if solves_hash:
        relations.append({"type": "solves", "target": solves_hash})

    fix_data = {
        "text": summary[:1500],
        "summary": summary[:300],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    ev = vmod.emit_fix_event(
        fix_data,
        source=source,
        parents=[previous_head] if previous_head else None,
        root=root,
        area="ci",
        relations=relations or None,
    )
    # emit_fix_event may not append — append explicitly
    vmod.append_event(ledger, ev)
    vmod.secure_compound_emit(
        lesson=f"CI fix: {summary[:200]}",
        report_source=source,
        ledger_path=ledger,
        previous_head=ev.get("content_hash"),
        root=root,
        area="ci",
    )
    return ev


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-github-env", action="store_true")
    ap.add_argument("--workflow", default="")
    ap.add_argument("--job", default="")
    ap.add_argument("--conclusion", default="failure")
    ap.add_argument("--url", default="")
    ap.add_argument("--log-snippet", default="")
    ap.add_argument("--log-file", type=Path, default=None)
    ap.add_argument("--ref", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--repository", default="")
    ap.add_argument("--source", default="ci-failure")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--fix-summary",
        default=None,
        help="Emit a fix event instead of a failure (optional --solves-hash)",
    )
    ap.add_argument("--solves-hash", default=None, help="content_hash of prior error event")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.fix_summary:
        if args.dry_run:
            print(f"DRY RUN fix: {args.fix_summary[:200]} solves={args.solves_hash}")
            return 0
        try:
            ev = emit_fix(
                summary=args.fix_summary,
                solves_hash=args.solves_hash,
                source=args.source,
                ledger=args.ledger,
            )
        except Exception as exc:
            print(f"vault-emit-ci-failure: FAILED {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"ok": True, "type": "fix", "hash": ev.get("content_hash")}))
        else:
            print(f"vault-emit-ci-failure: fix recorded {(ev.get('content_hash') or '')[:16]}")
        return 0

    meta = from_github_env() if args.from_github_env else {}
    workflow = args.workflow or meta.get("workflow") or "unknown-workflow"
    job = args.job or meta.get("job") or ""
    conclusion = (args.conclusion or meta.get("conclusion") or "failure").lower()
    url = args.url or build_url({**meta, "url": args.url})
    ref = args.ref or meta.get("ref") or ""
    sha = args.sha or meta.get("sha") or ""
    repository = args.repository or meta.get("repository") or ""

    log_snippet = args.log_snippet
    if args.log_file and args.log_file.is_file():
        try:
            log_snippet = args.log_file.read_text(encoding="utf-8", errors="replace")[-2000:]
        except OSError:
            pass

    # Only emit failures by default (success is noise)
    if conclusion in ("success", "skipped", "cancelled", "neutral"):
        print(f"vault-emit-ci-failure: skip (conclusion={conclusion})")
        return 2

    if args.dry_run:
        print("DRY RUN failure emit:")
        print(f"  {workflow} / {job} → {conclusion}")
        print(f"  url={url}")
        print(f"  snippet={(log_snippet or '')[:160]}")
        return 0

    try:
        ev = emit_failure(
            workflow=workflow,
            job=job,
            conclusion=conclusion,
            url=url,
            log_snippet=log_snippet or "",
            ref=ref,
            sha=sha,
            repository=repository,
            source=args.source,
            ledger=args.ledger,
        )
    except Exception as exc:
        print(f"vault-emit-ci-failure: FAILED {exc}", file=sys.stderr)
        return 1

    h = (ev.get("content_hash") or "")[:16]
    if args.json:
        print(json.dumps({"ok": True, "type": "error", "hash": ev.get("content_hash"), "url": url}))
    else:
        print(f"vault-emit-ci-failure: error recorded {h} ({workflow}/{job})")
        print(f"  query later: python3 scripts/_engine/vault_query.py --query \"{workflow} {job}\" --area ci")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

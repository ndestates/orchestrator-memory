#!/usr/bin/env python3
"""Safe multi-lane recommendation from workstreams + open TODO (Shape B).

Operator command (preferred):
  /multi-workstream diamond
  /multi-workstream recommend
  /chain multi-workstream-diamond

Reads lean registry + latest TODO open checkboxes. Classifies items into:
  - safe_parallel (docs/chore/test/minor — contract-sized)
  - serial_focus  (needs primary attention or medium risk)
  - blocked       (held / parked / legal / prod — do not touch)

Never auto-executes lanes. Never unholds. Never expands held tracks.
Preserves primary focus in the recommendation.

Outputs:
  reports/examples/agent-graphs/recommend-latest.md
  reports/examples/agent-graphs/recommend-latest.json
  stdout: compact operator brief
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports" / "sessions" / "workstreams.yaml"
TODO_DIR = ROOT / "TODO"
OUT_DIR = ROOT / "reports" / "examples" / "agent-graphs"

# Keyword classes (case-insensitive substring)
SAFE = (
    "docs",
    "guide",
    "readme",
    "changelog",
    "comment",
    "typo",
    "example",
    "mermaid",
    "index",
    "link",
    "chore",
    "lint",
    "test",
    "spell",
    "wording",
    "pointer",
    "catalog",
    "nav",
)
SERIAL_HINT = (
    "implement",
    "feature",
    "refactor",
    "schema",
    "migration",
    "api",
    "skill",
    "chain",
    "registry",
    "sync",
    "platform",
)
BLOCK = (
    "license",
    "apache",
    "eula",
    "patreon",
    "paypal",
    "production",
    "prod deploy",
    "force-push",
    "unhold",
    "secret",
    "master",
    "release tag",
    "live ",
    "billing",
    "payment",
)

MAX_PARALLEL = 4  # e.g. 3 minor + docs
MAX_LANES_SHOW = 8


def _latest_todo() -> Path | None:
    if not TODO_DIR.is_dir():
        return None
    files = sorted(TODO_DIR.glob("*_TODO.md"), reverse=True)
    return files[0] if files else None


def _open_todo_items(path: Path | None) -> list[str]:
    if not path or not path.is_file():
        return []
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*[-*]\s+\[ \]\s+(.+)$", line)
        if m:
            text = re.sub(r"\s+", " ", m.group(1)).strip()
            # strip leading priority markers noise lightly
            items.append(text[:160])
        if len(items) >= 20:
            break
    return items


def _classify_text(text: str) -> str:
    t = text.lower()
    if any(k in t for k in BLOCK):
        return "blocked"
    if any(k in t for k in SAFE):
        return "safe_parallel"
    if any(k in t for k in SERIAL_HINT):
        return "serial_focus"
    # default: serial to protect the project
    return "serial_focus"


def _classify_workstream(ws: dict) -> dict:
    status = str(ws.get("status") or "")
    wid = ws.get("id") or "?"
    title = ws.get("title") or wid
    blob = " ".join(
        [
            title,
            str(ws.get("open") or ""),
            str(ws.get("next") or ""),
            status,
        ]
    )
    if status.startswith("held") or status == "parked" or status == "done":
        risk = "blocked"
        reason = f"status={status} (do not expand without unhold/unpark)"
    else:
        risk = _classify_text(blob)
        reason = "heuristic from open/next/title"
        if risk == "blocked":
            reason = "keyword risk (legal/prod/payment/etc.)"
    return {
        "id": wid,
        "source": "workstream",
        "title": title,
        "status": status,
        "next": ws.get("next") or "",
        "branch": ws.get("branch") or "",
        "risk": risk,
        "reason": reason,
    }


def _classify_todo(text: str, idx: int) -> dict:
    risk = _classify_text(text)
    return {
        "id": f"todo-{idx + 1}",
        "source": "todo",
        "title": text,
        "status": "open",
        "next": text,
        "branch": "",
        "risk": risk,
        "reason": "heuristic from TODO open item",
    }


def build_recommendation(
    *,
    primary: str,
    candidates: list[dict],
) -> dict:
    blocked = [c for c in candidates if c["risk"] == "blocked"]
    serial = [c for c in candidates if c["risk"] == "serial_focus"]
    safe = [c for c in candidates if c["risk"] == "safe_parallel"]

    # Primary always first serial focus (preserve attention)
    primary_item = next((c for c in candidates if c["id"] == primary), None)
    if primary_item and primary_item["risk"] != "blocked":
        serial = [primary_item] + [c for c in serial if c["id"] != primary]
        safe = [c for c in safe if c["id"] != primary]

    parallel = safe[:MAX_PARALLEL]
    deferred_safe = safe[MAX_PARALLEL:]

    lanes = []
    # Lane 0: primary / serial focus (always)
    focus = primary_item or (serial[0] if serial else None)
    if focus:
        lanes.append(
            {
                "lane": "L0-primary",
                "depends_on": [],
                "risk": "serial_focus",
                "items": [focus],
                "contract_outputs": [
                    "primary progress note",
                    "no held-track edits",
                ],
            }
        )
    # Parallel safe lanes
    for i, item in enumerate(parallel, start=1):
        lanes.append(
            {
                "lane": f"L{i}-safe",
                "depends_on": [],
                "risk": "safe_parallel",
                "items": [item],
                "contract_outputs": [
                    "diff limited to declared paths",
                    "no secrets",
                    "no branch checkout unless clean+approved",
                ],
            }
        )

    merge_gates = [
        {
            "id": "merge-primary-safe",
            "checks": [
                "Primary L0 still matches registry primary",
                "Safe lanes did not touch held/parked workstream ids",
                "No license/PayPal/prod files unless unhold",
                "Git status reviewable; no force-push",
            ],
        }
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primary": primary,
        "preserve_focus": True,
        "auto_execute": False,
        "shape": "B",
        "summary": {
            "candidates": len(candidates),
            "safe_parallel": len(safe),
            "serial_focus": len(serial),
            "blocked": len(blocked),
            "lanes_recommended": len(lanes),
            "max_parallel_cap": MAX_PARALLEL,
        },
        "lanes": lanes,
        "blocked": blocked[:MAX_LANES_SHOW],
        "serial_remaining": [
            c for c in serial if not focus or c["id"] != focus["id"]
        ][:MAX_LANES_SHOW],
        "deferred_safe": deferred_safe[:MAX_LANES_SHOW],
        "merge_gates": merge_gates,
        "operator_next": [
            "Review this recommendation (do not assume auto-run)",
            "Approve safe lanes by saying: approve parallel" if parallel else "No safe parallel lanes — stay serial on primary",
            "Keep primary: " + (primary or "set with /multi-workstream focus <id>"),
            "Held/parked stay frozen until explicit unhold",
        ],
    }


def format_markdown(rec: dict, todo_path: str | None) -> str:
    lines = [
        "# Multi-workstream diamond recommendation (Shape B)",
        "",
        f"Generated: `{rec['generated_at']}`",
        f"Primary focus (preserve): **`{rec.get('primary') or 'none'}`**",
        f"Auto-execute: **{rec.get('auto_execute')}** (recommend-only)",
        f"TODO source: `{todo_path or '—'}`",
        "",
        "## One-command operator UX",
        "",
        "```text",
        "/chain session-start",
        "/multi-workstream diamond",
        "```",
        "",
        "Or: `/multi-workstream recommend` · `/chain multi-workstream-diamond`",
        "",
        "## Summary",
        "",
        f"- Candidates: {rec['summary']['candidates']}",
        f"- Safe parallel: {rec['summary']['safe_parallel']} (cap {rec['summary']['max_parallel_cap']})",
        f"- Serial focus: {rec['summary']['serial_focus']}",
        f"- Blocked (held/parked/high-risk): {rec['summary']['blocked']}",
        f"- Lanes recommended: {rec['summary']['lanes_recommended']}",
        "",
        "## Recommended Shape B lanes",
        "",
    ]
    for lane in rec.get("lanes") or []:
        lines.append(f"### {lane['lane']} · risk=`{lane['risk']}` · depends_on={lane['depends_on']}")
        for it in lane.get("items") or []:
            lines.append(
                f"- **{it['id']}** ({it['source']}) — {it.get('title') or it.get('next')}"
            )
            if it.get("reason"):
                lines.append(f"  - reason: {it['reason']}")
        lines.append(f"- contracts: {', '.join(lane.get('contract_outputs') or [])}")
        lines.append("")
    lines += [
        "## Do not touch (blocked)",
        "",
    ]
    blocked = rec.get("blocked") or []
    if not blocked:
        lines.append("_None classified blocked._")
    for it in blocked:
        lines.append(
            f"- **{it['id']}** — {it.get('title') or it.get('next')} ({it.get('reason')})"
        )
    lines += [
        "",
        "## Serial after / instead of parallel",
        "",
    ]
    for it in rec.get("serial_remaining") or []:
        lines.append(f"- **{it['id']}** — {it.get('title') or it.get('next')}")
    if not rec.get("serial_remaining"):
        lines.append("_No extra serial items beyond primary._")
    lines += [
        "",
        "## Merge gates",
        "",
    ]
    for g in rec.get("merge_gates") or []:
        lines.append(f"**{g['id']}**")
        for c in g.get("checks") or []:
            lines.append(f"- [ ] {c}")
    lines += [
        "",
        "## Operator next",
        "",
    ]
    for n in rec.get("operator_next") or []:
        lines.append(f"1. {n}")
    lines += [
        "",
        "## Safety",
        "",
        "- Does **not** unhold license/PayPal/parked tracks",
        "- Does **not** auto-start subagents (recommendation only)",
        "- Primary focus is always L0 — parallel lanes must not steal focus",
        "- Prefer docs/chore/test in parallel; implement/refactor serial unless you override",
        "",
    ]
    return "\n".join(lines)


def format_compact(rec: dict) -> str:
    lines = [
        "DIAMOND recommend (Shape B) · auto_execute=no · preserve_focus=yes",
        f"primary={rec.get('primary') or 'none'}",
        (
            f"lanes={rec['summary']['lanes_recommended']} "
            f"safe={rec['summary']['safe_parallel']} "
            f"serial={rec['summary']['serial_focus']} "
            f"blocked={rec['summary']['blocked']}"
        ),
    ]
    for lane in rec.get("lanes") or []:
        ids = ",".join(i["id"] for i in (lane.get("items") or []))
        lines.append(f"  {lane['lane']}: {ids} [{lane['risk']}]")
    if rec.get("blocked"):
        bids = ",".join(b["id"] for b in rec["blocked"][:6])
        lines.append(f"  blocked: {bids}")
    lines.append("next: review · say 'approve parallel' to execute safe lanes only")
    return "\n".join(lines) + "\n"


def main() -> int:
    if yaml is None:
        print("PyYAML required", file=sys.stderr)
        return 1
    if not REGISTRY.is_file():
        print(f"missing {REGISTRY}", file=sys.stderr)
        return 1

    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    primary = str(reg.get("primary") or "")
    workstreams = list(reg.get("workstreams") or [])
    todo_path = _latest_todo()
    todos = _open_todo_items(todo_path)

    candidates: list[dict] = []
    seen_titles: set[str] = set()
    for ws in workstreams:
        c = _classify_workstream(ws)
        candidates.append(c)
        seen_titles.add((c.get("title") or "").lower()[:80])
    for i, t in enumerate(todos):
        key = t.lower()[:80]
        if key in seen_titles:
            continue
        candidates.append(_classify_todo(t, i))

    rec = build_recommendation(primary=primary, candidates=candidates)
    md = format_markdown(
        rec, str(todo_path.relative_to(ROOT)) if todo_path else None
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "recommend-latest.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "recommend-latest.md").write_text(md, encoding="utf-8")
    sys.stdout.write(format_compact(rec))
    print(f"wrote {OUT_DIR / 'recommend-latest.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

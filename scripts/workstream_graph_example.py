#!/usr/bin/env python3
"""Diamond graph example: fan-out workstreams + vault tip → code reduce → synthesize.

Topology (graph engineering §07):
  split → parallel node briefs → barrier reduce → synthesize report

No LLM calls. Orchestration is free (code, not conversation).
Outputs:
  reports/examples/agent-graphs/latest.md
  reports/examples/agent-graphs/latest.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports" / "sessions" / "workstreams.yaml"
VAULT = ROOT / "reports" / "vault" / "events.jsonl"
OUT_DIR = ROOT / "reports" / "examples" / "agent-graphs"


def _git_head() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "unknown").strip()


def node_workstream(ws: dict) -> dict:
    """Fan-out node: one workstream → bounded contract output."""
    arts = ws.get("artifacts") or []
    existing = [a for a in arts if (ROOT / a).is_file()]
    return {
        "node": f"ws:{ws.get('id')}",
        "type": "workstream",
        "id": ws.get("id"),
        "status": ws.get("status"),
        "branch": ws.get("branch"),
        "next": ws.get("next"),
        "open": ws.get("open"),
        "artifacts_present": existing,
        "artifacts_missing": [a for a in arts if a not in existing],
        "ok": True,
    }


def node_vault_tip() -> dict:
    """Fan-out node: vault ledger tip (hash-chain head)."""
    if not VAULT.is_file():
        return {"node": "vault:tip", "type": "vault", "ok": False, "error": "missing"}
    last = None
    count = 0
    with VAULT.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    if not last:
        return {"node": "vault:tip", "type": "vault", "ok": False, "error": "empty"}
    return {
        "node": "vault:tip",
        "type": "vault",
        "ok": True,
        "events": count,
        "tip_id": last.get("id") or (last.get("content_hash") or "")[:16],
        "tip_type": last.get("type"),
        "tip_area": last.get("area"),
        "parents": last.get("parents") or [],
        "ts": last.get("ts"),
    }


def reduce_results(results: list[dict]) -> dict:
    """Edge reduce: pure code — no agent tokens."""
    ok = [r for r in results if r and r.get("ok")]
    bad = [r for r in results if r and not r.get("ok")]
    ws_nodes = [r for r in ok if r.get("type") == "workstream"]
    by_status: dict[str, int] = {}
    for r in ws_nodes:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "total_nodes": len(results),
        "ok": len(ok),
        "failed": len(bad),
        "workstreams": len(ws_nodes),
        "by_status": by_status,
        "failed_ids": [r.get("node") for r in bad],
    }


def synthesize(results: list[dict], reduced: dict, primary: str) -> tuple[dict, str]:
    """Fan-in synthesize: report + mermaid diamond."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_head(),
        "topology": "diamond",
        "primary_workstream": primary,
        "reduce": reduced,
        "nodes": results,
        "source": "scripts/workstream_graph_example.py",
        "principles": [
            "nodes=jobs edges=data",
            "fan-out parallel then barrier reduce",
            "orchestration in code not conversation",
        ],
    }

    lines = [
        "# Agent graph example — workstream diamond",
        "",
        f"Generated: `{payload['generated_at']}` · HEAD `{payload['git_head']}`",
        "",
        "## Topology",
        "",
        "```mermaid",
        "flowchart TD",
        "  split[\"split: load registry + probes\"]",
    ]
    for r in results:
        nid = "".join(c if c.isalnum() else "_" for c in str(r.get("node")))
        flag = "OK" if r.get("ok") else "FAIL"
        lines.append(f"  split --> {nid}[\"{r.get('node')} · {flag}\"]")
        lines.append(f"  {nid} --> reduce[\"reduce: code barrier\"]")
    lines += [
        "  reduce --> synth[\"synthesize: mermaid + JSON\"]",
        "```",
        "",
        "## Reduce (edge, free tokens)",
        "",
        "```json",
        json.dumps(reduced, indent=2),
        "```",
        "",
        "## Nodes",
        "",
        "| Node | Type | OK | Detail |",
        "|------|------|----|--------|",
    ]
    for r in results:
        detail = r.get("status") or r.get("tip_id") or r.get("error") or ""
        lines.append(
            f"| `{r.get('node')}` | {r.get('type')} | {r.get('ok')} | {detail} |"
        )
    lines += [
        "",
        "## How to re-run",
        "",
        "```text",
        "/multi-workstream list",
        "/multi-workstream example",
        "```",
        "",
        "Diamond probes **workstream registry + vault tip only** — not product demos.",
        "See plan: `docs/internal/MULTI-WORKSTREAM-SESSION-V2-PLAN.md`",
        "",
    ]
    return payload, "\n".join(lines)


def main() -> int:
    if yaml is None:
        print("PyYAML required", file=sys.stderr)
        return 1
    if not REGISTRY.is_file():
        print(f"missing {REGISTRY}", file=sys.stderr)
        return 1

    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    primary = reg.get("primary") or ""
    workstreams = list(reg.get("workstreams") or [])

    # --- fan-out (parallel nodes): one node per workstream + vault tip ---
    # No product-specific probes (WebMCP etc.) — multi-stream is track inventory only.
    jobs = []
    for ws in workstreams:
        jobs.append(("ws", ws))
    jobs.append(("vault", None))

    results: list[dict] = []

    def run_job(kind_payload):
        kind, payload = kind_payload
        if kind == "ws":
            return node_workstream(payload)
        if kind == "vault":
            return node_vault_tip()
        return {"node": "unknown", "ok": False}

    # Thread pool = parallel fan-out; failures isolated per node
    with ThreadPoolExecutor(max_workers=min(8, max(2, len(jobs)))) as ex:
        futs = {ex.submit(run_job, j): j for j in jobs}
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as exc:  # isolation: one failure ≠ graph death
                results.append(
                    {"node": "error", "type": "error", "ok": False, "error": str(exc)}
                )

    # stable order for reports
    results.sort(key=lambda r: str(r.get("node")))

    # --- barrier reduce + synthesize ---
    reduced = reduce_results(results)
    payload, md = synthesize(results, reduced, primary)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "latest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "latest.md").write_text(md, encoding="utf-8")
    print(f"wrote {OUT_DIR / 'latest.md'}")
    print(f"wrote {OUT_DIR / 'latest.json'}")
    print(
        f"graph: nodes={reduced['total_nodes']} ok={reduced['ok']} "
        f"failed={reduced['failed']} workstreams={reduced['workstreams']}"
    )
    return 0 if reduced["failed"] == 0 else 0  # demo always exits 0; report flags


if __name__ == "__main__":
    raise SystemExit(main())

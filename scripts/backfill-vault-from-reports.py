#!/usr/bin/env python3
"""
Backfill/expand the vault graph with structured knowledge from reports, codebase docs, and fleet data.

This significantly expands the graph beyond basic lessons to include:
- report summaries, findings, recommendations
- codebase architecture, concerns, structure
- fleet/wave app status and per-app knowledge

Supports "this error happened before" via richer event types and find_similar_events in synthesis.

Run: python3 scripts/backfill-vault-from-reports.py [--dry-run]

Respects non-destructive: appends only new (by text prefix), uses secure emit.
For wave apps: this seeds meta + fleet patterns; wave apps build their own from their reports/loops after scaffold (see backfill-wave-vault.sh).
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _engine import vault as vmod


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())[:120]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ledger", type=Path, default=Path("reports/vault/events.jsonl"))
    args = parser.parse_args()

    ledger = args.ledger
    root = Path(".")

    events = vmod.load_events(ledger)
    # Robust dedup on canonical knowledge text (any payload shape)
    existing = set()
    for e in events:
        p = e.get("payload", {})
        txt = p.get("text") or p.get("summary") or p.get("description") or str(p)
        existing.add(_normalize_text(txt))

    added = []

    # Reports - key ones with status, issues, fixes (Lane 1: area=process)
    reports = [
        ("reports/loops/2026-06-29-repo-health.md", "repo_health", "Repo health watch: master 18 commits behind develop; draft PR #72; stale local branches recommend cleanup; PASS with follow-up."),
        ("reports/loops/2026-06-29-github-ci.md", "github_ci", "CI watch: all success, zero failures; new run-chain.yml on develop pending master; healthy."),
        ("reports/loops/2026-06-29-chain-health.md", "chain_health", "Chain health: 100/100 audit; 51 chains all resolve; repo-health-watch added; no edits needed."),
        ("reports/loops/2026-07-02-fleet-compound-audit.md", "fleet", "Fleet audit: 3 READY (ndestates-io 7/7 spine 2 lessons, e-ndsign 3 lessons, lightstone 3 lessons); 5 GAP missing spine (jerseyhouseprices etc)."),
        ("reports/loops/2026-06-20-github-ci-host.md", "old_ci", "Historical: failure in branch promotion deploy to app current branch workflow."),
    ]

    for path, et, txt in reports:
        if _normalize_text(txt) not in existing:
            ev = vmod.emit_event(et, {"path": path, "summary": txt}, "backfill:report", root=root, area="process")
            added.append(ev)
            existing.add(_normalize_text(txt))

    # Codebase knowledge (Lane 1: use rich emitter + area="code")
    cb = [
        ("docs/codebase/ARCHITECTURE.md", "Core: manifest -> cache -> orchestrator/chains/loops/MCP. Durable spine includes vault graph for self-building lessons."),
        ("docs/codebase/CONCERNS.md", "10 concerns incl. prompt drift, cache staleness 14d, MCP security, wave blast radius, vault graph tampering risks. Mitigations: sync, audits, guards, hash-chain."),
        ("docs/codebase/STRUCTURE.md", "Layout: .grok/ (source), .github/, .claude/, mcp-server/, chains/, patterns/, docs/, TODO/, reports/, scripts/."),
        ("docs/codebase/STACK.md", "Generic template: no app runtime; MCP server is dev-only. Vault paths in manifest."),
    ]

    for path, txt in cb:
        if _normalize_text(txt) not in existing:
            ev = vmod.emit_codebase_knowledge_event(file=path, text=txt, source="backfill:codebase", area="code", root=root)
            added.append(ev)
            existing.add(_normalize_text(txt))

    # Wave/fleet codebases (Lane 1: area="wave", rich type)
    wave = "Wave apps use template for self-building: ndestates-io/e-ndsign/lightstone READY with 2-3 own lessons each; others GAP on spine. Codebases preserve custom skills; deploy non-destructive to current branch."
    if _normalize_text(wave) not in existing:
        ev = vmod.emit_event("wave_codebase", {"text": wave, "apps": ["ndestates-io", "e-ndsign", "lightstone"]}, "backfill:fleet", root=root, area="wave")
        added.append(ev)
        existing.add(_normalize_text(wave))

    # Lane 1: Demonstrate richer taxonomy + relations by emitting linked precedent/synthesis
    # Find prior error+fix pair (if present) and link via relation in a new synthesis node
    error_ev = next((e for e in vmod.load_events(ledger) if e.get("type") == "error"), None)
    fix_ev = next((e for e in vmod.load_events(ledger) if e.get("type") == "fix"), None)
    if error_ev and fix_ev:
        err_hash = error_ev.get("content_hash")
        fix_hash = fix_ev.get("content_hash")
        # Emit a linked precedent using relations
        prec = vmod.emit_precedent_event(
            description=str(error_ev.get("payload", {}))[:120],
            outcome="fixed via branch policy + current-working-branch deploys",
            source="backfill:lane1-linking",
            area="learning",
            relations=[{"type": "solves", "target": err_hash}, {"type": "solved_by", "target": fix_hash}],
            root=root,
        )
        # Use unique key for dedup (normalize the description)
        prec_key = _normalize_text(prec["payload"].get("description", ""))
        if prec_key not in existing:
            added.append(prec)
            existing.add(prec_key)

        # Emit a synthesis that references both (via parents/relations)
        syn = vmod.emit_synthesis_event(
            summary="Error in wave branch promotion was analogous to current-branch policy gaps; resolved by enforcing wave-app-branch current + --commit-push-only.",
            proposals=["Always target app current branch", "Scaffold+backfill vault on deploy"],
            source="backfill:lane1-synthesis",
            area="learning",
            parents=[err_hash, fix_hash] if err_hash and fix_hash else None,
            relations=[{"type": "solves", "target": err_hash}],
            root=root,
        )
        syn_key = _normalize_text(syn["payload"]["summary"])
        if syn_key not in existing:
            added.append(syn)
            existing.add(syn_key)

    if args.dry_run:
        print(f"DRY: would add {len(added)} events")
        for ev in added:
            print("  ", ev["type"], str(ev["payload"])[:60])
        return

    for ev in added:
        vmod.append_event(ledger, ev)
        print("Appended:", ev["type"], str(ev.get("payload", {}))[:60])

    print(f"Total events: {len(vmod.load_events(ledger))}")
    print("Verify:", vmod.verify_ledger(ledger)[0])

if __name__ == "__main__":
    main()

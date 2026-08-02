# Pattern: Compound Learning (steps 10–14)

**On-demand** — runs after every loop artifact passes `loop-verifier`.

## Purpose

Ensure the project **learns from each iteration** and the knowledge **vault builds itself securely**: lessons are captured into a hash-chained, provenance-rich graph ledger (`reports/vault/events.jsonl`) + `STATE.md` + `lessons-state.json`. Objective gates recorded; promotions queued (human approval at L1). Graph enables self-synthesis, tamper-evidence, and lean subgraph loads.

## Cadence

- After: any L1 loop report (`daily-triage`, weekly watches, manual `/loop-triage`)
- At session-start: `/app-compound-gate` when `LOOP.md` exists (per-app; not fleet audit)
- Command: `bash scripts/loop-compound.sh --report <artifact>`
- Skill: `/loop-compound`

## Required files

1. `VISION.md` — standing spec (reread each loop run)
2. `STATE.md` — spine including `Lessons → skills`, `Compound queue`
3. `reports/loops/lessons-state.json`
4. Loop report with `## Lessons` section

## Maker / verifier

| Role | Skill / script |
|------|----------------|
| Maker | `loop-compound` |
| Prerequisite | `loop-verifier` PASS on artifact |
| Gates | `loop-audit.sh`, `chain-audit.sh` |

## Outputs

- Secure vault graph events appended to `reports/vault/events.jsonl` (content-hashed, scrubbed, parent-chained)
- Ledger verification run (tamper detection)
- Updated `STATE.md` (lessons deduped)
- Updated `reports/loops/lessons-state.json` (`lessons_learned`, `gate_history`, `promotions`)
- Console promotion queue (CONCERNS / skill / memory) + vault integrity status

## L1 rules

- No auto-write to CONCERNS, skills, or memories — queue only
- `allow_l2: false` blocks automated promotion scripts
- Vault graph is append + verify only (L1). Synthesis proposals are reports; mutations require human + verifier + secrets guard. Hash chain + scrubbing provide strong integrity and confidentiality.

## Wave apps

Run `bash scripts/scaffold-loop-state.sh <app-root>` once when `STATE.md` is missing (not overwritten if present).
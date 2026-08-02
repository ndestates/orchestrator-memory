---
description: Compound learning closure (14-step roadmap steps 10–14): capture loop lessons, promote to STATE.md + secure hash-chained vault graph (reports/vault/events.jsonl with content hashes, provenance, secret scrubbing)…
argument-hint: --report reports/loops/YYYY-MM-DD-triage.md | --gates-only
allowed-tools: Read, Grep, Glob, Bash
---

# Loop Compound (steps 10–14)

Closes the learning loop: **each iteration must leave durable knowledge** for the next.

## Mandatory load (lean)

1. `VISION.md` — standing spec (read before maker work every loop)
2. `STATE.md` — `Lessons → skills`, `Compound queue`
3. `reports/loops/lessons-state.json` — machine-readable history
4. Loop report artifact (argument) — must include `## Lessons`

## Procedure

1. Confirm `loop-verifier` **PASS** on the report (do not compound FAIL artifacts).
2. Run:

```bash
bash scripts/loop-compound.sh --report <artifact-path>
```

3. Review promotion queue + vault integrity (CONCERNS / skill / memory) — **human approves at L1** before editing targets. Vault ledger verified automatically.
4. On wave deploy, ensure spine exists first:

```bash
bash scripts/scaffold-loop-state.sh /path/to/app
```

## Report contract (every loop)

```markdown
## Lessons

- <one concrete lesson from this run, or "none new">
```

## Objective gates (step 12 — not opinions)

Recorded automatically in `lessons-state.json` → `gate_history`:

| Gate | Script |
|------|--------|
| Loop infra | `bash scripts/loop-audit.sh` |
| Chain registry | `bash scripts/chain-audit.sh` |

Security gate on deploy: `git-push-secrets-guard.py --staged` (step 14).

## Steps 13–14 (human)

- **Comprehension debt:** spot-check loop PR diffs; do not let loops own architecture/auth at L1.
- **Security tax:** re-audit skill sources and loop permissions every 30 days.

## Anti-patterns

- Compounding without `## Lessons` in the report
- Auto-editing CONCERNS/skills/memories without approval at L1
- Treating verifier opinion as a gate (use scripts above)

User focus (optional): $ARGUMENTS

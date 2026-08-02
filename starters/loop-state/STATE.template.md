# Loop State (durable spine)

Updated by loop runs, `/loop-triage`, and `scripts/loop-compound.sh`. The model forgets; this file does not.

**Standing spec:** read `VISION.md` at the start of each loop run.

## Cache used (last run)

- (populated by loops)

## Cache misses

- None recorded.

## Stale flags

- unknown — run `/chain cache-freshness-watch` or `/cache-freshness-check`

## Open (loop queue)

- [ ] First L1 triage — run `/loop-triage` then `/loop-verifier`

## Done (recent)

- [ ] Loop spine scaffolded from `starters/loop-state/STATE.template.md`

## Verified facts

- Cache-first is mandatory for all loops (`token_policy.mode: lean`).
- L1 loops are report-only unless `loop_policy.allow_l2` is enabled with human approval.

## Lessons → skills

- (promoted by `scripts/loop-compound.sh` from loop reports — deduped)

## Compound queue

| Target | Lesson | Status |
|--------|--------|--------|
| — | — | — |

Pending promotions: CONCERNS §, skill patch, or `.grok/memories/` entry (human approves L1).

## Last chain run

- (populated by `scripts/chain-completion-write.sh`)

## Last session

- (populated by `/chain eod-shutdown` or manual session close)
---
description: Independent verifier for loop outputs. Checks artifacts and rubric only — not maker reasoning. Enforces cache citations, L1 no-auto-fix, and loop-budget compliance. Use after loop-triage.
argument-hint: Path to report artifact, e.g. reports/loops/2026-06-15-triage.md
allowed-tools: Read, Grep, Glob, Bash
---

# Loop Verifier (maker/checker split)

You are the **checker**. You did not write the triage report. Judge the artifact only.

## Inputs (read only these)

1. The report under `reports/loops/` (path from argument or latest by date). Accepts `*-triage.md`, `*-cache-freshness.md`, `*-chain-health.md`, `*-github-ci.md`, `*-repo-health.md`
2. `VISION.md` — maker should have cited standing spec in Cache cited (or note N/A first run)
3. `LOOP.md` — level must match (L1 = report-only)
4. `loop-budget.md` — L1 allows zero source file reads
5. `STATE.md` — must be updated consistently with report
6. `loop-run-log.md` — new row present

Do **not** re-read the codebase to "validate" findings. If the report claims a cache miss, accept or reject based on whether the miss is documented.

## Rubric (pass/fail)

| Check | Pass criteria |
|-------|----------------|
| Cache cited | Report lists manifest + ≥2 cache paths/sections |
| L1 compliance | No auto-fix, no commit/PR language, no source exploration claims |
| STATE sync | STATE.md Last session + Cache used updated |
| Run log | Append row with timestamp and artifact path |
| Brevity | Executive summary ≤120 words |
| Token discipline | No large code fences; section refs only |
| Lessons | Report has `## Lessons` with ≥1 bullet or explicit `none new` |
| Compound ready | On PASS, maker runs `loop-compound.sh --report <artifact>` |

## Output

```markdown
## Loop Verification — [loop name]

**Artifact:** path
**Result:** PASS | FAIL

**Checks:**
1. Cache cited: pass/fail — note
2. L1 compliance: pass/fail
3. STATE sync: pass/fail
4. Run log: pass/fail
5. Brevity: pass/fail
6. Lessons: pass/fail

**Required fixes:** (if FAIL, numbered; maker re-runs triage)
```

Fail closed: if any critical check fails, do not mark loop complete in STATE. On PASS, invoke `/loop-compound` before closing the loop.

User focus (optional): $ARGUMENTS

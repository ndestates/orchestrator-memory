# Daily workflow

[UPDATED 2026-08-04] — remote_last product rule + extension/CLI ease

## Overview

A repeatable session flow: load context, align with TODO, work on a feature branch, **pause mid-day or close the day**.

Token cost of that flow (lean spine vs naive full loads): [Cache and token savings](cache-and-token-savings.md).

### Product rules (always)

1. **GitHub is the shared machine.** Isolated laptops only meet at `origin`. Stash and
   uncommitted files do not travel. **session-start** lands on `remote_last`.
   **session-resume** lands on the prior **session-end** Branch after fetch (origin
   card if the other machine pushed a newer pause; this machine if the pause is
   unpushed). Fast-forward when behind and clean; never reset local dirty.
2. **Distinct open commands**
   | After… | Same day? | Run |
   |--------|-----------|-----|
   | `/chain session-end` (mid-day pause) | yes | **`/chain session-resume`** |
   | `/chain eod-shutdown` or new calendar day | — | **`/chain session-start`** |
3. **Already on tip:** local dirty is OK. Cross-branch switch still needs a clean tree.
4. **Same path extension + CLI** — session-start: fetch → remote_last → card. session-resume: fetch → **prior session Branch** (session-end card) → card. Never remote_last on resume.
5. **Numbered next actions** — operator picks a number (never re-describe bullets).

## Before you begin

- On a `feature/*` branch (not `master` or `develop` for direct commits)
- Latest `TODO/YYYY-MM-DD_TODO.md` exists

## Steps

1. **Start the session**

   ```text
   /chain session-start
   ```

   **Order is mandatory (remote_last first):**

   1. `git fetch origin --prune`
   2. Auto-switch to **`remote_last`** (newest remote work branch / team tip) when the tree is
      **clean** (or soft-dirty session noise only), then `git pull --ff-only`
   3. **Then** load **check + resume-card** from that tip (never from the pre-switch branch)
   4. Security sweep + lean work

   Surfaces **current↔remote_last**, align recommendations when off tip, and **develop/master
   ff offer** when local integration is behind. Real WIP **blocks cross-branch switch** (never
   discarded); if you are **already on** remote_last, dirty tree does not block. Session
   spin-up noise (`context-latest`, `situation-*`, `session-sweep-*`, spinup/vector probes) is
   soft-dirty and does not block. **Guardrails one-liner** (`session-guardrails-check.py` /
   spinup) cites prompt-injection posture — see
   [Prompt injection (installed apps)](prompt-injection-installed-apps.md).
   Session-end and eod-shutdown write a **rich** card and print the same next-start order reminder.

   **Multi-workstream:** CTX includes `ws primary=…`. Slash-first:
   `/multi-workstream list` · `focus` · `hold` · **`diamond`** (Shape B safe multi-lane **recommend**).
   After session-start: `/multi-workstream diamond` or `/chain multi-workstream-diamond`.
   Does **not** auto-run lanes or unhold tracks.  
   **Guides:** [multi-workstream hub](multi-workstream.md) · [IMPLEMENTATION](multi-workstream/IMPLEMENTATION.md).

   Or manually: `/load-project-cache-first` then `/daily-standup-with-cache`.

   First time on a machine? Run `bash scripts/setup-who-i-am.sh` and personalize `.grok/memories/who-i-am.md`.

2. **Confirm scope** from today's TODO open items.

3. **Work** using single skills or chains as needed. Say `no chain` to run one skill only.

4. **Pause mid-day** (leave and come back later — **not** end of day):

   ```text
   /chain session-end
   ```

   Or: `python3 scripts/session-end-checkpoint.py --summary "…"`.

   Writes a **rich resume card** with `Source: session-end`. Next open command is
   **`/chain session-resume`** (same day) — **not** full session-start.

   | | session-end | session-resume | eod-shutdown | session-start |
   |--|-------------|---------------|--------------|---------------|
   | When | Mid-day leave | Same-day return | Day closed | New day / after EOD |
   | Dirty git | **OK** | OK if already on tip | **Orchestrator preserves WIP** (commit on `feature/*`, or stash→switch→restore then commit). Operator does not stash. | soft-dirty OK |
   | Depth | Checkpoint + card | Lean card + security | Full close | Full open |
   | Next command | `/chain session-resume` | (work) | `/chain session-start` | (work) |

5. **Run L1 triage** (weekdays or before major merges):

   ```text
   /chain loop-daily
   ```

6. **Monday watches** (after CI host snapshots or manual host scripts):

   ```text
   /chain cache-freshness-watch scheduled
   /chain chain-health-watch scheduled
   /chain github-ci-watch scheduled
   /chain repo-health-watch scheduled
   ```

   Then run `/loop-verifier` on each final report and close with `scripts/chain-completion-write.sh`. See `patterns/chain-health-watch.md` for the full ritual.

7. **End of day** (finished for the day — clean shutdown):

   ```text
   /chain eod-shutdown scheduled
   ```

   Or: `/ddev-cleanup` on this template (no DDEV required).

   Vault graph (`reports/vault/events.jsonl`) gets a **guaranteed** write (v1.5.0+).

8. **After `.grok/` skill edits**, sync and verify:

   ```bash
   python3 scripts/sync_grok_to_github_claude.py
   python3 scripts/check_name_alignment.py
   ```

## Verify

- `STATE.md` and `loop-run-log.md` updated after triage or chain completion
- TODO items marked `[x]` when complete
- No uncommitted doc drift before leaving (optional commit on feature branch)

## Next steps

- [Chains and skills](chains-and-skills.md) — pick the right chain
- [Delivery](../operations/delivery.md) — commit, push, PR
- [Documentation](documentation.md) — refresh docs after major changes

## Related

- [Guides index](index.md)
# Chains and skills

[UPDATED 2026-07-07] — refreshed; vault graph emission in loop-compound (secure hash-chained events), multi-AI + wave context, manifest vault paths

## Overview

**Skills** are single-purpose instructions (one slash command). **Chains** run multiple skills in order with one shared cache load and minimal handoffs.

For **why shared cache and lean caps save tokens** (with size comparisons and meter steps), see [Cache and token savings](cache-and-token-savings.md).

## Before you begin

- Cache loaded (`/load-project-cache-first` or via chain step 1)
- Catalogs: [Chains reference](../reference/chains.md), [Skills reference](../reference/skills.md)

## Invoke a chain

```text
/chain session-start
/chain loop-daily
/chain documentation-refresh
/chain delivery
```

Or describe intent: `/chain commit and push this branch` → matches `delivery`.

## Scheduled chains (trusted allowlist)

Manifest field `chain_policy.scheduled_allowlist` lists chains that **skip the confirm prompt** when you pass an explicit id plus `scheduled`:

Vault features (self-building knowledge) are integrated into compound via secure graph (see reference/manifest for vault paths; reports/vault for ledger).

```text
/chain chain-health-watch scheduled
/chain repo-health-watch scheduled
/chain eod-shutdown scheduled
```

Also supported: env `CHAIN_SCHEDULED=1`, or GitHub Actions `run-chain.yml` dispatch (see [Testing](../operations/testing.md)).

**Loops vs chains:** recurring health → [When to use loops](when-to-use-loops.md). Scaffolded manual watches: `/chain vault-integrity-watch`, `/chain version-drift-watch`.

## Close the loop after `/chain`

After a successful chain run, append audit state:

```bash
bash scripts/chain-completion-write.sh \
  --chain-id <chain-id> \
  --outcome PASS \
  --cache "<paths cited>" \
  --artifact "<report path or —>" \
  --steps "<step ids>"
```

This updates `loop-run-log.md` and `STATE.md` → `## Last chain run`. The `/chain` skill requires this in Phase 4.

## Recent / notable chains (examples)

- `ci-branch-readiness`: load-cache → github-ci-readiness-expert → github-expert → git-workflow-guardrails (for wave PRs/deploys; notes no secrets in this project).
- `jersey-dp-safe-consult` and `jersey-aml-safe-screen`: safe invocation of jersey-data-protection-expert + jersey-aml-compliance-expert with personal-data guards (AUTHORITY/BASIS + refusal).
- `documentation-full` / `documentation-refresh`: load-cache → read-codebase (optional) → readme-specialist → documentation-specialist.
- `session-start`, `eod-shutdown`, `loop-*` family, `delivery`, `repo-health-watch`.

See `chains/registry.yaml` and reference/chains.md for full machine + human catalogs. New skills/chains must be registered and synced.

## Multi-AI and platform notes

The orchestrator supports Grok, Claude, Copilot, Gemini (and others) via parallel root dirs (`.grok/`, `.claude/`, `.github/`, `.gemini/`) + sync script. See `docs/codebase/README.md`, reports/research/ and `.grok/prompts/multi-ai-best-practices-setup.md`.

## Opt out

Say **no chain**, **skip chain**, or name a single skill:

```text
no chain, just loop-triage
/readme-specialist
```

The agent runs only that skill — never forced multi-step.

## Common chains (template)

| Chain | Use when |
|-------|----------|
| `session-start` | Default session opener |
| `loop-daily` | L1 triage + verifier |
| `documentation-full` | Full doc site + cache |
| `documentation-refresh` | Update docs without codebase scan |
| `delivery` | Commit, push, PR prep |
| `repo-health` | On-demand branch and GitHub hygiene (3 steps) |
| `repo-health-watch` | Weekly L1 repo hygiene + verifier (Mon) |
| `cache-freshness-watch` | Weekly cache staleness (Mon) |
| `chain-health-watch` | Weekly chain registry audit (Mon) |
| `github-ci-watch` | Weekly Actions health (Mon) |
| `eod-shutdown` | End of day cleanup |

Full list: [Chains reference](../reference/chains.md).

## Orchestrator-tier skills

| Skill | Purpose |
|-------|---------|
| `/chain` | Chain discovery and execution |
| `/script-not-shell` | Write script files instead of inline shell |
| `/documentation-specialist` | Full doc site producer |
| `/cache-efficient` | Lean token mode |

## After adding a skill

1. Create `.grok/skills/<name>/SKILL.md`
2. Add to `chains/registry.yaml` (`skills:` section) and `.grok/skills/README.md`
3. Run `python3 scripts/sync_grok_to_github_claude.py`
4. Run `python3 scripts/check_name_alignment.py`

## Verify

```bash
bash scripts/chain-audit.sh
bash scripts/loop-audit.sh
```

Expect chain score 100/100; loop readiness ≥ 80.

## Next steps

- [Manifest reference](../reference/manifest.md) — `chain_policy` and `scheduled_allowlist`
- [Daily workflow](daily-workflow.md) — Monday watch ritual
- [Testing](../operations/testing.md) — audit gates and `run-chain` workflow

## Related

- [Guides index](index.md)
# Vault learning expansion (v1.5.0)

[UPDATED 2026-07-11]

## Overview

Three mandatory pipes make the vault a **working brain** on the orchestrator template and on every upgraded app:

| ID | Pipe | When | Script |
|----|------|------|--------|
| **A** | Guaranteed EOD emit | End of every working day | `scripts/eod-vault-emit.py` |
| **B** | TODO-driven query | Session start / standup | `scripts/session-vault-todo-query.py` |
| **C** | CI failure emit | Red CI / manual | `scripts/vault-emit-ci-failure.py` |

Ledger: `reports/vault/events.jsonl` (per repo).

## A — Guaranteed EOD emit

### Behaviour

- **Always** writes at least one event (heartbeat) so app vaults cannot stay empty.
- On active days (changelog session and/or commits today): **rich** `synthesis` + `lesson` + workspace pointer.
- Quiet days: short **heartbeat** lesson only.

```bash
python3 scripts/eod-vault-emit.py
python3 scripts/eod-vault-emit.py --summary "Shipped X, fixed Y" --area process
# legacy opt-out only:
python3 scripts/eod-vault-emit.py --skip-if-empty
```

### Who runs it

| Trigger | Requirement |
|---------|-------------|
| `/chain eod-shutdown` | `vault-emit` step **required: true** |
| ddev-cleanup skill step 9 | Mandatory; non-zero exit fails EOD |

### Apps

After `orchestrator upgrade` to ≥1.5.0 with default `scripts` selection, run the same command in the app (host or ddev) at EOD.

## B — Session-start TODO → vault query

### Behaviour

1. Loads **latest** `TODO/*.md` (prefers dated files).
2. Collects open tasks (`- [ ] …`).
3. Queries the vault for similar past lessons/errors/fixes.
4. Prints precedents the agent **must cite** before re-planning.

```bash
python3 scripts/session-vault-todo-query.py
python3 scripts/session-vault-todo-query.py --json
python3 scripts/session-vault-todo-query.py --todo TODO/2026-07-11_TODO.md
```

### Who runs it

| Trigger | Requirement |
|---------|-------------|
| `/chain session-start` | After vault brief, before synthesis |
| `/daily-standup-with-cache` | Step 2 (vault brain) |

### Rule for agents

If precedents list past work as done, **do not re-plan** it. Confirm with the user if TODO still has an open checkbox.

## C — CI failure → vault error

### Behaviour

Records a structured **error** (+ searchable lesson) when CI fails, so later sessions can find “this broke before”.

```bash
# Manual
python3 scripts/vault-emit-ci-failure.py \
  --workflow tooling-tests \
  --job unit \
  --conclusion failure \
  --url "https://github.com/org/repo/actions/runs/123" \
  --log-snippet "AssertionError: expected 200"

# Inside GitHub Actions
python3 scripts/vault-emit-ci-failure.py --from-github-env

# Later, link a fix
python3 scripts/vault-emit-ci-failure.py \
  --fix-summary "Pinned dependency X" \
  --solves-hash <error_content_hash>
```

Exit codes: `0` recorded · `1` failed · `2` skipped (success/cancelled).

### Wiring CI (apps)

Example workflow (copy and adapt):

[`docs/examples/vault-ci-failure.workflow.yml`](../examples/vault-ci-failure.workflow.yml)

Commit vault updates on a feature branch (often via EOD), or accept ledger growth only on runners that persist artifacts.

### Query after a failure

```bash
python3 scripts/_engine/vault_query.py --query "tooling-tests failure" --area ci --hint
python3 scripts/session-vault-brief.py --query "CI failure"
```

## Full session-start spine (v1.5.0)

```bash
bash scripts/resume-branch.sh
python3 scripts/session-vault-brief.py
python3 scripts/session-vault-todo-query.py
python3 scripts/session-orchestrator-check.py
```

## Full EOD spine (v1.5.0)

```bash
# … clean tree, push, TODO …
python3 scripts/eod-vault-emit.py          # guaranteed
# workspace pointer included when possible
```

## Related

- [Knowledge vault](knowledge-vault.md) — graph model, synthesis, backfill
- [Per-app upgrade](per-app-upgrade.md) — deploy `scripts` selection
- [Daily workflow](daily-workflow.md) — session-start / eod-shutdown

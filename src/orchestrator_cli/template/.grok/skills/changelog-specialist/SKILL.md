---
name: changelog-specialist
description: "Incremental changelog for project: session log after every substantive action, consolidate into CHANGELOG.md [Unreleased] at EOD, generate PR body."
argument-hint: "init | append <category> <summary> | status | consolidate | pr-body"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# Changelog Specialist

Maintain a **living changelog** across the session: append after work, roll up at EOD.

## Files

| Path | Role |
|------|------|
| `CHANGELOG.md` | Project `[Unreleased]` (Keep a Changelog) |
| `reports/changelog/session-YYYY-MM-DD.md` | Today's append-only log |
| `reports/changelog/state.json` | Machine-readable entries |
| `reports/changelog/pr-<branch-slug>.md` | PR description (EOD) |

Format reference: [`references/format.md`](references/format.md)

## Always-on rule (agents)

After **every substantive action** (unless user says "skip changelog"):

1. Classify the change: `added` | `changed` | `fixed` | `removed` | `security` | `tests` | `infrastructure`
2. Run append (include commit hash when committed):

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py append \
  --category <category> \
  --summary "<one-line description>" \
  --commit "$(git rev-parse --short HEAD 2>/dev/null)" \
  --files "path/one,path/two"
```

3. **Do not** narrate the append in the user reply unless they asked — log silently; mention only on failure.

**Skip append for:** read-only answers, cache loads, failed attempts reverted, trivial acks.

## Commands

| Command | When |
|---------|------|
| `init` | Session start — open today's session log |
| `append` | After each substantive change |
| `status` | User asks "changelog" / before PR / sanity check |
| `consolidate` | EOD — merge session → `CHANGELOG.md [Unreleased]` |
| `pr-body` | EOD — write `reports/changelog/pr-<branch>.md` |

Script path: `.grok/skills/changelog-specialist/scripts/changelog_update.py`

### init (session-start chain)

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py init
```

- Creates `reports/changelog/session-<today>.md` and `state.json` if missing
- JSON output includes `unreleased_total` — mention in standup briefing when > 0

### status

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py status --json
```

### consolidate (eod-shutdown chain)

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py consolidate
```

- Appends new session bullets under `## [Unreleased]` (dedupes by normalized text)
- Run **after** todo-specialist closes tasks, **before** readme-specialist

### pr-body (eod-shutdown chain)

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py pr-body
```

- Writes PR markdown from session entries + unreleased counts
- Record path in TODO EOD section: `**Changelog PR body:** reports/changelog/pr-….md`

## Chain integration

| Chain | Step | Action |
|-------|------|--------|
| `session-start` | `changelog-init` | `init` — handoff `changelog_ready` |
| `eod-shutdown` | `changelog` | `consolidate` then `pr-body` — handoff `changelog_closed` |

## Manual invoke

User runs `/changelog-specialist` or `/changelog-specialist status`:

1. Run `status --json` or requested subcommand
2. Show session entry count + unreleased summary
3. On `append` requests, run script with user-provided category/summary

## Handoffs

| Handoff | Meaning |
|---------|---------|
| `changelog_ready` | Session log open; unreleased counts known |
| `changelog_closed` | Session consolidated; PR body path written |

## Coordination

- **todo-specialist** — EOD TODO should cite changelog PR body path
- **git-workflow-guardrails** — use `pr-body` output for `gh pr create --body-file`
- **readme-specialist** — do not duplicate changelog bullets in README; point to `CHANGELOG.md`
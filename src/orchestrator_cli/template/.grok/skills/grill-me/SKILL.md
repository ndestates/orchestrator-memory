---
name: grill-me
description: "Relentless design-tree interview until every branch is settled. Use before building, when a plan is fuzzy, or when the user says grill this."
argument-hint: "Topic or plan to stress-test"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Grill Me

**Purpose:** Reach a **shared understanding** before anyone writes code or a spec. Map the work as a design tree and close every branch.

**Adapted from:** Matt Pocock `grill-me` + `grilling` (MIT). Orchestrator additions: cache-first facts, no implementation until the user confirms.

**Cache is king.** Look up facts yourself. The user owns *decisions*, not filesystem trivia.

## Complements (do not duplicate)

| Skill | Role |
|-------|------|
| research-deep-dive | External topic memo (vendors, law, options) — not a design interview |
| orchestrator | Shape A/B execution *after* this interview |
| todo-specialist-agent | Persist agreed work into TODO — after confirmation |
| code-review | Diff quality gate after implementation |

## When to use

- User says grill / stress-test / interview me / I'm not sure what I want
- A plan, feature, or design is about to be built and branches are still assumed
- Alignment failed last time ("that's not what I meant")

**Do not** start implementing, editing app source, or opening PRs in this skill.

## Design tree

Every decision branches into the decisions that hang off it.

The **frontier** is every decision whose prerequisites are already settled — questions you can ask *now* without guessing unanswered ones.

Work in **rounds**:

1. Ask the **whole frontier** in one message.
2. Number each question. Give your recommended answer.
3. **Wait** for the user's answers.
4. Settled nodes push the frontier out. Recompute and ask the next round.
5. A question that depends on another still-open question belongs to a *later* round.

Stop when the frontier is empty: every branch visited, nothing silently assumed. Then restate the shared understanding in ≤12 bullets and ask: **confirm before we act?**

Do not act until the user confirms.

## Question format

```
❓ **Q1** — **<title>**: <body; choices if useful>

➡️ Recommended: <your answer>
```

Keep a round to **3–7** questions. Prefer concrete choices over open essays.

## Facts vs decisions

| Kind | Who |
|------|-----|
| Facts (files, stack, existing APIs, TODO, cache) | You — grep/read; spawn a read-only look-up if needed; do not block the rest of the frontier |
| Decisions (scope, UX, risk, what to cut) | User — ask and wait |

Manifest + lean cache first (`/load-project-cache-first` if not already loaded). Cite cache files in the first grilling round.

## Output (when frontier is empty)

```markdown
grill: topic=<slug>; rounds=N; open=0
shared:
- …
next: /orchestrator | /todo-specialist-agent | /research-deep-dive
```

No source edits. No tickets until the user says go.

## Anti-patterns

- Asking things you could grep
- One giant questionnaire that mixes dependent questions
- Implementing "just the obvious part" mid-grill
- Declaring alignment without an empty frontier

## Related

- Source: https://github.com/mattpocock/skills
- Ports: `reports/research/ports/skills-sh/README.md`

# .github/prompts/ — Project Prompt Library

This directory contains reusable, cache-aware prompts designed to reduce token usage and improve context accuracy across this project.

## Manifest-First (Required)

Use `.github/project-manifest.yaml` as the first read in every session.
It defines stack assumptions, key file paths, and lean token policy defaults.

Default cost mode should be `token_policy.mode=lean`.

## Skill chains (on-demand)

Use the **`chain`** skill (`.github/skills/chain/SKILL.md`, invoke `/chain`) to auto-compose skills and prompts from `chains/registry.yaml` with one shared cache load. Registry: `CHAIN.md`. Audit: `scripts/chain-audit.sh`.

## Master Loader (Start Here)

**`load-project-cache-first.prompt.md`** — The canonical entry point for almost every session.

- Forces agents to read manifest + minimal cache first.
- Enforced by `.github/copilot-instructions.md` (session startup order, step 3).
- Use this (or `daily-standup-with-cache.prompt.md`) at the beginning of normal work.

## Recommended Daily Prompt

**`daily-standup-with-cache.prompt.md`** — Best all-rounder for most development and review sessions.

**`daily-standup-generic.prompt.md`** — Lightweight standup variant for stack-agnostic projects.

Combines:

- Local codebase cache (manifest-guided)
- Current daily TODO
- Numbered open concerns from CONCERNS.md

## Task-Specific Cache-Aware Prompts

| Prompt | When to Use | Key Cache Files It References |
| ------ | ----------- | ----------------------------- |
| `beta-ready-checklist.prompt.md` | Determining if a repository is truly beta-ready | README.md, CONCERNS.md, latest TODO |
| `setup-cicd-beta.prompt.md` | Defining/implementing a generic CI/CD baseline for beta | README.md, CONCERNS.md, .github/workflows |
| `filament-panel-review.prompt.md` | Reviewing or auditing any of the 7 Filament panels | STRUCTURE.md, ARCHITECTURE.md, CONCERNS.md |
| `security-audit-using-cache.prompt.md` | After dependency changes or form input/rendering work | CONCERNS.md, CONVENTIONS.md, copilot-instructions.md |
| `model-schema-check.prompt.md` | Before/after migrations or suspected schema drift | CONVENTIONS.md, TESTING.md, CONCERNS.md |
| `read-codebase.prompt.md` | Full initial scan or major cache refresh (rare) | All of `docs/codebase/` + source |
| `amazon-ses-setup.prompt.md` | Amazon SES domain email setup (send + receive) | INTEGRATIONS.md, CONCERNS.md, DO/AWS skills |
| `aws-route53-dns-setup.prompt.md` | Route 53 DNS for domains and SES email records | INTEGRATIONS.md, CONCERNS.md, SES skill |
| `paypal-integration.prompt.md` | PayPal payments and billing document integration | INTEGRATIONS.md, CONCERNS.md, billing flows |
| `prompt-patterns.prompt.md` | Prompt engineering patterns (grounded RAG, Socratic review, strict formatting, complex prompts). Load when authoring skills/prompts/graders/agents. | `reports/research/prompt-patterns.md` (primary reference) |

Synced from `.grok/prompts/` via `scripts/sync_grok_to_github_claude.py`. Full procedural detail also lives in [`.github/skills/`](../skills/).

## How to Invoke

In VS Code Copilot Chat, type the prompt name (e.g. `/load-project-cache-first` or just paste the filename).

Agents should cite the specific cache files they used in every response.

## Practical Invocation Examples

Single-prompt examples:

- `/daily-standup-generic Focus on CI/bootstrap gaps`
- `/setup-cicd-beta Create a minimal stack-agnostic CI baseline`
- `/beta-ready-checklist Full repository beta gate check`

Orchestrator multi-step example:

- `/orchestrator Add onboarding docs, add CI baseline, run beta checklist, and update TODO with pass/fail outcomes.`

Multiple instructions for different agents in one request (recommended format):

1. `Use todo-specialist-agent to sync TODO scope for today's objective.`
2. `Use github-expert to propose workflow updates and required checks.`
3. `Use test-safety-agent to define minimal validation gates.`
4. `Use readme-specialist to update docs and usage examples.`
5. `Return one consolidated summary with file-level changes.`

When sending multi-agent requests, keep each instruction action-oriented and include expected output (for example: "update file", "return checklist", "summarize risks").

## Maintenance

- Update this README when adding or retiring prompts.
- Keep all prompts manifest-driven and avoid hardcoded paths where possible.
- Last updated: 2026-06-29 (added prompt-patterns from Anthropic tutorial distillation).

**Related**: [copilot-instructions.md](../copilot-instructions.md) — contains the mandatory session startup order that now requires cache loading.

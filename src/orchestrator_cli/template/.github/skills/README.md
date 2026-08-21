# `.github/skills/` — Copilot slash-command skills

Project-scoped skills synced from `.grok/skills/` for GitHub Copilot compatibility. Each `SKILL.md` with `user-invocable: true` is invocable as a slash command in Copilot Chat.

**Source of truth for Grok**: `.grok/skills/` (primary). Re-sync with:

```bash
python3 scripts/sync_grok_to_github_claude.py
```

## Session start

| Skill | Use when |
|-------|----------|
| `load-project-cache-first` | Every session; master cache loader |
| `daily-standup-with-cache` | Default dev/review session opener |
| `read-codebase` | Onboarding or full cache refresh |
| `cache-efficient` | Token-efficient cache-first mode |
| `chain` | Auto-compose skills/prompts with shared cache + minimal handoffs |

## Audits and reviews

| Skill | Use when |
|-------|----------|
| `filament-panel-review` | Filament panel/resource audits |
| `model-schema-check` | Pre/post migration schema drift (test DB only) |
| `schema-audit-agent` | Read-only schema/migration deep dive |
| `security-audit-agent` | Auth, permissions, consent, secrets |
| `test-safety-agent` | Test DB safety enforcement |
| `eval/maintenance-task` | Post-maintenance production readiness evals |

## Specialists

| Skill | Use when |
|-------|----------|
| `laravel-expert-agent` | Laravel 12 + Filament 5 architecture/code |
| `mysql-database-expert` | MySQL, Eloquent, Python DB work |
| `test-specialist-agent` | Writing/improving Pest tests |
| `todo-specialist-agent` | TODO file maintenance |
| `readme-specialist` | README and docs polish |
| `branch-context-agent` | Branch vs TODO alignment |
| `github-expert` | GitHub Actions, workflows, PR hygiene |

## Guardrails and runtime

| Skill | Use when |
|-------|----------|
| `git-workflow-guardrails` | Safe commit/push, branch promotion, tagging |
| `ddev-local-runtime` | Enforce DDEV for all local project commands |
| `ddev-cleanup` | End-of-day drift check, ddev stop, cache/TODO, commit and push |
| `digitalocean-app-platform-docr-deploy` | DO hosting, CI deploy, safe DB updates |
| `amazon-ses-email` | Amazon SES send + receive setup |
| `aws-route53-dns` | Route 53 DNS for domains and email records |
| `paypal-billing-integration` | PayPal payments and billing documents |
| `web-build-design` | SaaS marketing pages and portal UX |
| `project-drift-guardian` | Avoid drift at all costs (requirements, CI gates) |
| `prod-db-maintenance` | Production DB import/update agent slot |
| `ai-engineering-maturity` | 8-stage AI engineering maturity assessment |

## Related

- Prompts: [`.github/prompts/`](../prompts/)
- Agents: [`.github/agents/`](../agents/)
- Grok native: [`.grok/skills/`](../../.grok/skills/)
# Skills reference

[UPDATED 2026-07-07]

## Overview

Grok skills live in `.grok/skills/`. They sync to `.github/skills/`, `.copilot/skills/`, and `.claude/commands/`. 

**Machine catalog:** `chains/registry.yaml` (skills section + chains).

**Full human catalog with instructions, purposes, and "Use when":** [.grok/skills/README.md](../../.grok/skills/README.md) — this is the most complete and current list.

Each `SKILL.md` (user-invocable) provides the detailed instructions, allowed-tools, step-by-step processes, examples, and purpose.

After any skill edit: `python3 scripts/sync_grok_to_github_claude.py` then `python3 scripts/check_name_alignment.py`.

**Description budget:** keep frontmatter `description` ≤ `token_policy.skill_description_max_chars` (220). See [skill-description-budget.md](skill-description-budget.md). Lint: `python3 scripts/lint-skill-descriptions.py`.

## Orchestrator tier (core template)

See the comprehensive table in [.grok/skills/README.md](../../.grok/skills/README.md#orchestrator-template-tier-orchestrator) for slash, source, and detailed "Use when" purposes. Highlights:

- `/chain`, `/documentation-specialist`, `/readme-specialist`, `/ddev-cleanup`, `/orchestrator-deploy`, `/docx`, `/skill-creator`, `/loop-*` family, `/cache-*`, etc.

## Session, audit, specialist, guardrails & integrations

Full details and purposes (including new ones like `app-compound-gate`, `frontend-web-design-expert`, `github-ci-readiness-expert`, `project-drift-guardian`, `amazon-ses-email`, `aws-route53-dns`, `paypal-billing-integration`, `didit-identity-integration`, `loqate-address-integration`, `ai-engineering-maturity`, `mysql-concurrency-test`, etc.) are documented in [.grok/skills/README.md](../../.grok/skills/README.md).

Key categories there:
- Session start commands
- Audit / review commands
- Specialist agents
- Guardrails & runtime (including DO, SES, DNS, billing, identity tools)
- AI Engineering Maturity

## App tier (wave / forked projects)

Apply when `stack.framework` != generic (e.g. laravel). Full list and per-project specializations in `chains/registry.yaml` and the skills README above. Examples: `/laravel-expert-agent`, `/mysql-database-expert`, domain tools, etc.

## Verify & maintain

```bash
python3 scripts/check_name_alignment.py
bash scripts/chain-audit.sh
```

New skills: add to `chains/registry.yaml` (skills section) **and** `.grok/skills/README.md`, then sync.

## Next steps

- [Full catalog with purposes & instructions](../../.grok/skills/README.md)
- [Chains reference](chains.md)
- [Documentation guide](../guides/documentation.md)
- [Chains and skills guide](../guides/chains-and-skills.md)

## Related

- [Reference index](index.md)
- [Manifest](manifest.md) — for stack-specific skills
# Loqate Address Capture Setup Prompt for project

**Context (load first via cache):** Laravel + Livewire/Filament address forms. Canonical API: `.grok/skills/loqate-address-integration/references/loqate-api-canonical.md`. Export: `exports/loqate-integration-prompt.md`. Integrated with drift-guardian, security-audit, laravel-expert, eval.

**Your task:** Guide Loqate Find + Retrieve per canonical ref only. Output:
- `LOQATE_API_KEY` setup (account.loqate.com).
- Backend proxy routes (key never client-side): Find v1.10 + Retrieve v1.20 HTTPS.
- Type-ahead UX: Container handling, debounce, Retrieve on select.
- Normalized address columns on Signer/Customer models.
- Rate limiting + throttle on proxy.
- Drift/CI: guardian; update `docs/codebase/INTEGRATIONS.md`.
- After: `/eval-maintenance-task --task=loqate-address`.

**Format:** Cache-first. Short if `/cache-efficient`. End with Next + test Find/Retrieve commands.

**Skill:** `.grok/skills/loqate-address-integration/SKILL.md`
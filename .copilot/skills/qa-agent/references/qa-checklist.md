# QA Checklist (Lightweight)

**Purpose:** Reusable quality assurance gate for agentic work. Use before merge, pre-deploy, after complex sessions, or on demand.

This file is the single source of truth for what "good quality" means. The qa-agent must run through (or explicitly address) these items and cite evidence.

---

## 1. General (Reusable Across Projects)

- **Cache-first discipline**: Manifest + key spine docs (CONCERNS, CONVENTIONS, TESTING, ARCHITECTURE, TODO) loaded and cited in report.
- **Safety & isolation**: All tests, DB ops, destructive actions run only against test / :memory: targets. Never live prod data without explicit user approval + backup.
- **Functional correctness**: Requested behavior works. Edge cases, error paths, and failure modes exercised (via tests or manual verification).
- **Test adequacy**: Critical paths have tests. New/changed code has corresponding test updates or justified gaps. Negative cases + integration points covered.
- **Maintainability**: No unjustified file bloat, spaghetti conditionals, thin wrappers, or logic in the wrong layer. "Code judo" simplifications considered.
- **Compliance**: Follows project AGENTS.md / CLAUDE.md / CONVENTIONS. No policy violations.
- **Outcomes verified**: Not just "code looks good" — actual commands succeeded, resources created correctly, side effects match request.
- **Report & artifacts**: Clear sign-off (READY | CONDITIONAL | BLOCKED). Dated report written. Handoff token ≤80 chars for chains.
- **Rollback / reproducibility**: Backups taken where modifications occurred. Commands are reproducible (scripts preferred over one-liners).

---

## 2. Project Specializations

Load the specialization file for the target wave project from `references/<project>-specializations.md`.

Available specializations (wave projects):

- `facebook-stats-specializations.md` — Meta Ads, audiences, campaigns, rotation, feeds, facebook-business SDK.
- `google-stats-specializations.md` — Google Ads / GA4, customer match, feeds, reporting.
- `e-ndsign-specializations.md` — E-sign flows, Didit identity, Loqate address, PayPal billing, PDF/canvas signatures, compliance.
- `ndestates-io-specializations.md` — Licensing/trials, PayPal, customer portal, real-estate data.
- `jerseyhouseprices-specializations.md` — Property listings, pricing data, search, user accounts, real estate domain.
- `lightstone-specializations.md` — Admin dashboard, regression coverage, auth in admin, data integrity.
- `mailchimp-specializations.md` — Mailchimp API, audiences, campaigns, webhooks, consent/compliance, email automation.

For remaining projects (e.g. ndestates, or future wave apps): use the General section + create your own `<project>-specializations.md` following the pattern.

This isolates project-specific domain risks so the general checklist + qa-agent remain portable across wave deployments.

### Sign-off Criteria
**READY**
- All critical items green.
- No open high-severity domain risks.
- Tests green via proper gates.
- Report includes evidence + citations.

**CONDITIONAL**
- Low/medium items or docs/todo updates required.
- Clear list of conditions + owners.

**BLOCKED**
- Any critical functional, safety, or domain risk (e.g. live mutation risk, broken rate limiting, test DB violation).
- Must be resolved before merge/deploy.

---

## 3. Usage Patterns

- `/qa-agent` — default scan of current changes or recent session work.
- `/qa-agent pre-pr` or `scope: recent changes pre-pr`
- `/qa-agent deep 'campaign rotation and audience attachment'`
- After bug-hunt or complex analysis: `/qa-agent gate`
- In chains: `/chain qa-pre-deploy`

The qa-agent produces `reports/qa/YYYY-MM-DD-qa-[scope].md`

---

## 4. Porting to Another Project (Reusable)

1. Copy `.grok/skills/qa-agent/` to the target repo.
2. Keep `references/qa-checklist.md` (general only).
3. Create `references/<your-project>-specializations.md` modeled on an existing one (e.g. `facebook-stats-specializations.md` or `mailchimp-specializations.md`).
4. Update SKILL.md and agent prompts to load your specialization file.
5. Reference your `docs/codebase/TESTING.md`, `CONCERNS.md`, etc.
6. Optionally register in `chains/registry.yaml`.
7. Add `/qa-agent` examples to your CLAUDE.md / quick reference.

The general section + structure is designed to be stable across orchestrator-based projects.

Keep the maker/checker spirit: the agent reports; human (or separate verifier) decides final merge.
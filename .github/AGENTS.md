
# Project Custom Subagents

This file defines specialized subagents for recurring, high-stakes operations in this project. Each subagent has restricted scope to ensure correctness and safety.

## Orchestrator v2 (Advanced)

**Invocation**: `/orchestrator <request>`

**Purpose**: Token-efficient decomposition and coordination of complex tasks with mandatory TODO sync, manifest-first loading, and cache-first behavior.

**Key Improvements**:

- Always syncs with root TODO file first
- Aggressive cache reuse to save tokens
- Estimates token cost per step
- Requires TODO updates as part of completion

## Specialized Agents

### 1. Schema Audit Agent

**Invocation**: `/schema-audit-agent <question>`

**Purpose**: Verify database schema integrity, detect migration gaps, and report model/schema mismatches.

**Scope**: Read-only exploration of migrations, models, and traits. Run safe MySQL queries only.

### 2. Security Audit Agent

**Invocation**: `/security-audit-agent <scope>`

**Purpose**: Run security and permission-related checks, especially after changes to forms, consents, or authentication.

### 3. Test Safety Agent

**Invocation**: `/test-safety-agent <scope>`

**Purpose**: Assess test coverage and safety before and after code changes.

### 4. Laravel Expert Agent

**Invocation**: `/laravel-expert-agent <task>`

**Purpose**: Provide architecture-compliant Laravel solutions following project conventions (Services first, traits, Filament patterns, etc.).

### 5. Branch Context Agent

**Invocation**: `/branch-context-agent <feature/xxx>`

**Purpose**: Keep work aligned with current branch goals and scope.

### 6. Python Expert Agent

**Invocation**: `/python-expert-agent <task>`

**Purpose**: Idiomatic, type-annotated Python solutions for Flask, FastAPI, Django, scripts, and pytest. Service-layer first, dependency-light, 12-factor config. Declares HTTP contract + env vars + test command as lane outputs in multi-lane plans.

### 7. Frontend Expert Agent

**Invocation**: `/frontend-expert-agent <task>`

**Purpose**: UI work across Livewire 3, React/Next.js, Vue 3, HTMX, and Tailwind/daisyUI. Accessibility (WCAG AA), component composition, and progressive enhancement. Declares component public API + consumed endpoints as lane outputs in multi-lane plans.

### 8. MySQL Database Expert

**Invocation**: `/mysql-database-expert <task>`

**Purpose**: MySQL query design, indexing, performance, and schema work. Pairs with `schema-audit-agent` for read-only verification.

### 9. Test Specialist Agent

**Invocation**: `/test-specialist-agent <scope>`

**Purpose**: Write and improve tests (Pest, PHPUnit, pytest, vitest). Distinct from `test-safety-agent`, which assesses coverage and risk.

### 10. TODO Specialist Agent

**Invocation**: `/todo-specialist-agent <action>`

**Purpose**: Manage, prioritize, and synchronize the daily TODO list at the path defined in `.github/project-manifest.yaml` (`paths.todo_dir`).

### 11. GitHub Expert

**Invocation**: `/github-expert <task>`

**Purpose**: GitHub workflows, branching strategy, PR processes, CODEOWNERS, branch protection, release automation.

### 12. README Specialist

**Invocation**: `/readme-specialist <task>`

**Purpose**: Documentation, README, and markdown updates. Maintains `docs/codebase/` cache files.

---

## Multi-Lane Orchestration (New)

The Orchestrator v2 supports **multi-lane parallel execution** (Shape B in its plan JSON) for tasks that span multiple domains (e.g. DB + Python service + frontend).

- Each lane is owned by exactly one specialist agent from the list above.
- Lanes with `depends_on: []` run concurrently after approval.
- Each lane MUST declare `contract_outputs` (API shape, table columns, component props) — this is the coordination boundary.
- `merge_gates` synchronize dependent lanes via `contract_check`, `integration_tests`, `manual_review`, or `security_review`.

See `.github/prompts/orchestrator-v2.prompt.md` (Phase 2 and Phase 3b) for the full schema and rules.

---

## When to Use the Orchestrator

Use the Orchestrator for **any** instruction that includes more than one of the following:

- Multiple new or modified features
- Changes spanning Models + Services + Filament + Tests
- Significant modifications to document/lease/consent workflows
- Anything touching audit trails, permissions, or core tenancy logic

**Example Invocation**:
`/orchestrator Implement lease expiry email notifications, update the main dashboard widgets to show upcoming expiries, add consent logging for notification events, and ensure all changes are fully tested and audited.`

## Multi-Agent Instruction Patterns

Use this format when you want one orchestrated request to drive several specialized agents:

1. State the overall goal in one sentence.
2. Provide numbered agent assignments.
3. Define expected output for each assignment.
4. Ask for one final consolidated summary.

Example:

1. `Goal: prepare this repository for beta workflow readiness.`
2. `todo-specialist-agent: align TODO with remaining blockers.`
3. `github-expert: propose/adjust workflow files for CI and release.`
4. `test-safety-agent: define minimum test/validation gate.`
5. `readme-specialist: add user-facing usage examples and quickstart guidance.`
6. `Return: changed files, residual risks, and next 3 actions.`

---

## Mandatory Rules for All Agents

- **Manifest-First**: Every agent must read `.github/project-manifest.yaml` before any other context load.
- **Cache-First**: Every agent then loads context via `load-project-cache-first.prompt.md` or `daily-standup-with-cache.prompt.md`.
- Use manifest-defined paths and token policy (`token_policy.mode`) instead of hardcoded assumptions.
- In `lean` mode, read only the minimum relevant files and prefer section-level summaries.
- Always cite which cache files were used in responses.

**Last Updated**: June 2026  
**Related Files**: `.github/prompts/multi-faceted-instruction.prompt.md`, `copilot-instructions.md`

---
name: acquire-codebase-knowledge
description: "Map, document, and onboard into any project codebase."
argument-hint: 'Optional focus, e.g. "scripts only", "architecture and database", "web interface", "docker"'
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# Acquire Codebase Knowledge

Produces seven populated documents in `docs/codebase/` (`STACK.md`, `STRUCTURE.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `TESTING.md`, `CONCERNS.md`) covering everything needed to work effectively on **the repository where this skill is installed**.

## Critical rule: detect the host project's stack

This skill is **portable** — it ships with the orchestrator template but runs **inside the target repo** (Laravel app, Python service, orchestrator template, etc.). Never assume a stack from:

- Where the skill was authored (e.g. google-stats, project)
- Another project in the wave inventory
- Orchestrator template defaults (`stack.framework: generic` is a placeholder, not this repo's stack)

**Always** derive stack from the **installed project's** files: `project-manifest.yaml`, `scan.py` output (`=== DETECTED STACK ===`), manifests (`composer.json`, `package.json`, …), entry points, and targeted reads. If manifest and scan disagree, document both and flag `[ASK USER]`.

Only document what is verifiable from files or terminal output — never infer or assume. Follow manifest-first loading (`.claude/project-manifest.yaml` or `.github/project-manifest.yaml`), then project security rules from `copilot-instructions.md` / `.github/skills/copilot-instructions/SKILL.md`.

## Output Contract (Required)

Before finishing, all of the following must be true:

1. Exactly these files exist (or are refreshed) in `docs/codebase/`: `STACK.md`, `STRUCTURE.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `TESTING.md`, `CONCERNS.md`. Add `[UPDATED YYYY-MM-DD]` markers on refreshes.
2. Every claim is traceable to source files, config, or terminal output.
3. Unknowns are marked as `[TODO]`; intent-dependent decisions are marked `[ASK USER]`.
4. Every document includes a short "Evidence" list with concrete file paths (prefer absolute from repo root).
5. Final response includes numbered `[ASK USER]` questions and intent-vs-reality divergences.
6. Reference the project's security rules and TODO carry-forward workflow.

## Workflow

Copy and track this checklist:

```
- [ ] Phase 0: Load manifest (stack, runtime, paths) — do not hardcode stack assumptions
- [ ] Phase 1: Run scan, read intent documents (README, TODO/, copilot-instructions, existing cache)
- [ ] Phase 1.5: Perspective pass — multi-lens questions (max 20, tagged) before source reads
- [ ] Phase 2: Investigate using perspective agenda + inquiry checkpoints
- [ ] Phase 3: Populate / refresh all seven docs in docs/codebase/ (cite lens per section)
- [ ] Phase 4: Validate docs against checkpoints, present findings, resolve [ASK USER] items
```

### Phase 0: Manifest-first (host project)

1. Confirm **current working directory is the target project root** (where `docs/codebase/` will be written).
2. Read `.claude/project-manifest.yaml` (or `.github/project-manifest.yaml`) for `stack`, `runtime`, and `paths` **of this repo**.
3. Treat manifest `stack.*` as hints only until confirmed by scan + file evidence.
4. If stack is ambiguous after scan, load `references/stack-detection.md` and reconcile before writing `STACK.md`.

### Phase 1: Scan and Read Intent

1. Run the bundled scanner from the project root. Prefer the project's runtime when manifest says `ddev`:

   ```bash
   # DDEV projects (manifest runtime.environment_manager = ddev)
   ddev start
   ddev exec python3 "$SKILL_ROOT/scripts/scan.py" --output docs/codebase/.codebase-scan.txt

   # Fallback (orchestrator template, host-only, etc.)
   python3 "$SKILL_ROOT/scripts/scan.py" --output docs/codebase/.codebase-scan.txt
   ```

   `scan.py` also writes `docs/codebase/.codebase-freshness.txt` (≤35 lines) for cache-efficient / standup spine. Agents in lean mode must **never** Read the full `.codebase-scan.txt`.

   `$SKILL_ROOT` = absolute path to this skill (`.github/skills.github/skills/acquire-codebase-knowledge/SKILL.md`).

2. Read key intent / standing documents first:
   - README.md
   - `.github/copilot-instructions.md` or `.github/skills/copilot-instructions/SKILL.md`
   - `CLAUDE.md` / `AGENTS.md` if present
   - `TODO/` (latest dated file)
   - Existing `docs/codebase/` files (if present) to mark freshness
   - `.copilot/memories/INDEX.md` for prior cache pointers

3. Read `=== DETECTED STACK ===` from `.codebase-scan.txt` — this is the scan's view of **this** repo's stack.
4. Summarize the stated project purpose from README/TODO/manifest before diving into source.
5. If scan stack ≠ manifest stack, note divergence before Phase 1.5.

### Phase 1.5: Perspective pass (required before source reads)

Load `references/perspective-lenses.md`. Using **only** Phase 1 outputs (scan, README, TODO, manifest, existing cache):

1. Apply four default lenses: Developer, Operator, Security, Product/stakeholder.
2. Add **Compliance** lens only when manifest `stack.uses_database: true` or cache/TODO signals CDD, consent, e-sign, or audit.
3. Emit 3–5 questions per lens (**max 20 total**). Tag each: `answerable-from-cache` | `needs-source-read` | `[ASK USER]`.
4. List **cross-lens conflicts** (e.g. security vs delivery speed).
5. Optionally persist `reports/codebase/.perspective-pass.md`.
6. Build **investigation priority** list for Phase 2.

**Do not read application source in Phase 1.5.** Resolve all `answerable-from-cache` items from scan and standing docs first.

### Phase 2: Investigate

Use the **Phase 1.5 investigation priority** + `references/inquiry-checkpoints.md` for the per-template question list.

If stack detection is ambiguous, also load `references/stack-detection.md`.

**STACK.md must describe only what this repo uses** — e.g. Laravel 12 + Filament on project, generic orchestrator on the template repo, Flask + SQLite on a Python app. Do not copy stack text from other projects or from skill origin history.

**Stack-specific surfaces to detect** (evidence only — do not assume):
- Web frameworks (Laravel, Next.js, Django, Flask, etc.) from manifests and entry points
- Database layer (migrations, models, schema files)
- CI/CD (`.github/workflows/`, GitLab CI, Jenkins, etc.)
- Container runtime (Dockerfile, compose, DDEV config)
- External integrations (API clients, webhooks, payment, email, cloud SDKs)
- Test tooling (Pest, PHPUnit, pytest, Jest, etc.)
- Orchestrator paths (`.grok/`, `chains/`, `LOOP.md`, `docs/codebase/`)

### Phase 3: Populate / Refresh Templates

Copy (or refresh) each template from `assets/templates/` into `docs/codebase/`. Fill in this order using real evidence from the scan + targeted reads:

1. STACK.md — languages, frameworks, runtime, package managers, CI, containers
2. STRUCTURE.md — top-level dirs, entry points, orchestrator/agent paths
3. ARCHITECTURE.md — data flow, layers, services, key patterns
4. CONVENTIONS.md — naming, linting, commits, TODO workflow, runtime rules
5. INTEGRATIONS.md — APIs, databases, queues, third-party services
6. TESTING.md — test frameworks, commands, coverage, safety rules
7. CONCERNS.md — risks, debt, security surface, cache staleness

Use `[TODO]` for anything that cannot be determined from code. Use `[ASK USER]` where team intent is required.

Where a section was driven by a perspective lens, note it briefly (e.g. `Lens: Operator, Security` in section intro or Evidence).

### Phase 4: Validate, Repair, Verify

Run the mandatory validation loop (use `references/inquiry-checkpoints.md`):

- Validate each doc.
- Every non-trivial claim must have at least one concrete evidence path.
- Fix and re-validate until clean.
- Present summary of all seven documents.
- List every `[ASK USER]` as numbered questions.
- Highlight Intent vs. Reality divergences.

Then end with:
- Cache Status (which files were created/updated + freshness markers)
- 1-2 example follow-up prompts the user can use against the new cache
- Recommendation to run `.github/prompts/load-project-cache-first.prompt.md` or `/daily-standup` for next session

## Gotchas

- **Large generated dirs**: `node_modules`, `vendor`, `dist`, `coverage`, dated report/output dirs — exclude from deep scans; document at high level only. `scan.py` EXCLUDE_DIRS handles common cases.
- **Manifest vs reality**: If manifest says Laravel but no `composer.json`, flag divergence and use stack-detection reference.
- **Credentials**: Never document real tokens, API keys, or secrets. Describe loading patterns from env / config only.
- **Runtime rules**: Respect manifest `runtime.environment_manager` (DDEV, docker-compose, local).
- **Orchestrator template repos**: Document `.grok/`, `chains/registry.yaml`, `CHAIN.md`, loop spine — not application `app/` unless the project is an app repo.
- **TODO carry-forward**: Note dated `TODO/` workflow in CONVENTIONS when present.

## Anti-Patterns

| Don't | Do instead |
|-------|------------|
| Assume google-stats, Laravel, or any wave-app stack by default | Read **this** repo's manifest + scan `DETECTED STACK` + manifests on disk |
| Guess framework from one file | Check manifests + imports + entry points; use stack-detection reference |
| Assume DB engine from migration naming | Find actual connection config and schema files |
| Document generated artifacts as architecture | Point to generator scripts and naming conventions |
| Put real credentials in docs | Use placeholders; describe env/config loading pattern |

## Bundled Assets

| Asset | When to load |
|-------|-------------|
| `scripts/scan.py` | Phase 1 — run first (multi-language manifest + tree discovery) |
| `references/perspective-lenses.md` | Phase 1.5 — multi-lens questions before investigate |
| `references/inquiry-checkpoints.md` | Phase 2 — full per-template questions |
| `references/stack-detection.md` | Phase 2 — only if stack is ambiguous |
| `assets/templates/*.md` (7 files) | Phase 3 — copy into docs/codebase/ and fill |

After population, knowledge is locally cached for `.github/prompts/load-project-cache-first.prompt.md`, `/daily-standup`, and other agents.

**Canonical entry point** for onboarding and cache maintenance. `.github/prompts/read-codebase.prompt.md` is a backward-compatible alias (thin wrapper). Chains `cache-rebuild` and `documentation-full` invoke this skill for the scan step.

Run when architecture changes significantly or cache exceeds `token_policy.cache_stale_days` (manifest default: 14 days).
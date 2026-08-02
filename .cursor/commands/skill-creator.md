# /skill-creator

> Create new skills, modify and improve existing skills, and measure skill performance with quantitative evals, parallel subagent runs (with/without or old/new baselines), grading, benchmark aggregat...

**Platform:** Cursor · same skill as Grok `/skill-creator` · Claude `/skill-creator`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `e.g. 'create foo-skill for X', 'improve loop-verifier with new assertions', or describe the capability`

# Skill Creator (orchestrator)

**Cache is king.** Always begin with manifest + lean cache. This is a high-cost meta-tool for loop engineering — it rigorously measures and iterates the skills that loops and chains invoke.

**Status:** Skeleton + references. Full automation (grader harness, parallel spawn_subagent execution, viewer, description loop) is being ported in phases (see reports/research/skill-port-plan.md). For now, follow the workflow with manual subagent guidance + scripts as they land.

## Core Loop (adapted for Grok/orchestrator)

1. **Capture intent** — Interview user or extract from conversation. Clarify:
   - What the skill should do and when it triggers.
   - Expected outputs and verifiable success criteria.
   - Whether objective evals make sense (prefer for file transforms, data, code, fixed workflows; subjective for style/art may stay qualitative).

2. **Draft the skill** — Write SKILL.md with clear frontmatter (name + short "pushy" description). **Description budget:** ≤ `token_policy.skill_description_max_chars` (default **220**). Grok injects `name: description` for every skill into the session; long descriptions cause multi‑MB catalog bloat. Put procedure detail in the body, not the description. Run `python3 scripts/lint-skill-descriptions.py` after edits. **Declare `allowed-tools:`** (least privilege per `docs/reference/tools.md`). Use progressive disclosure. Bundle scripts/references/assets only when repeated work appears.

3. **Define evals** — Create 3–6 realistic test cases. Store in `evals/evals.json` (see references/schemas.md). Start with prompts only; add assertions later.

4. **Run evals (parallel where possible)**:
   - For each eval, launch **with-skill** and **baseline** (no-skill or snapshot of previous version) via spawn_subagent.
   - Workspace layout: `reports/skill-dev/<skill-name>/iteration-N/eval-M/{with_skill,without_skill}/outputs/`
   - Capture `timing.json` (total_tokens, duration) and `metrics.json` from subagent results immediately.
   - Use worktree isolation for safety on destructive or stateful tests.

5. **Grade + aggregate**:
   - Spawn grader subagent (or run inline) using references/agents/grader.md (or copied grader prompt).
   - Produce `grading.json` matching the schema exactly (`text`, `passed`, `evidence`).
   - Run aggregation (scripts/aggregate_benchmark.py when ready) → `benchmark.json` with stats + deltas.
   - Analyst pass for patterns (non-discriminating assertions, variance, token/time tradeoffs).

6. **Human review**:
   - Generate static review HTML (prefer `--static` to avoid browser assumptions): `python .../eval-viewer/generate_review.py ... --static /tmp/review.html`
   - User reviews outputs + benchmark; provides `feedback.json`.
   - Kill any temp servers.

7. **Iterate**:
   - Improve skill based on feedback + analyzer insights.
   - Rerun into new `iteration-N+1/`.
   - Repeat until user happy or no meaningful progress.

8. **Description optimization** (advanced):
   - Generate trigger eval set (should/should-not).
   - Run optimization (adapted scripts when complete) to improve frontmatter description.
   - Apply best description.

## Project-Specific Rules (non-negotiable)

- **Manifest + cache first**: Start every major step by loading your platform manifest (`.grok/project-manifest.yaml` for Grok) + `/load-project-cache-first`. Cite cache files. See `docs/reference/manifest.md`.
- **Token discipline**: This burns tokens (see estimates: 1–5M+ per useful cycle). Use `token-usage-meter`, lean mode, small N (start with 2–3 evals), fast model for executors where possible. Record everything.
- **Subagents**: Use `spawn_subagent` (with appropriate capability_mode and isolation). Launch with/without in same turn when possible.
- **Workspace**: Always under `reports/skill-dev/`. Never pollute the target skill dir during iteration.
- **Schemas**: Follow `references/schemas.md` exactly for viewer/agg compatibility (grading expectations use `text`/`passed`/`evidence`).
- **No surprise**: Skills must not contain exploits, secrets, or violate security. Explain "why" instead of heavy MUSTs.
- **L1 default**: New evals/benchmarks are report + human review first. Full auto-fix or L2+ requires explicit approval and verifier-style gates.
- **Integration**: After changes to .grok/skills, consider running sync scripts. Tie into `ai-engineering-maturity`, `loop-engineering`, and `create-skill`.

## References (load as needed)

- `references/schemas.md` — evals.json, grading.json, benchmark.json, timing.json etc.
- `references/agents/grader.md`, `comparator.md`, `analyzer.md` — prompts for subagents.
- `assets/eval_review.html` — for description trigger optimization UI (static version).
- Pulled source material: `reports/research/ports/skill-creator/` (original Anthropic reference).

## Scripts (being ported)

See `scripts/` (utils, aggregate_benchmark, grade_run.py, run-eval harness, viewer generator, etc.). 

**First adaptation done**: `scripts/grade_run.py`
- Collects transcript + outputs + metrics + timing.
- Runs *programmatic* checks for auto-verifiable expectations (file existence, simple contains, counts).
- Prepares a complete `grader_prompt.txt` (injects data into the grader role from `references/agents/grader.md`).
- Writes `grading.json` skeleton (with auto-results + placeholders for LLM parts) matching the schema.
- Usage inside the skill: `python -m scripts.grade_run --run-dir <path-to-run>` then feed the prompt to `spawn_subagent`.

Start with `python -m scripts.grade_run --help`. Adapt more scripts in subsequent phases. Prefer existing orchestrator tools (spawn_subagent + script-not-shell).

## Quick Start (skeleton)

1. `/load-project-cache-first`
2. Discuss intent with user.
3. Draft or edit target skill.
4. Create minimal `evals/evals.json` for 2–3 cases.
5. Manually (or via future harness) run with-skill vs baseline subagents.
6. Grade, review outputs, iterate.

For full details and when scripts are ready, re-read this skill + references.

**High value for loop engineering**: Better measured skills → better loops, chains, and agents.

See the full port plan at `reports/research/skill-port-plan.md` for phases, MCP follow-on, and integration with web-build-design + test skills.

Good luck — keep it lean and cite your cache.

User focus (optional): use any extra chat text as $ARGUMENTS.

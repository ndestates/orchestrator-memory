# Skill Port Plan: Anthropic Skills → Orchestrator (Grok)

**Date**: 2026-06-29
**Source**: /home/nickd/projects/skills (Anthropic agent-skills examples)
**Pulled to**: reports/research/ports/{skill-creator,mcp-builder,other-skills}/
**Target**: Integrate into orchestrator's `.grok/skills/`, `mcp-server/`, existing loop/chain/eval infrastructure.
**Principles**: Manifest-first, cache-first (lean), script-not-shell, subagent orchestration via spawn_subagent, no new runtime deps without explicit approval, model-agnostic where possible (Grok primary), L1 report-only by default for new loops.

## Pulled References (confirmed present)
- skill-creator/
  - SKILL.md (full lifecycle: capture → draft → evals → parallel with/without runs → grade → aggregate benchmark (mean±std) → viewer + feedback loop → improve → description optimization)
  - agents/{grader.md, comparator.md, analyzer.md}
  - references/schemas.md (evals.json, grading.json, benchmark.json, timing.json, metrics.json, comparison.json, analysis.json, history.json — very precise field names required by viewer)
  - scripts/{aggregate_benchmark.py, run_eval.py, run_loop.py, improve_description.py, utils.py, generate_report.py, package_skill.py, quick_validate.py}
  - eval-viewer/{generate_review.py (stdlib http + HTML), viewer.html}
  - assets/eval_review.html (for description trigger optimization UI)
- mcp-builder/
  - SKILL.md (4-phase: Research/Plan → Implement → Review/Test → Create Evaluations)
  - reference/{mcp_best_practices.md (naming, pagination, annotations, formats, transport, security), evaluation.md (10 hard read-only stable verifiable multi-hop Qs), python_mcp_server.md, node_mcp_server.md}
  - scripts/{evaluation.py (harness using anthropic + mcp client), connections.py, example_evaluation.xml, requirements.txt}
- other-skills/
  - webapp-testing/{SKILL.md, scripts/with_server.py (multi-server lifecycle + Playwright), examples/}
  - frontend-design/SKILL.md (opinionated non-templated design lead, token system, self-critique, rubric thinking)
  - theme-factory/{SKILL.md, themes/*.md (10 curated palettes+fonts), theme-showcase.pdf}

Document skills (docx/pptx/xlsx/pdf) were reviewed but deprioritized (licensing + already partially referenced globally).

## Why These? Gaps vs Current Orchestrator
- Orchestrator excels at: loop engineering (L1 triage + verifier + compound), cache discipline, chains (shared cache, minimal handoff), spawn_subagent multi-lane, domain experts, MCP server (FastMCP + manifest/cache-first tools + audit + sandbox), create-skill (light scaffolding), narrow eval-maintenance-task + ai-engineering-maturity.
- Missing: systematic **skill authoring + quantitative benchmarking + iteration harness** (skill-creator is meta-loop engineering).
- Missing: **MCP tool quality evaluation methodology** and codified best practices (orchestrator_mcp exists and uses FastMCP, but quality is manual).
- Partial overlap: test/QA, web-build-design (can absorb design patterns), basic skill creation.
- "Other models": web testing harness + distinctive design guidance + reusable themes add immediate value without core changes.

## Firm Port Strategy & Adaptations
1. **Names & Placement** (fit existing conventions)
   - Primary: `.grok/skills/skill-creator/` (SKILL.md + references/ + agents/ + scripts/ + assets/). User-invocable as /skill-creator. Mirrors loop-verifier style (maker/checker split).
   - Enhance existing: `.grok/skills/create-skill/` (global + project) to optionally launch full eval loop.
   - MCP: Copy best practices + evaluation.md into `mcp-server/reference/`. Create supporting `.grok/skills/mcp-quality/` (or extend into existing skills). Keep mcp-builder concepts as guidance for template consumers.
   - Other:
     - webapp-testing → new `.grok/skills/webapp-testing/` or concepts merged into `test-specialist-agent` + `qa-agent`.
     - Design → extend `web-build-design` with `references/themes/` + guidance excerpts (or new light `theme-factory` skill). Add to chain web-design.
   - Agents prompts: either bundle in skill/references/ (preferred for cache) or `.claude/agents/skill-grader.md` etc. (for orchestrator subagent dispatch).

2. **Execution & Subagents**
   - Replace Claude-specific subagent spawning + `claude -p` with:
     - `spawn_subagent` (with capability_mode read-write or execute as appropriate, worktree isolation for safety).
     - Explicit "executor" runs: one with skill mounted/instructed, one baseline (no skill or snapshot old version).
     - Grader/Comparator/Analyzer as focused subagent calls or direct skill references (like loop-verifier).
   - Parallel: spawn multiple in one turn where possible (existing pattern in skill-creator and orchestrator).
   - Timing/token capture: integrate with `token-usage-meter` references; capture from subagent notifications where exposed.
   - Workspace: `<reports/skill-dev/<skill-name>/iteration-N/eval-M/{with_skill,without_skill}/outputs/>` + `grading.json`, `timing.json`, `metrics.json` (mirror schemas exactly where viewer depends on names).

3. **Model & API Differences**
   - Primary: Grok (via host TUI/agent context). Secondary/optional: configurable model for grader (high-reasoning) vs executor.
   - Remove Anthropic SDK hard dep in core paths. MCP eval harness becomes optional or generalized (use mcp client + any model runner; provide Grok example).
   - Description optimization (`run_loop.py`): adapt to use agent self-prompting + train/test split + scoring; fall back to human-in-loop if no direct "claude -p" equivalent.
   - Token discipline: skill-creator SKILL.md **must** enforce cache-first + lean mode + budget awareness.

4. **Schemas & Compatibility**
   - Keep core JSON shapes from schemas.md (they are viewer contracts).
   - Adapt notes/fields: add "tokens", "grok_model", "cache_cited".
   - Viewer: port generate_review.py (stdlib-only good) to produce static HTML by default (no browser assumption in server/CI). Provide `--static` path.

5. **Cache & Token Policy (Non-negotiable)**
   - Creator skill itself starts with `/load-project-cache-first` or equivalent.
   - Evals run in lean mode by default.
   - High cost ops gated (explicit approval or `allow_l2` style).
   - Cite ports + cache in every generated report.

6. **Scripting & Safety**
   - All logic in checked-in Python scripts under the skill (script-not-shell).
   - Use existing patterns: helpers in scripts/, no direct shell in SKILL.md body except via bundled scripts.
   - Sandbox/audit where writes happen (align with mcp sandbox).
   - Destructive baseline snapshots use worktrees or safe copy.

7. **Integration**
   - Chains: possible new `skill-dev` or `skill-qa` chain; register after proven.
   - Loops: skill-creator usable inside compound learning or as L2 pattern.
   - create-skill: after scaffold, offer "run evals with skill-creator?"
   - mcp-server: reference best practices in README + add quality-eval tool or script.
   - ai-engineering-maturity: treat skill measurement as Stage 5/7/8 advancement.
   - Deploy: update deploy scripts + sync_grok if new skill.
   - Docs: update loop-engineering/SKILL.md, CLAUDE.md, README references.

## Phased Firm Implementation Plan (Small, Gated Steps)

**Phase 0: Baseline & Hygiene (do now)**
- [x] Pull references (done: reports/research/ports/).
- Write this plan to disk + TODO sync.
- Audit licenses (skill-creator + mcp-builder appear permissive; note doc skills separately).
- Run `bash scripts/loop-audit.sh` or equivalent before changes.
- Create branch or note in active TODO.

**Phase 1: Skeleton + Schemas (low risk)**
- Create `.grok/skills/skill-creator/SKILL.md` skeleton (high-level workflow adapted to Grok + cache-first mandatory start).
- Copy/adapt `references/schemas.md` → `skill-creator/references/schemas.md` (add Grok notes).
- Add minimal `scripts/utils.py` (parse_skill_md etc.).
- Update `reports/research/skill-port-plan.md` with status.
- Gate: human review of skeleton.

**Phase 2: Grader + Basic Grading Script**
- Adapt `agents/grader.md` → `skill-creator/references/grader.md` (or .claude/agents/).
- Write `scripts/grade_run.py` that implements the grader logic (reads transcript + outputs_dir, produces grading.json matching schema).
- Test manually on a synthetic eval dir for an existing small skill (e.g. loop-verifier or cache-efficient).
- No subagents yet.

**Phase 3: Workspace + Benchmark Aggregation**
- Port core of `aggregate_benchmark.py` (stats, layouts support for eval-N/ with_skill vs without_skill).
- Script `scripts/prepare_workspace.py` or integrated.
- Produce benchmark.json + notes (analyzer freeform patterns).
- Output to reports/skill-dev/...

**Phase 4: Parallel Execution Harness (core value)**
- Main logic in `scripts/run_skill_eval.py` (or equivalent).
- Use spawn_subagent (or documented orchestrator pattern) to launch:
  - With-skill executor (mounts skill instructions or passes SKILL.md path + prompt).
  - Baseline executor.
- Capture timing/tokens/outputs.
- Support multiple evals + runs_per.
- Respect worktree isolation for safety.
- Implement metrics.json capture.
- Gate: run 1-2 simple evals end-to-end on a toy skill.

**Phase 5: Human Review Viewer + Feedback Loop**
- Port `eval-viewer/generate_review.py` + assets (prefer --static HTML output).
- Support previous-workspace for iteration diffs.
- feedback.json roundtrip.
- Viewer shows outputs + benchmark tab.

**Phase 6: Iteration + Improve Flow (full maker/checker)**
- Wire SKILL.md to drive: draft → define evals.json → run → grade/aggregate/viewer → user feedback → edit skill → repeat.
- Add blind comparator + analyzer support (subagent calls).
- Simple history.json tracking.

**Phase 7: Description Optimization**
- Adapt run_loop + improve_description (train/test split, trigger evals).
- Since no direct `claude -p`, use spawn_subagent or orchestrator self-call patterns for "model proposes new description".
- Fallback: emit prompt + let user run.
- UI: static version of eval_review.html.

**Phase 8: MCP Port (parallel or after core)**
- Copy `mcp-builder/reference/mcp_best_practices.md` + `evaluation.md` into `mcp-server/reference/`.
- Update mcp-server/README.md and server instructions.
- Adapt `scripts/evaluation.py` + connections.py minimally (remove hard anthropic, make model configurable or example using available client; keep for stdio/SSE/HTTP).
- Create example XML + instructions for testing orchestrator_mcp itself or new MCPs.
- Optionally create `.grok/skills/mcp-quality/SKILL.md` that guides users through the 4-phase + runs evals.
- Test: create 3-5 stable questions for a subset of current orchestrator_mcp tools.

**Phase 9: Other Models Integration**
- webapp-testing: 
  - New skill `.grok/skills/webapp-testing/` with SKILL + scripts/with_server.py + examples (Playwright is optional/new-dep; document "requires playwright").
  - Or lightweight: add patterns/examples to test-specialist.
- frontend-design + theme-factory:
  - Copy themes/ into `web-build-design/assets/themes/` or new references.
  - Extend web-build-design/SKILL.md with "Ground in subject", "two-pass plan (token system + signature)", self-critique, and "use theme-factory when branding".
  - Add theme-showcase reference (or link).
- Update chains for web-design to optionally pull theme.

**Phase 10: Polish, Wiring, Documentation**
- Enhance create-skill to offer full creator flow.
- Add to CHAINS.md / chains/registry.yaml if a canonical "skill-dev-loop" emerges.
- Update:
  - loop-engineering/SKILL.md (new primitive for skill maturity).
  - ai-engineering-maturity references.
  - CLAUDE.md / .grok/README if needed.
  - Deploy scripts (copy new skill dir).
- Example: run full ported flow on an existing skill (e.g. improve a small one like "cache-freshness-check").
- Add guard: skill-creator itself must pass its own L1-style checks + token report.
- Success demo + report in reports/skill-dev/.

**Phase 11 (future/L2)**: Scheduled skill health watch, auto-suggest evals on skill edits via drift-guardian.

## Risks, Constraints, Mitigations
- **Token explosion**: Evals are expensive. Mitigate: default small N (2-3 evals × 1-2 runs), lean cache, explicit "confirm before heavy run", integrate token-usage-meter, use cheaper executor model.
- **Model mismatch**: Grok may behave differently than Claude on evals/grading. Mitigate: start with qualitative + human review heavy; tune assertions; document variance.
- **Deps**: Playwright (webapp), anthropic (MCP eval script) — make optional, document, gate behind approval. Core skill-creator uses only stdlib + existing spawn.
- **Viewer/server**: Prefer static HTML. Avoid assuming interactive browser in all envs (Cowork/CI).
- **Licensing**: skill-creator/mcp-builder/webapp etc. look Apache-friendly; confirm before final include. Document source.
- **Scope creep**: Stick to port of concepts + minimal scripts. Do not port full document editing engines unless separately requested.
- **Orchestrator specifics**: Always respect ddev-local-runtime (if running inside), test-safety, git-workflow-guardrails on any committed changes.
- **No auto-fix on L1**: New creator flows default to report + human edit.

## Success Criteria (Measurable)
- Can scaffold + run 3 evals on a skill, produce grading.json + benchmark.json with pass rates + deltas.
- Human reviews via generated static HTML + submits feedback.json.
- One iteration improves a real skill measurably (user confirms or blind comparator prefers new).
- MCP best practices referenced in mcp-server + at least one quality eval XML exists + harness runnable (Grok path or documented).
- Webapp or theme patterns used in at least one web-build or test flow.
- All new code follows cache-first in docs; no source reads before manifest in creator.
- Plan items tracked in active TODO.
- New skill passes internal verifier-style checks.

## Immediate Next Actions (after this plan review)
1. Sync this plan + ports into TODO (use todo-specialist or manual).
2. Phase 1 skeleton PR or commit (small).
3. Human approval gate before Phase 4 heavy execution code.
4. Optionally run loop-verifier or similar on this plan doc.

## References (local pulled copies)
See reports/research/ports/...

**Cache cited for this plan**: project manifest, loop-verifier, mcp-server snippets, CLAUDE.md patterns, existing eval/maintenance-task.

This is a firm, phased, constraint-respecting plan. Execute incrementally with gates.

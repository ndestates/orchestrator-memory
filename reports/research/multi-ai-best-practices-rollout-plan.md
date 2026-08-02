# Multi-AI Best Practices Rollout Plan

**Date**: 2026-06-27
**Branch**: feature/gemini-claude-best-practices-rollout
**Source Research**: 
- reports/research/claude_best_practices.md
- reports/research/claude_usage_guide.md
- Original: https://x.com/anatolikopadze/status/2054568935274549597 (18-step guide to using Claude at full capability via Projects, persistent context, "who I am", sparring, efficiency, etc.)

## Goals
- Extract universal best practices from the Claude thread.
- Adapt and make them portable across the project's supported platforms: Grok, Claude (Code), Copilot, and now Gemini.
- Create .gemini/ folder with structure and initial content.
- Improve user (and AI) effectiveness when working with this orchestrator template.
- Maintain the existing sync and portability model (.grok as source of truth where possible).

## Key Best Practices (Universal, from Research)
1. **Persistent Context**: Use Projects (Claude), memories/files (Grok), workspace instructions (Copilot), Gems + knowledge (Gemini). Never re-explain core context.
2. **"Who I am" Profile**: Detailed background (role, goals, style, preferences, what to avoid). Store in knowledge/instructions.
3. **Custom/System Instructions**: Turn profile into default behavior (tone, structure, no preambles, length specs).
4. **Mindset**: AI as thinking partner / sparring partner, not search engine. Ask it to ask you questions first.
5. **Techniques**:
   - Style cloning (provide 3-5 samples + analyze patterns).
   - Sparring: "Attack this ruthlessly, then steelman."
   - Extended / step-by-step thinking.
   - Meta-prompting: "Write the best prompt for [task]".
6. **Efficiency**:
   - Always specify output length upfront.
   - Kill preambles, restatements, disclaimers.
   - Isolate topics (fresh context per major task).
7. **Ready Prompts**: Feynman explainer, personalized planning, expense analysis, thinking partner, ruthless idea stress-test.

## Platform Rollout Plan

### Claude (Code / App)
- Leverage existing `.claude/` (commands, agents).
- Enhance project setup guidance using the "who I am" template.
- Create or adapt a prompt/skill for "claude-project-bootstrap" that helps users set up Projects + Custom Instructions with orchestrator context.
- Reference in .claude/README.md or new guide.

### Grok
- Use `.grok/memories/` (INDEX, repo, session) for persistent "who I am" and context.
- Update `skills/copilot-instructions/SKILL.md` or add new skill "ai-thinking-partner" / "best-practices-setup".
- Grok strengths to highlight: tool use, real-time, direct sparring, humor for creativity.
- Add prompts to `.grok/prompts/` for the ready-to-use ones.
- Leverage `/chain` and `/orchestrator` for the workflow.

### Copilot (GitHub)
- Primary mechanism: `.github/copilot-instructions.md` for persistent instructions.
- Add the "who I am" profile and efficiency rules there.
- Create workspace-specific instructions or chat modes.
- Use `.github/prompts/` for reusable prompt templates.
- Update `copilot-instructions.md` with adapted best practices.

### Gemini (New)
- Created `.gemini/` folder (this rollout).
- Structure:
  - `instructions/` : System/custom instructions.
  - `gems/` : Templates for creating Gems (instructions + knowledge files).
  - `prompts/` and `agents/`.
- Use Gems as the "persistent Projects" equivalent: one Gem per major role (e.g. "orchestrator-thinking-partner", "orchestrator-deploy").
- Upload key files as knowledge: profile, manifest, docs/codebase/README, memories.
- Gemini advantages: long context (good for full files), multimodal if useful.
- Initial artifacts created:
  - README.md
  - instructions/gemini-orchestrator-instructions.md (incorporates best practices)
  - gems/orchestrator-thinking-partner.gem.md

## Implementation Steps (This Branch)
- [x] Commit prior work, new branch created.
- [x] Create .gemini/ structure.
- [x] Extract/adapt "who-i-am" profile template into a reusable prompt (added to .grok/prompts/ + who-i-am-profile-template.md).
- [x] Create top-level prompt "multi-ai-best-practices-setup.md" (in .grok/prompts/). Created dedicated Grok version in reports/research/grok_usage_guide.md.
- [x] Update root README.md, docs/guides/daily-workflow.md, .grok/README.md, docs/codebase/README.md, .grok/memories/INDEX.md to reference the rollout + specific claude_* and grok_usage_guide.md files.
- [ ] Consider extending sync script for Gemini if needed (manual for now).
- [x] Added "who-i-am-template.md" in reports/research.
- [ ] Test: Use the techniques (ask questions first, sparring, efficiency, cache + research load) in sessions.
- [x] Updated TODO with progress. Created grok_usage_guide.md as the Grok-specific document.

## Next / Open
- Full content extraction of exact templates from the X thread (the md files have summaries).
- [x] Make the "who I am" profile + grok_usage_guide + multi-ai prompt part of the orchestrator template's own recommended default setup for users (2026-07-07: `.grok/memories/who-i-am.md`, `setup-who-i-am.sh`, quickstart, load-cache spine).
- Add more Gemini-specific examples.
- Evolve grok_usage_guide.md and claude sources as platform capabilities change.
- Once stable, merge to develop/master and update the sync story.
- Wave rollout now selective (see feature/selective-wave-rollout-control): no more automatic to all diverging apps. Use deploy-template-wave.sh with --all/list/interactive/none.

This makes the orchestrator not just a skill provider, but a **best-in-class multi-LLM workflow enabler**.

## Tool Use Rollout (Added in this iteration)

In addition to workflow best practices, we implemented support for **tools** across platforms:

- MCP is the primary cross-platform tool protocol (already mature in mcp-server/).
- Added:
  - `.gemini/mcp.gemini.example.json` for Gemini + MCP clients (e.g. Cursor Gemini).
  - `.gemini/prompts/gemini-tool-calling-example.md` — function declarations for Gemini native tool calling (maps to MCP tools).
  - `docs/reference/tools/multi-platform-tool-use.md` — central guide.
- Updated instructions/READMEs in .gemini, .grok, .claude, .github/copilot-instructions.md to reference tool usage.
- MCP tools cover: cache access, TODO, loops/state, chains, readonly audits.
- For all: Prefer MCP for clients; fall back to platform function calling (strongest in Gemini/Claude/Grok APIs).
- Copilot: Limited native, but works via MCP in hybrid clients or guide model to use external tools.

This completes tool support parity for the best practices rollout.

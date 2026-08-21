---
description: Invoke multi-ai-best-practices-setup
allowed-tools: Read, Grep, Glob, Bash
---

# Multi-AI Best Practices Setup (Grok, Claude, Copilot, Gemini)

You are helping the user adopt high-leverage workflows for frontier models, based on proven patterns (originally popularized for Claude but universal).

## Core Setup (Do this once per major context)
1. **Persistent Memory**:
   - Claude: Use a Project + upload knowledge files.
   - Grok: Use .copilot/memories/ + start sessions with `/load-cache` or reference key files.
   - Copilot: Use `CLAUDE.md` + workspace context.
   - Gemini: Create a Gem + upload knowledge files; use long context.

2. **"Who I am" Profile** (one-time setup, then loaded every session):
   - Run: `bash scripts/setup-who-i-am.sh` → edit `.copilot/memories/who-i-am.md`
   - Template: `.copilot/memories/who-i-am.template.md` · Guide: `docs/getting-started/who-i-am-setup.md`
   - Agents load `who-i-am.md` from cache spine when present (with `grok_usage_guide.md` for techniques)
   - Mirror the same content to Claude Project / Copilot instructions / Gemini Gem

3. **Custom Instructions / System Prompt**:
   Turn the above into default behavior. Add:
   - "Ask me the 5 most important questions before starting any complex task."
   - "Be a sparring partner: attack ideas ruthlessly then steelman."
   - "Always specify or respect output length. Kill preambles."
   - "Use style cloning if I provide samples."

## Key Techniques
- **Ask questions first**: Never assume.
- **Style cloning**: "Analyze these 3-5 writing samples for patterns. Then [task]."
- **Sparring**: "Attack this plan. Find every weak assumption. Then steelman the strongest version."
- **Meta-prompting**: "Write the best [Grok/Claude/Gemini/Copilot] prompt for [task]."
- **Extended thinking**: Explicitly ask for step-by-step or use model features.
- **Efficiency**: "Keep response under 300 words." "No summaries unless asked."

## Ready-to-Use Prompts (copy/adapt)
- Feynman: "Explain [concept] using simple analogies as if teaching a smart 12-year-old. Check my understanding at the end."
- Stress test: "Act as a ruthless VC. Stress-test this business/idea. Find fatal flaws."
- Thinking partner: "Help me think through [stuck point]. Ask good questions. No solutions until I ask."

Apply these when working on the orchestrator template or helping users adopt it.

**Technical caching (when coding directly against providers):**
- Anthropic (Claude): Use `cache_control={"type": "ephemeral"}` on system prompts, long documents, and tool definitions in the SDK.
  **Important:** These requests *are* respected by Anthropic when using the official SDK correctly (direct calls). Verify via the `usage` object.
  See:
  - `reports/research/anthropic-prompt-caching.py` (standalone runnable examples)
  - `reports/research/claude_usage_guide.md` (includes "Will our caching requests be respected?" section)
  - `reports/research/prompt-patterns.md` (section 6)
- xAI/Grok, Gemini, and Copilot/OpenAI have their own mechanisms (documented in the provider prompt and research guides).
- This is complementary to the orchestrator's own lean cache system (`docs/codebase/`).

**Source files to reference when relevant (load via cache or memories INDEX):**
- reports/research/claude_best_practices.md and claude_usage_guide.md (source 18-step distillation)
- reports/research/grok_usage_guide.md (Grok-optimized version with project cache + tool/MCP adaptations)
- reports/research/who-i-am-profile-template.md

When the task involves AI workflows, best practices, or improving how we use Grok here, explicitly load and follow the Grok usage guide + multi-AI setup. Cite sources (e.g. grok_usage_guide.md:42).

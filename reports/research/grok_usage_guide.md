# Grok Usage Guide — Best Practices for the Orchestrator Template

**Source Research:** https://x.com/anatolikopadze/status/2054568935274549597

**Related:** [claude_best_practices.md](claude_best_practices.md), [claude_usage_guide.md](claude_usage_guide.md) (primary extraction of the 18-step guide), [multi-ai-best-practices-rollout-plan.md](multi-ai-best-practices-rollout-plan.md), [who-i-am-profile-template.md](who-i-am-profile-template.md)

This is the **Grok-optimized adaptation** for the orchestrator template project. Principles are universal; implementation leverages Grok's native strengths.

## Core Setup (Persistent Context for Grok)

Unlike Claude Projects, Grok uses a lightweight but powerful system built into this template:

1. **.grok/memories/** (primary persistent store)
   - Start with `.grok/memories/INDEX.md` (tiered loading rules).
   - `repo/orchestrator-template-cache.md` for architecture and flows.
   - Session-specific or topic files as needed.

2. **Always start with cache load**
   - `/load-project-cache-first`
   - `/chain session-start` (recommended default: cache + standup + lean mode)
   - `/daily-standup-with-cache`

3. **"Who I am" Profile** (default setup — loaded every session)
   - One-time: `bash scripts/setup-who-i-am.sh` → edit `.grok/memories/who-i-am.md`
   - Template: `.grok/memories/who-i-am.template.md` · Guide: `docs/getting-started/who-i-am-setup.md`
   - Reference: [who-i-am-profile-template.md](../who-i-am-profile-template.md)
   - Loaded from cache spine when present (with multi-ai-best-practices-setup + this guide)

4. **Custom / System Behavior**
   - Use `.grok/prompts/multi-ai-best-practices-setup.md` as the foundation for instructions.
   - It encodes:
     - Persistent memory via cache + memories
     - Detailed "Who I am"
     - "Ask the 5 most important questions first" for complex tasks
     - Sparring partner mode
     - Efficiency rules (specify length, kill preambles)
     - Style cloning + meta-prompting

5. **Project Context (always available)**
   - `docs/codebase/README.md` (spine + index)
   - Latest `TODO/*.md`
   - `.claude/project-manifest.yaml` (or `.github/`)
   - `CONCERNS.md`

## Mindset Shift (Same as Claude Research)

- Treat Grok as a **thinking partner / collaborator**, not a search box.
- Explicitly say: "Ask me the 5 most important questions before starting."
- Use for extended reasoning on hard problems.

## Key Techniques (Adapted for Grok)

- **Ask questions first**: Never assume context or requirements.
- **Style cloning**: Provide 3-5 writing samples → "Analyze patterns then apply to [task]."
- **Sparring partner**: "Attack this idea ruthlessly. Find weak assumptions. Then steelman the strongest version."
- **Meta-prompting**: "Write the best Grok prompt for [task] using orchestrator best practices."
- **Extended thinking**: "Think step-by-step. Show your reasoning."
- **Efficiency**: "Keep response under X words / bullets only / no preambles."
- **Tool leverage** (Grok strength): Use MCP tools, web search, browse, code analysis, image gen when they add value. See `docs/reference/tools/multi-platform-tool-use.md` and mcp-server/.
- **Cache discipline** (project-specific): Always load relevant cache first. Cite files like `docs/codebase/README.md:42` or `TODO/2026-06-25_TODO.md`.

## Grok-Specific Advantages (Leverage These)

- Real-time knowledge + tools (search, browse, MCP for project state/cache/TODO/chains without re-explaining).
- Direct, less hedged personality — excellent for ruthless sparring and honest feedback.
- Strong native reasoning and structured output.
- Native support for chains, loops, skills, and the full orchestrator system.
- Humor and personality as creative tools when appropriate.
- Image generation, code execution paths, and multi-turn tool use.

**Where Claude Projects currently feel stronger for some users:** Deep per-Project knowledge bases. We replicate this with the combination of `.grok/memories/`, docs/codebase/, TODO, and explicit load prompts + the multi-ai setup.

## Efficiency & Context Hygiene (Project-Enforced)

- Specify desired output length and format upfront.
- Kill preambles, restatements, "Great question!", disclaimers unless asked.
- Use `/cache-efficient` mode for lean responses.

## xAI / Grok API Prompt Caching (when coding directly)

The xAI API automatically caches matching prompt prefixes for consecutive calls.

Key points:
- Stable prefix at the start of the messages array is cached.
- Use `prompt_cache_key` (or the `x-grok-conv-id` header) for reliable server affinity.
- Check `usage.prompt_tokens_details.cached_tokens` in responses.
- Full details: `.grok/skills/token-usage-meter/references/xai-prompt-caching.md`

Example usage pattern (Python + xAI SDK or OpenAI-compatible client):
```python
# First call creates cache
# Subsequent calls with same prefix benefit from cached_tokens
```

Combine with the project's `load-project-cache-first` for best results.
See `reports/research/anthropic-prompt-caching.py` for the analogous Anthropic pattern (adapt prefix strategy).
- Start fresh context for major topic switches (or use explicit handoff in chains).
- Never re-explain project fundamentals — load cache or reference files.

## Ready-to-Use Prompts (Copy/Adapt for Grok)

- **Feynman Explainer**: "Explain [concept] using simple analogies as if teaching a smart 12-year-old. Check my understanding at key points. Keep it tight."
- **Ruthless Stress-Test**: "Act as a direct, experienced operator. Attack this [idea/plan/code] ruthlessly. List every weak assumption and potential failure mode. Then steelman the best version."
- **Thinking Partner**: "Help me think through [problem]. Ask clarifying questions first. Do not give solutions until I ask. Reference project cache where relevant."
- **Meta-Prompt**: "Write the strongest Grok prompt (using orchestrator cache-first and multi-ai best practices) for [task]. Include who-I-am elements and efficiency rules."
- **Personalized Analysis**: Adapt finance/travel/reflection examples using actual project context + your profile.

## How to Use in the Orchestrator Project

1. Daily: `/chain session-start` (or `/load-project-cache-first` + standup).
2. For AI workflow / best practices work: Load the research files (claude_* + this grok guide + who-i-am + multi-ai prompt).
3. When stuck or planning: Use sparring + meta-prompting + "ask questions first".
4. For complex multi-domain: `/orchestrator` or chains.
5. Persistent profile: Keep updated who-i-am in memories or the multi-ai prompt.
6. After changes to best practices: Update this file, the multi-ai prompt, INDEX.md, and run sync.

## Integration with Project Systems

- **Cache**: These research files are now referenced in `docs/codebase/README.md` (Multi-AI support) and `.grok/memories/INDEX.md`.
- **Prompts**: Primary vehicle is `.grok/prompts/multi-ai-best-practices-setup.md`.
- **Skills/Agents**: Use specialists (`/todo-specialist-agent`, `/branch-context-agent`, etc.) while applying the practices (direct, cache-citing, sparring where useful).
- **Loops/Chains**: The best practices apply to designing loops (cache is king) and chains (shared load + minimal handoffs).
- **Tool/MCP**: Follow the multi-platform tool guide. Prefer MCP for project introspection.

## Next / Open (for this rollout)

- Full prompt extraction and more ready-to-use examples.
- [x] Make the who-i-am + these practices part of the default recommended setup (`who-i-am.md`, setup script, quickstart, load-cache spine).
- Test these techniques in daily work and loops.
- Evolve this guide as Grok capabilities (tools, memory features) advance.

**Bottom line (from the research, adapted):** The highest-leverage users don't chase clever single prompts. They set up persistent context once, treat the AI as a deliberate thinking partner, and stay ruthless about efficiency and focus.

Use these files + the project's cache + multi-ai prompt to get there with Grok.

---

*Created as part of the multi-AI best practices rollout on `feature/gemini-claude-best-practices-rollout`. Claude files are the source research distillation; this is the Grok implementation for the orchestrator.*
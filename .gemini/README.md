# Gemini Integration for Project Template (orchestrator)

**Project**: Reusable orchestrator template for fast start-to-beta delivery. Manifest-first, cache-first AI-assisted delivery. Read **`.gemini/project-manifest.yaml`** for stack and paths (synced from `.github/project-manifest.yaml`).

This directory provides support for Google Gemini (AI Studio, Gemini app, Gems, and IDE integrations like Cursor with Gemini or Gemini Code Assist).

## Structure

- `instructions/` - Base custom instructions and system prompts.
- `gems/` - Templates for creating custom Gemini Gems (with instructions + knowledge).
- `prompts/` - Reusable prompts adapted for Gemini.
- `agents/` - Agent personas for Gemini.

## Rolling Out Best Practices

The research in `reports/research/claude_best_practices.md` and `claude_usage_guide.md` (based on https://x.com/anatolikopadze/status/2054568935274549597) highlights:

- Persistent context (Gems + knowledge files or long context).
- Detailed "Who I am" profile.
- Custom instructions for behavior.
- Context Caching for large documents (see `prompts/gemini-context-caching.md`).
- Mindset: thinking partner (ask questions first, sparring).
- Techniques: style cloning, extended thinking, meta-prompting.
- Efficiency: specify length, no preambles.

### Adaptation for Gemini

- Use **Gems** for persistent specialized assistants (like Claude Projects).
- Upload knowledge files (e.g. profile, memories/INDEX.md excerpts, docs/codebase/).
- Use system instructions / custom instructions in AI Studio or app.
- Gemini excels at long context and real-time (via tools if using API).

See the rollout plan in `reports/research/multi-ai-best-practices-rollout-plan.md` (to be created) for how this is being adapted across Grok, Claude, Copilot, and Gemini.

## Usage

1. Create a Gem in Google AI Studio using templates from `gems/`.
2. Paste relevant instructions from `instructions/`.
3. For best results, start with the "who-i-am" profile adapted for your role.

This is part of the multi-AI portability effort. Source of truth remains `.grok/`.

## Tool Use with Gemini

Gemini supports function calling natively (see `.gemini/prompts/gemini-tool-calling-example.md`).

For MCP-based tools (recommended for cache, state, audits):

1. `bash scripts/ensure-mcp-host.sh`
2. Host: `.gemini/mcp.gemini.example.json` → client MCP settings (`scripts/mcp-host-stdio.sh`).
3. DDEV: `.gemini/mcp.gemini.ddev.example.json` + `mcp-server/ddev/Dockerfile.mcp`.

The orchestrator MCP tools (`health_check`, `read_cache_file`, `list_chains`, etc.) are read-only and sandboxed.

See: `docs/reference/tools/multi-platform-tool-use.md` · `docs/reference/platform-surfaces.md`.

Deploy: `orchestrator upgrade … --selections mcp,gemini` (per-app; no fleet wave).

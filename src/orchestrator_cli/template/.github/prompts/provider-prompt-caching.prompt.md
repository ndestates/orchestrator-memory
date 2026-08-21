# Provider Prompt Caching Best Practices (for Copilot)

When building custom agents or using the OpenAI-compatible APIs that power many Copilot experiences, apply these caching strategies:

## General Advice for Copilot Users
- Keep the most stable, largest context at the very beginning of conversations.
- Use workspace-level instructions (`.github/copilot-instructions.md`) for project-wide stable context instead of repeating it.
- For custom code calling OpenAI/Anthropic/etc., refer to the provider-specific guidance below.

## Anthropic (Claude) via Copilot or Direct
**Crucial: Will caching requests be respected?**

Yes — when using the official Anthropic SDK directly with correct `cache_control` placement. Not guaranteed in all chat UIs or non-official wrappers.

- Use `cache_control={"type": "ephemeral"}` on system and long context.
- Full examples: see `reports/research/anthropic-prompt-caching.py`
- Always check `response.usage` to confirm (look for cache_read_input_tokens).
- Tool caching and long document patterns apply directly.

## xAI / Grok
- Automatic prefix caching.
- Details in the xAI reference and grok_usage_guide.md.

## Gemini
- Use Google's explicit Context Caching API for large documents.
- See `.gemini/prompts/` for Gemini-specific tool and caching examples.

## Integration with Orchestrator
Load `reports/research/prompt-patterns.md` (section 6) and the multi-AI setup prompt for cross-platform patterns.

When writing code that directly calls LLMs, always demonstrate or reference appropriate provider caching. Cite the research docs.
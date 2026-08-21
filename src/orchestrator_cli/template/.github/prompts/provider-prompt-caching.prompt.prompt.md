# Provider Prompt Caching Best Practices

You are an expert on efficient LLM usage across providers.

## Anthropic (Claude) Caching
**Crucial: Will caching requests be respected?**

Yes — Anthropic respects `cache_control` when you use the official SDK and place the markers correctly. It is not guaranteed through all chat UIs or third-party wrappers.

Use the `anthropic` SDK with `cache_control`:

- Apply to system prompts, large documents, and tool definitions using `{"type": "ephemeral"}`.
- See the complete examples in `reports/research/anthropic-prompt-caching.py`.
- Always inspect `response.usage` (cache_read_input_tokens vs cache_creation_input_tokens) to confirm it worked.
- Monitor for savings (often 50-90% on cached portions).

Requirements for it to work: direct SDK, exact prefix match, supported model, sufficient context size.

## xAI / Grok Caching
The xAI API performs automatic prefix caching on consecutive requests that share the same initial messages.

- Use a stable `prompt_cache_key` or the `x-grok-conv-id` header for consistent server routing.
- Check `usage.prompt_tokens_details.cached_tokens`.
- Reference: `.github/skills/token-usage-meter/references/xai-prompt-caching.md`

## Gemini Context Caching
Google's Gemini API supports explicit context caching:

- Create a cached context with `cachedContents.create` for large files or repeated documents.
- Reference the cache by name in subsequent `generateContent` calls.
- Ideal for long documents, codebases, or stable instructions.
- See `.gemini/prompts/gemini-tool-calling-example.md` and Google docs for the exact API.

## Copilot / OpenAI-based
When using the OpenAI SDK (common for Copilot custom agents):

- OpenAI has limited built-in prompt caching compared to Anthropic (primarily in certain enterprise offerings).
- Best practices:
  - Keep stable context at the beginning of the messages array.
  - Use conversation history management.
  - For custom implementations, consider external caching layers or summary techniques.
- Prefer sending only what is necessary on each turn.

## Orchestrator Integration
- Use the project's lean cache (`.github/prompts/load-project-cache-first.prompt.md`, `docs/codebase/`) for session context.
- Apply provider-specific caching when your code makes direct LLM API calls.
- Always log usage details.
- Update `reports/research/prompt-patterns.md` and `CONVENTIONS.md` when new patterns emerge.

When the task involves writing code that calls LLMs directly, include provider-specific caching guidance and point to the example script and research docs.

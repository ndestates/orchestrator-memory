# Gemini Context Caching for Orchestrator

Gemini supports explicit **Context Caching** for large, stable content (perfect for long documents, specs, or repeated instructions).

## When to Use
- Large project documentation or code summaries that are referenced across many queries.
- Stable system-like instructions.
- Complements tool calling (see `gemini-tool-calling-example.md`).

## Basic Pattern (Google Gen AI SDK)

```python
from google import genai
from google.genai import types

client = genai.Client()

# Create a cached context once (can live for up to 1 hour or configured TTL)
cached_content = client.caches.create(
    model="gemini-1.5-pro",
    config=types.CreateCachedContentConfig(
        display_name="orchestrator-project-context",
        system_instruction="You are an expert on the orchestrator template...",
        contents=[types.Part.from_text(text=long_document_content)],
        ttl="3600s",  # 1 hour
    ),
)

# Use the cache in generation
response = client.models.generate_content(
    model="gemini-1.5-pro",
    contents="Explain how to add a new skill.",
    config=types.GenerateContentConfig(
        cached_content=cached_content.name,
    ),
)
```

## Best Practices in This Project
- Cache the biggest static parts (project overview, key docs from `docs/codebase/`).
- Use for wave app knowledge or compliance references.
- Combine with the orchestrator's cache-first discipline.
- Monitor token usage — cached content is billed at a reduced rate.

## Cross-Platform Notes
See:
- `reports/research/anthropic-prompt-caching.py` (Anthropic equivalent)
- `reports/research/prompt-patterns.md` (section 6)
- `.grok/prompts/provider-prompt-caching.prompt.md`
- `reports/research/claude_usage_guide.md`

For multi-AI agents, load the appropriate caching strategy based on the target model.
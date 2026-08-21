# xAI Prompt Caching Reference

## How Prompt Caching Works
The xAI API automatically caches prompt prefixes for consecutive requests that share the exact same starting messages. The cache is prefix-based: it matches from the beginning of the messages array.

- First request: Full prompt processed and cached.
- Subsequent requests: Matching prefix served from cache → faster TTFT and lower cost (cached tokens billed at reduced rate).

Cache is per-server; to maximize hits use `x-grok-conv-id` HTTP header (or `prompt_cache_key` in Responses API body) for sticky routing to same server.

Cache not guaranteed: can be evicted under memory pressure, different servers, or if prefix changes.

## Usage Reporting
In API responses, check `usage` object for cache metrics:

### Chat Completions API
```json
{
  "usage": {
    "prompt_tokens": 125,
    "completion_tokens": 48,
    "total_tokens": 173,
    "prompt_tokens_details": {
      "text_tokens": 125,
      "cached_tokens": 98
    }
  }
}
```

### Responses API
```json
{
  "usage": {
    "input_tokens": 125,
    "output_tokens": 48,
    "total_tokens": 173,
    "input_tokens_details": {
      "cached_tokens": 98
    }
  }
}
```

## Interpreting Cache Efficiency
- `cached_tokens == 0`: Cache miss (full computation). Common on first request, after eviction, prefix mismatch, or no sticky routing.
- `cached_tokens > 0`: Partial or full hit. Higher is better.
- Ideal in multi-turn: `cached_tokens` grows or stays high as conversation builds on previous context.
- Efficiency metric: `cache_hit_rate = (cached_tokens / prompt_tokens) * 100`
  - >80% excellent for long contexts
  - <20% or 0 indicates inefficiency

## Common Causes of Low/No Cache Usage
1. Missing `x-grok-conv-id` or `prompt_cache_key` → requests routed to different servers.
2. Modifying or inserting messages at the beginning of the conversation history.
3. Non-deterministic or varying system prompts / tool definitions in early turns.
4. Very long gaps between requests (cache eviction).
5. Using different models or parameters that affect caching.

## Recommendations for Efficient Cache Use
- Always include a stable conversation identifier (`x-grok-conv-id` header or `prompt_cache_key`).
- Keep the prefix (early messages, system prompt, tools) **identical** across related requests.
- Build conversations incrementally without rewriting history.
- Monitor `cached_tokens` in every response and alert on sustained low values.
- For maximum savings: design prompts so large static parts (instructions, examples, retrieved context) are in the cacheable prefix.

## Billing Impact
Cached prompt tokens cost significantly less than non-cached. Check current pricing on xAI docs. Long-context pricing applies to total prompt tokens.


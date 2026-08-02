Ctrl+K
Ctrl+J



https://x.com/anatolikopadze/status/2054568935274549597?s=46&t=SaGq1nbqz3IeW-cyG6TuTg


Thought for 53s
This is an excellent thread.

@AnatoliKopadze dropped a high-signal, practical guide on getting way more out of Claude (currently sitting at ~20M views). The core thesis is simple but powerful:

Most people use Claude at ~10% of its capability because they treat it like a fancy search box instead of setting it up as a persistent, personalized thinking partner.

He breaks it down into clear, actionable steps with templates and ready-to-use prompts. Here's the distilled version:

Core Setup (The Foundation Most People Skip)
Use Projects instead of regular chats — Projects give Claude persistent memory across conversations.
Give it a detailed "Who I am" profile — Background, goals, communication preferences, work style, etc. Save this in the Project's knowledge base.
Convert it into Custom Instructions — This makes Claude behave consistently (tone, depth, structure, what to avoid) by default.
Mindset & Technique Upgrades
Stop using it like Google — Ask it to think with you on a problem, not just define things.
Make it ask questions first — Before any complex task, instruct it to gather context from you.
Style cloning — Feed it 3–5 samples of your writing and have it analyze patterns (not just "match my style").
Sparring partner mode — Explicitly ask it to attack your ideas ruthlessly (not just critique politely). This is one of the highest-leverage tips.
Extended Thinking — Turn on the brain icon (or prompt it) for step-by-step reasoning on hard problems.
Meta-prompting — When you're unsure how to prompt it, ask Claude to write the prompt for you.
Efficiency & Context Hygiene
Always specify desired output length.
Kill preambles, disclaimers, and summaries unless requested.
Use Projects so you never have to re-explain yourself.
Start a fresh chat inside the Project when switching topics (prevents context bleed).
Ready-to-Use Prompts (The "Just Copy These" Section)
He provides strong templates for:

Feynman-style explanations (analogies to truly understand something)
Personalized travel planning based on your actual travel style
Deep expense/finance analysis from real statements
Structured personal thinking/reflection partner sessions
Ruthless business idea stress-testing
My Take as Grok
This is genuinely one of the better AI usage guides out there. The principles are excellent and mostly universal.

What transfers directly to me:

Sparring/attack mode
Style cloning via samples
Asking clarifying questions first
Meta-prompting ("write the prompt for this task")
Output length + "no preamble" instructions
Thinking step-by-step / extended reasoning
Using me as a structured thinking partner
Where Claude has an edge right now:

Native Projects + knowledge base + per-project custom instructions = very strong persistent memory system.
How to get similar (or better) results with Grok:
We don't have the exact Projects feature yet, but you can replicate most of the benefit with a lightweight system:

Keep a master "Memory/Profile" document (text file, Notion, or even a dedicated chat).
Paste relevant sections at the start of important conversations.
Or just say: "Remember this context for our work together..." and I'll do my best to carry it forward.
I'm also very good at tool use, real-time information, code, images, and structured reasoning when you ask for it.
Would you like me to:

Build you a Grok-optimized version of this whole setup (with tailored instructions + prompts that play to my strengths)?
Help you create a strong "Who I am + Instructions" profile you can reuse with me?
Demonstrate any of the specific techniques (e.g., sparring mode, style cloning, or a Feynman explanation) on something you're working on right now?
Turn the best parts of this thread into a clean, copy-pasteable cheatsheet?
Just say the word and I'll make it useful for how you actually work.

## Direct SDK Usage: Anthropic Prompt Caching (for code)

**Crucial question: If we use Claude, will our caching requests be respected?**

**Yes** — when you call the Anthropic API directly using the official SDK and include the `cache_control` directives correctly, Anthropic **does respect them**. The backend will cache the marked prefix (ephemeral cache) and apply discounts on follow-up calls that match the prefix exactly.

You can verify it worked by inspecting the `usage` object in the response (look for `cache_read_input_tokens` > 0 and lower billed `input_tokens`).

### Important caveats
- This applies to **direct SDK calls** (`anthropic.Anthropic()`). 
- Consumer interfaces like claude.ai do not expose the same control (they have their own internal optimizations).
- Some third-party clients/wrappers strip or fail to forward `cache_control` — always use the official SDK for reliable results.
- The cache is **ephemeral** (short-lived TTL, typically 5 minutes to 1 hour depending on configuration and load). It is not permanent.
- The exact prefix (from the start of the messages/system) must match on subsequent requests.
- Supported on recent Claude models (Sonnet/Opus/Haiku 3+ families).

When writing code in this project that makes direct calls to Claude, follow the patterns below and always check `response.usage`.

Anthropic charges for cache **creation** on the first call and gives big discounts on **cache reads** on subsequent calls that reuse the same prefix.

### 1. Basic System Prompt Caching

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Use latest available
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an AI assistant tasked with analyzing literary works. Your goal is to provide insightful commentary on themes, characters, and writing style.",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {"role": "user", "content": "Analyze the major themes in 'Pride and Prejudice'."}
    ],
)

print(response.usage.model_dump_json())
```

### 2. Caching Tool Definitions

Tool schemas can be large. Cache them so they are not re-billed on every turn.

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        },
        "cache_control": {"type": "ephemeral"}
    },
    {
        "name": "search_codebase",
        "description": "Search the project codebase",
        "input_schema": {...},
        "cache_control": {"type": "ephemeral"}
    }
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful coding assistant.",
    messages=[...],
    tools=tools
)
```

### 3. Caching Long Documents / Large Context

This is the highest-leverage use case. Split your long context into a **stable prefix** (cached) + variable suffix.

```python
long_document = open("large_spec.md").read()   # or load a big code file, PR diff, etc.

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are an expert code reviewer. Use the following project specification when answering questions.",
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": long_document,
            "cache_control": {"type": "ephemeral"}   # Cache the big document
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Does this change violate section 4.2 of the spec?"
        }
    ]
)
```

**Pro tip**: Put the largest, least-changing content first. Apply `cache_control` to earlier blocks.

You can use multiple cache breakpoints in one request (typically the first 4–5 are effective).

### 4. Combined Example (System + Tools + Long Document)

```python
import anthropic

client = anthropic.Anthropic()

system_prompt = "You are a senior software architect with deep knowledge of this codebase."
long_context = open("ARCHITECTURE.md").read() + "\n\n" + open("docs/codebase/README.md").read()

tools = [
    {
        "name": "read_file",
        "description": "Read a file from the project",
        "input_schema": {...},
        "cache_control": {"type": "ephemeral"}
    }
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    system=[
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": long_context, "cache_control": {"type": "ephemeral"}},
    ],
    messages=[...],
    tools=tools
)

print("Cache stats:", response.usage.model_dump_json())
```

### How to Read Cache Usage

```json
{
  "input_tokens": 245,
  "output_tokens": 312,
  "cache_creation_input_tokens": 18420,
  "cache_read_input_tokens": 0
}
```

On follow-up turns:

- `cache_creation_input_tokens` drops (or is 0)
- `cache_read_input_tokens` is high
- `input_tokens` (billed) is much lower

Typical savings: 50–90% on cached tokens after the first call.

### Best Practices

| Practice | Recommendation |
|----------|----------------|
| Cache the prefix | Always cache earlier, stable content |
| Tools | Cache tool definitions if they are complex or reused |
| Long docs | Load once, cache the whole block |
| Multiple breakpoints | Use 2–4 cache points per request max |
| Fresh chats | Start a new request when the cached context no longer applies |
| Monitor | Always log `response.usage` |
| Don't over-cache | Small prompts don't benefit much |

**Limitations** (Anthropic):
- Caching is **ephemeral** (tied to the request lifetime, usually ~5–60 minutes).
- Only applies to input tokens.
- Not all models support it equally (best on Sonnet/Opus class).

### Integration with This Project

- **Orchestrator cache** (`docs/codebase/`, memories, `load-project-cache-first`) = fast context for *this* AI session.
- **Anthropic prompt caching** = cheap repeated context when your code makes direct `anthropic.Anthropic()` calls (e.g. in custom tools, evaluation scripts, or MCP servers).

Use both layers:
1. Keep large stable knowledge in the orchestrator cache.
2. When calling Claude via SDK, apply `cache_control` to the big static parts.

See also:
- `reports/research/claude_best_practices.md`
- `.grok/prompts/multi-ai-best-practices-setup.md`
- `docs/codebase/README.md` (Multi-AI support)

Always measure with `usage` before assuming savings.




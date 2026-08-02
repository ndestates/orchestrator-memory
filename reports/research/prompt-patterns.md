# Prompt Patterns (Distilled from Anthropic Tutorial)

**Source:** Anthropic Prompt Engineering Interactive Tutorial (public course notebooks + `hints.py` solutions).  
**Date added:** 2026-06-29  
**Purpose:** Provide clean, reusable prompt templates and techniques for skill authoring, grader design, research agents, bug-hunting, and complex prompt construction inside orchestrator.

These are foundational patterns (role + structure + grounding + output control + refusal). Orchestrator already encodes many at the system level (cache-first, evidence citation, XML-ish tags, multi-perspective). Use these as concrete reference implementations or starting points.

**Attribution:** Patterns adapted from the public Anthropic tutorial (chapters 6–9 + appendices on hallucinations, complex prompts, and evaluations). Always cite sources when using in research memos.

## 1. Grounded Response + Explicit Refusal (RAG / Anti-Hallucination)

Best single pattern for any task that must stay faithful to provided context.

```markdown
You are a master tax accountant. Your task is to answer user questions using any provided reference documentation.

Here is the material you should use to answer the user's question:
<docs>
{DOCS}
</docs>

First, gather quotes in <quotes></quotes> tags that are relevant to answering the user's question. If there are no quotes, write "no relevant quotes found".

Then insert two paragraph breaks before answering the user question within <answer></answer> tags. Only answer the user's question if you are confident that the quotes in <quotes></quotes> tags support your answer. If not, tell the user that you unfortunately do not have enough information to answer the user's question.

Here is the user question: {QUESTION}
```

**Key mechanics:**
- Force extraction of supporting evidence first.
- Strict gate before generating an answer.
- Explicit, natural-language refusal when unsupported.
- Example block shows desired output shape.

**Where to use in this project:**
- `research-deep-dive` memos
- `bug-hunter-agent`, `qa-agent`
- Grader expectations that involve facts from docs
- Any skill that processes external reference material (`project-drift-guardian`, schema checks, etc.)

## 2. Socratic Code Reviewer ("Codebot")

Encourages learning instead of spoon-feeding fixes. Strong for code review, test improvement, or refactoring assistance.

```markdown
You are Codebot, a helpful AI assistant who finds issues with code and suggests possible improvements.

Act as a Socratic tutor who helps the user learn.

You will be given some code from a user. Please do the following:
1. Identify any issues in the code. Put each issue inside separate <issue> tags.
2. Invite the user to write a revised version of the code to fix the issue.

Here's an example:

<example>
<code>
def calculate_circle_area(radius):
    return (3.14 * radius) ** 2
</code>
<issues>
<issue>
3.14 is being squared when it's actually only the radius that should be squared.
</issue>
<response>
That's almost right, but there's an issue related to order of operations. It may help to write out the formula for a circle and then look closely at the parentheses in your code.
</response>
</example>

Here is the code you are to analyze:

<code>
{CODE}
</code>

Find the relevant issues and write the Socratic tutor-style response. Do not give the user too much help! Instead, just give them guidance so they can find the correct solution themselves.

Put each issue in <issue> tags and put your final response in <response> tags.
```

**Key mechanics:**
- `<issue>` per problem (structured output).
- Socratic `<response>` that guides rather than dictates.
- Example demonstrates exact desired format.

**Where to use:**
- `bug-hunter-agent`
- `test-specialist-agent` suggestions
- `code-review` flows or skill authoring reviews

## 3. Strict Output Control (Speaking for the Model + Few-Shot)

Classic techniques for forcing exact formats (classification, structured answers).

**Core ideas (apply when you need machine-parsable output):**
- Tell the model the exact categories (or schema) up front, often inside `<categories>` or similar.
- Use "speaking for the model": prefill the beginning of the assistant response (e.g. start with `(` or `The correct category is:`).
- Provide 2–3 few-shot `<examples>` that demonstrate the exact desired output format (including tags).
- Keep instructions minimal after the examples.

Example skeleton (classification):

```
Please classify emails into the following categories, and do not include explanations: 
<categories>
(A) Pre-sale question
(B) Broken or defective item
(C) Billing question
(D) Other (please explain)
</categories>

Here are a few examples of correct answer formatting:
<examples>
Q: How much does it cost to buy a Mixmaster4000?
A: The correct category is: A

Q: My Mixmaster won't turn on.
A: The correct category is: B
</examples>

Here is the email for you to categorize: {email}

The correct category is:
```

(Then let the model continue from the prefilled line.)

## 4. Recommended Structure for Complex Prompts

When building larger skills or multi-step agents, combine elements in roughly this order (ordering matters for some parts):

1. Role / persona + high-level task
2. Context / reference material (wrapped in clear tags: `<docs>`, `<context>`, `<categories>`)
3. Step-by-step instructions or process
4. Few-shot examples (wrapped in `<example>`)
5. Output format constraints + "speak for" prefill
6. Grounding / refusal rules (e.g. the quotes pattern above)
7. What to do on insufficient information

Not every prompt needs every element. Start rich, then slim down after it works.

## 5. Evaluation & Grading Patterns

From the tutorial's empirical evaluations appendix:

- **Code-based grading**: Use deterministic checks (exact strings, counts, regex, file content inspection) for objective tasks.
- **Human grading**: Provide clear rubrics when nuance is required.
- **Model-based grading** (LLM-as-judge): Give the model the original task + output + a structured rubric. Ask it to return PASS/FAIL + evidence + suggestions for improving the eval itself.

Orchestrator's `grader_prompt.txt` and `skill-creator` already implement strong model-based grading + self-critique of the assertions. Add rubric items that are hard to fake without actually succeeding.

## Usage in This Project

- Load `reports/research/prompt-patterns.md` when authoring or reviewing prompts, skills, or graders.
- For direct use, invoke `/prompt-patterns` (skill) or load the prompt from `.grok/prompts/prompt-patterns.md`.
- Always cite the source file when these patterns influence output.

**See also:**
- `reports/research/claude_best_practices.md`, `grok_usage_guide.md`
- `.grok/skills/skill-creator/` (for building high-quality evals)
- `grader_prompt.txt`
- Original tutorial (public): chapters on "Avoiding Hallucinations", "Complex Prompts from Scratch", and appendices.

**Port notes:** Templates cleaned and adapted for modern agent use (typos fixed, paths generalized, XML tag style preserved because it works well with our existing practices).

## 6. Provider-Specific Prompt Caching (Efficiency Pattern)

Different frontier providers offer server-side caching to reduce cost and latency on repeated large context.

### Anthropic (Claude)
Use `cache_control: {"type": "ephemeral"}` on stable prefixes.

**Example locations:**
- System prompt block
- Long documents / specs
- Tool / function definitions

See the full runnable examples in `reports/research/anthropic-prompt-caching.py` and the detailed guide in `reports/research/claude_usage_guide.md` ("Direct SDK Usage: Anthropic Prompt Caching").

Pattern template:
```
system: [
    {"type": "text", "text": "<stable system + instructions>", "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": "<large document or codebase summary>", "cache_control": {"type": "ephemeral"}}
]
tools: [ { ..., "cache_control": {"type": "ephemeral"} } ]
```

Monitor `usage.cache_read_input_tokens` vs `cache_creation_input_tokens`.

### xAI / Grok
Automatic prefix-based caching on consecutive requests sharing the same starting messages.

Use a stable `prompt_cache_key` or `x-grok-conv-id` header for routing consistency.

See: `.grok/skills/token-usage-meter/references/xai-prompt-caching.md`

### Gemini
Use Google's Context Caching API for long-lived cached content.

Create a cached context once, then reference it by name in subsequent calls (reduces token costs significantly for large files).

### General Orchestrator Advice
- Combine project-level cache (`docs/codebase/`, memories) with provider-level caching.
- Cache the biggest stable prefixes.
- Always inspect usage objects.
- See `CONVENTIONS.md` (Efficiency section) and multi-AI best practices.

This pattern belongs in skills that make direct LLM calls (`research-deep-dive`, custom evals, tool-using agents).

---
name: prompt-patterns
description: "High-signal prompt engineering patterns (grounded RAG with refusal, Socratic code review, strict formatting, complex structure)."
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# Prompt Patterns

**Source (distilled):** Anthropic Prompt Engineering Interactive Tutorial (public notebooks + solutions).  
**When to load:** Authoring or reviewing skills, prompts, agents, grader rubrics, research agents, or any work requiring precise grounding, output control, or refusal behavior.

**Primary reference:** `reports/research/prompt-patterns.md`

**Quick prompt version:** `.grok/prompts/prompt-patterns.md`

## Key Patterns (use these templates)

### 1. Grounded Response + Explicit Refusal
Force evidence extraction before answering. Refuse cleanly when unsupported.

See full template and guidance in the research file (Section 1) and the reusable prompt file.

Core shape:
- Role as domain expert
- `<docs>` or context block
- "First gather relevant quotes in `<quotes>`"
- "Only answer inside `<answer>` if quotes support it"
- Explicit refusal: "I unfortunately do not have enough information..."

### 2. Socratic Code Reviewer (Codebot)
Structured issues + guiding response. Helps the user discover fixes.

Core shape:
- "You are Codebot..."
- `<issue>` per problem (separate tags)
- Socratic `<response>` that invites revision
- Provide a tight example of desired format
- "Do not give the user too much help"

### 3. Strict Output Control
- Declare categories/schema in tagged blocks
- "Speak for the model" by pre-filling the start of the answer
- 2–4 few-shot examples showing **exact** desired formatting
- Minimal instructions after the examples

### 4. Complex Prompt Structure
Role → Context (tagged) → Process → Examples (exact output) → Format + prefill → Grounding rules.

### 5. Grading
Use code-based + model-based with strong rubrics. Critique the eval itself for triviality.

## Project Integration Rules

- Always cite `reports/research/prompt-patterns.md` (and the pattern used) when these influence your output.
- Combine with orchestrator disciplines: manifest-first, cache citation, evidence before claims, lean responses.
- Prefer these in new skills, especially graders, research-deep-dive, bug-hunter, and test work.
- Complementary section for github-expert-agent (conflict/grounded/Socratic/strict patterns + invocation hints) lives in `.grok/prompts/prompt-patterns.md` (section 6) and is referenced from the github-expert agent.
- For direct loading in Copilot or chains, use the file in `.grok/prompts/prompt-patterns.md`.

Load the research reference for the complete templates and usage examples.

**Invocation:** `/prompt-patterns` (this skill) or load the prompt file directly.

**See also:** 
- `reports/research/claude_best_practices.md` and `grok_usage_guide.md`
- `skill-creator` (for building evals)
- `grader_prompt.txt`
- `research-deep-dive` and `bug-hunter-agent` references

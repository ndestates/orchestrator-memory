# Prompt Engineering Patterns (Anthropic Tutorial Distilled)

**Source:** Anthropic Prompt Engineering Interactive Tutorial (public).  
**Use this when:** Writing or reviewing new skills/prompts, building graders, research agents, or any work that requires precise control, grounding, or good output formatting.

**Load the full reference for depth:** `reports/research/prompt-patterns.md`

## Core Patterns

### 1. Grounded Response + Refusal (Recommended Default for Reference Tasks)

```
You are [expert role appropriate to the domain]. Your task is to answer user questions using any provided reference documentation.

Here is the material you should use:
<docs>
{DOCS_OR_CONTEXT}
</docs>

First, gather quotes in <quotes></quotes> tags that are relevant to answering the user's question. If there are no relevant quotes, write "no relevant quotes found".

Then insert two paragraph breaks before answering within <answer></answer> tags. 

Only answer if you are confident that the quotes support your answer. If not, tell the user that you unfortunately do not have enough information to answer the user's question.

Here is the user question: {QUESTION}
```

**Apply this** for research-deep-dive, bug reports involving docs, drift analysis, etc.

### 2. Socratic Code Reviewer (Codebot)

```
You are Codebot, a helpful AI assistant who finds issues with code and suggests possible improvements.

Act as a Socratic tutor who helps the user learn.

You will be given some code from a user. Please do the following:
1. Identify any issues in the code. Put each issue inside separate <issue> tags.
2. Invite the user to write a revised version of the code to fix the issue.

[Include a short <example> block showing the exact <issue> + <response> format desired]

Here is the code you are to analyze:

<code>
{CODE}
</code>

Find the relevant issues and write the Socratic tutor-style response. Do not give the user too much help! Put each issue in <issue> tags and your final response in <response> tags.
```

**Use for:** bug-hunter, test-specialist suggestions, refactoring assistance.

### 3. Strict Formatting via Speaking-for + Few-Shot

- Explicitly list allowed categories / schema inside clear tags.
- Prefill the start of the desired assistant response.
- Provide 2–4 exact-format examples inside `<examples>`.
- Keep post-example instructions very short.

Example skeleton:
```
Classify the following into these categories only. Do not add extra text.

<categories>
(A) ...
(B) ...
</categories>

Here are examples of the exact format required:
<examples>
...
</examples>

Input: {input}

The correct category is:
```

### 4. Quick Complex Prompt Checklist

When building bigger prompts:
- Role + task first
- Context wrapped in explicit tags
- Step-by-step instructions
- Few-shot examples (exact output shape)
- Output format + prefill
- Grounding/refusal rules
- Behavior on missing info

Start comprehensive, then prune.

### 5. Grading Mindset

Combine:
- Code-based assertions (exact matches, structure checks)
- Model-based grading with a clear rubric
- Always ask the judge: "Is this eval too easy to game?"

## Instructions for Use

- When the user asks for prompt help, skill writing, or output formatting, load this prompt + the research reference.
- Cite `reports/research/prompt-patterns.md` (and the specific pattern) in your response.
- Prefer these structures in new `.github/skills/*/SKILL.md`, grader rubrics, and agent prompts.
- Combine with orchestrator principles: manifest-first, cache citation, lean output, evidence before conclusion.
- For github-expert-agent invocations (conflicts, merges, PRs, deploys): load the complementary section (6) and apply grounded/Socratic/strict as indicated in the agent.md hints.

**Full details and more examples:** `reports/research/prompt-patterns.md`

End responses that use these patterns with a note: "Patterns applied from prompt-patterns (Anthropic tutorial distilled)."

### 6. Complementary Patterns for GitHub Expert Agent (with Invocation Hints)

When `/github-expert` (or github-expert-agent) is invoked — especially for git delivery, PRs, wave deploys, branch promotion, or any mention of "conflict", "merge", "rebase", "push", "drift", "non-ff" — internally apply these complementary patterns + hints. Combine with the agent's dedicated Git & Merge Conflict section.

**A. Grounded Git Context + Refusal (Default for Conflict Tasks)**
```
You are a GitHub Platform Architect expert in this project's git flow (feature/* → develop → master, guardrails, wave deploys).

Gather relevant context first:
<context>
{output of `git status`, `gh pr view`, recent TODO branch notes, docs/github/*, wave-inventory.yaml, previous commits}
</context>

Extract supporting evidence into <quotes> (exact commands, file paths, prior resolutions). Only proceed to solution if quotes support it.

If insufficient (e.g. no access to target repo state), refuse: "I do not have enough information on the current state of <branch> in <target>. Please share `git status` + PR link."
```

**B. Socratic Merge Conflict Coach**
Use when user needs guidance (not spoon-feed):
```
You are GitCoach, a Socratic tutor for GitHub merge conflicts and git friction.

Given the conflict report:
1. Put each distinct issue in <issue> tags (e.g. marker location, hook failure, non-ff).
2. Provide a <response> that guides the user to discover the fix themselves. Ask clarifying questions. Do not give the full solution commands up front.

Here is the conflict:
<conflict>
{git status + diff markers + error logs + branch info}
</conflict>
```

**C. Strict Git Resolution Output (for Prompt, Sensible Solutions)**
Force machine-readable + ready-to-run:
```
Provide resolution in this exact structure only. Use the tags. Tailor commands to the exact branches/SHAs from context.

<diagnosis>
One-sentence root cause.
</diagnosis>

<options>
1. ...
2. ...
</options>

<commands>
git ...
# comment on why + verification
</commands>

<verification>
- python3 scripts/git-push-secrets-guard.py ...
- Update TODO...
</verification>

<rollback>
git ...
</rollback>
```

**Invocation Hints (internal to github-expert):**
- Always open with grounded extraction from current project state (TODO branch, docs/github/repo-health.md, .githooks, recent wave logs).
- For user coaching → switch to Socratic pattern.
- For actionable output → use Strict pattern + agent's command templates.
- After resolution: reference git-workflow-guardrails, run guards, suggest docs/github/ update, tie to next wave or promotion.
- Cite: "Using complementary prompt-patterns (grounded + strict/Socratic) for this conflict."
```

Now update the Instructions for Use to reference this.

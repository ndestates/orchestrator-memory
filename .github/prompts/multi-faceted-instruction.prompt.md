# Multi-Faceted Instruction Handler

**Purpose**: Canonical handler for complex, multi-part user requirements that benefit from structured decomposition, one-at-a-time execution, and anti-drift checks. Use this (directly or via the orchestrator) when a request spans multiple files, agents, or concerns.

## How to Use This Prompt (User Instructions)

Provide your complex requirement after the `**Full Requirement**:` marker (or pass it as the "arguments" when invoking).

**Recommended format for multi-agent / multi-faceted requests** (action-oriented, explicit delegation):

1. State the overall `Goal:` in one sentence.
2. Provide numbered instructions, each assigned to an exact agent name from `.github/agents/` (e.g. `todo-specialist-agent`, `readme-specialist`, `github-expert`, `test-safety-agent`).
3. For each assignment, describe the specific action + expected output (e.g. "update file X", "return checklist", "propose changes and risks").
4. End with a request for one consolidated summary / checkpoint (changed files, residual risks, next actions).

**Example**:

**Full Requirement**:

Goal: Ensure proper, discoverable instructions exist for using multi-faceted and multi-agent prompt patterns in this template.

1. `readme-specialist: Audit current guidance in prompts/README.md, AGENTS.md, orchestrator-v2.prompt.md, and this file. Identify gaps in user-facing "how to structure a multi-part request".`
2. `readme-specialist: Add or enhance a "How to Use" user section in this multi-faceted-instruction.prompt.md with the recommended numbered format, concrete examples, and cross-references.`
3. `todo-specialist-agent: Record the documentation improvement in the active TODO file.`
4. `Return: locations of all multi-instruction guidance, summary of what was added, and any suggested follow-ups.`

See also:
- `.github/AGENTS.md` → "Multi-Agent Instruction Patterns"
- `.github/prompts/README.md` → "Practical Invocation Examples" (includes single-prompt, `/orchestrator`, and multi-agent numbered formats)
- `.github/prompts/orchestrator-v2.prompt.md` → embedded "Multi-Agent Instruction Example (Recommended)"

**Full Requirement**: [PASTE YOUR COMPLEX MULTI-PART INSTRUCTION HERE]

**Mandatory Process (Do NOT deviate)**:

1. **Load Context First**
   - Read `.github/AGENTS.md`
   - Read relevant files from `docs/`, `IMPLEMENTATION_SUMMARY.md`, `BRANCH_ANALYSIS.md`
   - Use `load-project-cache-first.prompt.md` logic

2. **Decomposition (Planner Step)**
   - Break into small, independent steps
   - For each step: exact files to touch, risks, dependencies
   - Output as structured JSON or numbered list

3. **Execution Rules**
   - Execute **ONE step at a time**
   - Delegate to the most appropriate specialized agent from `.github/agents/` when possible
   - Always reference existing patterns (e.g. manifest-first + cache-first loading, exact agent names per CONVENTIONS.md and .github/agents/, AGENT_HANDOFF_SCHEMA for inter-agent communication)

4. **Anti-Drift Gates (After Every Step)**
   - Self-review against original requirement
   - Run relevant workflow guards (auth-stability, schema checks, tests)
   - Flag any potential impact on tenancies, consents, audits, or permissions

5. **Final Output**
   - Summary of changes
   - Updated TODO / IMPLEMENTATION_SUMMARY if needed
   - Suggested next step or PR title

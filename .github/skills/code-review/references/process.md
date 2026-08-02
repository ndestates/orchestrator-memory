# Ideal code review process

Canonical narrative: `docs/reference/code_review_article.md`.

## Purpose

Improve **code health** — catch issues early, consistency, knowledge sharing, quality. Not perfection or gatekeeping.

## Flow

1. **Author prepares well**
   - Clear title + description (what + why)
   - Small, focused PR (ideally ~200–400 lines)
   - Tests passing, linters clean, self-review done
   - Links to tickets / design / context

2. **Reviewer understands context first**
   - Read description and requirements before the diff
   - Know the intent and problem being solved

3. **Systematic review**
   - Shared or mental checklist (stack-aware)
   - Sustainable pace (&lt; ~500 lines/hour; short sessions)
   - High-level design → logic, edges, tests, security
   - Automation handles style; humans do high-value work

4. **Constructive feedback**
   - Specific, actionable, kind
   - Blocking → suggestions → nits
   - Explain why; offer alternatives
   - Praise good code too

5. **Iteration**
   - Author responds (fix / clarify / trade-off)
   - Reviewer re-checks updated parts
   - Respectful, code-focused discussion

6. **Approval & merge**
   - Approve when the change **improves overall code health**
   - Merge after CI passes

## What should not happen

- Rubber-stamping
- Vague or harsh feedback / personal attacks
- Endless style nitpicking when linters exist
- Huge unreviewable PRs
- Long silent delays
- Blocking on personal preference rather than real issues

## Severity ranking (impact first)

| Tier | Topics |
|------|--------|
| High-impact (blocking / must-discuss) | Correctness, design/architecture, security, tests for critical behaviour |
| Important | Readability, maintainability, performance, error handling |
| Lower | Style, formatting, minor comments (prefer automation) |

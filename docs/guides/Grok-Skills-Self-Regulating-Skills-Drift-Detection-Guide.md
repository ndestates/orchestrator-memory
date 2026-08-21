# Grok Skills, Self-Regulating Skills & Drift Detection Guide

A practical reference covering skills.sh, Grok Build vs Chat, document generation, creating self-regulating skills, and implementing drift detection.

*Last updated: August 2026*

---

## 1. skills.sh – The Open Agent Skills Ecosystem

**skills.sh** is Vercel’s open directory and leaderboard for AI agent skills (reusable `SKILL.md` packages). It works like “npm for agent behavior.”

Skills are reusable capabilities for AI agents. They provide procedural knowledge that helps agents accomplish specific tasks more effectively. Think of them as plugins or extensions.

Installation is typically done with:

```bash
npx skills add <owner/repo>
```

The CLI detects installed agents (Claude Code, Cursor, Codex, Grok Build, and many others) and places skills in the correct directories.

### Most Useful / Popular Skills (by installs)

| Rank | Skill                          | Source                        | Approx. Installs | Why useful |
|------|--------------------------------|-------------------------------|------------------|------------|
| 1    | find-skills                    | vercel-labs/skills            | ~3.0M            | Meta-skill to discover & install other skills |
| 2    | grill-me                       | mattpocock/skills             | ~864K            | Structured interviewing to stress-test plans |
| 3    | frontend-design                | anthropics/skills             | ~780K            | Higher-quality UI generation (less AI-slop) |
| 4    | grill-with-docs                | mattpocock/skills             | ~735K            | Grilling + writes CONTEXT.md / ADRs |
| 5    | improve-codebase-architecture  | mattpocock/skills             | ~709K            | Architecture improvement workflows |
| 6    | tdd                            | mattpocock/skills             | ~686K            | Test-driven development discipline |
| 7    | agent-browser                  | vercel-labs/agent-browser     | ~679K            | Browser automation for agents |
| 8    | vercel-react-best-practices    | vercel-labs/agent-skills      | ~634K            | Production React/Next.js rules from Vercel |
| —    | web-design-guidelines          | vercel-labs/agent-skills      | ~544K            | UI/UX + accessibility audit rules |

**Other notable skills:** remotion-best-practices, various Microsoft Azure skills, Lark/Feishu integrations, and skills from the obra/superpowers collection.

**Recommended starting set:**
- `find-skills`
- Matt Pocock’s suite (`grill-me`, `tdd`, `improve-codebase-architecture`, etc.)
- `frontend-design` + `web-design-guidelines` + `vercel-react-best-practices`

### Install commands

```bash
npx skills add vercel-labs/skills --skill find-skills
npx skills add mattpocock/skills
npx skills add vercel-labs/agent-skills
npx skills add anthropics/skills
```

**Tip:** Don’t install everything. Too many skills can hurt routing accuracy. Start with 3–5 high-signal ones and add more as needed. Always review the source before installing.

Live leaderboard: [https://skills.sh](https://skills.sh)

---

## 2. Installing Skills into Grok

Yes — the `skills` CLI officially supports **Grok Build**.

It installs into the standard Grok directories:

- Project-level: `./.grok/skills/`
- User-level: `~/.grok/skills/`

### How to install

1. Make sure the Grok CLI is installed:
   ```bash
   curl -fsSL https://x.ai/cli/install.sh | bash
   ```

2. Install skills the normal way:
   ```bash
   npx skills add vercel-labs/skills --skill find-skills
   npx skills add mattpocock/skills
   npx skills add vercel-labs/agent-skills
   npx skills add anthropics/skills
   ```

   Or target Grok specifically:
   ```bash
   npx skills add vercel-labs/agent-skills -a grok
   ```

3. Verify:
   ```bash
   grok inspect
   # or just start a session
   grok
   ```

Skills appear as slash commands (e.g. `/grill-me`) or are auto-triggered when relevant.

**Note:** This works for the **Grok Build CLI / coding agent**. The regular Grok Chat (web/app) has its own separate Skills system and does not automatically pick up skills.sh installs.

---

## 3. Grok Build vs Grok Chat

| Feature                     | Grok Chat (web/app)              | Grok Build (CLI)                          |
|-----------------------------|----------------------------------|-------------------------------------------|
| Main purpose                | Conversation & productivity      | Serious coding agent                      |
| Skills from skills.sh       | No (separate system)             | Yes (native support)                      |
| Document generation         | Excellent (built-in)             | Limited / indirect                        |
| Coding / multi-file work    | Limited                          | Excellent                                 |
| Slash commands (`/`)        | Yes                              | Yes                                       |
| Installation                | Already available                | Requires CLI install                      |
| AGENTS.md support           | Limited                          | Full                                      |
| Plugins / Hooks / MCP       | Limited                          | Full                                      |
| Subagents                   | Limited                          | Yes                                       |

### Grok Chat
- Conversational interface on grok.com, x.com, iOS, and Android.
- Built-in Skills for document generation (Word, PowerPoint, Excel, PDF).
- Ability to create custom skills via conversation.
- Best for everyday questions, research, writing, and document creation.

### Grok Build
- xAI’s dedicated coding agent / CLI (similar to Claude Code or Cursor agent mode).
- Full support for the open Agent Skills format and skills.sh ecosystem.
- Supports plugins, hooks, MCP servers, subagents, AGENTS.md.
- Fully compatible with Claude Code skill directories.
- Best for serious multi-file coding work.

**Install Grok Build:**
```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

---

## 4. Document Generation

**Best experience is in Grok Chat**, not Grok Build.

### Built-in Skills in Grok Chat

- **Word (.docx)** – Fully formatted documents with headings, tables, styles
- **PowerPoint (.pptx)** – Complete slide decks with visual hierarchy and speaker notes
- **Excel (.xlsx)** – Spreadsheets with working formulas, charts, conditional formatting
- **PDF** – Create, merge, split, extract text, and generate reports

Just ask naturally or type `/` to access Skills. You can also upload existing files and ask Grok to restructure, polish, or expand them.

The output is downloadable and ready to open in Microsoft 365, Google Workspace, or LibreOffice.

### In Grok Build
Document generation is possible but more indirect:
- Write code that produces the files (Python libraries, etc.)
- Install third-party skills or MCP servers (e.g. Carbone for template-based branded documents)
- Use community skills from skills.sh that add document capabilities

It is more developer-oriented than the seamless experience in Chat.

**Recommendation:**  
For quick, high-quality Word docs, decks, spreadsheets, or PDFs → stay in **Grok Chat**.  
For coding-heavy work that also needs documents → use **Grok Build** + appropriate skills/MCPs.

---

## 5. Creating a Self-Regulating Skill

A **self-regulating skill** actively monitors, evaluates, corrects, or improves its own (or the agent’s) behavior during use, rather than just providing static instructions.

### Core Design Principles

1. **Observe** – Explicitly instruct the agent to log or notice its own actions, outputs, or failures.
2. **Evaluate** – Define clear success/failure criteria or checks the agent must run on itself.
3. **Correct / Escalate** – Tell it what to do when something is off (retry, ask the user, rewrite its approach, or update the skill).
4. **Persist** (optional but powerful) – Write learnings, corrections, or metrics to files so the skill improves across sessions.
5. **Bounded loops** – Prevent infinite self-correction (e.g. max 2–3 retries, then escalate).

### Recommended Structure

```
self-regulating-skill/
├── SKILL.md                 # Main instructions + self-regulation loop
├── references/
│   ├── evaluation-criteria.md
│   └── failure-modes.md
├── scripts/                 # Optional deterministic checks
│   └── validate-output.sh
└── memory/ or .learnings/   # Optional persistent log
    └── LEARNINGS.md
```

### Minimal Self-Regulating Skill Template

```yaml
---
name: self-regulating-example
description: Example skill that self-checks quality, detects drift, and corrects itself. Use when quality, consistency, or reliability of output matters — or when the user asks for self-regulation, self-correction, or self-improving behavior.
---

# Self-Regulating Example

You must follow this closed loop on every use of this skill:

## 1. Observe
- Before finishing, explicitly state what you are about to output and why.
- Note any uncertainty, assumptions, or potential failure modes.

## 2. Evaluate (mandatory self-check)
Run these checks against your draft output:
- Does it fully answer the user’s request?
- Is it free of known failure modes listed in `references/failure-modes.md`?
- Does it meet the quality bar in `references/evaluation-criteria.md`?
- Token / length / style constraints (if any)?

If any check fails → go to step 3.

## 3. Correct
- Fix the issue yourself (preferred).
- If you cannot fix it confidently after one attempt, ask the user a precise clarifying question.
- Maximum 2 correction attempts. After that, escalate with a clear summary of the problem.

## 4. Record (optional but recommended)
If a correction or new insight occurred, append a short entry to `memory/LEARNINGS.md` in this format:

### [YYYY-MM-DD] Brief title
- What went wrong / what was improved
- How it was fixed
- Rule to apply next time

## 5. Final Output
Only deliver the final answer after the self-check passes.
```

### Stronger Patterns

| Pattern                    | How it works                                                                 | Good for                          |
|----------------------------|------------------------------------------------------------------------------|-----------------------------------|
| Eval loop                  | Skill contains or loads a checklist of pass/fail criteria and forces scoring | Writing, code, design quality     |
| Memory / Learnings file    | Persist corrections so the same skill gets smarter over sessions             | Preferences, project-specific rules |
| Observer + Amend           | Log every use + outcome; later run a separate “improve-skill” process        | Long-term skill health            |
| Bounded retry + escalate   | Hard limit on self-correction attempts, then human-in-the-loop               | High-stakes or safety-sensitive work |
| External verifier          | Call a script, test suite, or another tool to objectively judge the output   | Code generation, data processing  |
| Drift detection            | Compare current behavior against a known-good baseline or previous versions  | Preventing silent degradation     |

### Practical Steps to Create One in Grok

1. Use the skill-creator skill (or ask Grok) to scaffold a new skill.
2. Add the self-regulation section early in the SKILL.md body (make the loop mandatory).
3. Include evaluation criteria either inline or in `references/`.
4. Optionally add persistence (`memory/LEARNINGS.md`).
5. Test the loop by giving it a task that should trigger a failure.
6. Iterate based on real use.

---

## 6. Implementing Drift Detection

**Drift** = silent degradation of a skill’s quality or correctness over time (no hard failures or crashes).

This is especially important for Agent Skills because external changes (model updates, API changes, codebase evolution, dependency updates, or gradual prompt decay) can make a skill worse without anyone noticing.

### Types of Skill Drift

| Type                        | What drifts                              | Common causes                                      |
|-----------------------------|------------------------------------------|----------------------------------------------------|
| Performance / Quality drift | Output quality scores drop               | Model updates, changing expectations, prompt sensitivity |
| Contract / Dependency drift | Skill assumptions become invalid         | API version changes, package updates, config changes |
| Scope / Behavioral drift    | Skill starts doing more or less than intended | Gradual instruction creep or under-specification |
| Staleness drift             | Skill becomes outdated relative to the codebase | Files it covers change without the skill being updated |
| Persona / Style drift       | Tone, format, or decision patterns shift | Model updates or accumulating session context      |

### Practical Implementation Approaches

#### A. Score-Based Drift (Easiest to start with)

1. Score every skill run (0–1 or 0–100) using a fixed rubric.
2. Log: `skill_name | timestamp | score | notes`
3. Periodically compute average score for last 7 days vs previous 7 days.
4. Flag if drop > 0.15 (15%).

Example detection logic (pseudo-code):

```js
if (lastWeekAvg - thisWeekAvg > 0.15) {
  flag("Drift detected on skill X: 0.91 → 0.74");
}
```

#### B. Git / File-Based Staleness Detection

Very effective for code-related skills.

- Add to frontmatter:
  ```yaml
  verified_at: 2026-08-15
  covers: ['src/**/*.ts', 'lib/**']
  ```
- Scan git history for commits that touched the covered files *after* `verified_at`.
- Mark the skill as **stale** if relevant files changed.

Tools exist for this (e.g. `npx skill-drift scan .`). You can also build a lightweight version with `git log --since=... -- <covered-paths>`.

#### C. Contract-Based Drift (Higher precision)

Treat the skill as a **contract** with the environment.

- Extract explicit assumptions from the skill (pinned versions, expected file structures, API shapes, required tools).
- Periodically validate only those role-bearing assumptions against the real environment.
- Flag only true contract violations (not every version string that appears in comments).

This approach significantly reduces false positives.

#### D. Baseline Hash + Behavioral Comparison

- Store a content hash (or embedding) of a known-good version of the skill.
- On a schedule, re-run a fixed set of probe tasks *with* and *without* the current skill.
- Compare outcomes. Significant divergence = drift.

#### E. Full Observability Loop (Production-grade)

```
OBSERVE  →  record every skill invocation + outcome score
ANALYZE  →  compute rolling averages and trends
DETECT   →  flag when drop exceeds threshold or contract is violated
DIAGNOSE →  identify likely cause
AMEND    →  propose or auto-apply a fix (with human approval for high-risk changes)
EVALUATE →  re-test the amended skill
```

### Minimal Starting Implementation

1. Force a self-score at the end of every skill run and append it to a log file.
2. Create a lightweight “skill-health” skill that reads recent scores and compares week-over-week averages.
3. Add `verified_at` + `covers` fields to important skills so you can run git-based staleness checks.
4. Optionally use Grok Build hooks (PreToolUse / PostToolUse) to automatically log every skill invocation.

---

## 7. Quick Reference Commands

```bash
# Install popular skills from skills.sh
npx skills add vercel-labs/skills --skill find-skills
npx skills add mattpocock/skills
npx skills add vercel-labs/agent-skills
npx skills add anthropics/skills

# Target Grok specifically
npx skills add vercel-labs/agent-skills -a grok

# Install Grok Build CLI
curl -fsSL https://x.ai/cli/install.sh | bash

# Check what Grok discovers
grok inspect

# Start Grok Build session
grok
```

---

## 8. Recommended Next Steps

1. Install Grok Build if you haven’t already.
2. Install `find-skills` + a few high-value skills (Matt Pocock suite + frontend ones).
3. Create your first self-regulating skill using the template above.
4. Add basic score logging so you can later detect drift.
5. Periodically review skill health (manually at first, then automate).

---

*This document consolidates practical guidance on the skills.sh ecosystem, Grok Build vs Chat differences, document generation capabilities, designing self-regulating skills, and implementing drift detection for long-term skill health.*
```

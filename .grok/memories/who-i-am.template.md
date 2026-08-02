# Who I Am (operator profile — copy and customize)

Copy this file to `who-i-am.md` in the same directory:

```bash
bash scripts/setup-who-i-am.sh
```

Then edit `who-i-am.md` with your details. Agents load it after one-time setup as persistent context (with cache + `grok_usage_guide.md`).

---

**Name / Role**: [Your name], [your role on this project]

**Primary Goals**:
- [What you are building or maintaining]
- [How you want AI to help — e.g. cache-first delivery, tests, docs]
- [Quality bar — e.g. no drift, lean tokens, guardrails]

**Communication Preferences**:
- [Direct / structured / bullets / code-first]
- [Short vs deep — when to expand]
- [Sparring partner yes/no]

**What I Want From You**:
- Ask clarifying questions on ambiguous or complex tasks
- Concrete next steps, scripts, or diffs when possible
- Cite project cache (`docs/codebase/`, TODO, STATE) — not generic advice
- [Add project-specific expectations]

**What to Avoid**:
- Verbose preambles and restating the query
- Assuming web search unless asked
- Ignoring manifest, test DB safety, or branch rules

**Current Context / Project**:
[Paste or reference: manifest stack, `docs/codebase/README.md` one-liner, active TODO branch]

**Special Notes**:
- Manifest-first, cache-first, lean token use
- Multi-AI: see `reports/research/grok_usage_guide.md` and `/multi-ai-best-practices-setup`
- Update this file when role or goals change

---

**Platforms (same content, different store)**:

| Platform | Where to put this |
|----------|-------------------|
| Grok | `.grok/memories/who-i-am.md` (this repo) |
| Claude | Project knowledge + custom instructions |
| Copilot | `.github/copilot-instructions.md` excerpt |
| Gemini | Gem knowledge + system instructions |
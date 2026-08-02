# Who I Am setup (persistent operator profile)

[UPDATED 2026-07-07]

## Overview

The orchestrator template treats **who you are** as first-class persistent context — alongside cache, TODO, and the vault brain. One profile powers Grok, Claude, Copilot, and Gemini with the same intent.

## Before you begin

- Repository cloned and `bash scripts/install.sh` run (optional)
- You know your role, goals, and how you want the AI to communicate

## Steps

1. **Create your profile file (Grok / this repo)**

   ```bash
   bash scripts/setup-who-i-am.sh
   ```

   Edit `.grok/memories/who-i-am.md` — replace placeholders with your details.  
   Canonical blank: `.grok/memories/who-i-am.template.md`  
   Long-form reference: `reports/research/who-i-am-profile-template.md`

2. **Load multi-AI behavior defaults**

   In your AI client:

   ```text
   /multi-ai-best-practices-setup
   ```

   Or read `reports/research/grok_usage_guide.md` (Grok) / `claude_usage_guide.md` (Claude).

3. **Verify session load**

   ```text
   /chain session-start
   ```

   Agents should cite `who-i-am.md` when relevant (spine load when file exists).

4. **Mirror on other platforms**

   | Platform | Action |
   |----------|--------|
   | Claude | Paste profile into Project knowledge + custom instructions |
   | Copilot | Add summary to `.github/copilot-instructions.md` (or workspace instructions) |
   | Gemini | Upload to Gem knowledge + system prompt (see `.gemini/README.md`) |

5. **Keep it current**

   Update `who-i-am.md` when role, project, or preferences change.  
   Major shifts can emit a vault lesson: `python3 scripts/emit-session-lesson.py "..."`.

## Verify

- `.grok/memories/who-i-am.md` exists and is personalized (not still placeholders)
- `/.grok/memories/INDEX.md` lists who-i-am in tier-1
- `/chain session-start` briefing feels aligned with your stated preferences

## Next steps

- [Quickstart](quickstart.md) — first session
- [Daily workflow](../guides/daily-workflow.md) — ongoing habits
- [Grok usage guide](../../reports/research/grok_usage_guide.md) — techniques (sparring, ask-first, efficiency)

## Related

- `.grok/prompts/multi-ai-best-practices-setup.md`
- `reports/research/multi-ai-best-practices-rollout-plan.md`
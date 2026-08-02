---
name: daily-standup
description: >
  Alias for .github/prompts/daily-standup-with-cache.prompt.md. Start a daily session: fetch remote branches,
  report latest remote branch worked on, then cache + TODO + briefing.
argument-hint: "Optional focus, e.g. 'tests', 'deploy', 'chains', 'template-deploy'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---

# Daily Standup (alias)

Same workflow as `.github/prompts/daily-standup-with-cache.prompt.md`. Follow [`.github/skills.github/prompts/daily-standup-with-cache.prompt.md/SKILL.md`](...github/prompts/daily-standup-with-cache.prompt.md/SKILL.md) exactly.

**Mandatory first actions** (before cache): `git fetch origin --prune`, then identify **latest remote branch worked on** (`remote-last`) via `scripts/resume-branch.sh`. Report current vs remote-last **with commit diff** (`vs_remote_last_*`), integration (develop/master) ff offer, and run `scripts/session-security-sweep.sh` when used from `.github/skills/chain/SKILL.md session-start`.

Keep all standup responses concise.
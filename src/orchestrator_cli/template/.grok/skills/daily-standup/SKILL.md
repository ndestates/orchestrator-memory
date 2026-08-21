---
name: daily-standup
description: >
  Alias for /daily-standup-with-cache. Start a daily session: fetch remote branches,
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

Same workflow as `/daily-standup-with-cache`. Follow [`.grok/skills/daily-standup-with-cache/SKILL.md`](../daily-standup-with-cache/SKILL.md) exactly.

**Mandatory first actions** (before cache): `git fetch origin --prune`, then identify **latest remote branch worked on** (`remote-last`) via `scripts/resume-branch.sh`. Report current vs remote-last **with commit diff** (`vs_remote_last_*`), integration (develop/master) ff offer, and run `scripts/session-security-sweep.sh` when used from `/chain session-start`.

Keep all standup responses concise.
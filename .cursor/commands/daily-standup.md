# /daily-standup

> Alias for /daily-standup-with-cache. Start a daily session: fetch remote branches, report latest remote branch worked on, then cache + TODO + briefing.

**Platform:** Cursor · same skill as Grok `/daily-standup` · Claude `/daily-standup`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Optional focus, e.g. 'tests', 'deploy', 'chains', 'template-deploy`

# Daily Standup (alias)

Same workflow as `/daily-standup-with-cache`. Follow [`.grok/skills/daily-standup-with-cache/SKILL.md`](../daily-standup-with-cache/SKILL.md) exactly.

**Mandatory first actions** (before cache): `git fetch origin --prune`, then identify **latest remote branch worked on** (`remote-last`) via `scripts/resume-branch.sh`. Report current vs remote-last **with commit diff** (`vs_remote_last_*`), integration (develop/master) ff offer, and run `scripts/session-security-sweep.sh` when used from `/chain session-start`.

Keep all standup responses concise.

User focus (optional): use any extra chat text as $ARGUMENTS.

# Third-party skill authors

[UPDATED 2026-08-15]

Orchestrator adapts a few community agent skills. We do **not** `npx skills add` them into the template. Each procedure is rewritten cache-first, with a short description and a complements table.

Apache-2.0 still applies to *our* adaptations. The originals remain MIT, copyright their authors. Keep this page and root `NOTICE` when you redistribute.

Directory used for discovery: [skills.sh](https://www.skills.sh/).

## Acknowledgements (2.2.5)

| Author | Original | License | In this template |
|--------|----------|---------|------------------|
| **Vercel Labs** | [`find-skills`](https://github.com/vercel-labs/skills/tree/main/skills/find-skills) | MIT | `/find-skills` |
| **Matt Pocock** | [`grill-me`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) + [`grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) | MIT | `/grill-me` |
| **Matt Pocock** | [`tdd`](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md) | MIT | folded into `/test-specialist-agent` |
| **Matt Pocock** | [`teach`](https://github.com/mattpocock/skills/blob/main/skills/productivity/teach/SKILL.md) | MIT | `/teach` |
| **Jesse Vincent** and **Prime Radiant** ([obra/superpowers](https://github.com/obra/superpowers)) | [`systematic-debugging`](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md) | MIT | `/systematic-debugging` |
| **Jesse Vincent** and **Prime Radiant** | [`verification-before-completion`](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md) | MIT | `/verification-before-completion` |
| **Vercel Engineering** / **Vercel Labs** | [`vercel-react-best-practices`](https://github.com/vercel-labs/agent-skills) | MIT | table inside `/nextjs-expert` |
| **Vercel Labs** | [`web-design-guidelines`](https://github.com/vercel-labs/agent-skills) + [web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | MIT | UI-review step in `/frontend-web-design-expert` |

Thank you to these authors. Bugs in the *adapted* skills are ours.

## How we credit

- Root [`NOTICE`](../../NOTICE) — Apache attribution (required on redistribute)
- This page — human-readable table
- Each adapted `SKILL.md` — “Adapted from” line
- Ports note: [`reports/research/ports/skills-sh/README.md`](../../reports/research/ports/skills-sh/README.md)

## Related

- [Skills reference](skills.md)
- [Licensing](licensing.md)
- [skills.sh complement report](../../reports/research/skills-sh-complement-2026-08-15.md)

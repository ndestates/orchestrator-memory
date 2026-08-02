# Google Chrome security flywheel — source map

[UPDATED 2026-08-01]

Public source: [Stronger with every update](https://blog.google/security/chrome-stronger-with-every-update/) (Chrome Security Team).

| Chrome concept | Orchestrator / app encoding |
|----------------|----------------------------|
| Life of a bug: find→triage→fix→release→apply | `docs/reference/stronger-with-every-update.md` + `docs/guides/security-flywheel.md` |
| AI multi-model finding | model-route catalog + bug-hunter + security-audit |
| Critic ≠ fixer | code-review / loop-verifier |
| SECURITY.md trust boundaries | root `SECURITY.md` |
| Shrink patch gap | self-upgrade, per-app upgrade, small merges |
| Class elimination | guardrails, secrets guard, MCP off default, CSE |
| Continuous dashboard | `scripts/security-flywheel-status.sh` |
| Interdependent products | `scripts/security/flywheel-peers.yaml` (ndestates ↔ lightstone) |

**Retention:** keep this map + the flywheel guide in onboarding; do not drop without replacement.

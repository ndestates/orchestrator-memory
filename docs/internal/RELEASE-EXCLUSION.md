# Keeping internal docs out of release

**Status:** Internal process — not a customer feature.

## Packaging checks

| Channel | Includes `docs/internal/`? | Mechanism |
|---------|----------------------------|-----------|
| **npm `@ndestates/orchestrator`** | **No** | `package.json` → `"files"` is only `bin/`, `scripts/npm/`, `LICENSE`, `README.md`, `INSTALL.md`, `VERSION` |
| **PyPI / hatch wheel** (if used) | Verify on release | Do not add `docs/internal` to package data |
| **App deploy-bundle** (`scripts/deploy-bundle.yaml`) | **No by default** | Selections copy explicit paths; `docs/internal` is not listed |
| **GitHub Pages / public docs site** | **No** | Do not add to `docs/index.md` nav |
| **Git history** | Yes if merged | Prefer `docs/internal-*` branches; if merged, exclusion still applies to packaging |

## Release checklist (add for maintainers)

Before tagging:

1. Confirm `package.json` `files` still omits `docs/internal/`.
2. Confirm no deploy selection lists `docs/internal/**`.
3. Confirm public `docs/index.md` has no link to `docs/internal/`.
4. Prefer not merging large internal dumps to `master` without need; `docs/internal-*` branch is enough for the team.

## Intentionally public security docs

These **are** public/operator-facing and stay under normal docs:

- `docs/operations/security-malware-defence.md` (if present)
- `.grok/references/ai-content-guardrails.md` (agent policy — required at runtime)
- Session-start skills that mention guardrails at a high level

Internal docs go deeper (threat model, inventory of every chain, residual risks).

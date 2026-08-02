# Internal documentation (NOT FOR RELEASE)

**Classification:** Internal engineering reference only.  
**Branch:** `docs/internal-security-and-system-map-2026-07-17` (and future `docs/internal-*` branches).  
**Do not** publish these files in npm packages, public site builds, or customer-facing release notes.

## Why this folder exists

Public docs under `docs/guides/`, `docs/getting-started/`, and `docs/reference/` are for operators and app adopters.  
**This folder** is for maintainers: full security posture, code map, every skill, and every chain—including threat model detail that is not useful (and can be harmful) to ship as a product surface.

## Contents

| Document | Purpose |
|----------|---------|
| [SECURITY-POSTURE.md](SECURITY-POSTURE.md) | End-to-end project security: layers, engines, CI gates, gaps |
| [CODEBASE-MAP.md](CODEBASE-MAP.md) | Repository layout, runtimes, major subsystems |
| [SKILLS-CATALOG.md](SKILLS-CATALOG.md) | Each skill: path, what/why, invocation |
| [CHAINS-CATALOG.md](CHAINS-CATALOG.md) | Each chain: steps, invoke targets, intents |
| [RELEASE-EXCLUSION.md](RELEASE-EXCLUSION.md) | How we keep this out of packaging / app deploy |
| [APP-INSTALLABLE-AND-DROP-WAVE-PLAN.md](APP-INSTALLABLE-AND-DROP-WAVE-PLAN.md) | Install from npm/PyPI/VS Code; remove fleet wave forever |
| [FREEMIUM-LICENSE-AND-SERVER-PLAN.md](FREEMIUM-LICENSE-AND-SERVER-PLAN.md) | Free Light + Pro £99/mo (annual 2 mo free); license server on DO / ndestates.io |
| [WEBMCP-BETA-PLAN.md](WEBMCP-BETA-PLAN.md) | Browser WebMCP beta (page tools) — not host MCP; multi-workstream abandoned |
| [MCP-RECOMMEND-TOOLS-SCHEMA.md](MCP-RECOMMEND-TOOLS-SCHEMA.md) | Design-only schema for future `recommend_tools` (static map; no outbound client) |
| [_generated/](_generated/) | Machine inventory JSON used to build catalogs |

## Refresh catalogs

From repo root on this branch:

```bash
# Regenerate skill/chain inventory + markdown catalogs
python3 docs/internal/_generate_catalogs.py
```

## Branch policy

- Prefer keeping work on **`docs/internal-*`** branches.
- If merged to `develop` for backup, **`docs/internal/` must remain excluded** from npm `files` and deploy-bundle app selections (see RELEASE-EXCLUSION.md).
- Never link these pages from the public docs index (`docs/index.md`) or marketing site.

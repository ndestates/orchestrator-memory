# Documentation site blueprint (GitHub Docs style)

Use this layout for **human-navigable** project docs. Agent cache stays in `docs/codebase/`; this tree is for contributors and operators.

## Top-level hub — `docs/index.md`

```markdown
# <Project Name> Documentation

[UPDATED YYYY-MM-DD]

Short one-paragraph purpose. Link to repo README for clone/install only.

## Getting started
- [Overview](getting-started/index.md) — what this project is
- [Quickstart](getting-started/quickstart.md) — first successful session in &lt;15 minutes

## Guides
- [Guides index](guides/index.md) — task-oriented how-tos

## Reference
- [Reference index](reference/index.md) — manifests, chains, configuration shapes

## Operations
- [Operations index](operations/index.md) — testing, CI, delivery

---

**Agent cache** (for AI sessions): [docs/codebase/README.md](codebase/README.md)
```

## Section index pattern — `docs/<section>/index.md`

Each section folder **must** have an `index.md` that lists every page with a one-line description (sidebar-style).

## Page pattern — every guide/reference page

1. **Title** (H1) + `[UPDATED date]`
2. **Overview** — 2–4 sentences; who this is for
3. **Before you begin** — prerequisites (branch, tools, cache loaded)
4. **Steps** — numbered; one action per step; link out for detail
5. **Verify** — how to confirm success (command or checklist)
6. **Next steps** — 2–3 relative links (required)
7. **Related** — optional cross-links

## Full document set (create or refresh)

| Path | Audience | Purpose |
|------|----------|---------|
| `docs/index.md` | Everyone | Navigable hub |
| `docs/getting-started/index.md` | New contributor | Section index |
| `docs/getting-started/quickstart.md` | New contributor | First session |
| `docs/getting-started/project-overview.md` | New contributor | Architecture summary (no trade secrets) |
| `docs/guides/index.md` | Daily dev | Section index |
| `docs/guides/daily-workflow.md` | Daily dev | Session start, TODO, standup |
| `docs/guides/chains-and-skills.md` | Daily dev | `/chain`, skill catalog, opt-out |
| `docs/guides/documentation.md` | Maintainers | How docs are produced and updated |
| `docs/reference/index.md` | Maintainers | Section index |
| `docs/reference/manifest.md` | Maintainers | Manifest fields (from project-manifest.yaml) |
| `docs/reference/chains.md` | Maintainers | Chain ids and steps (from CHAIN.md / registry) |
| `docs/reference/skills.md` | Maintainers | Skill catalog (from chains/registry.yaml skills section) |
| `docs/operations/index.md` | Delivery | Section index |
| `docs/operations/testing.md` | Delivery | Audit scripts, CI gates |
| `docs/operations/delivery.md` | Delivery | Branch promotion, PR flow |

Adapt rows for app repos (add `guides/local-runtime.md`, `reference/api.md`, etc.).

## Content policy (mandatory)

### Include

- Procedural instructions (step-by-step)
- Public architecture and directory layout
- Chain/skill/loop invocation and when to use each
- Branch workflow, audit commands, manifest field meanings
- Placeholders for config: `YOUR_API_KEY`, `YOUR_APP_ID`

### Exclude — never write

| Category | Examples |
|----------|----------|
| **Secrets** | API keys, tokens, passwords, private URLs, `.env` values, PEM contents |
| **Trade secrets** | Undisclosed pricing logic, proprietary algorithms, confidential partner terms |
| **Coding tips** | Clever hacks, non-standard shortcuts, "tricks", opinionated micro-optimizations |
| **Live credentials** | Production hostnames with auth, database connection strings with passwords |

If documenting config, use **shape only** (field name, type, purpose) — not production values.

### Borderline (allowed when procedural)

- Chain composition steps, handoff rules, token policy — **in scope**
- "Use Services layer over fat models" as **convention** — OK in CONVENTIONS-style docs
- "Prefer X over Y for performance" as **coding tip** — **exclude** unless it's an encoded project standard in CONVENTIONS.md

## Linking rules

- Hub → sections → pages (max 2 clicks from `docs/index.md` to any page)
- Every page links back to its section `index.md` in **Related**
- Root `README.md` links to `docs/index.md` as **Documentation**
- `docs/codebase/README.md` links to `docs/index.md` for human readers
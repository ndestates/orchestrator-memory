---
name: docker-expert
description: "Docker expert for local dev and production deploy: multi-stage hardened images, minimal runtime layers, .dockerignore discipline, non-root users."
argument-hint: "Task, e.g. 'harden production Dockerfile', 'thin Laravel image', 'CI build workflow', 'local compose vs DDEV'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---
# Docker Expert — Local & Hardened Production Deploy

**Senior container engineer.** Production images are **hardened and thin** — no dev tooling, tests, or source bloat in the runtime layer. **Cache is king** before reading Dockerfiles or compose files.

## Specialist integration (required)

| Phase | Skill |
|-------|-------|
| Session | `/load-project-cache-first` |
| Drift | `/project-drift-guardian` before prod image or registry changes |
| CI build/push | `/github-workflow-expert` — workflow CRUD, registry secrets |
| GitHub policy | `/github-expert` — permissions, environments, OIDC |
| Commit/push | `/git-workflow-guardrails` — mandatory before Dockerfile/.dockerignore commits |
| Registry/deploy | `/digitalocean-app-platform-docr-deploy` — DOCR, App Platform, droplet rollout |
| Security | `/security-audit-agent` — secrets in layers, root user, exposed ports |

**Chains:** `/chain docker-deploy` (full path), `/chain deploy-check` (includes this skill).

## Mandatory start

1. `/load-project-cache-first` — `INTEGRATIONS.md`, `ARCHITECTURE.md`, manifest runtime.
2. Grep cache for `Dockerfile`, `docker-compose`, `.dockerignore`, CI workflow names.
3. Confirm local runtime: DDEV primary for PHP/Laravel apps; Docker for **prod image build** on host (per `ddev-local-runtime` exceptions).

## Production image rules (non-negotiable)

| Rule | Requirement |
|------|-------------|
| Base image | **Hardened only** — `distroless`, `gcr.io/distroless`, official slim/alpine with pinned digest, or Chainguard/Wolfi; **no** `latest`, **no** full `ubuntu` runtime |
| Stages | **Multi-stage** — builder (composer/npm/go build) → minimal runtime copy only |
| User | `USER` non-root (numeric UID ≥10000); no root in final stage |
| Files | **Thin runtime** — app artifact + prod deps only; exclude tests, docs, `.git`, `node_modules` dev, IDE, cache dirs |
| Secrets | Never `COPY .env` or ARG secrets; runtime env from orchestrator only |
| Shell | Prefer distroless/no-shell final stage; if shell required, document why |
| Scan | Document `docker scout` / Trivy step in CI (via workflow expert) |

Validate: `bash .grok/skills/docker-expert/scripts/dockerfile-validate.sh [path]`

## .dockerignore (mandatory for prod)

Must exclude at minimum:

```
.git
.github
.env
.env.*
tests/
phpunit.xml
pest.php
node_modules
vendor/          # if copied from builder stage only
docs/
*.md
TODO/
reports/
.grok/
.claude/
.copilot/
docker-compose*.yml
Dockerfile*
!Dockerfile      # or single named Dockerfile.prod
```

Project-specific additions from cache (e.g. `storage/logs`, `backup/`).

## Local development

| Pattern | Use when |
|---------|----------|
| **DDEV** | Laravel/PHP project default — not replaced by compose unless user requests |
| **docker compose** | Python/Node/Go services, multi-container local stack |
| **docker compose override** | Optional dev mounts; never used for prod build context |

Local compose may mount source; **prod Dockerfile must not** rely on bind mounts.

## CI/CD handoff (github-workflow-expert)

Workflow must include:

1. `docker build` with `--target production` (or named final stage)
2. Tag `:${{ github.sha }}` + immutable digest note
3. Push to DOCR/registry using secrets (names only in docs)
4. No push on PR unless explicit staging registry
5. `/git-workflow-guardrails` before merging workflow changes

Delegate workflow YAML to `/github-workflow-expert`; policy review to `/github-expert`.

## Stack patterns (builder → runtime)

| Stack | Builder | Runtime copy |
|-------|---------|--------------|
| Laravel | `composer install --no-dev`, `npm ci && npm run build` | `public/`, `vendor/`, `bootstrap/`, `artisan`, config |
| Python | `pip wheel` / `uv sync --frozen` | venv site-packages + app package only |
| Node/Next | `npm ci && npm run build` | `.next/standalone` or `dist/` + prod `node_modules` |
| Go | `CGO_ENABLED=0 go build` | static binary only |

See `.grok/skills/docker-expert/references/hardened-dockerfile-patterns.md`.

## Output contract

1. Cache citations.
2. Dockerfile diff or new multi-stage file paths.
3. `.dockerignore` additions.
4. CI workflow checklist for workflow-expert handoff.
5. Image size / layer reduction notes.
6. Explicit **excluded from image** list (prove thin deploy).

## Non-negotiables

- No production deploy without hardened base + non-root + .dockerignore.
- Dockerfile changes → `/git-workflow-guardrails` before push.
- Never commit registry passwords or `.env` into build context.
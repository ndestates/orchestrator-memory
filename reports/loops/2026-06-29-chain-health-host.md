# Chain Health Host Snapshot — 2026-06-29

**Level:** L1 host-only (agent completes report via `/chain chain-health-watch`)

## Registry summary

```
chains: 51
  - session-start
  - token-monitor
  - loop-daily
  - cache-freshness-watch
  - chain-health-watch
  - github-ci-watch
  - repo-health-watch
  - delivery
  - code-review
  - push-secrets-guard
  - promote-master
  - migration-safe
  - database-design
  - laravel-database-design
  - vector-db-assess
  ... +36 more
```

## chain-audit.sh (exit 0)

```
YAML parse OK
OK: chain session-start: prompt/load-project-cache-first
OK: chain session-start: skill/changelog-specialist
OK: chain session-start: skill/daily-standup-with-cache
OK: chain session-start: skill/token-usage-meter
OK: chain session-start: skill/cache-efficient
OK: chain token-monitor: skill/token-usage-meter
OK: chain loop-daily: skill/loop-triage
OK: chain loop-daily: skill/loop-verifier
OK: chain cache-freshness-watch: skill/cache-freshness-check
OK: chain cache-freshness-watch: skill/loop-verifier
OK: chain chain-health-watch: skill/loop-engineering
OK: chain chain-health-watch: skill/loop-verifier
OK: chain github-ci-watch: skill/github-workflow-expert
OK: chain github-ci-watch: skill/loop-verifier
OK: chain repo-health-watch: skill/github-expert
OK: chain repo-health-watch: skill/git-workflow-guardrails
OK: chain repo-health-watch: skill/loop-verifier
OK: chain delivery: skill/branch-context-agent
OK: chain delivery: skill/bug-hunter-agent
OK: chain delivery: skill/git-workflow-guardrails
OK: chain delivery: skill/test-safety-agent
OK: chain delivery: skill/test-specialist-agent
OK: chain code-review: skill/bug-hunter-agent
OK: chain code-review: skill/security-audit-agent
OK: chain push-secrets-guard: skill/github-expert
OK: chain push-secrets-guard: skill/git-workflow-guardrails
OK: chain promote-master: skill/branch-context-agent
OK: chain promote-master: skill/git-workflow-guardrails
OK: chain promote-master: skill/github-expert
OK: chain promote-master: skill/git-workflow-guardrails
OK: chain migration-safe: prompt/model-schema-check
OK: chain migration-safe: skill/schema-audit-agent
OK: chain migration-safe: skill/test-safety-agent
OK: chain migration-safe: skill/mysql-database-expert
OK: chain migration-safe: skill/mariadb-database-expert
OK: chain migration-safe: skill/sqlite-database-expert
OK: chain migration-safe: skill/laravel-expert-agent
OK: chain migration-safe: skill/filament-panel-review
OK: chain database-design: skill/data-architect-expert
OK: chain database-design: prompt/model-schema-check
OK: chain database-design: skill/schema-audit-agent
OK: chain database-design: skill/laravel-expert-agent
OK: chain database-design: skill/mysql-database-expert
OK: chain database-design: skill/mariadb-database-expert
OK: chain database-design: skill/sqlite-database-expert
OK: chain database-design: skill/filament-panel-review
OK: chain laravel-database-design: skill/data-architect-expert
OK: chain laravel-database-design: prompt/model-schema-check
OK: chain laravel-database-design: skill/schema-audit-agent
OK: chain laravel-database-design: skill/laravel-expert-agent
OK: chain laravel-database-design: skill/mysql-database-expert
OK: chain laravel-database-design: skill/mariadb-database-expert
OK: chain laravel-database-design: skill/sqlite-database-expert
OK: chain laravel-database-design: skill/filament-panel-review
OK: chain vector-db-assess: prompt/load-project-cache-first
OK: chain vector-db-assess: skill/vector-database-expert
OK: chain vector-db-setup: skill/vector-database-expert
OK: chain vector-db-setup: skill/data-architect-expert
OK: chain vector-db-setup: skill/vector-database-expert
OK: chain vector-db-setup: skill/security-audit-agent
OK: chain vector-db-setup: skill/laravel-expert-agent
OK: chain vector-db-setup: skill/mysql-database-expert
OK: chain security-review: skill/security-audit-agent
OK: chain security-review: skill/test-safety-agent
OK: chain cyber-essentials-review: skill/cyber-security-essentials
OK: chain cyber-essentials-review: skill/security-audit-agent
OK: chain cyber-essentials-hunt: prompt/load-project-cache-first
OK: chain cyber-essentials-hunt: skill/cyber-security-essentials
OK: chain cyber-essentials-hunt: skill/bug-hunter-agent
OK: chain cyber-essentials-hunt: skill/security-audit-agent
OK: chain cyber-essentials-pre-deploy: skill/project-drift-guardian
OK: chain cyber-essentials-pre-deploy: skill/cyber-security-essentials
OK: chain cyber-essentials-pre-deploy: skill/bug-hunter-agent
OK: chain cyber-essentials-pre-deploy: skill/security-audit-agent
OK: chain cyber-essentials-pre-deploy: skill/test-safety-agent
OK: chain cyber-essentials-maturity: skill/cyber-security-essentials
OK: chain cyber-essentials-maturity: skill/ai-engineering-maturity
OK: chain cyber-essentials-maturity: skill/security-audit-agent
OK: chain deploy-check: skill/project-drift-guardian
OK: chain deploy-check: skill/docker-expert
OK: chain deploy-check: skill/github-workflow-expert
OK: chain deploy-check: skill/github-expert
OK: chain deploy-check: skill/git-workflow-guardrails
OK: chain deploy-check: skill/digitalocean-app-platform-docr-deploy
OK: chain deploy-check: skill/eval/maintenance-task
OK: chain docker-deploy: prompt/load-project-cache-first
OK: chain docker-deploy: skill/docker-expert
OK: chain docker-deploy: skill/github-workflow-expert
OK: chain docker-deploy: skill/github-expert
OK: chain docker-deploy: skill/git-workflow-guardrails
OK: chain docker-deploy: skill/digitalocean-app-platform-docr-deploy
OK: chain deploy-dns-infra: prompt/load-project-cache-first
OK: chain deploy-dns-infra: skill/aws-route53-dns
OK: chain deploy-dns-infra: skill/digitalocean-app-platform-docr-deploy
OK: chain deploy-dns-infra: skill/amazon-ses-email
OK: chain deploy-dns-infra: skill/git-workflow-guardrails
OK: chain deploy-dns-infra: skill/eval/maintenance-task
OK: chain github-workflow-setup: prompt/load-project-cache-first
OK: chain github-workflow-setup: skill/github-expert
OK: chain github-workflow-setup: skill/github-workflow-expert
OK: chain github-workflow-setup: skill/security-audit-agent
OK: chain github-workflow-setup: skill/git-workflow-guardrails
OK: chain ses-email-setup: skill/aws-route53-dns
OK: chain ses-email-setup: skill/amazon-ses-email
OK: chain repo-health: skill/github-expert
OK: chain repo-health: skill/git-workflow-guardrails
OK: chain repo-health: skill/project-drift-guardian
OK: chain eod-shutdown: skill/todo-specialist-agent
OK: chain eod-shutdown: skill/changelog-specialist
OK: chain eod-shutdown: skill/readme-specialist
OK: chain eod-shutdown: skill/token-usage-meter
OK: chain eod-shutdown: skill/ddev-cleanup
OK: chain documentation-full: prompt/load-project-cache-first
OK: chain documentation-full: skill/acquire-codebase-knowledge
OK: chain documentation-full: skill/readme-specialist
OK: chain documentation-full: skill/documentation-specialist
OK: chain documentation-refresh: prompt/load-project-cache-first
OK: chain documentation-refresh: skill/readme-specialist
OK: chain documentation-refresh: skill/documentation-specialist
OK: chain research-deep-dive: prompt/load-project-cache-first
OK: chain research-deep-dive: skill/research-deep-dive
OK: chain research-deep-dive: skill/research-deep-dive
OK: chain research-deep-dive: skill/research-deep-dive
OK: chain template-deploy: prompt/load-project-cache-first
OK: chain template-deploy: skill/orchestrator-deploy
OK: chain template-deploy: skill/template-decontaminate
OK: chain complex-task: prompt/load-project-cache-first
OK: chain complex-task: prompt/orchestrator-v2
OK: chain loop-engineering-audit: prompt/load-project-cache-first
OK: chain loop-engineering-audit: skill/loop-engineering
OK: chain pre-flight: skill/branch-context-agent
OK: chain pre-flight: skill/project-drift-guardian
OK: chain pre-flight: skill/test-safety-agent
OK: chain laravel-feature: prompt/load-project-cache-first
OK: chain laravel-feature: skill/branch-context-agent
OK: chain laravel-feature: skill/laravel-expert-agent
OK: chain laravel-feature: skill/test-safety-agent
OK: chain laravel-feature: skill/test-specialist-agent
OK: chain filament-review: prompt/load-project-cache-first
OK: chain filament-review: skill/filament-panel-review
OK: chain filament-review: skill/security-audit-agent
OK: chain paypal-setup: skill/project-drift-guardian
OK: chain paypal-setup: skill/paypal-billing-integration
OK: chain didit-identity-setup: skill/project-drift-guardian
OK: chain didit-identity-setup: skill/didit-identity-integration
OK: chain loqate-address-setup: skill/project-drift-guardian
OK: chain loqate-address-setup: skill/loqate-address-integration
OK: chain prod-db-ops: skill/project-drift-guardian
OK: chain prod-db-ops: skill/prod-db-maintenance
OK: chain prod-db-ops: skill/eval/maintenance-task
OK: chain cache-rebuild: prompt/load-project-cache-first
OK: chain cache-rebuild: skill/acquire-codebase-knowledge
OK: chain ai-maturity: prompt/load-project-cache-first
OK: chain ai-maturity: skill/ai-engineering-maturity
OK: chain web-design: prompt/load-project-cache-first
OK: chain web-design: skill/web-build-design
OK: chain web-design: skill/nextjs-expert
OK: chain web-design: skill/astro-expert
OK: chain web-design: skill/nuxt-expert
OK: chain web-design: skill/go-expert
OK: chain web-design: skill/laravel-expert-agent
OK: chain web-design: skill/readme-specialist
OK: chain beta-ready: prompt/load-project-cache-first
OK: chain beta-ready: prompt/beta-ready-checklist
OK: chain beta-ready: skill/project-drift-guardian
OK: chain bug-hunt: prompt/load-project-cache-first
OK: chain bug-hunt: skill/bug-hunter-agent
OK: chain bug-hunt-fix: prompt/load-project-cache-first
OK: chain bug-hunt-fix: skill/bug-hunter-agent
OK: chain bug-hunt-fix: skill/test-safety-agent
OK: chain bug-hunt-fix: skill/test-specialist-agent
OK: chain bug-hunt-deep: prompt/load-project-cache-first
OK: chain bug-hunt-deep: skill/bug-hunter-agent
OK: chain bug-hunt-deep: skill/security-audit-agent
OK: chain bug-hunt-deep: skill/schema-audit-agent
OK: chain bug-hunt-deep: skill/test-safety-agent
OK: chain bug-hunt-deep: skill/test-specialist-agent
OK: chain bug-hunt-fix-deep: prompt/load-project-cache-first
OK: chain bug-hunt-fix-deep: skill/bug-hunter-agent
OK: chain bug-hunt-fix-deep: skill/security-audit-agent
OK: chain bug-hunt-fix-deep: skill/test-safety-agent
OK: chain bug-hunt-fix-deep: skill/test-specialist-agent
OK: chain bug-hunt-fix-deep: skill/schema-audit-agent
OK: chain bug-hunt-pre-deploy: skill/project-drift-guardian
OK: chain bug-hunt-pre-deploy: skill/bug-hunter-agent
OK: chain bug-hunt-pre-deploy: skill/security-audit-agent
OK: chain bug-hunt-pre-deploy: skill/test-safety-agent
OK: chain bug-hunt-pre-deploy: prompt/model-schema-check
OK: chain bug-hunt-pre-deploy-fix: skill/project-drift-guardian
OK: chain bug-hunt-pre-deploy-fix: skill/bug-hunter-agent
OK: chain bug-hunt-pre-deploy-fix: skill/security-audit-agent
OK: chain bug-hunt-pre-deploy-fix: skill/test-safety-agent
OK: chain bug-hunt-pre-deploy-fix: skill/test-specialist-agent
OK: chain bug-hunt-pre-deploy-fix: prompt/model-schema-check
OK: cache path exists or expected: docs/codebase/README.md
OK: cache path exists or expected: docs/codebase/CONCERNS.md
OK: cache path exists or expected: TODO/
OK: cache path exists or expected: .grok/memories/INDEX.md
OK: cache path exists or expected: reports/tokens/latest-summary.json
OK: cache path exists or expected: LOOP.md
OK: cache path exists or expected: STATE.md
OK: cache path exists or expected: loop-budget.md
OK: cache path exists or expected: docs/codebase/.codebase-freshness.txt
OK: cache path exists or expected: chains/registry.yaml
OK: cache path exists or expected: CHAIN.md
OK: cache path exists or expected: docs/codebase/INTEGRATIONS.md
OK: cache path exists or expected: docs/codebase/CONVENTIONS.md
OK: cache path exists or expected: docs/codebase/TESTING.md
OK: cache path exists or expected: .gitguardian.yaml
OK: cache path exists or expected: docs/codebase/ARCHITECTURE.md
OK: cache path exists or expected: .github/workflows/
OK: cache path exists or expected: scripts/deploy-bundle.yaml
OK: cache path exists or expected: patterns/registry.yaml

Chain audit score: 100/100 (issues: 0)
```

## Next (human / agent)

1. Run `/chain chain-health-watch` per patterns/chain-health-watch.md
2. Write `2026-06-29-chain-health.md` and update STATE.md
3. Run `/loop-verifier` on final artifact

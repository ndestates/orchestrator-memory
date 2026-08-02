# project Alignment / Drift Report Template

**Project:** project (Laravel e-signature platform)
**Date:** YYYY-MM-DD
**Branch / Action:** 
**Guardian Run By:** (grok / human + this skill)
**Cache Loaded:** (yes + which: INDEX, docs/codebase/*, TODO, prior evals)

## Executive Summary
- Overall alignment: Strong / Minor drift / Significant drift (blocker)
- Key drifts flagged: N (blockers: M)
- Recommendation: PROCEED / BLOCK until remediated / PROCEED with conditions (list)
- Hosting context: Droplet | App Platform | Both (note current target)

## Requirements Coverage (from DB or docs/codebase/CONCERNS + TODO)
List critical ones checked (expand as needed):
- [ ] Public canvas signature roundtrip + PDF embed + audit (hash, ip/ua)
- [ ] Multi-signer ordered requests + token magic links (roundtrip, consent, expiry guards)
- [ ] Signature immutability (no post-sign mutations; append-only audit)
- [ ] Filament admin for core entities (Documents, Signers, Requests)
- [ ] DDEV local parity
- [ ] DigitalOcean hosting: droplet (control) + App Platform (DOCR auto-deploy, limited tokens)
- [ ] CI: tests + schema/model checks + drift guardian + security + hardened build + safe deploy + post-eval
- [ ] Safe DB updates: backup first, pre-checks (model-schema + audit), guarded apply (prod-db-maintenance style), post-verify (counts + signature samples), evals
- [ ] No drift policy enforcement (scope, code, schema, container tags/images, infra)

Status for each: Delivered / In progress / Drift detected (details below) / N/A

## Drifts Detected (evidence-based)
For each:
- Type: scope | code | schema | container/infra | deploy | security/audit | other
- Requirement(s) impacted
- Evidence (git diff path:line, migration vs model, doctl output, image tags, etc.)
- Severity + why critical for project (e.g. "risks tamper evidence for signatures/audit/compliance")
- Suggested remediation (specific + skill calls)

## Pre-Deploy / Pre-DB / Pre-CI Gates Status
- Branch discipline + git-workflow-guardrails: 
- Schema/model alignment (model-schema-check + schema-audit-agent):
- Container / image drift (tags vs prod, SBOM/Trivy in CI, DOCR vs droplet):
- Scope vs requirements DB:
- Security/audit implications (uploads, tokens, signature data):
- Full guardian + cache load:

## Post-Action Verification (after deploy or change)
- Deploy type + target (droplet details or App Platform ID):
- DB update applied (migration(s), backup ref):
- Verification: counts, sample hashes, roundtrip test, image running, no new drifts:
- Eval/maintenance-task report ref:
- Requirements DB updated (decisions logged):

## Recommendations & Next
1. ...
2. (include calls to other skills: /github-expert for workflow updates, /prod-db-maintenance, /eval-maintenance-task, re-run guardian, security-audit if PII involved, etc.)

## Appendix
- Full diff or plan summary
- Requirements DB snapshot (or query output)
- Links to docs/codebase/ files, TODO items, prior reports
- Raw guardian output / AI analysis

**Signed off by:** (human + guardian log ID if applicable)

This report should be logged (via db_ops or commit to reports/) and referenced in TODO / decisions. Use it to keep project hosting, CI, and DB changes drift-free.
# GitHub CI Host Snapshot — 2026-06-29

**Level:** L1 host-only (agent completes report via `/chain github-ci-watch`)

## Local workflow files

branch-promotion-prs.yml,chain-audit.yml,loop-daily-triage.yml,loop-weekly-watch.yml,mcp-security.yml,release.yml,repository-sync.yml,run-chain.yml,template-decontamination.yml,tooling-tests.yml
branch-promotion-prs.yml
chain-audit.yml
loop-daily-triage.yml
loop-weekly-watch.yml
mcp-security.yml
release.yml
repository-sync.yml
run-chain.yml
template-decontamination.yml
tooling-tests.yml

## gh workflow list

```
Branch Promotion PRs	active	287719308
Chain Registry Audit	active	297051564
Loop Daily Triage (L1 host)	active	296131500
Loop Weekly Watch (L1 host)	active	299360958
MCP Security	active	300722115
Release	active	287719311
Repository Sync & Maintenance	active	287719312
Template Decontamination	active	301264456
Tooling Tests	active	301320535
Dependabot Updates	active	296122695
Dependency Graph	active	299254848
```

## Recent runs (≤10)

```
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Tooling Tests	develop	pull_request	28357298493	29s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Chain Registry Audit	develop	pull_request	28357298485	20s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Template Decontamination	develop	pull_request	28357298465	10s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Tooling Tests	develop	push	28357296571	30s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Branch Promotion PRs	develop	push	28357296567	15s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Chain Registry Audit	develop	push	28357296541	22s	10m
completed	success	Merge pull request #74 from ndestates/feature/loop-chain-automation-phase-ab	Template Decontamination	develop	push	28357296507	12s	10m
completed	success	docs: refresh site and cache for Phase A/B chain automation	Chain Registry Audit	feature/loop-chain-automation-phase-ab	pull_request	28356821487	21s	19m
completed	success	docs: refresh site and cache for Phase A/B chain automation	Template Decontamination	feature/loop-chain-automation-phase-ab	pull_request	28356821432	9s	19m
completed	success	docs: refresh site and cache for Phase A/B chain automation	Tooling Tests	feature/loop-chain-automation-phase-ab	pull_request	28356821428	26s	19m
```

## Failed runs (≤5, JSON)

```json
[]
```

## Secret names (repo + production if present)

```

```

## Next (human / agent)

1. Run `/chain github-ci-watch` per patterns/github-ci-watch.md
2. Write `2026-06-29-github-ci.md` and update STATE.md
3. Run `/loop-verifier` on final artifact

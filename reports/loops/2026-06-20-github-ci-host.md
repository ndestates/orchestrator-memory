# GitHub CI Host Snapshot — 2026-06-20

**Level:** L1 host-only (agent completes report via `/chain github-ci-watch`)

## Local workflow files

branch-promotion-prs.yml,chain-audit.yml,loop-daily-triage.yml,loop-weekly-watch.yml,release.yml,repository-sync.yml
branch-promotion-prs.yml
chain-audit.yml
loop-daily-triage.yml
loop-weekly-watch.yml
release.yml
repository-sync.yml

## gh workflow list

```
Branch Promotion PRs	active	287719308
Chain Registry Audit	active	297051564
Loop Daily Triage (L1 host)	active	296131500
Release	active	287719311
Repository Sync & Maintenance	active	287719312
Dependabot Updates	active	296122695
Dependency Graph	active	299254848
```

## Recent runs (≤10)

```
completed	success	Repository Sync & Maintenance	Repository Sync & Maintenance	master	schedule	27867793537	13s	2026-06-20T10:02:08Z
completed	action_required	chore(sync): promote feature/work-2026-06-21 to develop	Chain Registry Audit	feature/work-2026-06-21	pull_request	27865532543	0s	2026-06-20T08:23:37Z
completed	success	chore(todo): note v1.0.1, master #46, wave redeploy	Chain Registry Audit	feature/work-2026-06-21	push	27865528201	19s	2026-06-20T08:23:26Z
completed	success	chore(todo): note v1.0.1, master #46, wave redeploy	Branch Promotion PRs	feature/work-2026-06-21	push	27865528200	11s	2026-06-20T08:23:26Z
completed	success	Merge pull request #43 from ndestates/develop	Release	v1.0.1	push	27865393387	10s	2026-06-20T08:17:31Z
completed	success	Merge pull request #45 from ndestates/feature/eod-orchestrator-2026-0…	Chain Registry Audit	develop	push	27865390475	15s	2026-06-20T08:17:22Z
completed	success	Merge pull request #45 from ndestates/feature/eod-orchestrator-2026-0…	Branch Promotion PRs	develop	push	27865390474	11s	2026-06-20T08:17:22Z
completed	success	chore(eod): close 2026-06-20 session — TODO carry-forward, changelog,…	Chain Registry Audit	feature/eod-orchestrator-2026-06-21	push	27865249348	15s	2026-06-20T08:11:10Z
completed	success	chore(eod): close 2026-06-20 session — TODO carry-forward, changelog,…	Branch Promotion PRs	feature/eod-orchestrator-2026-06-21	push	27865249345	18s	2026-06-20T08:11:10Z
completed	success	chore(sync): promote develop to master	Chain Registry Audit	develop	pull_request	27865223375	19s	2026-06-20T08:10:04Z
```

## Failed runs (≤5, JSON)

```json
[{"conclusion":"failure","displayTitle":"feat(wave): deploy to each app's current working branch","updatedAt":"2026-06-20T08:09:17Z","workflowName":"Branch Promotion PRs"}]
```

## Secret names (repo + production if present)

```

```

## Next (human / agent)

1. Run `/chain github-ci-watch` per patterns/github-ci-watch.md
2. Write `2026-06-20-github-ci.md` and update STATE.md
3. Run `/loop-verifier` on final artifact

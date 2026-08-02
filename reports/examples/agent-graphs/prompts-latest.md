MULTI-WORKSTREAM prompts · auto_merge=no · report-only
primary=multi-stream-graphs
summary: merge_ready=0 ready_for_pr=0 wip=1 frozen=4 total=5

## What is going on
- FOCUS: #1 `multi-stream-graphs` is primary with **uncommitted** work.
- SAFEGUARD: multi-workstream never merges to develop/staging/master for you.

## Per stream
*#1 multi-stream-graphs  status=active  phase=wip  branch=feature/multi-workstream-session-v2-2026-07-22  ahead=28 behind=0
    prompt: #1 multi-stream-graphs is PRIMARY focus — do serial work here first.
    prompt: #1 has **uncommitted work** in main tree.
    → Commit or stash before PR/merge readiness.
    → Next note: Use focus/hold/note to juggle day items (not product demos)
    pr: https://github.com/ndestates/orchestrator/pull/187 (OPEN)
 #2 opensource-license  status=held_ready  phase=held_ready  branch=feature/opensource-apache-patreon-2026-07-22  ahead=4 behind=0
    prompt: #2 opensource-license is held_ready — frozen until you unhold.
    → To open: /multi-workstream activate 2
    → Do not merge held tracks.
 #3 freemium-paypal  status=held  phase=held  branch=feature/freemium-license-publish-2026-07-18  ahead=0 behind=18
    prompt: #3 freemium-paypal is held — frozen until you unhold.
    → To open: /multi-workstream activate 3
    → Do not merge held tracks.
 #4 webmcp-beta  status=parked  phase=parked  branch=feature/webmcp-beta-setup-2026-07-21  ahead=2 behind=0
    prompt: #4 webmcp-beta is parked — not in active work set.
    → Unpark only if intentional: /multi-workstream activate 4
 #5 product-graph  status=parked  phase=parked  branch=—  ahead=0 behind=0
    prompt: #5 product-graph is parked — not in active work set.
    → Unpark only if intentional: /multi-workstream activate 5

## Operator next
1. Act on ACTION/FOCUS lines above
2. Re-run /multi-workstream prompts after commits or PR changes
3. Merge only via GitHub/gh when checks green — not via multi-workstream


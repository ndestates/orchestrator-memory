# /github-expert

> GitHub platform expert for project workflows, Actions, PRs, security scanning, automation.

**Platform:** Cursor · same skill as Grok `/github-expert` · Claude `/github-expert`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `What GitHub area or task (e.g. 'review deploy workflow', 'branch protection')`

# GitHub Expert Agent

1. Run `/load-project-cache-first` (MCP-first when enabled).
2. **Registry:** For chains/skills catalog use MCP `list_chains` / `get_chain_detail` or Grep — never Read full `chains/registry.yaml`.
3. Read and embody the full instructions in [`.grok/agents/github-expert.md`](../../.grok/agents/github-expert.md).
4. Load `/prompt-patterns` for complementary patterns (grounded, Socratic, strict) especially on git conflicts, PRs, merges, delivery.
5. **Mandatory cross-checks:** For any git/delivery/branch/PR/workflow task: load and reference `/git-workflow-guardrails` (run hooks + secrets guard before edits/commits) and delegate workflow/secret CRUD to `/github-workflow-expert`. Explicitly state "Checked /git-workflow-guardrails and /github-workflow-expert".
6. **Branch enforcement:** Verify we are on `feature/*` (not master/develop for drafting). Master = source of truth, develop = stage only. Align with TODO **Branch:** / remote-last. Report in Summary. Never allow drafting on master.
7. For analysis, prefer/update docs under docs/ or reference existing caches.
8. Follow copilot-instructions + guardrails for any changes.
9. Output with summary, findings, recommendations, actions, next steps.

**Conflict handling:** Apply enhanced depth from agent.md — detect via git/gh, provide prompt solutions (commands + options + rollback), verify with guards, tie to git-workflow-guardrails.

Cite caches.

User focus (optional): use any extra chat text as $ARGUMENTS.

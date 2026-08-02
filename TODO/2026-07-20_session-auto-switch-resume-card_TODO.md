# TODO — Session auto-switch + resume-card + 1.8.7 (2026-07-20) — EOD closed

**Branch:** `feature/context-window-literacy-2026-07-18`  
**Version:** 1.8.7  
**EOD:** 2026-07-20  
**Status:** implemented this session; closed EOD

## Done this session

1. [x] `resume-branch.sh --apply` auto-switches to remote_last when clean; blocks if dirty
2. [x] session-context-envelope default applies remote_last; surfaces switch + check/card
3. [x] session-resume-brief: always surface card on check; `--rich` write for session-end/eod
4. [x] session-end-checkpoint + eod-vault-emit write rich resume cards
5. [x] chains session-start / session-end / eod-shutdown policy + docs/skills
6. [x] Install/deploy: never overwrite project-manifest; seed/amend stack-aware for new apps
7. [x] Bug-hunt + CSE on this slice; fixed lstrip protect, safe checkout/pull, EOD dirty hint
8. [x] Bump **1.8.7** (this branch only; freemium stays Unreleased/held)
9. [x] Session-start **automatic** orch upgrade check in envelope (`orch kind/offer`)

## Open (carry to 2026-07-21)

1. [ ] **PR → develop** for 1.8.7 (context literacy + session/manifest policy)
2. [ ] Optional: sync AGENTS.md / copilot-instructions platform prose if drift remains
3. [ ] (Later) Unhold PayPal only on explicit ask
4. [ ] (Later) Freemium/license Unreleased — not part of 1.8.7

## Standing

- session-start always check + card + orch auto-check (offer only)
- auto-switch remote_last when clean only
- rich resume card mandatory at session-end and eod-shutdown
- project-manifest never overwritten by template deploy

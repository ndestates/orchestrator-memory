# Context literacy plan + abandonments (2026-07-18)

**Branch:** `feature/context-window-literacy-2026-07-18`  
**Status:** Active = context literacy only  

## Decisions

| Topic | Decision |
|-------|----------|
| Multi-session / multi-lane SDK patterns in orchestrator | **Abandon** — leave in **mailchimp** (`scripts/copilot_multiple_sessions_demo.py`, `src/copilot_multi_session.py`) |
| Vector DB product push | **Abandon** this initiative (skill fit-assess remains available; no adopt-by-default) |
| PayPal production | **Held** (P0) — no live plan IDs / webhook production push without explicit unhold |
| Context-window literacy | **Proceed** — operator/agent guide + index links |

## Deliverable

- Guide: `docs/guides/context-window-literacy.md`  
- Links from guides index + cache-and-token-savings “related”  
- Day TODO + resume card updated  

## Non-goals

- Port multi-session manager into template  
- Install pgvector / transformers / embedding pipelines  
- Unhold PayPal or license-api production deploy  

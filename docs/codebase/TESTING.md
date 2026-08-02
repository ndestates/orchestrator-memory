# Testing

[UPDATED 2026-07-07] — aligned to full docs update; see human operations/testing.md.

This template has no application test suite. Validation is **registry/policy audit** driven, plus a small unit test for the MCP server.

See human guide: operations/testing.md for procedures and CI gates (includes `python3 scripts/docs-link-audit.py` for docs site).

## Audit Scripts

| Script | Pass criteria |
|--------|---------------|
| `bash scripts/chain-audit.sh` | YAML valid; all chain `invoke` targets exist; score 100/100 |
| `bash scripts/loop-audit.sh` | Loop registry maturity ≥ 80 (scored /160) |
| `bash scripts/chain-completion-write.sh` | Appends `loop-run-log.md`; updates `STATE.md` last-chain section |
| `bash scripts/run-chain-host.sh <id>` | Validates chain id; optional host snapshot; writes dispatch note |
| `python3 scripts/check_name_alignment.py` | Skill/agent/command names aligned across surfaces |
| `python3 scripts/verify_github_actions_node24.py` | No Node 20 in workflows (Node 24 enforced) |
| `bash scripts/mcp-threat-scan.sh` | MCP server has no unsafe exec / unsandboxed reads |

## MCP Server Tests

- `mcp-server/tests/test_helpers.py` — helper unit tests.
- `mcp-server/tests/test_security.py` — sandbox allowlist integrity (denies `.env`/`.git`/traversal/symlink escape), bearer-auth semantics, and the fail-closed HTTP startup gate.
- Run: `pip install -e "mcp-server/[dev]"` then `pytest mcp-server/tests -q`.
- **CI:** `.github/workflows/mcp-security.yml` runs the tests + `scripts/mcp-threat-scan.sh` on changes to `mcp-server/`.

## CI Checks (GitHub)

- GitGuardian security scan on PRs (external app)
- `chain-audit.yml` — `scripts/chain-audit.sh` on PRs to `develop`/`master` and pushes to `develop`/`feature/**`
- `loop-daily-triage.yml` / `loop-weekly-watch.yml` — host snapshot scripts for L1 loops
- `run-chain.yml` — `workflow_dispatch` chain prep via `run-chain-host.sh`
- Node 24 enforcement step (`verify_github_actions_node24.py`) in workflows
- `branch-promotion-prs.yml` self-test on qualifying pushes

## Manual Verification Gates

| Gate | Command / artifact |
|------|-------------------|
| Sync parity | `python3 scripts/sync_grok_to_github_claude.py` then `git diff` |
| Name alignment | `python3 scripts/check_name_alignment.py` |
| Script-first rule | `/script-not-shell` — no multi-line inline shell |
| Chain registry | `bash scripts/chain-audit.sh` |
| Loop L1 | `/chain loop-daily` → `reports/loops/YYYY-MM-DD-triage.md` + verifier PASS |
| Beta readiness | `beta-ready-checklist` skill (when adopting template) |
| MCP threat scan | `bash scripts/mcp-threat-scan.sh` |

## L1 Loop Rubric (verifier)

- Cache cited in report
- No auto-fix / no source exploration at L1
- `STATE.md` and `loop-run-log.md` updated (triage or `chain-completion-write.sh`)
- Executive summary ≤ 120 words

## Evidence

- `scripts/chain-audit.sh`, `scripts/loop-audit.sh`, `scripts/check_name_alignment.py`, `scripts/verify_github_actions_node24.py`, `scripts/mcp-threat-scan.sh`
- `mcp-server/tests/test_helpers.py`, `mcp-server/pyproject.toml`
- `.github/workflows/chain-audit.yml`, `loop-daily-triage.yml`, `loop-weekly-watch.yml`

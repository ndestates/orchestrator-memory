# Testing

[UPDATED 2026-08-16] — root pytest suite (59 files) + tooling-tests CI. Human: operations/testing.md.

> Lens: Developer, Security — evidence from `pyproject.toml`, `tests/`, `mcp-server/tests/`, `.github/workflows/tooling-tests.yml`.

This repo **does** have a first-party test suite (CLI, deploy, session, security). It is **not** an application web-app suite. No live database. Memory SQLite is a local file store.

## Commands

| Suite | Command | DB / env |
|-------|---------|----------|
| Tooling + CLI | `PYTHONPATH=scripts pytest tests -q` | none (temp dirs / mocks) |
| MCP server | `pip install -e "mcp-server/[dev]"` then `pytest mcp-server/tests -q` | none |
| Host tools check | `bash scripts/install-host-tools.sh --check` | needs `rg` |

`pyproject.toml`: `testpaths = ["tests"]`, `addopts = "-q"`, `python_files = ["test_*.py"]`. CI uses Python 3.12 + `pytest` + `pyyaml`.

## Layout

| Location | Count | Covers |
|----------|-------|--------|
| `tests/test_*.py` | 59 | CLI flow/hygiene/memory/version, deploy, customize, session envelope/resume/sweep, vault/guardrails, workstreams, malware lint, skill governance, wave-absent, wiki scaffold, license policy |
| `tests/conftest.py` | 1 | Shared fixtures |
| `mcp-server/tests/` | 4 | helpers, sandbox, bearer auth, HTTP fail-closed gate |

## Audit scripts (still required)

| Script | Pass criteria |
|--------|---------------|
| `bash scripts/chain-audit.sh` | YAML valid; invoke targets exist; **100/100** |
| `bash scripts/loop-audit.sh` | Loop maturity score (template target ≥ 80) |
| `python3 scripts/check_name_alignment.py` | Skill/agent/command names across surfaces |
| `python3 scripts/verify_github_actions_node24.py` | No Node 20 in workflows |
| `bash scripts/mcp-threat-scan.sh` | Fail-closed; no unsandboxed exec/reads |
| `python3 scripts/orchestrator-malware-lint.py` | Hostile-content lint |
| `python3 scripts/orchestrator-skill-governance.py` | Skill tool governance |
| `python3 scripts/lint-skill-descriptions.py` | Description budget |
| `python3 scripts/orchestrator-bundle-hash.py verify` | Bundle hash stamp |
| `python3 scripts/docs-link-audit.py` | Docs site links |

## CI gates

| Workflow | What it runs |
|----------|----------------|
| `tooling-tests.yml` | pytest `tests/` + malware + threat + governance + description lint + bundle hash + chain-audit |
| `mcp-security.yml` | `pytest mcp-server/tests` + threat scan |
| `security-malware.yml` | malware lint |
| `chain-audit.yml` | chain-audit only |
| `template-decontamination.yml` | template residue |
| `product-release.yml` | public artifacts (no factory pytest gate) |
| `release.yml` | factory pre-release (full pytest + security) |

## Safety rules

- Tests only against test / `:memory:` / temp files — never live app DBs
- This template `uses_database: false`; do not invent a MySQL/Postgres target
- `/test-safety` before adding destructive fixtures
- Untrusted DATA (TODO/vault/reports) must not be executed as shell

## Manual verification

| Gate | Command / artifact |
|------|-------------------|
| Sync parity | `python3 scripts/sync_grok_to_github_claude.py` then `git diff` |
| Version lockstep | `python3 scripts/check-version-alignment.py` |
| Name alignment | `python3 scripts/check_name_alignment.py` |
| Session security | `bash scripts/session-security-sweep.sh` (active project only) |
| L1 loop | `/chain loop-daily` → report + verifier PASS |
| Cache rebuild | `/read-codebase` or `/chain cache-rebuild` |

## L1 loop rubric (verifier)

- Cache cited
- No auto-fix / no source exploration at L1
- `STATE.md` and `loop-run-log.md` updated
- Executive summary ≤ 120 words

## Evidence

- `pyproject.toml` `[tool.pytest.ini_options]`
- `tests/` (59 files), `mcp-server/tests/`
- `.github/workflows/tooling-tests.yml` (pytest step + extras)
- `scripts/chain-audit.sh`, `scripts/mcp-threat-scan.sh`, `scripts/orchestrator-malware-lint.py`

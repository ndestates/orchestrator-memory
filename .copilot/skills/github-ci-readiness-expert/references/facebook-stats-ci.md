# Facebook Stats — CI/CD specialization

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `option-c-quality-gate.yml` | PR | Unit + targeted + integration tests (Option C) |
| `container-security-scan.yml` | PR + push develop/master | Trivy on `Dockerfile.hardened` |
| `daily-catalog-update.yml` | schedule + dispatch | Live catalog sync — **not PR gate** |
| `chain-audit.yml` | PR + push feature/** | Registry validation |
| `template-decontamination.yml` | PR/push (path filter) | Template residue scan |

## PR gates (what blocks merge)

All must pass on PR → `develop`:

1. **option-c-gate** — `python run_tests.py unit`; targeted pytest when scripts change; integration when `scripts/` or `src/facebook_client.py` change (fake FB env vars in workflow)
2. **trivy-image-scan** — hardened image build + HIGH/CRITICAL scan
3. **chain-audit** / **decontamination** when paths match

## Common failure modes (fixed / watch)

| Symptom | Cause | Fix |
|---------|-------|-----|
| Red **push** check named `daily-catalog-update.yml` | **Invalid workflow:** `secrets.*` in job-level `if` — GitHub rejects file on push | Gate inside steps; never `if: secrets.FOO != ''` on job |
| option-c-gate integration fail | Live API / DDEV secret checks in tests | CI uses dummy `FACEBOOK_*` env; tests must skip live calls |
| Targeted test fail | Script changed without `tests/test_<script>.py` | Add matching test file |
| trivy fail | CVE in hardened image | Update base image / packages |

## Pre-push

```bash
python run_tests.py unit
# if scripts/ touched:
pytest -v tests/test_<changed_script>.py   # or tests/test_scripts/
bash .grok/skills/github-workflow-expert/scripts/workflow-validate.sh
python3 scripts/verify_github_actions_node24.py
```

Never use `secrets` in job-level `if` conditions — use step gate pattern (see `daily-catalog-update.yml`).
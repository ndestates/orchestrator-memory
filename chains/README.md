# Chain registry (split model)

Wave apps use a **split registry** so template updates never wipe app-owned wiring.

| File | Owner | Deploy policy |
|------|-------|---------------|
| `registry.template.yaml` | Orchestrator template | Copied on full template wave |
| `registry.app.yaml` | Target app | **Never** overwritten by wave deploy |
| `registry.yaml` | Composed (generated) | `compose-registry.py` merges template + app |

## Edit workflow

**Orchestrator template** — edit `registry.template.yaml` for shared skills and standard chains, then:

```bash
python3 scripts/compose-registry.py
bash scripts/chain-audit.sh
```

**Wave app** — edit `registry.app.yaml` for project skills, aliases, and chain overrides, then:

```bash
python3 scripts/compose-registry.py
```

`register-project-skills.py` appends missing local skill dirs to `registry.app.yaml` automatically after deploy.

## Migration

One-time split from legacy monolith:

```bash
python3 scripts/split-registry.py              # orchestrator template
python3 scripts/migrate-app-registry-split.py --target /path/to/app
```

Full wave deploy runs `deploy-registry-wave.py` (template copy + migrate-if-needed + compose).
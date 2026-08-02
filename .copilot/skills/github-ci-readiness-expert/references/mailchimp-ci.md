# Mailchimp — CI/CD specialization

## Workflows (deploy-heavy)

| Workflow | Risk |
|----------|------|
| `deploy-digitalocean.yml` | Production deploy — confirm branch/ref |
| `deploy-droplet.yml` | Droplet deploy |
| `build-digitalocean-image.yml` | Image build |
| `deploy-digitalocean-db-manual.yml` | **Manual DB** — never accidental dispatch |
| `ddev-mysql8-migration.yml` | Migration workflow |
| `chain-audit.yml` | Registry gate |

## Pre-push on feature branches

- Ensure push does **not** trigger production deploy workflows (check readiness `triggers_on_push`)
- Secrets for DO/registry must exist (names only)
- Use `workflow_dispatch` deploys only with explicit operator approval
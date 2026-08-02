# Wave project CI specializations

| Slug | File | CI model |
|------|------|----------|
| lightstone | `lightstone-ci.md` | Laravel DDEV + `ci.yml` static/lint on PR+push |
| google-stats | `google-stats-ci.md` | Container image build/deploy workflows |
| facebook-stats | `facebook-stats-ci.md` | Catalog/quality gates + container scan |
| e-ndsign | `generic-laravel-ci.md` | Laravel e-sign app |
| ndestates-io | `generic-laravel-ci.md` | Laravel marketing/app |
| jerseyhouseprices | `generic-laravel-ci.md` | Laravel listings |
| mailchimp | `mailchimp-ci.md` | DO image + deploy workflows |
| ndestates | `generic-laravel-ci.md` | Laravel estates |
| orchestrator | `orchestrator-template-ci.md` | Template repo — chain-audit + MCP |

Invoke: `/github-ci-readiness-expert` or `/chain ci-branch-readiness` with slug in args when ambiguous.
# Facebook Stats Specializations

**Project-specific QA checklist items** for the facebook-stats wave project (Meta Ads analytics + automation).

This file isolates domain-specific concerns. The core qa-agent (general checklist) + this specialization file = project-specific qa-agent.

Other wave projects get their own `*-specializations.md` (see below).

## Usage

- General checklist always loaded.
- Load this (or your project's specialization) for domain checks.
- When using: `/qa-agent pre-pr facebook-stats` or pass via skill_args / scope.

---

## Meta / Facebook API & Ads Domain

- Rate limiting, backoff, retry, and `make_api_call_with_retry` / RateLimiter usage respected in changed client or script code.
- Dry-run, `--auto-approve`, `--select-all` flags honored; no unintended live mutations.
- Audience management: listing audiences, buyers audience (52607588940839), create/attach/delete flows correct and idempotent.
- Campaign / AdSet / Ad labeling and groups: rotation tags, AvailableToRun, price tiers, Advantage+ vs classic naming conventions followed.
- Catalog / feed / product sets: consistency between feed, product sets, and ad creatives (carousels, Advantage+ catalog).
- Ad creative & UTM / tracking parameters handled safely (especially new carousel UTM + listing adsets work from feature/carousel-utm-and-listing-adsets).
- activate_listing_only, add_buyers_audience_to_property_adsets, create_campaign_tags, manage_campaign_groups, setup_lifetime_scheduling correctness and safety.
- Insights / performance / analysis scripts: date ranges, attribution windows, and output CSVs are accurate and not stale.
- API version pinned (v24.0 or current) and error handling for common Meta error codes (17 rate limit, 100, etc.).
- facebook_client.py: tightened broad except blocks, proper logging, no direct SDK without rate limiter wrapper.
- web/api/feed_preview.php: no @ suppression, try/except + logging for file_get_contents etc.
- Test gates observed: narrow unit + targeted integration (e.g. test_facebook_client, audience, adset, rotation) via ddev only.

## Runtime & Ops Safety

- All Python execution via `ddev exec` (never bare host python for project scripts/tests).
- Database target explicitly `test` or equivalent when running tests or analysis that touches data.
- Secrets / tokens: no leakage in reports, logs, or diffs. `.env*` respected.
- High-churn areas (manage_campaigns.py, rotation scripts, audience scripts, client) receive extra regression attention.
- Reports / artifacts (in `reports/`) are gitignored; no accidental commit of generated CSVs.

## Testing & Verification Gates

- `test-safety-agent` invoked (or equivalent checks) before any test execution.
- Relevant narrow unit + targeted integration tests run for the scope (e.g. facebook_client, adset creators, audience flows, campaign rotation).
- End-to-end or script smoke tests where the change affects automation (campaign creation, rotation, audience attach, feed processing).
- No reliance on live Meta calls during routine QA unless explicitly in scope + dry-run first.

## Project Process & Cache

- TODO items updated or handed off when scope touches active work.
- Cache files cited (docs/codebase/* + TODO + STATE if loops involved).
- For loops: if touching loop artifacts, `loop-verifier` rubric can be applied.
- Branch alignment: work matches the active feature branch purpose (use branch-context if unsure).

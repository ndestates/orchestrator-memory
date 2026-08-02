# Google Stats Specializations

**Project-specific QA checklist items** for the google-stats wave project (Google Ads / GA4 analytics + automation).

Analogous to facebook-stats but for Google ecosystem.

## Meta / Google Ads & Analytics Domain

- Google Ads API rate limits, quota, retry/backoff logic respected (including customer match, asset, campaign services).
- Dry-run / simulation modes and `--auto-approve` style flags honored; no unintended live mutations or bid changes.
- Audience / customer match lists: creation, upload, removal flows correct and compliant with consent.
- Campaign / AdGroup / Asset labeling, groups, rotation, scheduling, and performance max / standard distinctions followed.
- Feed / product data / asset sync consistency between Google Merchant Center, product sets, and ad creatives.
- UTM / tracking / conversion action handling safe (especially custom parameters, enhanced conversions).
- High-churn automation: report fetching, rule engines, audience sync scripts, pixel/CAPI equivalents.
- API version and error handling for common Google errors (rate limit 429, quota, permission issues).
- Client libraries: proper auth (service account or OAuth), logging, no broad catches that hide quota problems.
- Test gates: unit + integration for ads client, audience sync, feed processing, reporting via ddev only.

## Runtime & Ops Safety

- All Python/Flask execution via `ddev exec`.
- Database target `test` when touching analytics data or reports.
- No leakage of Google API keys / refresh tokens in reports/logs/diffs.
- High-churn areas (feed scripts, rotation, audience builders) get extra regression focus.
- Artifacts (reports/, CSVs) remain gitignored.

## Testing & Verification Gates

- `test-safety-agent` (or equivalent) before any test runs.
- Relevant tests for google client, audience, feed, reporting, campaign creation flows.
- Smoke / e2e where automation affects live campaigns.
- Prefer dry / mock for live Google calls in routine QA.

## Project Process & Cache

- TODO / branch alignment respected.
- Cache files cited.
- For loops or heavy automation: apply loop-verifier where relevant.

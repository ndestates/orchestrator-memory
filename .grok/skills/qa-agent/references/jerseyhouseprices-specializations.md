# Jersey House Prices Specializations

**Project-specific QA checklist items** for the jerseyhouseprices wave project (Laravel real estate / property pricing platform).

## Property / Real Estate Domain

- Property listing data accuracy: prices, addresses, features, status, images.
- Search, filtering, and pricing algorithms / comparables logic correctness.
- User accounts, saved searches, alerts, favorites integrity.
- Data ingestion / import pipelines (if any) for property data sources.
- Maps, geocoding, location-based features.
- Public vs private data separation (e.g. premium listings).

## Safety & Compliance

- All data ops against test database or fixtures. Never live production property/user data without explicit approval.
- No leakage of user PII, saved searches, or internal pricing data in reports, logs, or diffs.
- Auth and authorization for user-specific content.
- GDPR / data protection considerations for user accounts and alerts.

## Testing & Verification

- `test-safety-agent` before any test execution.
- Targeted tests for listing CRUD, search, pricing logic, user account flows.
- Integration tests for any external data sources or maps.
- Regression on high-churn areas like listing updates, search performance, notifications.

## Project Process & Cache

- Strong branch alignment with property data or pricing features.
- Cache files cited, especially for data-heavy changes.
- TODO updates for listing / pricing work.
- Use `branch-context-agent` when scope touches user-facing property features.

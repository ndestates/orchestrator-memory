# Lightstone Specializations

**Project-specific QA checklist items** for the lightstone wave project (admin dashboard + regression testing focus).

## Admin Dashboard & Regression Domain

- Dashboard UI components, filters, reports, admin actions — correctness and performance.
- Regression coverage: areas that previously had regressions (dashboard controls, migration guardrails, etc.).
- Data integrity in admin views (listings, users, stats).
- Authorization / role checks in admin panel.
- High-churn admin automation or bulk operations.

## Safety

- Never run destructive admin actions against prod data; use test DB or isolated fixtures.
- Secrets / config not exposed in dashboard views or reports.
- CSRF, auth, permission checks verified on any new admin endpoints or actions.

## Testing & Verification

- Heavy emphasis on `test-safety-agent`.
- Regression suites for known problem areas.
- UI / integration tests for dashboard flows (where possible via ddev).
- Smoke tests after deploys or migrations affecting admin.

## Project Process

- Explicit regression sign-off in pre-deploy / pre-pr for lightstone.
- Cache and TODO updates when touching admin or data layers.
- Branch context for admin-dashboard-regression work.

# Mailchimp Specializations

**Project-specific QA checklist items** for the mailchimp wave project (Python Flask + Mailchimp email marketing automation).

## Email Marketing / Mailchimp API Domain

- Mailchimp API usage: campaigns, automations, audiences, segments, templates.
- Audience management: list creation, subscriber import, merge fields, tags, compliance with consent.
- Webhook handling for events (subscribe, unsubscribe, bounce, click).
- Campaign sending logic, scheduling, A/B testing, content personalization.
- Sync between local data (users, segments) and Mailchimp.
- Deliverability, unsubscribe handling, and double opt-in flows.
- Reporting / insights from Mailchimp (opens, clicks, bounces) used in app.

## Safety & Compliance

- All Mailchimp API calls and data ops via proper test lists / test mode where available.
- Never send to real subscribers in test environments.
- Strict handling of unsubscribe and consent data (GDPR, CAN-SPAM).
- No leakage of API keys, subscriber data, or campaign content in logs, reports, or diffs.
- Webhook signature verification.

## Testing & Verification

- `test-safety-agent` before tests.
- Unit + integration tests for Mailchimp client, webhook receivers, audience sync, campaign builders.
- Smoke tests for campaign creation and send flows (using sandbox/test lists).
- Regression on audience segmentation, webhook processing, reporting imports.

## Runtime & Ops Safety (Flask / Python)

- Execution via `ddev exec` (Python Flask profile).
- Database target `test` when touching subscriber or campaign data.
- Secrets (Mailchimp API keys) never committed or exposed.
- High-churn areas (sync scripts, campaign rules) receive extra attention.
- Artifacts and CSV exports remain gitignored.

## Project Process & Cache

- Cache discipline for Mailchimp-related config and audience data.
- TODO and branch alignment for newsletter / marketing automation work.
- Use `project-drift-guardian` for changes affecting external Mailchimp state.

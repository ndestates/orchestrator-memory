# ndestates-io Specializations

**Project-specific QA checklist items** for the ndestates-io wave project (Laravel real-estate software platform + marketing/customer portal).

## Domain Risks

- Licensing / trials / first-party checks: Lease model, is_first_party, trial semantics, server-side validation gate.
- Marketing site + portal: product pages, downloads (license gated), PayPal purchases/subscriptions.
- Customer data: account, property/listing data, e-sign integration points.
- Billing flows: PayPal invoices, receipts, refunds, subscription state.
- Identity / address (if using didit/loqate for signers).

## Safety & Compliance

- License validation endpoints and fail-open / fail-closed behavior.
- No leakage of licensing keys, PayPal creds, or user data in reports or client-side.
- Dry-run vs live for billing and external calls.
- Proper test data for licensing and customer flows.

## Testing & Verification

- `test-safety-agent` + targeted tests for licensing API, PayPal integration, portal downloads, user flows.
- Integration with orchestrator licensing CLI/MCP if in scope.
- Regression on gated content and subscription state transitions.

## Project Process

- Strong alignment with feature/licensing-validate-api branch work.
- Cache citation for licensing and billing changes.
- TODO updates for ndestates-io specific milestones.

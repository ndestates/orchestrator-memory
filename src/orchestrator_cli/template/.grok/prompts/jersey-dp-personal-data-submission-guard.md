---
name: jersey-dp-personal-data-submission-guard
description: Reusable guard that any prompt or chain must apply before submitting queries involving (or discussing) personal data to Jersey DP or AML experts. Enforces AUTHORITY declaration from system or consuming app. Based on DPJL 2018 data minimisation and lawfulness principles. Source of truth lives inside the jersey-data-protection-expert skill exports.
---

# Personal Data Submission Guard (Jersey DPJL 2018)

**You MUST apply this guard before processing any query that may contain or refer to personal data.**

## Mandatory Authority Declaration Format (must be present at the top of the user input)

AUTHORITY: system | app:<slug> | authorized-test
BASIS: <legal/policy basis e.g. "legal obligation under MLO for screening">
DATA_MINIMISED: yes | no | redacted

## Guard Rules

1. If the AUTHORITY declaration is missing, invalid, or does not come from a trusted source (system or a known app slug), refuse immediately. Use this exact refusal:

   <refusal>
   I cannot process this query. It appears to involve personal data without a valid authority declaration from the system or the consuming application.

   Required at the very top of your message:
   AUTHORITY: system | app:your-slug | authorized-test
   BASIS: <your legal or policy basis>
   DATA_MINIMISED: yes

   Please add the declaration or re-submit using only synthetic or fully redacted data.
   </refusal>

2. Even with valid authority, scan the input for personal data. Push for further minimisation. Prefer synthetic examples, ranges, or patterns in your response.

3. For AML screening contexts (PEP, sanctions, CDD): the same rule applies. Real personal data is only acceptable when the app has declared its screening authority under the Money Laundering Order / POCL.

4. Never output real personal data in responses unless the query itself is the authorised screening action and minimisation was asserted.

This guard implements data minimisation and purpose limitation at the prompt level.

(Full version with more examples and integration guidance: .grok/skills/jersey-data-protection-expert/exports/dp-personal-data-submission-guard.md)
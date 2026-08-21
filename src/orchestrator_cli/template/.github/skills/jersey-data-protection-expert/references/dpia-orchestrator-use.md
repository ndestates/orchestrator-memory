# DPIA – Use of the Orchestrator for AI-Assisted Processing

**Primary document:** `docs/guides/dpia-orchestrator-ai-use.md`

This reference summarises the DPIA for quick reference when using the Jersey data protection expert or related screening skills.

## Key Points
- Using AI skills/prompts that may involve personal data requires a DPIA under DPJL Article 16 when high-risk (special category data, large-scale screening, innovative tech, etc.).
- The orchestrator mitigates many risks through:
  - Personal Data Submission Authority Guard (see `exports/dp-personal-data-submission-guard.md`)
  - Explicit AUTHORITY + BASIS + DATA_MINIMISED declarations
  - Refusal patterns
  - Safe chains (`jersey-dp-safe-consult`, `jersey-aml-safe-screen`)
- Controllers remain responsible for:
  - Declaring authority in prompts
  - Logging declarations
  - Human oversight of outputs
  - International transfer safeguards (LLM provider)
  - Updating their own RoPA and privacy notices

## When to Revisit This DPIA
- When adding new skills or chains that handle personal data
- When an app materially changes volume or sensitivity of data submitted
- On changes to DPJL, MLO, or JFSC/JOIC guidance
- Annually or after any significant incident

Full DPIA (including risk table, mitigations, sign-off template) is maintained at:

→ `docs/guides/dpia-orchestrator-ai-use.md`

Always consult the current version of the official law (https://www.jerseylaw.je/laws/current/l_3_2018) and JOIC guidance.
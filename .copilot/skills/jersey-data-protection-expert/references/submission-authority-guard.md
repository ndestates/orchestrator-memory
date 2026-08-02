# Personal Data Submission Authority Guard (for Jersey DP Expert & Screening)

## Why This Exists
Under the Data Protection (Jersey) Law 2018, processing of personal data (including feeding it into AI prompts or screening systems) must be:
- Lawful
- Fair and transparent
- Limited to what is necessary (data minimisation)
- For a specified, explicit and legitimate purpose

When using LLM-based experts (jersey-data-protection-expert, jersey-aml-compliance-expert, or any screening logic), the act of including real personal data in the prompt context is "processing".

This guard provides a practical, prompt-level control so that:
- The system or consuming app must declare authority.
- The model is instructed to refuse otherwise.
- Real data is not casually submitted.

## Authority Model
Authority must come from one of:
- **system** — the orchestrator, official chains, or internal tooling.
- **app:<slug>** — the specific Jersey wave application (e.g. e-ndsign, ndestates-io, jerseyhouseprices) has its own legal basis and has implemented the guard.
- **authorized-test** — clearly synthetic data.

The declaration must appear **before** any potential personal data.

## Integration with Screening
AML/compliance screening (customer due diligence, PEP screening, sanctions, adverse media) necessarily involves personal data.

The guard does **not** prevent legitimate screening. It ensures:
- The app using the prompt has declared its authority (usually "legal obligation" under the Money Laundering Order / POCL).
- The data is minimised where possible for the advisory interaction.
- The expert refuses "casual" or unauthorized use of real names/DOBs/etc.

## Refusal Behavior
When the guard triggers refusal, the response must be clear, non-helpful on the underlying query, and point back to the required declaration format. This prevents accidental or malicious leakage.

## Chain Enforcement (Recommended)
See chains in `chains/registry.yaml`:
- `jersey-dp-safe-consult`
- `jersey-aml-safe-screen`

These chains load cache, apply the guard prompt, validate authority, then invoke the expert only on clean inputs.

Apps that directly call the experts should copy the guard template into their own prompt construction.

## Relationship to DP Principles
- Data minimisation → force redaction or synthetic data
- Purpose limitation → BASIS field
- Accountability → explicit declaration that can be logged
- Lawfulness → only process when authority + basis declared

## Maintenance
Keep this reference and the exported prompt templates in sync with the main SKILL.md and official law text.

When deploying via orchestrator-deploy, these templates travel with the skill so consuming apps inherit the control.

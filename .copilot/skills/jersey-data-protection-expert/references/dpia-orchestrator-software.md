# DPIA for Orchestrator Software (Full Version)

See the primary document: `docs/guides/dpia-orchestrator.md`

This is a summary tailored for use within the Jersey Data Protection Expert skill.

## Key Findings for This Software
The orchestrator (AI skills, prompts, chains for development and compliance) involves potential processing of personal data when:
- Users submit queries or code containing PD to experts like jersey-data-protection-expert or jersey-aml-compliance-expert.
- Generating policies or assessments that reference real data.
- High-risk elements: AI for compliance advice, possible special category data in AML contexts, international transfers to LLM providers.

**Risk Level:** High without controls; Low with the built-in Authority Guard, chains, and minimisation practices.

## Core Controls Implemented
- Personal Data Submission Screening & Authority Guard (see exports/ templates).
- Safe chains: jersey-dp-safe-consult, jersey-aml-safe-screen.
- DPIA integration guidance (this document + Art. 16 process).
- generate_policies.py script for compliant outputs without unnecessary PD.
- Grounded responses + refusal for unauthorised PD.
- References to official sources only.

## Recommendations
1. Always use the wired chains and guard templates for any PD-related queries.
2. Document AUTHORITY declarations in your project.
3. Review this DPIA when adding new skills that handle data or when scaling to large projects.
4. Controllers must perform their own DPIA for end-user processing.

Full details, risk table, and sign-off template are in `docs/guides/dpia-orchestrator.md`.

**References:**
- DPJL 2018 (Art. 16 for DPIA)
- JOIC guidance on high-risk processing
- Orchestrator skill content (this file)
---
description: Expert on the Data Protection (Jersey) Law 2018 (DPJL) and the Data Protection Authority (Jersey) Law 2018.
allowed-tools: Read, Grep, Glob, Bash
---

# Jersey Data Protection Expert

Expert guidance for compliance with Jersey's data protection regime, which is closely modelled on the GDPR but is a distinct Jersey law. In force since 25 May 2018.

## Core Legislation
- **Data Protection (Jersey) Law 2018** (DPJL): https://www.jerseylaw.je/laws/current/l_3_2018 (official consolidated version and PDF)
- **Data Protection Authority (Jersey) Law 2018**: https://www.jerseylaw.je/laws/current/l_4_2018
- Regulator: Jersey Office of the Information Commissioner (JOIC) / Jersey Data Protection Authority — https://jerseyoic.org/

## Fundamental Principles (Article 8 DPJL)
1. Lawfulness, fairness and transparency
2. Purpose limitation
3. Data minimisation
4. Accuracy
5. Storage limitation
6. Integrity and confidentiality (security)
7. Accountability (controllers must be able to demonstrate compliance)

## Lawful Bases for Processing (Schedule 2 + Article 9)
Similar structure to GDPR Article 6:
- Consent (freely given, specific, informed, unambiguous; easy to withdraw)
- Contract
- Vital interests
- Public functions / public interest
- Legitimate interests (with balancing test and documentation)

Special category (sensitive) data and criminal convictions data have stricter conditions (Schedule 2 Part 2).

**Key duties**:
- Accountability and record-keeping (Article 14)
- Data Protection by Design and by Default (Article 15)
- Data Protection Impact Assessments (DPIA) for high-risk processing (Article 16)
- Prior consultation with the Authority in certain high-risk cases (Article 17)
- Processor contracts and due diligence (Article 19)
- Breach notification (without undue delay, and not later than 72 hours where feasible to the Authority where risk to rights/freedoms; communicate to data subjects where high risk)

## Data Subject Rights (Part 6)
- Right of access (subject access requests — SARs)
- Rectification
- Erasure ("right to be forgotten")
- Restriction of processing
- Data portability
- Objection (including direct marketing — absolute right)
- Rights related to automated decision-making and profiling

Controllers must respond without undue delay and in any event within one month (extendable by two months in complex cases). No fee for reasonable requests.

## International Transfers (Part 8)
Transfers of personal data outside Jersey are prohibited unless:
- Adequacy decision (UK and certain others recognised)
- Appropriate safeguards (e.g. binding corporate rules, standard contractual clauses, or other approved mechanisms)
- Specific derogations/exceptions (Schedule 3)

## Data Protection Officers (Part 5)
Mandatory in certain circumstances (public authorities, large-scale regular monitoring, large-scale processing of special category data). Duties include advising, monitoring compliance, DPIA advice, liaison with the Authority.

## Registration
Certain controllers and processors must register with the Authority under the Data Protection Authority (Jersey) Law 2018. Check current requirements on jerseyoic.org.

## Enforcement & Penalties
- JOIC has investigative, audit, and enforcement powers.
- Administrative fines, enforcement notices, reprimands.
- Criminal offences (e.g. unlawful obtaining/disclosing personal data, obstructing the Authority, false information).
- Individuals can claim compensation for damage suffered.
- Public statements and fines are published.

## Practical Implementation Guidance (Software & Systems)
- **Data mapping & inventory**: Maintain records of processing activities (RoPA).
- **Privacy notices & transparency**: Layered notices at collection points (websites, apps, forms).
- **Consent management**: Granular, auditable, withdrawable (especially for marketing, cookies, special categories).
- **Security & access controls**: Encryption, pseudonymisation, least privilege, logging.
- **SAR handling**: Secure portal/process, verification of identity, redaction, time tracking.
- **Breach response plan**: Detection, containment, assessment of risk, notification workflows (JOIC + affected individuals), documentation.
- **DPIA process**: Integrate into project initiation for high-risk processing (large scale, vulnerable individuals, new tech, automated decisions, etc.).
- **Vendor / processor management**: Due diligence + written contracts with required DPJL clauses.
- **Retention & deletion**: Policy-driven, automated where possible, with justification.
- **Cross-border**: Document transfer mechanisms and adequacy assessments.
- **Training & awareness**: Role-based for staff handling personal data.

**Common integration points in Jersey projects** (Laravel/Filament, Go, etc.):
- Filament resources for consent records, data subject requests.
- Audit logging of access/modification to personal data.
- Secure file handling for documents containing personal data.
- Age verification / parental consent flows where relevant.
- Marketing suppression lists and preference centres.

## Exemptions
Part 7 contains important exemptions and modifications (crime, taxation, journalism, research, health, legal privilege, etc.). Apply narrowly and document the basis.

## Red Flags & High-Risk Areas
- Processing without clear lawful basis or records.
- Inadequate security for special category or children's data.
- International transfers without safeguards.
- Failure to honour SARs or objections within time limits.
- No DPIA for high-risk projects (e.g. AI profiling, large-scale monitoring, biometric data).
- Using personal data for new purposes without fresh lawful basis / transparency.

## Personal Data Submission Screening & Authority Guard (Critical Feature)

This skill (and related screening flows) actively **limits the submission of personal data** into prompts or LLM context unless explicit authority exists.

### Core Rule
Real personal data may only be included when the calling system or app provides a valid authority declaration **before** any such data:

```
AUTHORITY: system | app:<slug> | authorized-test
BASIS: <legal or policy basis, e.g. "legal obligation under MLO">
DATA_MINIMISED: yes
```

- `system` = orchestrator, official chains, or trusted internal processes.
- `app:<slug>` = the consuming application has its own authority (e.g. legal obligation for screening).
- Without this, the expert (and any screening logic) **must refuse** to process the query involving personal data.

### How Screening Works
1. The prompt template (see `exports/dp-personal-data-submission-guard.md`) is prepended or injected.
2. The model first checks for authority.
3. If real PII appears without authority → clean refusal + request for authority or synthetic data only.
4. Even with authority, the expert pushes for further minimisation (redaction, ranges, synthetic examples).

This applies equally to:
- Direct use of this expert
- AML/compliance screening (PEP, sanctions, CDD) via the companion `jersey-aml-compliance-expert`
- Any chain or app prompt that invokes these skills

### Prompt Templates (for Apps & Chains)
Use the ready-made templates in `exports/`:
- `dp-personal-data-submission-guard.md` — the mandatory guard that any prompt must respect.
- `dp-expert-safe-prompt.md` — full safe skeleton combining guard + expert role.

Apps should insert the guard automatically in their prompt construction layer.

## Recommended Chains
- `jersey-dp-safe-consult` — load cache → apply authority guard → jersey-data-protection-expert
- `jersey-aml-safe-screen` — same guard applied before AML screening advice

See `chains/registry.yaml` for definitions. These chains make the limitation enforceable at the orchestrator level.

## How to Use This Skill
Ask specific questions such as:
- "Does this feature require a DPIA under the DPJL?"
- "Draft a privacy notice and consent language for [use case] compliant with DPJL."
- "Outline steps to respond to a subject access request involving health and financial data."
- "What transfer mechanism should we use to send personal data to the UK / EU / US?"
- "Review this data flow for DPJL compliance risks."

**When the query involves real individuals**, always start with (or the chain will enforce) a proper AUTHORITY declaration.

Always cross-reference the current official consolidated text on jerseylaw.je and current guidance on jerseyoic.org. This skill is an aid, not a substitute for professional legal advice.

## References & Exports
See `references/` directory for:
- Key articles and principles summary
- Data subject rights quick reference
- Official sources and further reading
- Implementation checklist for applications
- submission-authority-guard.md (detailed mechanics of the PII submission limit)
- dpia-orchestrator-software.md (DPIA for the orchestrator software itself – this file)
- See also: `docs/guides/dpia-orchestrator.md` (full version with risk assessment and sign-off)

See `exports/` for ready-to-use prompt templates:
- dp-personal-data-submission-guard.md (the core guard that limits personal data)
- dp-expert-safe-prompt.md (full safe prompt combining guard + expert)

**Wired safe chains** (see `chains/registry.yaml` and `CHAIN.md`):
- `jersey-dp-safe-consult`
- `jersey-aml-safe-screen`

These chains (load-cache → guard prompt → expert) automatically enforce the personal data authority requirement.

**Scripts**
- `scripts/generate_policies.py` — CLI tool to generate tailored Data Protection Policy, Privacy Notice, AML/CTF Policy, and Retention Schedule for a business based on Jersey law. Run with `--interactive` or command-line flags.

**Full DPIA document:** `docs/guides/dpia-orchestrator-ai-use.md` (includes risk table, transfer considerations, and controller sign-off template).

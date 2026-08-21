# Data Protection Impact Assessment (DPIA)

[UPDATED 2026-07-07] — minor refresh aligned with full docs site update.

**Title:** DPIA for Use of the Orchestrator AI Skills, Prompts, Agents, and Chains (including Jersey Data Protection Expert and AML/Compliance Screening)

**Project / System:** Orchestrator (template for multi-AI skills, prompts, agents, and chains supporting various AI agents and models (Grok, Claude, Copilot, Gemini, and others) via the project root structure structure: .grok/, .claude/, .github/, .gemini/, multi-AI best practices, and cross-platform syncs as documented in `docs/codebase/README.md`)  
**Version:** 1.0  
**Date:** 2026-07-04  
**Prepared with reference to:** Data Protection (Jersey) Law 2018 (DPJL) and Data Protection Authority (Jersey) Law 2018  
**Regulator:** Jersey Office of the Information Commissioner (JOIC) – https://jerseyoic.org/

**Status:** Draft for review and adoption by controller organisations using the orchestrator in Jersey projects (application repositories using this template).

See guides/knowledge-vault.md for the secure self-building vault used for persistent context in AI workflows.

---

## 1. Introduction and Scope

This DPIA assesses the privacy and data protection risks associated with using the orchestrator's AI capabilities (skills, prompt templates, agents, and chains) to support compliance, advisory, and screening activities.

Particular focus is given to:
- The newly introduced `jersey-data-protection-expert` skill.
- The `jersey-aml-compliance-expert` skill (covering Proceeds of Crime (Jersey) Law 1999 and Money Laundering (Jersey) Order 2008).
- The built-in **Personal Data Submission Authority Guard**, prompt templates, and chains that limit submission of personal data.

The orchestrator itself is a development and runtime toolkit. Real personal data processing occurs when consuming applications invoke these skills/chains (e.g., for DPIA support, AML screening advice, or compliance review).

**Scope includes:**
- AI prompt construction and submission to the underlying AI model providers (various, including Grok/xAI, Anthropic/Claude, OpenAI/Copilot, Google/Gemini, and others supported via the orchestrator's multi-platform setup in the project root: `.grok/`, `.claude/`, `.github/`, `.gemini/`, etc.).
- Use of official chains such as `jersey-dp-safe-consult` and `jersey-aml-safe-screen`.
- Prompt templates in `exports/` that enforce authority declarations.
- Any app-level integration that passes context containing (or about) personal data.

The orchestrator provides unified AI skills, prompts, agents, and chains that work across these platforms (synced via `scripts/sync_grok_to_github_claude.py` and supporting multi-AI best practices as documented in `docs/codebase/README.md`).

**Out of scope:**
- Purely synthetic or non-personal data queries.
- Processing performed entirely within an app's own backend without invoking orchestrator skills.
- Downstream decisions taken by the controller based on AI advice (separate DPIA may be needed).

A DPIA is required under DPJL Article 16 where processing is likely to result in high risk to the rights and freedoms of natural persons (large-scale processing, special category data, monitoring, automated decision-making with significant effects, etc.).

---

## 2. Description of the Processing

### Nature of the processing
- AI-assisted analysis and advisory using structured prompts and expert skills.
- The LLM receives context (which may include personal data if authority is declared) and returns reasoned advice grounded in Jersey law and guidance.
- Screening-related processing (CDD patterns, PEP indicators, sanctions logic) is supported via the AML expert.
- No direct access by the orchestrator to live databases or production personal data stores — data is only present when explicitly supplied in authorised prompts.

### Scope
- Limited to queries from authorised systems or apps that have declared authority.
- Data volume depends on the consuming app (e.g., occasional compliance queries vs. high-volume screening support).

### Context
- Used in regulated Jersey financial services, e-sign, property, and related applications.
- Controllers are subject to both DPJL and AML/CFT obligations (MLO, POCL).
- AI is used as a tool to improve quality and speed of compliance work, not to replace human accountability.

### Purposes
- Supporting controllers in meeting legal obligations (AML screening, record-keeping, DPIA processes).
- Providing consistent, up-to-date advice aligned with official sources (jerseylaw.je, JFSC Handbook, JOIC guidance).
- Enforcing data minimisation at the point of AI interaction.

---

## 3. Lawful Basis and Data Protection Principles

**Primary bases for the underlying processing (in consuming apps):**
- Legal obligation (Art. 9(2)(c) and Schedule 2) — especially for AML/CFT screening and related record-keeping.
- Legitimate interests (with balancing test documented).
- Consent (rarely for core screening).

**For the AI prompt processing itself:**
- The authority guard + templates ensure processing only occurs where the controller has already identified a lawful basis and declared it.
- Data minimisation is built into the guard (refusal if not asserted; preference for synthetic/redacted data).

**Assessment against DPJL principles (Article 8):**
- **Lawfulness, fairness, transparency** — Guard forces explicit declaration; advice references official sources.
- **Purpose limitation** — Prompts and chains are scoped to the declared BASIS.
- **Data minimisation** — Core feature of the submission guard and templates.
- **Accuracy** — Grounded response pattern + refusal when evidence is insufficient.
- **Storage limitation** — Prompts are session-scoped; no persistent storage of real PD by the skill itself.
- **Integrity and confidentiality** — Relies on the underlying platform security + app-level controls.
- **Accountability** — Declarations can be logged by the app; DPIA itself demonstrates accountability.

---

## 4. Categories of Personal Data and Data Subjects

**Data subjects:**
- Customers, signers, beneficial owners, directors, trustees, applicants (primarily Jersey or UK-linked individuals, but potentially international).

**Categories of personal data (examples that may appear in authorised prompts):**
- Identity data (name, DOB, nationality, passport/ID numbers).
- Contact data (address, email, phone).
- Financial/wealth data (source of funds/wealth, transaction patterns).
- PEP/sanctions/adverse media flags and supporting details.
- Special category data (criminal convictions, health data in limited contexts for AML or e-sign).
- Unique identifiers used for screening.

**Special category / criminal data:** Yes — AML screening routinely involves this. Higher risk, stricter conditions required.

---

## 5. Data Flows, Recipients and Retention

**Data flow (high level):**
1. App or chain prepares prompt (with authority declaration + minimised data).
2. Guard template evaluates authority.
3. If authorised → prompt (including any PD) sent to LLM provider.
4. Expert skill returns advice.
5. Response used by human controller; no automated decisions.

**Recipients:**
- The controller's own systems and staff.
- LLM provider (Grok/xAI, Anthropic/Claude, OpenAI/Copilot, Google/Gemini, and others) for the duration of the prompt processing.
- Potentially audit / compliance logs within the app.

**International transfers:**
- LLM processing occurs with the model provider (typically US-based).
- Jersey has UK adequacy. UK has mechanisms for US transfers.
- Controllers must ensure appropriate safeguards (e.g., standard contractual clauses + supplementary measures, or rely on any future adequacy decisions).
- The authority guard and minimisation reduce the volume and sensitivity of data transferred.

**Retention:**
- Session / query level only for the AI interaction.
- App-level retention follows the controller's policies (aligned with MLO 5+ year requirements for AML records).
- The orchestrator skills and templates do not retain personal data.

---

## 6. Necessity and Proportionality

**Necessity:**
- Use of AI experts significantly improves consistency, speed, and quality of compliance advice and screening support.
- Alternative (manual research only) is slower and more prone to inconsistency.
- Guards and templates make the AI route more privacy-protective than ad-hoc use of general LLMs.

**Proportionality:**
- Risks are mitigated at the prompt layer before any data reaches the model.
- Only authorised, minimised data is processed.
- Benefit (better compliance outcomes for data subjects and controllers) outweighs residual risk when controls are followed.

---

## 7. Risk Assessment and Mitigation

| Risk | Likelihood | Impact | Risk Level (pre-mitigation) | Mitigation Measures (implemented) | Residual Risk |
|------|------------|--------|-----------------------------|-----------------------------------|---------------|
| Unauthorised submission of real PD into prompts | Medium | High | High | Mandatory AUTHORITY declaration + guard template + refusal pattern in all recommended chains and exports | Low |
| LLM provider receives more PD than necessary | High | High | High | DATA_MINIMISED flag, synthetic data preference, redaction encouragement in templates | Low |
| Inaccurate legal advice leading to controller non-compliance | Medium | High | High | Grounded RAG + refusal when unsupported; references to official sources (jerseylaw.je, JFSC Handbook); human oversight required | Medium (human accountability) |
| Special category / criminal data processed without proper basis | Medium | Very High | Very High | Guard requires explicit legal obligation basis for screening; higher scrutiny in AML template | Low |
| International transfer of PD to LLM provider without safeguards | High | High | High | Volume minimised; controllers must document SCCs/supplementary measures; guard reduces volume transferred | Medium (depends on controller's transfer arrangements) |
| Lack of transparency to data subjects | Medium | Medium | Medium | Advice must reference sources; controllers update privacy notices for AI-assisted processing | Low |
| Model "hallucination" on Jersey-specific rules | Medium | High | High | Strict grounding requirement + official source references in skill | Low |

**High-risk processing indicators addressed:**
- Special category data (AML context).
- Systematic monitoring / large-scale processing (via app usage).
- Innovative technology (LLM use for compliance).

---

## 8. Technical and Organisational Measures

**Built into the orchestrator (these skills):**
- Personal Data Submission Authority Guard (exports/ templates).
- Explicit refusal pattern when authority is missing.
- Recommended safe chains (`jersey-dp-safe-consult`, `jersey-aml-safe-screen`).
- Grounded response + evidence extraction (from prompt-patterns).
- Preference for synthetic / minimised examples in all guidance.
- References to primary law and official guidance only.
- Separation of advisory role (skills do not make binding decisions).

**Expected controller / app measures:**
- Implement the guard in all prompt construction that touches these experts.
- Log authority declarations for auditability.
- Human review of AI outputs before acting on compliance matters.
- Maintain RoPA (records of processing activities) covering AI-assisted steps.
- Update privacy notices and DPIAs for affected processing.
- Ensure appropriate safeguards for transfers to the LLM provider.
- Regular review of prompt templates and chain usage.
- Staff training on when real vs. synthetic data may be used.

---

## 9. Consultation

- Internal: Development of the guard, templates, and chains drew on the jersey-data-protection-expert and prompt-patterns skills.
- External: Controllers using the orchestrator should consult their Data Protection Officer (where appointed), compliance team, and (where appropriate) the JOIC or external counsel.
- Data subjects: Transparency via privacy notices; subject access rights remain available.

---

## 10. Conclusions, Recommendations and Review

**Conclusion:** With the authority guard, prompt templates, and safe chains in place, the residual risk of using the orchestrator's AI skills for data-protection and AML/compliance work is **low**, provided controllers:
- Always declare authority when real personal data is involved.
- Prefer minimised or synthetic data.
- Maintain human oversight.
- Address international transfers separately.

**Recommendations:**
1. Adopt the `jersey-dp-safe-consult` and `jersey-aml-safe-screen` chains as the standard route for these experts.
2. Include the guard templates in any custom prompt construction.
3. Document authority declarations in audit logs.
4. Review this DPIA whenever the orchestrator skills are updated or when an app materially changes how it invokes them.
5. Controllers should integrate this DPIA (or an adapted version) into their own overall DPIA register.

**Next review date:** 2026-10-04 (or earlier if significant changes to skills, law, or LLM provider practices).

**Sign-off (to be completed by controller):**
- Data Protection Officer / Responsible Person: ___________________________ Date: ________
- Compliance / MLRO (for AML aspects): ___________________________ Date: ________
- Senior Management: ___________________________ Date: ________

---

## 11. Related Documents and Templates

- `jersey-data-protection-expert` skill (especially `exports/` and `references/submission-authority-guard.md`)
- `jersey-aml-compliance-expert` skill
- Prompt templates: `dp-personal-data-submission-guard.md`, `aml-screening-personal-data-guard.md`
- Chains: `jersey-dp-safe-consult`, `jersey-aml-safe-screen` (chains/registry.yaml)
- Official sources: https://www.jerseylaw.je/laws/current/l_3_2018 and https://jerseyoic.org/
- JOIC guidance on DPIAs and high-risk processing
- JFSC AML/CFT/CPF Handbook

---

**This DPIA is provided as a practical starting point for controllers using the orchestrator. It is not formal legal advice. Adapt it to the specific processing activities, data flows, and risk appetite of your organisation and seek appropriate professional advice.**
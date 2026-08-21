# Data Protection Impact Assessment (DPIA) for Orchestrator Software

[UPDATED 2026-07-07] — minor refresh for full site update; cross-references to knowledge vault and multi-AI guides.

## Overview
This DPIA assesses the privacy and data protection risks associated with using the orchestrator software — the reusable template for multi-AI skills, prompts, agents, chains, and related tooling supporting various AI agents and models (Grok, Claude, Copilot, Gemini, and others) via the project root structure (.grok/, .claude/, .github/, .gemini/, multi-AI best practices, and cross-platform syncs) — in Jersey-regulated projects.

**Primary lens:** Compliance (for controllers, DPOs, and developers using the orchestrator in apps handling personal data).

The orchestrator itself does not store personal data persistently. Risks arise mainly from AI interactions (prompts and responses) that may involve or advise on personal data, especially via the `jersey-data-protection-expert` and `jersey-aml-compliance-expert` skills, policy generators, and code reviews. High-risk indicators include use of AI (new tech), potential special category or criminal data in AML contexts, and international transfers to LLM providers (Grok/xAI, Anthropic/Claude, OpenAI/Copilot, Google/Gemini, and others). The unified skills/prompts/agents are synced across frontends via `scripts/sync_grok_to_github_claude.py` and support multi-AI best practices as documented in `docs/codebase/README.md` (Multi-AI support section).

This document follows the requirements of Article 16 of the Data Protection (Jersey) Law 2018 for high-risk processing. It is a template; each controller must adapt and maintain their own DPIA.

See also the secure knowledge vault guide (guides/knowledge-vault.md) for how persistent context (including potential personal data in prompts) is managed.

## Before you begin
- Read the [jersey-data-protection-expert skill](../../.grok/skills/jersey-data-protection-expert/SKILL.md) for DPJL 2018 details, DPIA triggers, the Personal Data Submission Screening & Authority Guard, and recommended chains.
- Review the project manifest (`.grok/project-manifest.yaml` or `.claude/project-manifest.yaml`) for stack and token policy.
- Load relevant cache with `/load-project-cache-first` or `/chain session-start`.
- Understand high-risk processing under DPJL Article 16 (large-scale, special category data, new technologies like AI, monitoring, automated decisions with legal effects).
- Confirm if your use involves real personal data in prompts (if not, DPIA may not be required, but best practice to document).

## Steps

### 1. Description of the processing
The orchestrator provides:
- Skills (e.g. `jersey-data-protection-expert`, `jersey-aml-compliance-expert`)
- Prompt templates and chains (e.g. `jersey-dp-safe-consult`, `jersey-aml-safe-screen`)
- Scripts (e.g. `generate_policies.py`)
- Agents for codebase knowledge, security, etc.

**Processing activities that may involve personal data:**
- Submitting prompts or context containing or referencing personal data to AI experts for compliance advice or screening guidance.
- Generating policies, notices, or DPIA drafts.
- Reviewing code, schemas, or integrations that handle personal data.
- Using chains that combine skills.

**Purposes:** Legal compliance (DPJL, POCL/MLO), legitimate interests (improving development and compliance processes), contractual (in client apps).

**Data subjects:** Clients, users, employees in Jersey or Jersey-impacted apps (e.g. e-sign, property, financial services).

**Categories of personal data:** Identity, contact, financial, special category (health, criminal in AML), technical logs.

**Recipients:** AI model providers (international transfers), human reviewers, no third-party sharing beyond declared.

The orchestrator uses built-in controls: the Authority Guard requires explicit `AUTHORITY: system | app:<slug>` declaration before processing personal data; otherwise refuses. No persistent storage of PD; processing is transient.

### 2. Assessment of necessity and proportionality
**Necessity:** AI assistance enables consistent, efficient compliance support for complex Jersey laws. Manual methods are slower and error-prone. The guard ensures only minimal, authorised data is used.

**Proportionality:** Benefits (better compliance outcomes, reusable templates, reduced human error) outweigh risks when controls are applied. Processing is limited to advisory outputs. Special category data is handled only under strict legal obligations (e.g. AML). Risks are mitigated at input (guard + chains).

### 3. Risks to rights and freedoms + measures
High-risk indicators: AI/new tech, potential special category data, international transfers, systematic processing in client apps.

**Risks and mitigations (per DPJL principles):**

- Unauthorised/excessive PD in prompts: Medium likelihood, high impact. **Mitigation:** Mandatory Authority Guard (refusal if missing), preference for synthetic data, chains that enforce guard first. `generate_policies.py` produces templates without real data.
- Inaccurate advice leading to non-compliance: Low likelihood, high impact. **Mitigation:** Grounded in official sources (jerseylaw.je, JOIC, JFSC Handbook), refusal when unsupported, human oversight required.
- International transfers to LLM providers: High likelihood, high impact. **Mitigation:** Guard minimises volume sent; controllers must apply SCCs or other safeguards; reference official law only.
- Breach of data subject rights (access, erasure): Low. **Mitigation:** Advice on rights in skill; no retention by orchestrator; transparency via generated privacy notices.
- Security/confidentiality (prompt leakage): Medium. **Mitigation:** Least-privilege tools in skills, audit logging guidance, refusal on unauthorised data.
- Lack of accountability: Low. **Mitigation:** Authority declarations create audit trail; this DPIA + skill references demonstrate compliance; update RoPA and TODO.

See full risk table and more details in the skill's `references/dpia-orchestrator-software.md` and the extended version in this guide's related links.

### 4. Measures (safeguards)
- **Data Protection by Design/Default (Art. 15):** Guard is default in recommended chains and templates.
- **DPIA process (Art. 16):** Integrate into project initiation for high-risk features (AI profiling, large-scale monitoring, biometric, new purposes). Revisit on skill updates or law changes.
- **Authority Guard + templates:** See `exports/dp-personal-data-submission-guard.md` and `dp-expert-safe-prompt.md`. Must be used before any PD.
- **Safe chains:** `jersey-dp-safe-consult` and `jersey-aml-safe-screen` (load cache → guard → expert).
- **Minimisation:** Synthetic/redacted data preferred; script generates policies without PD.
- **No storage/retention:** Transient only.
- **Vendor controls:** Guidance on processor contracts.
- **Records:** RoPA guidance, authority logs, this DPIA as evidence.
- **Prior consultation (Art. 17):** For very high risk, consult JOIC.

### 5. Conclusions
With the implemented controls (especially the guard, chains, and minimisation), residual risk is low for authorised uses. However, controllers remain responsible for their own DPIA, transfer safeguards, and human oversight.

## Verify
- The document references current DPJL 2018 Article 16 and the orchestrator's guard/chains.
- Check against JOIC guidance and official law at jerseylaw.je.
- Confirm in your project: authority declarations are logged, chains are used for PD-related tasks, and this DPIA is adapted for your specific processing.
- Run `python3 scripts/sync_grok_to_github_claude.py` after edits.
- Update `TODO` and this file's `[UPDATED]` date on changes.

## Next steps
- Review this DPIA annually or when adding high-risk skills.
- Use `/jersey-data-protection-expert` for updates or specific risks.
- Integrate into your project's DPIA register and privacy notices (use `scripts/generate_policies.py` for templates).
- For full docs site, see `docs/guides/documentation.md`.
- Related: `docs/guides/dpia-orchestrator-ai-use.md` (extended version), `.grok/skills/jersey-data-protection-expert/references/dpia-orchestrator-software.md`, the expert skill itself.

**This is a template for controllers. Adapt to your specific use and seek legal advice as needed. It demonstrates the orchestrator's built-in safeguards for high-risk AI processing.**

## 1. Description of the Processing

### 1.1 Nature of Processing
The orchestrator is a reusable template providing:
- Skills (e.g., `jersey-data-protection-expert`, `jersey-aml-compliance-expert`)
- Prompt templates and chains
- Agents for tasks like codebase acquisition, security audits, etc.
- Chains for multi-step workflows (e.g., `jersey-dp-safe-consult`, `jersey-aml-safe-screen`)

When used via the orchestrator's supported AI frontends and models in the project root (Grok, Claude, Copilot, Gemini, and others), users interact with AI models. Prompts and context may include or reference personal data, especially when:
- Using DP/AML experts for compliance advice.
- Reviewing code, schemas, or integrations that handle user data.
- Generating policies, notices, or assessments.

Core mechanism to control this: **Personal Data Submission Screening & Authority Guard** (enforced via prompt templates and chains). Real personal data is only processed if an explicit `AUTHORITY` declaration is provided (e.g., `system`, `app:<slug>`).

The orchestrator does **not** store personal data persistently. Processing is transient (prompt → model response). No direct database access for live personal data in core skills.

### 1.2 Scope and Context
- **Data subjects**: End users, clients, employees, beneficial owners in Jersey-based or Jersey-impacted applications (e.g., e-sign users, property clients, financial services customers).
- **Categories of personal data**:
  - Identity and contact data (names, addresses, emails, phone).
  - Special category data (where relevant to AML/compliance: health, criminal convictions, biometric in limited contexts).
  - Financial/transaction data (for AML screening).
  - Technical logs (if code reviews include PD).
- **Processing activities**:
  - AI analysis and advice on data protection/AML compliance.
  - Policy and document generation (via scripts like `generate_policies.py`).
  - Code/schema/integration reviews that may touch data-handling code.
  - DPIA support and risk assessment drafting.
- **Purposes**:
  - Legal compliance (AML/CFT under POCL/MLO, DPJL obligations).
  - Legitimate interests (improving software development, security, and compliance processes).
  - Contractual (service delivery in client apps).
- **Recipients**: 
  - The underlying AI model providers (various, including Grok/xAI, Anthropic/Claude, OpenAI/Copilot, Google/Gemini, and others supported via the orchestrator's multi-platform setup in the project root: `.grok/`, `.claude/`, `.github/`, `.gemini/`, etc.) – international transfers apply depending on the AI frontend used.
  - Human developers/compliance officers reviewing outputs.
  - No sharing with third parties beyond declared processors.

### 1.3 International Transfers
Prompts sent to LLM providers (e.g., depending on the AI platform: US-based for Grok/xAI or others) constitute transfers of personal data outside Jersey. 
- Relies on UK adequacy (Jersey recognises UK adequacy) + appropriate safeguards where needed (e.g., SCCs, BCRs, or derogations), as documented in the multi-AI support section of `docs/codebase/README.md`.
- Minimised by the Authority Guard: only authorised, necessary data is submitted.
- Controllers must document transfer mechanisms in their own records.

### 1.4 Retention and Storage
- No long-term storage of personal data by the orchestrator itself.
- Session-based: prompts and responses exist only for the duration of the AI interaction.
- Any generated files (e.g., policies, DPIA drafts) are stored in the user's project repo per their retention policy.
- Logs (if any) are minimised and subject to the same guard.

## 2. Assessment of Necessity and Proportionality

### 2.1 Necessity
- The orchestrator enables efficient, consistent compliance support in regulated Jersey environments.
- Manual methods are slower and more error-prone for complex areas like DPJL principles, DPIAs, AML screening, and policy drafting.
- AI assistance is necessary for scaling compliance in software development without increasing human error.
- The built-in guard ensures only minimal data is used when required.

### 2.2 Proportionality
- Benefits (faster compliance, better risk identification, reusable templates) outweigh risks when controls are followed.
- Risks are mitigated at the point of data submission (refusal if no authority; preference for synthetic data).
- Processing is limited to advisory outputs – no automated decisions with legal effects on data subjects.
- Special category data is only handled under strict conditions (e.g., legal obligation for AML).

## 3. Risks to the Rights and Freedoms of Data Subjects

High-risk indicators present (per DPJL Art. 16 and Schedule):
- Use of new technologies (AI/LLM for compliance).
- Large-scale or systematic processing (if used across multiple client records).
- Special category/criminal data (in AML contexts).
- Potential for international transfers.
- AI profiling/monitoring risks if prompts contain behavioural data.

**Identified Risks and Mitigations**:

1. **Unauthorised or excessive submission of personal data into AI prompts**
   - Likelihood: Medium (user error or misunderstanding).
   - Impact: High (breach of minimisation, potential unlawful processing).
   - **Mitigation**: Mandatory AUTHORITY declaration + guard prompt (refuses without it). Chains enforce this. Preference for synthetic/redacted data. Script `generate_policies.py` produces templates without real data.
   - Residual: Low.

2. **International transfer to LLM provider without safeguards**
   - Likelihood: High (inherent to AI use).
   - Impact: High (loss of control, potential unauthorised access).
   - **Mitigation**: Guard minimises volume. Controllers must apply SCCs/BCRs or rely on adequacy. No persistent storage by orchestrator. Reference official sources in outputs.
   - Residual: Medium (depends on controller's transfer assessment).

3. **Inaccurate or incomplete compliance advice leading to controller non-compliance**
   - Likelihood: Low (grounded in official sources + refusal when unsupported).
   - Impact: High (fines, reputational damage, harm to data subjects).
   - **Mitigation**: All advice cross-references jerseylaw.je, JOIC, JFSC Handbook. Grounded RAG pattern. Human oversight required. DPIA process integrated into project initiation.
   - Residual: Low.

4. **Breach of data subject rights (e.g., access, erasure) due to AI processing**
   - Likelihood: Low.
   - Impact: Medium.
   - **Mitigation**: Outputs advise on rights. SAR handling guidance in skill. No retention by orchestrator. Transparency via privacy notices (templates generated by script).
   - Residual: Low.

5. **Security/confidentiality risks (e.g., prompt injection, data leakage in logs)**
   - Likelihood: Medium.
   - Impact: High.
   - **Mitigation**: Least-privilege allowed-tools in skills. Security & access controls guidance. Audit logging of access. Chain refusal on unauthorised data.
   - Residual: Low.

6. **Lack of accountability / records of processing**
   - Likelihood: Low.
   - Impact: Medium.
   - **Mitigation**: RoPA guidance. Authority declarations create audit trail. DPIA template and implementation checklist provided. Update TODO/CHANGELOG on changes.

## 4. Measures to Address Risks (Safeguards)

- **Data Protection by Design and by Default** (Art. 15 DPJL): Guard is built into every recommended use of DP/AML skills. Chains and templates default to refusal/minimisation.
- **DPIA Integration**: This assessment + `docs/guides/dpia-orchestrator-ai-use.md` (full version) and skill reference. Must be revisited for high-risk projects (AI profiling, large-scale monitoring, biometric, new purposes).
- **Authority Guard + Prompt Templates**: See `exports/dp-personal-data-submission-guard.md` and `dp-expert-safe-prompt.md`. Must be prepended or enforced via chain.
- **Safe Chains**: `jersey-dp-safe-consult` and `jersey-aml-safe-screen` – load cache first, apply guard, then expert.
- **Minimisation and Synthetic Data**: Explicit instruction to use ranges, examples, or synthetic profiles unless authority declared.
- **Vendor/Processor Controls**: Guidance on contracts with LLM providers and other processors. Due diligence recommended.
- **Records and Transparency**: Maintain RoPA. Generate privacy notices and policies via `scripts/generate_policies.py`. Reference official legislation.
- **Breach Response**: Guidance on notification (72 hours to JOIC where risk). Containment via refusal/minimisation.
- **Training/Awareness**: Role-based guidance in skill. Staff must understand when authority is required.
- **International Transfers**: Controllers must assess and document safeguards. Orchestrator reduces volume transferred.
- **Prior Consultation**: For high-risk (e.g., large-scale AI monitoring), consult JOIC where required (Art. 17).

## 5. Stakeholder Consultation

- Internal: Development of guard, chains, and templates involved review against DPJL principles.
- External: Controllers using the orchestrator should consult their DPO (if appointed), MLRO (for AML aspects), and legal counsel.
- Data subjects: Transparency through privacy notices and rights mechanisms. No direct consultation needed for advisory tooling.
- Regulator: This DPIA should be made available to JOIC on request.

## 6. Conclusions and Recommendations

This processing is **high-risk** in contexts involving special category data, large-scale client screening, or innovative AI use for compliance. However, with the implemented safeguards (particularly the Authority Guard, minimisation defaults, and safe chains), risks are reduced to acceptable levels when controllers:
- Always declare authority for any real personal data.
- Prefer synthetic data and review outputs.
- Maintain their own DPIA register and RoPA.
- Apply appropriate transfer safeguards.
- Revisit this DPIA on material changes (new skills, increased volume, law updates).

**Recommendations**:
1. Adopt the recommended chains as default for DP/AML work.
2. Run `scripts/generate_policies.py` to bootstrap compliant documents.
3. Integrate DPIA checks into project initiation for any high-risk feature.
4. Log authority declarations for accountability.
5. Review this DPIA annually or on significant updates (e.g., new LLM capabilities or law changes).
6. Controllers must conduct their own full DPIA tailored to their specific processing.

**Approval**:
- Data Protection Officer / Responsible Person: ________________ Date: ________
- Senior Management / MLRO (if AML-relevant): ________________ Date: ________

**Next Review Date**: 2026-10-04 (or earlier on change).

## 7. References

- Data Protection (Jersey) Law 2018: https://www.jerseylaw.je/laws/current/l_3_2018
- JOIC Guidance: https://jerseyoic.org/
- Orchestrator skill: `jersey-data-protection-expert` (full guidance, guards, chains, script)
- Related: `docs/guides/dpia-orchestrator-ai-use.md`, `scripts/generate_policies.py`, `exports/` templates, `chains/registry.yaml`
- JFSC AML Handbook (for overlapping AML processing)

This DPIA demonstrates accountability and should be retained as part of the controller's records of processing activities. 

**This document was generated with reference to the Jersey Data Protection Expert skill and is provided as a template. Adapt and validate for your specific use.**
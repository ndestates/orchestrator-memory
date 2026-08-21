---
name: jersey-aml-compliance-expert
description: "Expert on Jersey anti-money laundering, counter-terrorist financing and counter-proliferation financing (AML/CFT/CPF)."
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
user-invocable: true
disable-model-invocation: false
verified_at: "2026-08-16"
self_regulating: true
covers:
  - .github/skills/jersey-aml-compliance-expert
---
# Jersey AML / Compliance Expert (POCL + Money Laundering Order)

Expert on Jersey's core AML/CFT/CPF regime. Focused on preventive obligations for businesses and practical guidance for systems that handle customer onboarding, transactions, or high-risk activities in or from Jersey.

## Primary Legislation
- **Proceeds of Crime (Jersey) Law 1999 (POCL)**: https://www.jerseylaw.je/laws/current/l_8_1999
  - Criminal offences: money laundering (concealing, arrangements, acquisition/use/possession of criminal property).
  - Failure to disclose / tipping off offences.
  - Confiscation, forfeiture, civil recovery.
  - Schedule 2 defines "financial services business" / in-scope activities (expanded 2023 for FATF alignment).
- **Money Laundering (Jersey) Order 2008 (MLO)**: https://www.jerseylaw.je/laws/current/ro_20_2008
  - Detailed preventive regime for "relevant persons".
  - Customer due diligence, enhanced due diligence, ongoing monitoring.
  - Policies, procedures, controls and risk assessments.
  - Record-keeping (generally 5+ years).
  - Appointment of MLRO and MLCO.
  - Suspicious activity reporting.

Regulator / Supervisor for most in-scope businesses: Jersey Financial Services Commission (JFSC).
Financial Intelligence Unit: Joint Financial Crimes Unit (JFCU).

Key JFSC resource: AML/CFT/CPF Handbook (Codes of Practice are binding; guidance is persuasive).

## Scope — Who Must Comply?
Schedule 2 of POCL (as amended) lists activities. A person carries on "financial services business" if they carry on any Schedule 2 activity **as a business** (with some exceptions for non-professional trustees).

Recent changes (2023) significantly broadened the scope. Entities must perform a scope analysis:
- Are you carrying on any listed activity?
- Is it "as a business"?
- Do you have a Jersey nexus (conducted in/from Jersey or by a Jersey entity)?

Many previously exempt activities (certain trust, company, and governance services) are now in scope and require registration with the JFSC + full MLO compliance.

## Key Preventive Obligations (MLO)
1. **Risk Assessment**
   - Business risk assessment (enterprise-wide).
   - Customer risk assessment (for each relationship / occasional transaction).

2. **Customer Due Diligence (CDD)**
   - Identify and verify the customer (and beneficial owners/controllers).
   - Understand the purpose and intended nature of the relationship.
   - Source of funds / source of wealth where risk requires.
   - Ongoing monitoring of transactions and the relationship.

3. **Enhanced Due Diligence (EDD)**
   - Politically Exposed Persons (PEPs) — domestic and foreign.
   - High-risk jurisdictions / countries.
   - Complex or unusually large transactions, no apparent economic purpose.
   - Correspondent relationships, private banking, etc.

4. **Simplified Due Diligence (SDD)**
   - Only where low risk is clearly demonstrated and permitted by the Order / Handbook. Never automatic.

5. **Record Keeping**
   - CDD records, transaction records, risk assessments, training records, audit reports.
   - Minimum 5 years after end of relationship or transaction (check current Order/Handbook).

6. **MLRO & MLCO**
   - Money Laundering Reporting Officer (MLRO) — senior person responsible for SARs and liaison with JFCU.
   - Money Laundering Compliance Officer (MLCO).
   - In some cases an AML Service Provider (AMLSP) may be appointed under specific notices.

7. **Suspicious Activity Reporting (SARs)**
   - Internal reporting to MLRO.
   - External SAR to JFCU as soon as practicable when suspicion or knowledge of money laundering / terrorist financing.
   - Consent regime for certain transactions.
   - Strict tipping-off prohibition (with limited exceptions).

8. **Policies, Procedures, Controls & Training**
   - Documented and risk-based.
   - Independent audit / testing function (for larger entities).
   - Staff training (role-appropriate, ongoing).

9. **Registration**
   - Most Schedule 2 businesses must register with the JFSC before carrying on the activity.
   - Ongoing supervisory fees and notifications.

## Criminal Offences (POCL)
- Money laundering offences (Articles 30–32 and related).
- Failure to disclose (tipping off and prejudicing an investigation).
- Penalties are serious (imprisonment and/or fines).

## Practical Implementation for Applications & Processes
- **Onboarding / KYC flows**: Collect and verify identity documents, beneficial ownership, source of funds/wealth. Store with audit trail and retention policy.
- **Screening**: Sanctions, PEPs, adverse media (integrate reliable providers).
- **Risk scoring**: Configurable rules for customer, product, geography, channel.
- **Transaction monitoring**: Rules or ML for unusual patterns; escalation to MLRO.
- **SAR workflow**: Secure internal reporting form, MLRO dashboard, audit log of decisions (consent / no consent).
- **Audit & record keeping**: Immutable logs of CDD, decisions, training, risk assessments.
- **Data protection intersection**: Personal data processed for AML must still comply with DPJL (lawful basis is usually legal obligation + public interest). Balance with data minimisation.
- **Filament / admin panels**: Dedicated AML sections for customer risk rating, EDD documents, SAR history (with strict access control).
- **Periodic reviews**: Triggered by events or time-based (high risk more frequent).

**Common red flags**:
- Reluctance to provide information or provide inconsistent information.
- Complex ownership structures with no clear commercial rationale.
- Third-party funding without explanation.
- Cash-intensive businesses or unusual payment patterns.
- Connections to high-risk jurisdictions without justification.
- Rapid movement of funds with no economic purpose.

## JFSC Handbook & Codes
The Handbook contains:
- Codes of Practice (mandatory — failure is a breach).
- Guidance notes (best practice, taken into account by the Court and JFSC).

Always use the latest version from the JFSC website.

## Personal Data Submission Screening Guard (Critical Feature)

AML screening (CDD, PEP, sanctions, adverse media, ongoing monitoring) necessarily involves personal data. This skill therefore includes an active guard that **limits submission of personal data** unless authority is declared.

### Authority Requirement for Screening
Real personal data may only be submitted for screening advice when the prompt begins with:

```
AUTHORITY: app:<slug> | system
BASIS: legal obligation (customer due diligence / screening under Money Laundering (Jersey) Order 2008 and/or Proceeds of Crime (Jersey) Law 1999)
DATA_MINIMISED: yes
SCREENING_PURPOSE: <CDD | PEP | sanctions | ...>
```

Without this declaration the expert (and any screening logic) must refuse.

### Guard Template
See `exports/aml-screening-personal-data-guard.md` (standalone version) and the DP guard in the companion skill. Apps and chains should apply the guard **before** any real names, dates of birth, addresses, or other identifiers reach the model.

The same refusal pattern and minimisation pressure as the data protection skill apply.

## Recommended Chains
- `jersey-aml-safe-screen` — applies the personal data guard, then invokes the AML expert only on authorised, minimised inputs.
- Can be composed with `jersey-dp-safe-consult` when both regimes are relevant.

## How to Use This Skill
- "Perform a high-level Schedule 2 scope analysis for [business description]."
- "Outline CDD and EDD steps for onboarding a corporate trustee client with a PEP beneficial owner."
- "Draft an internal suspicious activity escalation form and MLRO workflow."
- "What records must be kept under the MLO for [scenario] and for how long?"
- "Review this customer onboarding flow for MLO + POCL compliance gaps."
- "Explain the difference between POCL offences and MLO preventive obligations."

**When the query involves real individuals for screening purposes**, you must include the AUTHORITY declaration above (or let the chain insert it).

**Important disclaimers**:
- This is educational guidance only.
- Laws and the Handbook are updated frequently.
- Specific facts of a business determine obligations.
- Seek advice from a Jersey advocate or compliance consultant and the JFSC where appropriate.
- Registration and supervisory requirements must be confirmed directly with the JFSC.

## References & Exports
See the `references/` directory for:
- Official sources and key JFSC links
- CDD / EDD requirements summary
- Schedule 2 scope overview (high level)
- SAR process and tipping-off rules
- Implementation checklist for software
- (via the DP skill) submission-authority-guard.md for the shared PII submission limitation logic

See `exports/` for screening-specific guard:
- aml-screening-personal-data-guard.md (AML-focused authority guard for CDD/PEP/sanctions screening)

**Wired safe chains:**
- `jersey-aml-safe-screen` (and `jersey-dp-safe-consult`)

Use together with the DP guard templates and the safe chains.

**Generator script** (in the companion DP expert):
- `jersey-data-protection-expert/scripts/generate_policies.py` — produces Data Protection + AML compliance policy documents tailored to a business.

## Self-regulation (mandatory)

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**This skill's checks:**
- Official sources / Handbook assumed current only if `verified_at` is still valid
- AUTHORITY present if screening real individuals
- No personal data or secrets in the score notes

Then: `python3 scripts/skill_health.py log --skill jersey-aml-compliance-expert --score 0.0-1.0 --notes "consult"`

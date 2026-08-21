# AML Screening Personal Data Guard (Jersey MLO + POCL)

Apply this in addition to the general DP submission guard when the query concerns screening of individuals or entities.

## Required Declaration (before any real identifiers)

AUTHORITY: app:<slug> | system
BASIS: legal obligation (customer due diligence / screening under Money Laundering (Jersey) Order 2008 and/or Proceeds of Crime (Jersey) Law 1999)
DATA_MINIMISED: yes
SCREENING_PURPOSE: CDD | PEP | sanctions | adverse media | ongoing monitoring

If missing or the input contains real personal data without it → refuse using the standard refusal format from the DP guard.

This ensures that even when screening is a legal obligation, the prompt layer still enforces minimisation and explicit authority.

(Full version: .github/skills/jersey-aml-compliance-expert/exports/aml-screening-personal-data-guard.md)

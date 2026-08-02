#!/usr/bin/env python3
"""
generate_policies.py

Generate tailored Data Protection and Compliance policy documents for a user's business,
compliant with Jersey Data Protection (Jersey) Law 2018 and Proceeds of Crime (Jersey) Law 1999 + Money Laundering (Jersey) Order 2008.

Usage examples:
  python generate_policies.py --name "Acme Trust Services Ltd" --sector "Financial Services" --activities "Trust administration, company management" --clients "international" --aml-regulated --output ./policies

  python generate_policies.py --interactive

Outputs Markdown files ready for customization and legal review.
"""

import argparse
import os
import sys
from datetime import datetime
from textwrap import dedent

def get_args():
    parser = argparse.ArgumentParser(
        description="Generate Jersey-compliant data protection and AML/CTF policies for a business."
    )
    parser.add_argument("--name", help="Business / company name")
    parser.add_argument("--sector", default="General Business", help="Industry sector (e.g. Financial Services, E-sign, Property)")
    parser.add_argument("--activities", default="General commercial activities", help="Description of main business activities")
    parser.add_argument("--clients", default="local and international", help="Client types (e.g. individuals, corporates, international)")
    parser.add_argument("--employees", type=int, default=10, help="Approximate number of employees")
    parser.add_argument("--processes-personal-data", action="store_true", default=True, help="Whether the business processes personal data of clients/employees")
    parser.add_argument("--aml-regulated", action="store_true", help="Subject to AML/CFT obligations under MLO/POCL")
    parser.add_argument("--has-special-category", action="store_true", help="Processes special category or criminal data")
    parser.add_argument("--international-transfers", action="store_true", help="Transfers personal data outside Jersey")
    parser.add_argument("--output", default="./generated-policies", help="Output directory for policy files")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode to collect details")
    return parser.parse_args()

def interactive_collect():
    print("=== Jersey Data & Compliance Policy Generator ===\n")
    data = {}
    data["name"] = input("Business / Company name: ").strip() or "Your Business Ltd"
    data["sector"] = input("Sector / Industry: ").strip() or "Financial Services"
    data["activities"] = input("Main business activities: ").strip() or "Trust and company administration"
    data["clients"] = input("Types of clients: ").strip() or "international corporates and individuals"
    data["employees"] = int(input("Approx number of employees (default 10): ") or 10)
    data["aml_regulated"] = input("Is the business AML/CFT regulated under MLO/POCL? (y/n): ").lower().startswith("y")
    data["has_special"] = input("Does it process special category or criminal data? (y/n): ").lower().startswith("y")
    data["international"] = input("Does it transfer personal data outside Jersey? (y/n): ").lower().startswith("y")
    data["processes_pd"] = True
    return data

def render_template(template, **kwargs):
    return dedent(template).format(**kwargs).strip() + "\n"

def generate_policies(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    # Common context
    ctx = {
        "business_name": data["name"],
        "sector": data["sector"],
        "activities": data["activities"],
        "clients": data["clients"],
        "employees": data["employees"],
        "today": today,
        "aml_note": "This business is subject to the Proceeds of Crime (Jersey) Law 1999 and Money Laundering (Jersey) Order 2008." if data.get("aml_regulated") else "This business monitors AML risks where relevant.",
        "dp_law": "Data Protection (Jersey) Law 2018",
        "special_note": "The business processes special category or criminal conviction data and applies additional safeguards." if data.get("has_special") else "The business does not routinely process special category data.",
        "transfer_note": "The business transfers personal data outside Jersey and relies on appropriate safeguards (e.g. adequacy decisions, SCCs or binding corporate rules)." if data.get("international") else "The business does not routinely transfer personal data outside Jersey.",
    }

    # 1. Data Protection Policy
    dp_policy = render_template("""
# Data Protection Policy

**{business_name}**  
**Effective Date:** {today}  
**Last Reviewed:** {today}

## 1. Introduction
{ business_name } is committed to complying with the {dp_law} and the Data Protection Authority (Jersey) Law 2018. This policy sets out how we collect, use, store, and protect personal data.

## 2. Scope
This policy applies to all personal data processed by {business_name} in the course of its {sector} activities, including {activities}.

We process personal data of {clients} and approximately {employees} employees / contractors.

## 3. Data Protection Principles
We adhere to the seven principles in the {dp_law}:
1. Lawfulness, fairness and transparency
2. Purpose limitation
3. Data minimisation
4. Accuracy
5. Storage limitation
6. Integrity and confidentiality (security)
7. Accountability

## 4. Lawful Bases
We rely on the following bases (as applicable):
- Legal obligation (particularly where {aml_note})
- Legitimate interests
- Consent (where required)
- Contract

## 5. Rights of Data Subjects
Individuals have the right to:
- Access their data (Subject Access Requests)
- Rectification, erasure, restriction, portability
- Object to processing and automated decision-making
- Withdraw consent

Requests should be sent to [data-protection@{business_name.lower().replace(' ', '')}.com or insert contact].

## 6. Security and Retention
We implement appropriate technical and organisational measures.
Personal data is retained only for as long as necessary for the stated purpose or to meet legal obligations (e.g. 5+ years for AML records).

{special_note}
{transfer_note}

## 7. Data Protection Officer / Contact
[Name or "We have appointed / are not required to appoint a DPO"]  
Email: [contact]  
Telephone: [contact]

## 8. Policy Owner and Review
This policy is reviewed at least annually or upon significant changes to our processing activities or the law.

**Approved by:** ___________________________ Date: {today}
""", **ctx)

    # 2. Privacy Notice (simplified)
    privacy_notice = render_template("""
# Privacy Notice

**{business_name}**  
**Last updated:** {today}

This notice explains how we collect and use your personal data in accordance with the {dp_law}.

## What data we collect
- Identity and contact information
- Financial and transaction data (where relevant to our {sector} services)
- Information provided in the course of {activities}

## How we use it
We use your data to:
- Provide our services
- Comply with legal obligations including {aml_note}
- Manage our relationship with you

## Your rights
See our Data Protection Policy for details on how to exercise your rights.

## Contact
Data Protection enquiries: [insert email]

Full details of our processing are available on request or in our Data Protection Policy.
""", **ctx)

    # 3. AML / Compliance Policy (if regulated or always provide)
    aml_policy = render_template("""
# Anti-Money Laundering and Counter-Terrorist Financing Policy

**{business_name}**  
**Effective:** {today}

## Commitment
{business_name} is committed to preventing money laundering, terrorist financing and proliferation financing.

{aml_note}

## Our Obligations
We comply with:
- Proceeds of Crime (Jersey) Law 1999
- Money Laundering (Jersey) Order 2008
- JFSC AML/CFT/CPF Handbook and Codes of Practice

## Customer Due Diligence (CDD)
We perform risk-based CDD, including:
- Identification and verification of clients and beneficial owners
- Enhanced Due Diligence for higher-risk clients (PEPs, high-risk jurisdictions, etc.)
- Understanding the source of funds and wealth
- Ongoing monitoring

## Record Keeping
Records are kept for at least five years after the end of the business relationship.

## Suspicious Activity Reporting
Staff must report suspicions internally to the MLRO without tipping off the client.

## Training and Governance
All relevant staff receive regular training. We maintain appropriate policies, procedures and controls.

**MLRO:** [Name]  
**MLCO:** [Name]

{special_note if special else ""}

This policy is reviewed annually.
""", **ctx)

    # 4. Data Retention Schedule (simple)
    retention = render_template("""
# Data Retention Schedule

**{business_name}**

| Data Category              | Retention Period          | Legal Basis / Reason                  |
|----------------------------|---------------------------|---------------------------------------|
| Client identification (CDD)| 5 years after relationship ends | MLO / POCL requirements              |
| Transaction records        | 5 years after transaction | AML obligations                      |
| Employee records           | 6 years after employment ends | Employment law + tax                 |
| Marketing consents         | Until withdrawn + 1 year  | Consent management                   |
| General business records   | 6-10 years                | Companies Law / tax / limitation     |
| Special category data      | Minimised; deleted when no longer necessary | Strict necessity test                |

Data is securely destroyed at the end of the retention period.
""", **ctx)

    files = {
        "data-protection-policy.md": dp_policy,
        "privacy-notice.md": privacy_notice,
        "aml-ctf-policy.md": aml_policy,
        "data-retention-schedule.md": retention,
    }

    for filename, content in files.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Created: {path}")

    print(f"\nPolicies generated for {data['name']} in {output_dir}")
    print("IMPORTANT: These are starting templates only. Obtain legal advice before adoption. Customise to your exact operations and keep under regular review.")

def main():
    args = get_args()

    if args.interactive:
        data = interactive_collect()
    else:
        if not args.name:
            print("Error: --name is required unless using --interactive")
            sys.exit(1)
        data = {
            "name": args.name,
            "sector": args.sector,
            "activities": args.activities,
            "clients": args.clients,
            "employees": args.employees,
            "aml_regulated": args.aml_regulated,
            "has_special": args.has_special_category,
            "international": args.international_transfers,
            "processes_pd": args.processes_personal_data,
        }

    generate_policies(data, args.output)

if __name__ == "__main__":
    main()

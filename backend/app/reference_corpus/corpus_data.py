"""
LexPilot - Reference Corpus Data
--------------------------------
Standard baseline contract templates derived from publicly available standard commercial contracts
and the open-source CUAD (Contract Understanding Atticus Dataset) public examples.
Note: These are preloaded reference benchmarks; no model was fine-tuned on them.
"""

REFERENCE_CORPUS = {
    "employment": {
        "termination": {
            "standard_title": "Termination of Employment",
            "standard_text": "Either party may terminate this Agreement without cause upon providing thirty (30) days' prior written notice to the other party. Employer may terminate immediately for Cause upon written notice specifying the grounds thereof.",
            "standard_notice_days": 30,
            "standard_cure_days": 15,
            "typical_triggers": ["death", "disability", "material breach", "convenience with 30 days notice"]
        },
        "payment": {
            "standard_title": "Compensation and Benefits",
            "standard_text": "Company shall pay Employee a base salary payable in semi-monthly installments in accordance with Company's standard payroll practices. Employee is eligible for standard health and retirement benefits.",
            "standard_frequency": "semi-monthly or bi-weekly"
        },
        "non_compete": {
            "standard_title": "Restrictive Covenants and Non-Competition",
            "standard_text": "During the term of employment and for a period of twelve (12) months following termination, Employee shall not directly engage in or perform services for a competing business within a 25-mile radius of Employee's primary office.",
            "standard_duration_months": 12,
            "standard_geographic_scope": "reasonable geographic territory (e.g., 25-50 miles)"
        },
        "confidentiality": {
            "standard_title": "Confidential Information",
            "standard_text": "Employee shall maintain in strict confidence all proprietary technical, financial, and customer information of Employer, and shall not disclose such information during or after employment, except in the performance of duties.",
            "standard_duration": "perpetual for trade secrets, 3-5 years for commercial info"
        },
        "governing_law": {
            "standard_title": "Governing Law",
            "standard_text": "This Agreement shall be governed by and construed in accordance with the laws of the State of employment, without regard to conflict of laws principles."
        }
    },
    "nda": {
        "confidentiality": {
            "standard_title": "Protection of Confidential Information",
            "standard_text": "Receiving Party agrees to hold Disclosing Party's Confidential Information in strict confidence and to exercise the same degree of care as it uses for its own proprietary information, but in no event less than reasonable care.",
            "standard_duration_years": 3
        },
        "termination": {
            "standard_title": "Term and Return of Materials",
            "standard_text": "This Agreement shall remain in effect for two (2) years. Upon written request, Receiving Party shall promptly return or certify the destruction of all Confidential Information within ten (10) business days.",
            "standard_return_days": 10
        },
        "liability": {
            "standard_title": "Equitable Relief & Remedies",
            "standard_text": "The parties acknowledge that unauthorized disclosure causes irreparable harm for which damages alone are inadequate, entitling Disclosing Party to seek preliminary and permanent injunctive relief."
        }
    },
    "residential_lease": {
        "termination": {
            "standard_title": "Lease Term & Notice of Termination",
            "standard_text": "Tenant or Landlord may terminate this month-to-month tenancy upon delivering at least thirty (30) days' prior written notice before the end of the current rental month.",
            "standard_notice_days": 30
        },
        "payment": {
            "standard_title": "Rent Payment & Grace Period",
            "standard_text": "Rent is due on the first (1st) day of each calendar month. A late fee not exceeding 5% of monthly rent shall apply if payment is not received by the fifth (5th) calendar day.",
            "standard_grace_days": 5,
            "standard_late_fee_percent": 5
        },
        "notice": {
            "standard_title": "Landlord Entry Notice",
            "standard_text": "Landlord reserves the right to enter the leased premises for inspection or repairs upon providing at least twenty-four (24) hours' advance notice to Tenant, except in cases of emergency.",
            "standard_entry_notice_hours": 24
        }
    },
    "msa": {
        "liability": {
            "standard_title": "Limitation of Liability",
            "standard_text": "Except for indemnification obligations and breach of confidentiality, neither party's aggregate liability under this Agreement shall exceed the total fees paid or payable by Client in the twelve (12) months preceding the claim.",
            "standard_cap": "12 months fees paid",
            "standard_disclaimer": "waiver of indirect, special, or consequential damages"
        },
        "indemnification": {
            "standard_title": "Mutual Indemnification",
            "standard_text": "Service Provider shall defend, indemnify, and hold Client harmless against third-party claims alleging that the Deliverables infringe intellectual property rights. Client shall indemnify Service Provider against claims arising from Client Materials.",
            "standard_scope": "IP infringement defense and gross negligence"
        },
        "payment": {
            "standard_title": "Invoicing & Payment Terms",
            "standard_text": "Invoices shall be rendered monthly and are payable Net 30 days from the invoice date. Past-due balances accrue interest at 1.0% per month or the maximum legal rate.",
            "standard_net_days": 30
        },
        "termination": {
            "standard_title": "Termination for Cause and Convenience",
            "standard_text": "Either party may terminate for material breach if not cured within thirty (30) days of written notice. Client may terminate for convenience upon sixty (60) days' written notice.",
            "standard_cure_days": 30,
            "standard_convenience_days": 60
        }
    }
}

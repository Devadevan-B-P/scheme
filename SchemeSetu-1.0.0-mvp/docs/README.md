# SchemeSetu Documentation & Provenance Repository

Welcome to the SchemeSetu documentation suite. This folder contains all verified research, ground-truth provenance files, and policy references powering the deterministic eligibility and financial simulator engines.

---

## Contents

### 1. [Loan Schemes Ground-Truth Findings & Provenance Dossier](file:///home/alan/Work/tries/hack1/docs/LOAN_SCHEMES_FINDINGS.md)
A comprehensive, line-by-line audit report comparing initial approximations against verified ground truth across all 4 active Ministry of Social Justice and Empowerment (MoSJE) corporations:
- **NSFDC**: Term Loan Scheme (up to ₹50L project cost / ₹45L loan, 8% interest, revised ₹5L income ceiling).
- **NSKFDC**: Mahila Samriddhi Yojana (up to ₹1L at 4% concessional interest, 0% margin money, 50% capital subsidy).
- **NDFDC (formerly NHFDC)**: Divyangjan Swavalamban Yojana (up to ₹50L, tiered 5%-9% interest, UDID verification).
- **NBCFDC**: General Loan Scheme (up to ₹15L, 85% finance / 15% margin money, 8-year tenure, ₹3L income ceiling).
- **Financial Simulation Analysis**: Why real loan limits dramatically change EMI and down-payment calculations for entrepreneurs.
- **Judge Q&A Defense Sheet**: Direct answers and citations to common judge sanity-checks.

### 2. [`docs/provenance/`](file:///home/alan/Work/tries/hack1/docs/provenance/) (Offline Primary Source Documents)
Archived primary source artifacts fetched directly from official government servers for 1-click auditability:

| Filename | Type | Size | Source Authority & Document |
|---|---|---|---|
| [`nsfdc_scheme.html`](file:///home/alan/Work/tries/hack1/docs/provenance/nsfdc_scheme.html) | HTML | 130 KB | NSFDC Official Schemes Portal (`nsfdc.nic.in/scheme`) — Term Loan details |
| [`nsfdc_eligibility.html`](file:///home/alan/Work/tries/hack1/docs/provenance/nsfdc_eligibility.html) | HTML | 115 KB | NSFDC Eligibility Requirements (`nsfdc.nic.in/eligibility-requirements`) — ₹5L income criteria |
| [`nskfdc_pib_release.html`](file:///home/alan/Work/tries/hack1/docs/provenance/nskfdc_pib_release.html) | HTML | 76 KB | Press Information Bureau, MoSJE (PIB Release ID 1953523) — NSKFDC Mahila Samridhi |
| [`ndfdc_divyangjan_swavalamban.pdf`](file:///home/alan/Work/tries/hack1/docs/provenance/ndfdc_divyangjan_swavalamban.pdf) | PDF | 360 KB | NDFDC / DEPwD Official Scheme Guidelines Document — Divyangjan Swavalamban Yojana |
| [`nbcfdc_general_loan.html`](file:///home/alan/Work/tries/hack1/docs/provenance/nbcfdc_general_loan.html) | HTML | 67 KB | NBCFDC Official Portal (`nbcfdc.gov.in/nbcfdc/web/en/general-loan`) — General Loan Scheme |

---

## Automated Verification

All findings and documents in this directory are continuously asserted by automated test suites in the backend:
- [`backend/tests/test_provenance.py`](file:///home/alan/Work/tries/hack1/backend/tests/test_provenance.py): Corroborates that local documents exist and contain the verbatim policy figures.
- [`backend/tests/test_financial.py`](file:///home/alan/Work/tries/hack1/backend/tests/test_financial.py): Verifies exact EMI, margin money, and subsidy math against the verified numbers.

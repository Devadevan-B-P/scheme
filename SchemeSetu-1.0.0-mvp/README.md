# SchemeSetu (SIH PS 26092)

## 0. Product Definition — Freeze This First

**Product goal**
Build a multilingual, low-friction platform that helps marginalized entrepreneurs (SC, ST, Safai Karamchari, OBC, Divyangjan):
- Understand their need
- ↓
- Build a profile conversationally
- ↓
- Find eligible government schemes
- ↓
- Understand why they qualify / fail
- ↓
- Calculate financial implications
- ↓
- Find an appropriate nearby partner
- ↓
- Take the next action

**Core architectural principle**
AI understands the user; the deterministic engine makes the decision. Gemini must never independently determine eligibility, subsidy, margin money, loan amount, or EMI.

**Primary product actors**
1. Beneficiary / Entrepreneur
2. CSC Agent
3. Channel Partner / SCA / Bank
4. Administrator / Auditor

**Product channels**
- Current MVP: Web text interface
- Later: WhatsApp, Voice, CSC assisted mode

---

## Architecture

```
User (Web Chat)
   │
   ▼
[Sanitization Shield] (Aadhaar / PAN / Phone Redaction)
   │
   ▼
[Gemini 3.8 Flash] (Extract: age, income, category, business, location + Intent)
   │
   ▼
[UserProfile Builder] (Incremental Profile State)
   │
   ▼
[Deterministic Rule Engine] (Hardcoded, auditable evaluation against verified rules)
   │
   ├── [Eligible] ──► [Financial Simulator] (Subsidy, Margin Money, EMI)
   │                       │
   │                       ▼
   │                  [Partner Routing] (Haversine Nearest SCA/Bank/CSC)
   │
   ├── [Ineligible] ──► [Explainable Reason] (Specific failed criteria + CSC guidance)
   │
   └── [Missing Info] ──► [Next-Best-Question] (Discriminates candidate schemes)
```

## Key Technical Decisions & Innovations

1. **Deterministic Financial Decisions**: LLM NEVER approves loans or calculates eligibility. The FastAPI deterministic rule engine is the single source of financial truth.
2. **Independent Rule & Scheme Versioning**: `scheme_version` and `rule_version` vary independently, creating an auditable provenance trail for every decision.
3. **Workflow-Enforced Data Provenance**: Scheme numbers originate from official MoSJE/NSFDC/NSKFDC/NHFDC/NBCFDC gazettes and circulars (see full [Loan Schemes Ground-Truth Findings & Provenance Dossier](file:///home/alan/Work/tries/hack1/docs/LOAN_SCHEMES_FINDINGS.md) and offline artifacts in [`docs/provenance/`](file:///home/alan/Work/tries/hack1/docs/provenance/)). Unverified candidate schemes are kept in `status: draft` and excluded from matching.
4. **Pre-LLM Privacy Shield**: Sanitized message context is stored in conversation history; raw PII never reaches Gemini.
5. **Discriminator Next-Best-Question**: Instead of an arbitrary 30-field form, the system identifies which missing field narrows candidate schemes fastest.
6. **Modern Stack**: Python 3.12, FastAPI, Beanie ODM (Async MongoDB), Gemini 3.8 Flash, `uv` package manager, React + Vite + Vanilla CSS.

---

## Documentation

Detailed phase deliverables, migration decisions, and architectural records can be found in the `docs/` directory:
- [Current State Audit](docs/CURRENT_STATE.md)
- [Migration Map](docs/MIGRATION.md)
- [API Migration & Contract](docs/API_MIGRATION.md)
- [AI Boundaries](docs/AI_BOUNDARY.md)
- [Final Target Architecture](docs/ARCHITECTURE.md)
- [Compliance & DPDP Framework](docs/COMPLIANCE.md)
- [Security Defenses](docs/SECURITY.md)
- [Audit Trail & Hashing](docs/AUDIT.md)
- [Data Flow Diagram](docs/DATA_FLOW.md)
- [Threat Model](docs/THREAT_MODEL.md)

---

## Quick Start

### Backend

```bash
cd backend

# Run with uv
uv sync
uv run pytest -v
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
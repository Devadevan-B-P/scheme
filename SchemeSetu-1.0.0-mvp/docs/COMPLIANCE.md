# Compliance Statement

This document outlines the compliance handling and data privacy framework for the UdyamMitra platform, specifically addressing guidelines such as the Digital Personal Data Protection Act (DPDP).

## 1. Data Categories & Purpose Limitation
- **Collected Data**: Age, state, business type, annual income, location.
- **Purpose**: Exclusively for determining eligibility for verified government schemes and identifying appropriate channel partners (CSCs/Banks).
- **Data Minimization**: The platform only collects data required by the deterministic rules of the schemes.

## 2. Consent Handling
- **Explicit Consent**: Document upload (OCR) requires explicit `ocr_document_upload` consent.
- **Persistence**: Consents are recorded in the `consents` collection with `granted` and `withdrawn` timestamps.
- **Withdrawal**: Users can withdraw consent, immediately halting specific processing paths.

## 3. Retention Policy
- **Absolute Expiration**: All user sessions and extracted profiles have a strict 24-hour absolute lifespan.
- **Cleanup**: MongoDB TTL indexes enforce automatic deletion of expired session data and OCR tokens.

## 4. Aadhaar / UIDAI Boundary
- **Status**: Aadhaar number collection is strictly **out of scope** for the digital MVP.
- **Justification**: To minimize risk and comply with data minimization, identity verification is delegated to the manual/CSC partner stage. Raw Aadhaar and PAN strings are stripped from conversational inputs.

## 5. Third-Party Processing (Gemini)
- **Sanitization**: All conversational input passes through a pre-LLM regex/DLP privacy shield.
- **Policy**: Gemini is used strictly for extraction and phrasing. No PII is sent beyond what is strictly sanitized and necessary for intent extraction.

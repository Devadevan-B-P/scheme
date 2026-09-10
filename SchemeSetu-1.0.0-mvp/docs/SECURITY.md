# Security Hardening & Defenses

## 1. PII Handling & Sanitization
- Raw PII is never intentionally sent to Gemini or stored in long-term audit logs.
- Sensitive strings like 12-digit Aadhaar numbers and 10-character PANs are actively redacted before hitting any third-party APIs.

## 2. Authentication Boundary
- Sessions use anonymous correlation UUIDs. They are not authentication credentials.
- Administrative mutation endpoints (scheme ingestion) are locked behind environment-level API keys (or CLI execution only).

## 3. File Security (OCR)
- Uploads are strictly limited by file size and MIME type (JPEG, PNG, PDF).
- **In-Memory Processing**: Uploaded documents are read into memory for PaddleOCR processing and immediately discarded. Raw bytes are NEVER persisted to disk or object storage.

## 4. Rate Limiting
- Core endpoints (`/chat`, `/ocr/*`, `/financial/simulate`) are guarded against abuse to prevent resource exhaustion or quota depletion (e.g., Gemini quotas).

## 5. Input Validation
- All inputs are strictly validated against Pydantic models at the API boundary, actively rejecting `NaN`, negative invalid numbers, or malformed JSON payloads.

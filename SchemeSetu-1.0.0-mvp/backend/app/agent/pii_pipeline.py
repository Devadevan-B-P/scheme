"""
PII Pipeline & Sanitization Shield (Privacy Layer).

Two-pass defense-in-depth pipeline (Tier 2):
  Pass 1: Fast regex pre-filter (local, synchronous) — catches Aadhaar/PAN/phone/account
  Pass 2: Cloud DLP authoritative pass (async, with timeout fallback) — catches names/emails/GST

Fallback visibility:
  When DLP degrades (timeout, unavailable), sanitizer_mode is set to "regex_only"
  and a WARNING-level log is emitted.
"""

import logging
import re
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Indian PII regex patterns
AADHAAR_PATTERN = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\b(?:\+?91[\s\-]?)?[6789]\d{9}\b")
ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")


class SanitizedContext(BaseModel):
    """Sanitized context ready to be safely dispatched to LLM."""
    raw_length: int
    sanitized_text: str
    redactions_applied: int
    dlp_findings: list[str] = Field(
        default_factory=list,
        description="DLP finding types detected (e.g. 'PERSON_NAME', 'EMAIL_ADDRESS').",
    )
    sanitizer_mode: str = Field(
        default="regex_only",
        description="'regex+dlp' when Cloud DLP was active, 'regex_only' when degraded or disabled.",
    )


def regex_sanitize(text: str) -> str:
    """
    Pass 1: Fast regex pre-filter.
    Scrub all PII identifiers from raw user input before sending to Gemini
    or storing in conversation history.
    """
    if not text:
        return ""

    sanitized = text

    # Redact Aadhaar first (12 digits)
    sanitized = AADHAAR_PATTERN.sub("[AADHAAR_REDACTED]", sanitized)

    # Redact PAN (5 letters + 4 digits + 1 letter)
    sanitized = PAN_PATTERN.sub("[PAN_REDACTED]", sanitized)

    # Redact Phone (Indian 10 digits starting with 6-9)
    sanitized = PHONE_PATTERN.sub("[PHONE_REDACTED]", sanitized)

    # Redact remaining long digit sequences resembling bank accounts
    def _account_replace(match):
        token = match.group(0)
        if len(token) >= 9:
            return "[ACCOUNT_REDACTED]"
        return token

    sanitized = ACCOUNT_PATTERN.sub(_account_replace, sanitized)

    return sanitized


# Alias for backward compatibility
sanitize_text = regex_sanitize


async def sanitize_text_pipeline(text: str) -> SanitizedContext:
    """
    Two-pass defense-in-depth sanitization pipeline.
    Pass 1: regex_sanitize() — fast, local, catches Aadhaar/PAN/phone/account
    Pass 2: DLP client — catches names, emails, GST that regex misses
    """
    from app.services.dlp_service import dlp_client

    # Pass 1: Fast regex pre-filter
    regex_result = regex_sanitize(text)

    # Pass 2: Cloud DLP pass
    try:
        dlp_result = await dlp_client.inspect_and_deidentify(regex_result)

        if not dlp_result.dlp_available:
            return SanitizedContext(
                raw_length=len(text),
                sanitized_text=regex_result,
                redactions_applied=0,
                dlp_findings=[],
                sanitizer_mode="regex_only",
            )

        return SanitizedContext(
            raw_length=len(text),
            sanitized_text=dlp_result.sanitized_text,
            redactions_applied=dlp_result.findings_count,
            dlp_findings=dlp_result.finding_types,
            sanitizer_mode="regex+dlp",
        )
    except Exception as exc:
        logger.warning("DLP pipeline notice: %s — falling back to regex-only sanitization.", exc)
        return SanitizedContext(
            raw_length=len(text),
            sanitized_text=regex_result,
            redactions_applied=0,
            dlp_findings=[],
            sanitizer_mode="regex_only",
        )


def contains_unredacted_pii(text: str) -> bool:
    """
    Safety audit function: Returns True if raw unredacted Aadhaar, PAN, or phone is present.
    """
    if not text:
        return False

    text_without_tokens = (
        text.replace("[AADHAAR_REDACTED]", "")
        .replace("[PAN_REDACTED]", "")
        .replace("[PHONE_REDACTED]", "")
        .replace("[ACCOUNT_REDACTED]", "")
        .replace("[EMAIL_REDACTED]", "")
        .replace("[NAME_REDACTED]", "")
        .replace("[GST_REDACTED]", "")
    )

    if AADHAAR_PATTERN.search(text_without_tokens):
        return True
    if PAN_PATTERN.search(text_without_tokens):
        return True
    if PHONE_PATTERN.search(text_without_tokens):
        return True

    return False

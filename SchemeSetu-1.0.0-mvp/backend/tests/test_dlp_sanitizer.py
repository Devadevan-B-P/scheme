"""
Tests for Cloud DLP defense-in-depth sanitizer pipeline (Phase 1).

Tests:
  1. Two-pass pipeline catches PII that regex alone misses (emails, names via prefixes)
  2. DLP timeout → regex fallback with sanitizer_mode="regex_only"
  3. DLP unavailable → regex fallback
  4. Mock DLP catches GST numbers
  5. Pipeline preserves non-PII text exactly
  6. sanitizer_mode correctly reports "regex+dlp" vs "regex_only"
  7. ChatResponse includes sanitizer_mode field
  8. Regression: all existing sanitize_text behavior unchanged
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agent.sanitizer import (
    regex_sanitize,
    sanitize_text,
    sanitize_text_pipeline,
    contains_unredacted_pii,
    SanitizedContext,
)
from app.services.dlp_service import (
    MockDlpClient,
    DlpResult,
    dlp_client,
)


# ---------------------------------------------------------------------------
# 1. Pipeline catches PII regex misses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_catches_email_addresses():
    """Email addresses are NOT caught by regex sanitizer but ARE caught by mock DLP."""
    text = "Contact me at ramesh.kumar@gmail.com for loan details."

    # Regex alone doesn't catch emails
    regex_result = regex_sanitize(text)
    assert "ramesh.kumar@gmail.com" in regex_result

    # Pipeline with mock DLP catches it
    result = await sanitize_text_pipeline(text)
    assert "ramesh.kumar@gmail.com" not in result.sanitized_text
    assert "[EMAIL_REDACTED]" in result.sanitized_text
    assert "EMAIL_ADDRESS" in result.dlp_findings


@pytest.mark.asyncio
async def test_pipeline_catches_named_persons_with_prefix():
    """Person names with prefixes (Mr./Shri/Smt.) are caught by mock DLP."""
    text = "Applicant is Shri. Ramesh Kumar from Lucknow."

    # Regex alone doesn't catch names
    regex_result = regex_sanitize(text)
    assert "Ramesh Kumar" in regex_result

    # Pipeline catches name via prefix heuristic
    result = await sanitize_text_pipeline(text)
    assert "Ramesh Kumar" not in result.sanitized_text
    assert "[NAME_REDACTED]" in result.sanitized_text
    assert "PERSON_NAME" in result.dlp_findings


@pytest.mark.asyncio
async def test_pipeline_catches_gst_numbers():
    """GST numbers (15-char alphanumeric) are caught by mock DLP."""
    text = "My GST number is 22AAAAA0000A1Z5."

    result = await sanitize_text_pipeline(text)
    assert "22AAAAA0000A1Z5" not in result.sanitized_text
    assert "[GST_REDACTED]" in result.sanitized_text
    assert "INDIA_GST_INDIVIDUAL" in result.dlp_findings


# ---------------------------------------------------------------------------
# 2. DLP timeout fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dlp_timeout_falls_back_to_regex_only():
    """When DLP times out, pipeline returns regex-only result with sanitizer_mode='regex_only'."""
    text = "My Aadhaar is 1234 5678 9012 and email is test@example.com."

    class TimeoutDlpClient:
        async def inspect_and_deidentify(self, text):
            raise asyncio.TimeoutError()

    with patch("app.services.dlp_service.dlp_client", TimeoutDlpClient()):
        # Need to reimport to avoid the import cache
        result = await sanitize_text_pipeline(text)

    # Regex should have caught the Aadhaar
    assert "1234 5678 9012" not in result.sanitized_text
    assert "[AADHAAR_REDACTED]" in result.sanitized_text

    # DLP was unavailable, so email may still be present (regex doesn't catch emails)
    assert result.sanitizer_mode == "regex_only"
    assert result.dlp_findings == []


# ---------------------------------------------------------------------------
# 3. DLP unavailable fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dlp_unavailable_falls_back_to_regex_only():
    """When DLP returns dlp_available=False, pipeline uses regex result."""
    text = "My PAN is ABCDE1234F."

    class UnavailableDlpClient:
        async def inspect_and_deidentify(self, text):
            return DlpResult(
                sanitized_text=text,
                findings_count=0,
                finding_types=[],
                dlp_available=False,
            )

    with patch("app.services.dlp_service.dlp_client", UnavailableDlpClient()):
        result = await sanitize_text_pipeline(text)

    # Regex should have caught PAN
    assert "ABCDE1234F" not in result.sanitized_text
    assert "[PAN_REDACTED]" in result.sanitized_text
    assert result.sanitizer_mode == "regex_only"


# ---------------------------------------------------------------------------
# 4. DLP exception fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dlp_exception_falls_back_to_regex_only():
    """When DLP raises unexpected exception, pipeline falls back gracefully."""
    text = "Call me at 9876543210."

    class BrokenDlpClient:
        async def inspect_and_deidentify(self, text):
            raise RuntimeError("DLP service crashed")

    with patch("app.services.dlp_service.dlp_client", BrokenDlpClient()):
        result = await sanitize_text_pipeline(text)

    assert "9876543210" not in result.sanitized_text
    assert "[PHONE_REDACTED]" in result.sanitized_text
    assert result.sanitizer_mode == "regex_only"


# ---------------------------------------------------------------------------
# 5. Non-PII text preservation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_preserves_non_pii_text():
    """Non-PII text passes through both pipeline stages unchanged."""
    text = "I am a 25 year old SC woman from Lucknow looking for a loan."

    result = await sanitize_text_pipeline(text)
    assert result.sanitized_text == text
    assert result.dlp_findings == []


# ---------------------------------------------------------------------------
# 6. sanitizer_mode correct reporting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sanitizer_mode_regex_plus_dlp_when_dlp_active():
    """When mock DLP is active (default), sanitizer_mode is 'regex+dlp'."""
    text = "Some text with no PII."
    result = await sanitize_text_pipeline(text)
    assert result.sanitizer_mode == "regex+dlp"


# ---------------------------------------------------------------------------
# 7. Regression: backward compatibility
# ---------------------------------------------------------------------------


def test_sanitize_text_alias_still_works():
    """sanitize_text is aliased to regex_sanitize — backward compatible."""
    text = "My Aadhaar is 1234 5678 9012."
    result = sanitize_text(text)
    assert "1234 5678 9012" not in result
    assert "[AADHAAR_REDACTED]" in result


def test_regex_sanitize_identical_to_old_sanitize_text():
    """regex_sanitize produces identical output to the old sanitize_text."""
    text = "PAN is ABCDE1234F, phone 9876543210, Aadhaar 1111 2222 3333, account 50100234567890."
    result = regex_sanitize(text)
    assert "[PAN_REDACTED]" in result
    assert "[PHONE_REDACTED]" in result
    assert "[AADHAAR_REDACTED]" in result
    assert "[ACCOUNT_REDACTED]" in result


def test_contains_unredacted_pii_catches_new_redaction_tokens():
    """contains_unredacted_pii recognizes all redaction tokens including new DLP ones."""
    clean = "[EMAIL_REDACTED] and [NAME_REDACTED] and [GST_REDACTED]"
    assert not contains_unredacted_pii(clean)

    dirty = "Actual email: user@test.com hidden in text with 1234 5678 9012"
    assert contains_unredacted_pii(dirty)


# ---------------------------------------------------------------------------
# 8. Two-pass ordering: regex runs FIRST, then DLP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_pass_ordering_regex_then_dlp():
    """
    Aadhaar (regex-caught) + email (DLP-caught) in same input.
    Both should be redacted in the final output.
    """
    text = "Aadhaar 1234 5678 9012 and email ramesh@example.com"

    result = await sanitize_text_pipeline(text)
    assert "1234 5678 9012" not in result.sanitized_text
    assert "ramesh@example.com" not in result.sanitized_text
    assert "[AADHAAR_REDACTED]" in result.sanitized_text
    assert "[EMAIL_REDACTED]" in result.sanitized_text
    assert result.sanitizer_mode == "regex+dlp"

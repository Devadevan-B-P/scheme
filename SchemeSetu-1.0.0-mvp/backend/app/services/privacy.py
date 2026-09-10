"""
Privacy and PII masking service for SchemeSetu.

Provides centralized PII masking utility functions to sanitize user input
(e.g., Aadhaar identity numbers, mobile phone numbers) before sending data
to downstream AI models or external services.
"""

import re


def mask_pii(text: str) -> str:
    """
    Sanitizes user input by redacting personally identifiable information (PII).

    - Redacts 12-digit identity numbers (e.g. Aadhaar pattern: 12 digits, with or without spaces)
      and replaces them with '[Aadhaar Redacted]'.
    - Redacts 10-digit mobile phone numbers and replaces them with '[Phone Omitted]'.

    Parameters
    ----------
    text : str
        Raw input text.

    Returns
    -------
    str
        Sanitized string with PII redacted.
    """
    if not text:
        return text

    # a) Redact 12-digit identity numbers (e.g. 123456789012 or 1234 5678 9012)
    sanitized = re.sub(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[Aadhaar Redacted]", text)

    # b) Redact 10-digit mobile phone numbers
    sanitized = re.sub(r"\b\d{10}\b", "[Phone Omitted]", sanitized)

    return sanitized

"""
Privacy & Sanitization Shield Unit Tests.
"""

from app.agent.sanitizer import (
    sanitize_text,
    contains_unredacted_pii,
)
from app.models.user import UserSession, ConversationMessage, ConversationRole, UserProfile


def test_aadhaar_sanitization():
    # Spaced 12 digits
    t1 = "My Aadhaar number is 1234 5678 9012 please check"
    s1 = sanitize_text(t1)
    assert "[AADHAAR_REDACTED]" in s1
    assert "1234 5678 9012" not in s1
    assert not contains_unredacted_pii(s1)

    # Hyphenated
    t2 = "Aadhaar: 4321-8765-2109"
    s2 = sanitize_text(t2)
    assert "[AADHAAR_REDACTED]" in s2
    assert "4321-8765-2109" not in s2
    assert not contains_unredacted_pii(s2)

    # Continuous 12 digits
    t3 = "UID 987654321098"
    s3 = sanitize_text(t3)
    assert "[AADHAAR_REDACTED]" in s3
    assert "987654321098" not in s3
    assert not contains_unredacted_pii(s3)


def test_pan_sanitization():
    t = "My PAN card is ABCDE1234F."
    s = sanitize_text(t)
    assert "[PAN_REDACTED]" in s
    assert "ABCDE1234F" not in s
    assert not contains_unredacted_pii(s)


def test_phone_sanitization():
    # Standard 10 digit Indian mobile
    t1 = "Call me at 9876543210 tomorrow"
    s1 = sanitize_text(t1)
    assert "[PHONE_REDACTED]" in s1
    assert "9876543210" not in s1
    assert not contains_unredacted_pii(s1)

    # With +91
    t2 = "Mobile: +91 9123456780"
    s2 = sanitize_text(t2)
    assert "[PHONE_REDACTED]" in s2
    assert "9123456780" not in s2
    assert not contains_unredacted_pii(s2)


def test_bank_account_sanitization():
    t = "Bank account no 123456789012345 for loan transfer"
    s = sanitize_text(t)
    assert "[ACCOUNT_REDACTED]" in s
    assert "123456789012345" not in s


def test_conversation_history_stores_no_unredacted_pii():
    # Verify UserSession conversation_history invariant
    raw_user_input = "My Aadhaar is 5555 4444 3333 and phone is 9876543210"
    sanitized = sanitize_text(raw_user_input)

    session = UserSession(
        session_id="sess_test",
        profile=UserProfile(),
        conversation_history=[
            ConversationMessage(
                role=ConversationRole.USER,
                content=sanitized,
            )
        ],
    )

    stored_message = session.conversation_history[0].content
    assert not contains_unredacted_pii(stored_message)
    assert "5555 4444 3333" not in stored_message
    assert "9876543210" not in stored_message

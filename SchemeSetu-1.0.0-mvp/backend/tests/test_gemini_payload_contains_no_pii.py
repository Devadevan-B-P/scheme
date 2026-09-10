"""
Security Audit Tests: Verifies outbound payload to Gemini contains ZERO unredacted PII across all identifier types and multi-turn context replays.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.contracts import ChatRequest
from app.agent.conversation import handle_chat_message
from app.agent.sanitizer import contains_unredacted_pii
from app.agent.gemini_client import gemini_agent



async def _run_chat_and_capture_prompts(session_id: str, message: str) -> list[str]:
    """Helper to dispatch a message to handle_chat_message and capture outbound Gemini prompt."""
    dispatched_prompts: list[str] = []

    async def fake_generate_content(*args, **kwargs):
        contents = kwargs.get("contents")
        if contents:
            dispatched_prompts.append(str(contents))
        return None

    mock_client = AsyncMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=fake_generate_content)

    with patch.object(gemini_agent, "api_key", "test_api_key_active"), \
         patch.object(gemini_agent, "_client", mock_client):
        req = ChatRequest(session_id=session_id, message=message, language="en")
        await handle_chat_message(req)

    return dispatched_prompts



@pytest.mark.asyncio
async def test_outbound_payload_redacts_aadhaar_variants():
    """Verify all formats of 12-digit Aadhaar (spaced, dashed, continuous) are redacted from outbound Gemini prompt."""
    raw_msg = "My Aadhaar numbers are 1234 5678 9012 and 4321-8765-2109 and 987654321098."
    prompts = await _run_chat_and_capture_prompts("sess_aadhaar_audit", raw_msg)

    assert len(prompts) >= 1
    for prompt in prompts:
        assert not contains_unredacted_pii(prompt)
        assert "1234 5678 9012" not in prompt
        assert "4321-8765-2109" not in prompt
        assert "987654321098" not in prompt
        assert "[AADHAAR_REDACTED]" in prompt


@pytest.mark.asyncio
async def test_outbound_payload_redacts_pan():
    """Verify Indian PAN numbers are scrubbed from outbound Gemini prompt."""
    raw_msg = "Here is my business PAN: ABCDE1234F and personal pan: BKZPM9988Q."
    prompts = await _run_chat_and_capture_prompts("sess_pan_audit", raw_msg)

    assert len(prompts) >= 1
    for prompt in prompts:
        assert not contains_unredacted_pii(prompt)
        assert "ABCDE1234F" not in prompt
        assert "BKZPM9988Q" not in prompt
        assert "[PAN_REDACTED]" in prompt


@pytest.mark.asyncio
async def test_outbound_payload_redacts_phone_numbers():
    """Verify 10-digit mobile numbers with and without +91 prefix are scrubbed from outbound Gemini prompt."""
    raw_msg = "Contact me at 9876543210 or alternate mobile +91 9123456780."
    prompts = await _run_chat_and_capture_prompts("sess_phone_audit", raw_msg)

    assert len(prompts) >= 1
    for prompt in prompts:
        assert not contains_unredacted_pii(prompt)
        assert "9876543210" not in prompt
        assert "9123456780" not in prompt
        assert "[PHONE_REDACTED]" in prompt


@pytest.mark.asyncio
async def test_outbound_payload_redacts_bank_accounts():
    """Verify bank account numbers are scrubbed from outbound Gemini prompt."""
    raw_msg = "Please deposit subsidy to SBI account 50100234567890."
    prompts = await _run_chat_and_capture_prompts("sess_account_audit", raw_msg)

    assert len(prompts) >= 1
    for prompt in prompts:
        assert "50100234567890" not in prompt
        assert "[ACCOUNT_REDACTED]" in prompt


@pytest.mark.asyncio
async def test_outbound_payload_multi_turn_history_does_not_leak_prior_pii():
    """
    CRITICAL MULTI-TURN AUDIT:
    Turn 1: User provides Aadhaar 8888 7777 6666 and Phone 9876500000.
    Turn 2: User sends a benign follow-up: 'What is the next step?'
    Verify that when Turn 2 replays conversation history to Gemini, Turn 1's history
    contains ONLY redacted tokens and zero unredacted PII.
    """
    session_id = "sess_multiturn_pii_audit"

    # Turn 1
    turn1_msg = "My Aadhaar is 8888 7777 6666 and phone is 9876500000."
    prompts1 = await _run_chat_and_capture_prompts(session_id, turn1_msg)
    for p in prompts1:
        assert not contains_unredacted_pii(p)

    # Turn 2 (benign message)
    turn2_msg = "What is the next step for my loan application?"
    prompts2 = await _run_chat_and_capture_prompts(session_id, turn2_msg)

    assert len(prompts2) >= 1
    for p in prompts2:
        # Check that prior turn history included in prompt 2 does NOT leak raw PII
        assert not contains_unredacted_pii(p), f"Turn 2 history leaked prior PII: {p}"
        assert "8888 7777 6666" not in p
        assert "9876500000" not in p
        assert "[AADHAAR_REDACTED]" in p
        assert "[PHONE_REDACTED]" in p

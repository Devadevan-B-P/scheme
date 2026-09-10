"""
Conversational Chat Flow Integration Tests.

Tests the full multi-turn conversational journey:
  Turn 1: Partial details -> Next-Best-Question asked
  Turn 2: Remaining demographic facts -> Eligible outcome + Financial Summary + Nearest Partner
  Turn 3: Ineligible profile -> Transparent failed criteria + CSC guidance (No dead end)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_full_conversational_journey_eligible():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Partial business & location intent
        payload_1 = {
            "message": "Hello, I want to start a tailoring shop in Lucknow.",
            "language": "en",
        }
        res1 = await client.post("/api/v1/chat", json=payload_1)
        assert res1.status_code == 200
        data1 = res1.json()

        session_id = data1["session_id"]
        assert session_id
        assert data1["profile_completeness"] > 0.0
        # No eligible schemes yet, arbitrator asks for missing discriminator
        assert data1["financial_summaries"] is None
        assert "?" in data1["response_text"]

        # Turn 2: Provide age, category, and income
        payload_2 = {
            "session_id": session_id,
            "message": "I am 28 years old, from SC category, and my yearly family income is 2.5 lakh.",
            "language": "en",
        }
        res2 = await client.post("/api/v1/chat", json=payload_2)
        assert res2.status_code == 200
        data2 = res2.json()

        assert data2["session_id"] == session_id
        assert data2["profile_completeness"] >= 0.7

        # Should now be eligible for NSFDC Term Loan!
        results = data2["eligibility_results"]
        assert results is not None
        nsfdc = next((r for r in results if r["scheme_id"] == "nsfdc_term_loan"), None)
        assert nsfdc is not None
        assert nsfdc["decision"] == "eligible"
        assert len(nsfdc["passed_rules"]) >= 3

        # Financial summary must be populated
        assert data2["financial_summaries"] is not None
        assert len(data2["financial_summaries"]) >= 1
        fin = data2["financial_summaries"][0]
        assert fin["loan_amount"] == 4500000.0
        assert fin["margin_money"] == 450000.0
        assert fin["bank_loan"] == 4050000.0
        assert fin["emi"] > 0

        # Nearest partner list attached
        assert data2["partner_list"] is not None
        assert len(data2["partner_list"]) >= 1
        assert data2["partner_list"][0]["distance_km"] < 15.0


@pytest.mark.asyncio
async def test_ineligible_journey_no_dead_ends():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: User with General category and high income (fails SC/OBC schemes, but NHFDC disability is still unanswered)
        payload1 = {
            "message": "I am from General category, age 35, annual family income is 1000000.",
            "language": "en",
        }
        res1 = await client.post("/api/v1/chat", json=payload1)
        assert res1.status_code == 200
        data1 = res1.json()

        # NHFDC Swavalamban doesn't have category/income limits, so engine asks if applicant has a disability
        assert "disability" in data1["response_text"].lower()

        # Turn 2: User answers "No disability"
        payload2 = {
            "session_id": data1["session_id"],
            "message": "No, I do not have any disability.",
            "language": "en",
        }
        res2 = await client.post("/api/v1/chat", json=payload2)
        assert res2.status_code == 200
        data2 = res2.json()

        # Now all central schemes are evaluated as ineligible
        assert data2["financial_summaries"] is None
        # Verify NO DEAD ENDS: CSC partner guidance attached
        assert "CSC" in data2["response_text"] or "Common Service Centre" in data2["response_text"]
        assert data2["partner_list"] is not None
        assert len(data2["partner_list"]) >= 1


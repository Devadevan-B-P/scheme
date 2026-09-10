"""
Tests for Legacy Compatibility Adapters.

Verifies:
  - Deprecation headers are attached (X-API-Deprecated: true).
  - Admin seed endpoint is protected (403 when disabled, 401 with wrong key, 200 with correct key).
  - Chat adapter correctly maps beneficiary_id as a session correlation identifier.
  - Partner match adapter handles latitude/longitude queries.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core.config import settings
from app.main import app
from app.core.config import settings
from app.models.contracts import ChatResponse, EligibilityResult, Decision


@pytest.mark.asyncio
async def test_legacy_admin_seed_forbidden_by_default():
    """Verify /admin/seed is disabled and forbidden by default outside explicit activation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/admin/seed")
        assert response.status_code == 403
        assert response.headers.get("X-API-Deprecated") == "true"
        assert "disabled" in response.json()["detail"].lower()

        # Also test top-level route
        resp_root = await ac.post("/admin/seed")
        assert resp_root.status_code == 403


@pytest.mark.asyncio
async def test_legacy_admin_seed_with_auth_when_enabled():
    """Verify /admin/seed requires X-Admin-Key when ENABLE_ADMIN_SEED_ENDPOINT is true."""
    with patch.object(settings, "ENABLE_ADMIN_SEED_ENDPOINT", True), \
         patch.object(settings, "ADMIN_API_KEY", "secret-test-key-123"), \
         patch("app.services.scheme_service.SchemeService.seed_schemes", new_callable=AsyncMock) as mock_seed_schemes, \
         patch("app.services.partner_service.PartnerService.seed_partners", new_callable=AsyncMock) as mock_seed_partners:
        
        mock_seed_schemes.return_value = 7
        mock_seed_partners.return_value = 10

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Missing header -> 401
            r_unauth = await ac.post("/api/v1/admin/seed")
            assert r_unauth.status_code == 401

            # 2. Invalid header -> 401
            r_bad = await ac.post("/api/v1/admin/seed", headers={"X-Admin-Key": "wrong-key"})
            assert r_bad.status_code == 401

            # 3. Valid header -> 200
            r_ok = await ac.post("/api/v1/admin/seed", headers={"X-Admin-Key": "secret-test-key-123"})
            assert r_ok.status_code == 200
            data = r_ok.json()
            assert data["scheme_count"] == 7
            assert data["partner_count"] == 10
            assert r_ok.headers.get("X-API-Deprecated") == "true"


@pytest.mark.asyncio
async def test_legacy_chat_adapter():
    """Verify /chat/{beneficiary_id} maps to chat_service and uses beneficiary_id as session correlation."""
    fake_response = ChatResponse(
        session_id="ben_corr_999",
        response_text="We found several schemes matching your profile.",
        language="en",
        profile_completeness=0.75,
        extracted_entities={"annual_income": 120000},
        eligibility_results=[
            EligibilityResult(
                scheme_id="mosje_post_matric_sc",
                scheme_version="v1.0.0",
                rule_version="v1.0.0",
                decision=Decision.ELIGIBLE,
                passed_rules=[],
                failed_rules=[],
                missing_fields=[],
            )
        ],
    )


    with patch("app.services.chat_service.chat_service.process_chat_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = fake_response

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/chat/ben_corr_999",
                json={"message": "I need help with my college fees"},
            )
            assert response.status_code == 200
            assert response.headers.get("X-API-Deprecated") == "true"
            data = response.json()
            assert data["beneficiary_id"] == "ben_corr_999"
            assert data["reply"] == fake_response.response_text
            assert data["profile_completeness_pct"] == 75
            assert len(data["eligibility_results"]) == 1
            assert data["eligibility_results"][0]["scheme_id"] == "mosje_post_matric_sc"


@pytest.mark.asyncio
async def test_legacy_partner_matching():
    """Verify legacy /partners/match calls PartnerService and returns legacy structure."""
    from app.models.contracts import PartnerInfo

    mock_partner = PartnerInfo(
        partner_id="part_test_1",
        name="CSC Jan Seva Kendra",
        type="CSC",
        address="Connaught Place, New Delhi",
        phone="011-23456789",
        distance_km=1.2,
        schemes_served=["mosje_pm_daksh"],
    )

    with patch("app.services.partner_service.PartnerService.get_nearest_partners", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [mock_partner]


        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/partners/match",
                json={
                    "scheme_id": "mosje_pm_daksh",
                    "latitude": 28.61,
                    "longitude": 77.20,
                    "limit": 3,
                },
            )
            assert response.status_code == 200
            assert response.headers.get("X-API-Deprecated") == "true"
            data = response.json()
            assert "partners" in data
            assert len(data["partners"]) == 1
            assert data["partners"][0]["partner_id"] == "part_test_1"

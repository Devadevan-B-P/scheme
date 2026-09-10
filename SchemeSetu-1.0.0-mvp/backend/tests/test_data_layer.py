import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_active_schemes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/schemes")
        assert response.status_code == 200
        schemes = response.json()
        assert len(schemes) >= 4

        # Verify draft schemes are strictly excluded!
        scheme_ids = [s["scheme_id"] for s in schemes]
        assert "nsfdc_term_loan" in scheme_ids
        assert "nskfdc_mahila_samriddhi" in scheme_ids
        assert "draft_pm_daksh_stipend" not in scheme_ids

        # Check that all 5 required provenance fields exist and are populated with official sources
        for s in schemes:
            assert "provenance" in s
            prov = s["provenance"]
            assert prov["source_name"], "Missing source_name"
            assert prov["source_url"] and prov["source_url"].startswith("http"), "Missing or invalid source_url"
            assert prov["source_document"], "Missing source_document"
            assert prov["effective_date"], "Missing effective_date"
            assert prov["last_verified_at"], "Missing last_verified_at"
            assert s["scheme_version"]
            assert s["rule_version"]



@pytest.mark.asyncio
async def test_get_scheme_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/schemes/nsfdc_term_loan")
        assert response.status_code == 200
        scheme = response.json()
        assert scheme["scheme_id"] == "nsfdc_term_loan"
        assert scheme["loan_limits"]["max_amount"] == 4500000.0


@pytest.mark.asyncio
async def test_get_nearest_partners():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query near Lucknow center (26.8467, 80.9462)
        response = await client.get("/api/v1/partners/nearest?lat=26.8467&lng=80.9462&limit=3")
        assert response.status_code == 200
        partners = response.json()
        assert len(partners) <= 3
        assert len(partners) > 0

        # Verify sorted by distance_km
        distances = [p["distance_km"] for p in partners]
        assert distances == sorted(distances)
        assert distances[0] < 10.0  # Lucknow partner should be within 10 km

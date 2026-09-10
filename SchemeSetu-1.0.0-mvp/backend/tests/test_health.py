import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


from app.config import settings


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == settings.PROJECT_NAME
        assert data["gemini_model"] == settings.GEMINI_MODEL
        assert "architecture_tier" in data

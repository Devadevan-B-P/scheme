"""
Legacy Admin Seed Compatibility Adapter.
Protected: Disabled by default, requires X-Admin-Key if enabled.
CLI is the primary seeding mechanism: uv run python -m app.seed.seed_data
"""

from fastapi import APIRouter, Response, Header, HTTPException, status
from typing import Optional

from app.core.config import settings
from app.services.scheme_service import SchemeService
from app.services.partner_service import PartnerService

router = APIRouter(tags=["Legacy Compatibility"])


@router.post("/admin/seed")
async def legacy_admin_seed_adapter(
    response: Response,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
) -> dict:
    """
    Deprecated and protected compatibility endpoint for /admin/seed.
    Disabled outside development. CLI is the primary seeding method.
    """
    deprecation_headers = {
        "X-API-Deprecated": "true",
        "X-API-Deprecation-Notice": "Use CLI: uv run python -m app.seed.seed_data",
    }
    response.headers.update(deprecation_headers)

    if not settings.ENABLE_ADMIN_SEED_ENDPOINT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin seed endpoint is disabled. Use CLI: uv run python -m app.seed.seed_data",
            headers=deprecation_headers,
        )

    if settings.ADMIN_API_KEY and x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header.",
            headers=deprecation_headers,
        )


    schemes_count = await SchemeService.seed_schemes(force=True)
    partners_count = await PartnerService.seed_partners(force=True)

    return {
        "msg": "Seeded successfully via legacy adapter",
        "scheme_count": schemes_count,
        "partner_count": partners_count,
    }

"""
Legacy Partner Matching Compatibility Adapter.
Maps legacy POST /partners/match to unified PartnerService.
"""

from fastapi import APIRouter, Response
from pydantic import BaseModel
from app.services.partner_service import PartnerService

router = APIRouter(tags=["Legacy Compatibility"])


class LegacyPartnerMatchRequest(BaseModel):
    scheme_id: str
    latitude: float
    longitude: float
    limit: int = 3


@router.post("/partners/match")
async def legacy_partners_match_adapter(
    request: LegacyPartnerMatchRequest,
    response: Response,
) -> dict:
    """
    Deprecated compatibility route for /partners/match.
    Adapts to unified PartnerService and returns results with deprecation headers.
    """
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Deprecation-Notice"] = "Use GET /api/v1/partners/nearest"

    nearest = await PartnerService.get_nearest_partners(
        user_lat=request.latitude,
        user_lng=request.longitude,
        scheme_id=request.scheme_id,
        limit=request.limit,
    )

    return {
        "partners": [p.model_dump() for p in nearest],
    }

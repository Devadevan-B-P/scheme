"""
Partners Router — API for discovering nearest SCAs, Banks, and CSCs.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from app.models.partner import Partner
from app.models.contracts import PartnerInfo
from app.services.partner_service import PartnerService

router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("", response_model=List[Partner])
async def list_partners():
    """List all registered channelizing partners."""
    return await PartnerService.get_all_partners()


@router.get("/nearest", response_model=List[PartnerInfo])
async def get_nearest_partners(
    lat: float = Query(..., ge=-90, le=90, description="Applicant latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Applicant longitude"),
    scheme_id: Optional[str] = Query(None, description="Optional scheme_id filter"),
    limit: int = Query(5, ge=1, le=20, description="Max number of partners to return"),
):
    """
    Find nearest active channelizing partners using Haversine distance.
    Returns partner details with distance_km.
    """
    return await PartnerService.get_nearest_partners(
        user_lat=lat,
        user_lng=lng,
        scheme_id=scheme_id,
        limit=limit,
    )

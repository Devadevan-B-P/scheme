"""
Schemes Router — Public API for querying verified MoSJE schemes.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.scheme import Scheme
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=List[Scheme])
async def list_active_schemes():
    """
    List all active verified schemes.
    Draft schemes are strictly excluded from public listing.
    """
    return await SchemeService.get_active_schemes()


@router.get("/{scheme_id}", response_model=Scheme)
async def get_scheme_detail(scheme_id: str):
    """Get full details of a specific scheme including provenance and rules."""
    scheme = await SchemeService.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found",
        )
    return scheme

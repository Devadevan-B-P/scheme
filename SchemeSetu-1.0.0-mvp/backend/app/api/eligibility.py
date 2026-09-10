"""
Eligibility Router — Deterministic rule checking endpoint.
"""

from typing import List
from fastapi import APIRouter
from app.models.contracts import EligibilityResult
from app.models.user import UserProfile
from app.services.scheme_service import SchemeService
from app.engine.eligibility import check_all_schemes

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


@router.post("/check", response_model=List[EligibilityResult])
async def check_eligibility_endpoint(profile: UserProfile):
    """
    Deterministically check applicant profile against all active MoSJE schemes.
    Returns audit-ready EligibilityResult list with passed and failed criteria.
    """
    schemes = await SchemeService.get_active_schemes()
    return check_all_schemes(schemes, profile)

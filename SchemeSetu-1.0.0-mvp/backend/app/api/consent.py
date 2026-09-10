"""
Consent Router — DPDP Act 2023 Compliance API.
"""

from fastapi import APIRouter, Request, HTTPException
from app.models.consent import ConsentRequest, ConsentResponse
from app.services.consent_service import consent_service

router = APIRouter(prefix="/consent", tags=["Consent"])


@router.post("/grant", response_model=ConsentResponse)
async def grant_consent(request: Request, body: ConsentRequest):
    """
    Grant explicit consent for data processing (DPDP Act).
    Records IP and User-Agent.
    """
    try:
        return await consent_service.grant_consent(
            session_id=body.session_id,
            consent_type=body.consent_type,
            request=request,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/withdraw", response_model=ConsentResponse)
async def withdraw_consent(request: Request, body: ConsentRequest):
    """
    Withdraw consent. Instantly deletes ephemeral session PII.
    """
    try:
        return await consent_service.withdraw_consent(
            session_id=body.session_id,
            consent_type=body.consent_type,
            request=request,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=ConsentResponse)
async def get_consent_status(session_id: str, consent_type: str = "global"):
    """
    Get the current consent status for a session.
    """
    try:
        return await consent_service.get_consent_status(
            session_id=session_id,
            consent_type=consent_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

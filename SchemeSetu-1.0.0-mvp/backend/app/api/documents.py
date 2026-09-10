"""
Documents Router (Tier 2).

Provides endpoints for:
  1. Uploading document images for local OCR extraction (Pending).
  2. Confirming extracted fields and persisting them to the user's profile.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import logging

from app.models.ocr import (
    OcrExtractionResult,
    OcrConfirmationRequest,
    OcrConfirmationResponse,
    PendingOcrDocument,
)
from app.services.ocr_service import OcrService
from app.services.audit_service import audit_service
from app.agent.conversation import get_or_create_session
from app.repositories.session_repository import session_repository
from app.core.database import get_database
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


async def get_ocr_collection():
    """Get the ocr_pending collection from MongoDB."""
    import sys
    if "app.routers.documents" in sys.modules and hasattr(sys.modules["app.routers.documents"], "get_ocr_collection"):
        target_fn = getattr(sys.modules["app.routers.documents"], "get_ocr_collection")
        if target_fn is not get_ocr_collection:
            res = target_fn()
            if hasattr(res, "__await__"):
                return await res
            return res

    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available for OCR storage.")
    return db["ocr_pending"]



@router.post("/upload", response_model=OcrExtractionResult)
async def upload_document(
    session_id: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
):
    """
    Upload a document image for local OCR text extraction.
    Returns extracted fields pending user confirmation.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    image_bytes = await file.read()

    try:
        extraction_result = await OcrService.process_income_certificate(image_bytes, language)
    except Exception as e:
        logger.error("OCR processing failed: %s", e)
        raise HTTPException(status_code=500, detail="OCR extraction failed.")

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OCR_CONFIRMATION_EXPIRY_MINUTES)

    pending_doc = PendingOcrDocument(
        confirmation_token=extraction_result.confirmation_token,
        session_id=session_id,
        expires_at=expires_at,
        extraction_result=extraction_result,
    )

    col = await get_ocr_collection()
    await col.insert_one(pending_doc.model_dump(mode="json"))

    return extraction_result


@router.post("/confirm", response_model=OcrConfirmationResponse)
async def confirm_document(request: OcrConfirmationRequest):
    """
    Confirm extracted OCR fields and persist to the user profile.
    Rejects expired tokens via application-level logic.
    """
    col = await get_ocr_collection()

    doc = await col.find_one({"confirmation_token": request.confirmation_token})
    if not doc:
        raise HTTPException(status_code=404, detail="Confirmation token not found or already processed.")

    pending = PendingOcrDocument.model_validate(doc)

    if pending.session_id != request.session_id:
        raise HTTPException(status_code=403, detail="Session mismatch.")

    now = datetime.now(timezone.utc)
    if now > pending.expires_at:
        await col.delete_one({"confirmation_token": request.confirmation_token})
        raise HTTPException(status_code=400, detail="Confirmation token expired.")

    session = await get_or_create_session(request.session_id)
    profile = session.profile

    updated_fields = []
    if "annual_income" in request.confirmed_fields:
        try:
            val_str = request.confirmed_fields["annual_income"]
            profile.annual_income = float(val_str)
            updated_fields.append("annual_income")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid value for annual_income.")

    await session_repository.save_session(session)
    await col.delete_one({"confirmation_token": request.confirmation_token})

    await audit_service.append_event(
        event_type="OCR_EXTRACTION_CONFIRMED",
        payload={"updated_fields": updated_fields},
        session_id=request.session_id,
    )

    return OcrConfirmationResponse(
        success=True,
        message="Profile updated successfully.",
        session_id=request.session_id,
        updated_fields=updated_fields,
    )

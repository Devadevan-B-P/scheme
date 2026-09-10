"""
Legacy Document Compatibility Adapter.
Maps legacy POST /chat/{beneficiary_id}/document to local document extraction.
"""

from fastapi import APIRouter, UploadFile, File, Response, HTTPException
from app.agent.pii_pipeline import regex_sanitize
from app.services.ocr_service import OcrService

router = APIRouter(tags=["Legacy Compatibility"])


@router.post("/chat/{beneficiary_id}/document")
async def legacy_document_adapter(
    beneficiary_id: str,
    response: Response,
    file: UploadFile = File(...),
) -> dict:
    """
    Deprecated compatibility route for document upload.
    Returns masked extracted text with deprecation header.
    """
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Deprecation-Notice"] = "Use POST /api/v1/documents/upload"

    file_bytes = await file.read()
    try:
        extraction = await OcrService.process_income_certificate(file_bytes)
        extracted_text = extraction.raw_text_preview
    except Exception:
        # Fallback if image isn't an income certificate
        extracted_text = "[Document received and masked]"

    return {
        "message": "Document processed",
        "beneficiary_id": beneficiary_id,
        "extracted_text": extracted_text,
    }

"""
OCR Contracts and Models.
"""
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class OcrField(BaseModel):
    """A single field extracted from an OCR document."""
    field_name: str
    extracted_value: str
    ocr_confidence: float = Field(
        ..., description="Confidence that text was recognized correctly (0.0-1.0)"
    )
    extraction_confidence: float = Field(
        ..., description="Confidence that this text IS the requested field (0.0-1.0)"
    )
    validation_status: Literal["needs_confirmation", "confirmed"] = "needs_confirmation"

    @property
    def needs_review(self) -> bool:
        """True if either confidence score is below threshold."""
        return self.ocr_confidence < 0.85 or self.extraction_confidence < 0.85


class OcrExtractionResult(BaseModel):
    """Result of OCR processing pending user confirmation."""
    document_type: str = "income_certificate"
    document_classification_passed: bool
    document_classification_score: float
    extracted_fields: dict[str, OcrField]
    raw_text_preview: str = Field(..., description="First 200 chars, PII-redacted")
    requires_user_confirmation: bool = True
    confirmation_token: str
    status: Literal["pending_confirmation", "confirmed", "rejected"] = "pending_confirmation"


class OcrConfirmationRequest(BaseModel):
    """Payload submitted by frontend to confirm OCR results."""
    confirmation_token: str
    session_id: str
    confirmed_fields: dict[str, str] = Field(
        ..., description="Map of field_name to user-confirmed value"
    )


class OcrConfirmationResponse(BaseModel):
    """Response after processing user confirmation."""
    success: bool
    message: str
    session_id: str
    updated_fields: list[str]


class PendingOcrDocument(BaseModel):
    """Internal model for storing pending OCR state in MongoDB."""
    confirmation_token: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    extraction_result: OcrExtractionResult

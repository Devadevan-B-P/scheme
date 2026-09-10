"""
Tests for OCR Service and Documents Router (Phase 2).
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.ocr import OcrExtractionResult, OcrConfirmationRequest, PendingOcrDocument
from app.services.ocr_service import _score_document_classification, _extract_income_amount, OcrService

# ---------------------------------------------------------------------------
# Unit Tests for Heuristics
# ---------------------------------------------------------------------------

def test_document_classification_score_rejects_non_certificate():
    """Classification gate rejects documents without enough keywords."""
    # A generic grocery receipt
    text = ["Supermarket", "Total Amount", "Rs 500", "Thank you"]
    passed, score = _score_document_classification(text)
    assert not passed
    assert score < 2.0


def test_document_classification_score_accepts_income_certificate():
    """Classification gate accepts valid income certificates."""
    text = ["Government of Uttar Pradesh", "Tehsildar Office", "Income Certificate", "Annual Income is Rs 2,50,000"]
    passed, score = _score_document_classification(text)
    assert passed
    assert score >= 2.0


def test_field_extraction_confidence_separation():
    """Verifies ocr_confidence and extraction_confidence are separated."""
    text = ["Income Certificate", "Annual Income: Rs 2,50,000"]
    confidences = [0.99, 0.95]
    
    result = _extract_income_amount(text, confidences)
    assert result is not None
    val, ocr_conf, ext_conf = result
    
    assert val == "250000"
    assert ocr_conf == 0.95  # Confidence of the specific bounding box
    assert ext_conf == 0.85  # Boosted because 'income' is in the document


def test_field_extraction_low_confidence_without_keywords():
    """Extraction confidence is lower if context keywords are missing."""
    text = ["Some Random Document", "Rs 1,00,000"]
    confidences = [0.99, 0.90]
    
    result = _extract_income_amount(text, confidences)
    assert result is not None
    val, ocr_conf, ext_conf = result
    
    assert val == "100000"
    assert ocr_conf == 0.90
    assert ext_conf == 0.6  # Base confidence without strong context


# ---------------------------------------------------------------------------
# Router / Integration Tests (Mocked)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_paddle_engine():
    """Mocks PaddleOCR engine to avoid loading ML models during tests."""
    with patch("app.services.ocr_service._get_ocr_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def mock_db_collection():
    """Mocks MongoDB collection for pending OCR documents."""
    with patch("app.routers.documents.get_ocr_collection") as mock_get_col:
        mock_col = AsyncMock()
        mock_get_col.return_value = mock_col
        yield mock_col


@pytest.mark.asyncio
async def test_ocr_service_processes_valid_document(mock_paddle_engine):
    """OcrService processes document and returns pending confirmation."""
    # Mock PaddleOCR return format: list of lines, each line is [box, (text, score)]
    mock_paddle_engine.ocr.return_value = [[
        [None, ("Income Certificate", 0.99)],
        [None, ("Annual Income Rs 3,00,000", 0.95)]
    ]]
    
    result = await OcrService.process_income_certificate(b"fake_image_bytes")
    
    assert result.document_type == "income_certificate"
    assert result.document_classification_passed is True
    assert result.requires_user_confirmation is True
    assert "annual_income" in result.extracted_fields
    
    field = result.extracted_fields["annual_income"]
    assert field.extracted_value == "300000"
    assert field.ocr_confidence == 0.95
    assert field.validation_status == "needs_confirmation"


@pytest.mark.asyncio
async def test_confirm_endpoint_app_level_expiry(mock_db_collection):
    """The /confirm endpoint rejects expired tokens explicitly via app logic."""
    from app.routers.documents import confirm_document
    
    # Create an expired pending document
    token = str(uuid.uuid4())
    session_id = "test_session_123"
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    mock_doc = {
        "confirmation_token": token,
        "session_id": session_id,
        "expires_at": expired_time,
        "extraction_result": {
            "document_classification_passed": True,
            "document_classification_score": 3.0,
            "extracted_fields": {},
            "raw_text_preview": "test",
            "requires_user_confirmation": True,
            "confirmation_token": token,
            "status": "pending_confirmation"
        }
    }
    
    mock_db_collection.find_one.return_value = mock_doc
    
    req = OcrConfirmationRequest(
        confirmation_token=token,
        session_id=session_id,
        confirmed_fields={"annual_income": "300000"}
    )
    
    with pytest.raises(Exception) as exc:
        await confirm_document(req)
        
    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()
    
    # Verify it eagerly deletes the expired token
    mock_db_collection.delete_one.assert_called_once_with({"confirmation_token": token})

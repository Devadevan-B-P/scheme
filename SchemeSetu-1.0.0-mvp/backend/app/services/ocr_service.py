"""
OCR Service — Local Document Extraction (Tier 2).

Architecture:
  - PaddleOCR lazy-loaded on demand: Model weights are NEVER loaded at server startup.
  - Runs completely locally. No cloud OCR APIs.
  - Document Classification Gate (score-based heuristic).
  - Field extraction + Confidence split.
  - Returns Pending result (always requires user confirmation).
"""

import logging
import uuid
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from app.models.ocr import OcrExtractionResult, OcrField
from app.agent.pii_pipeline import regex_sanitize
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy singleton instances for supported languages
_ocr_engines: dict[str, Any] = {}

PADDLE_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
}


def _get_ocr_engine(lang: str) -> Optional[Any]:
    """Lazy initialize PaddleOCR only on the first OCR request."""
    paddle_lang = PADDLE_LANG_MAP.get(lang, "en")

    if paddle_lang not in _ocr_engines:
        try:
            from paddleocr import PaddleOCR
            logger.info("Lazy-loading PaddleOCR engine for language: %s", paddle_lang)
            # Suppress verbose paddle logging
            logging.getLogger("ppocr").setLevel(logging.ERROR)
            logging.getLogger("paddle").setLevel(logging.ERROR)
            _ocr_engines[paddle_lang] = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)
        except Exception as e:
            logger.warning("PaddleOCR initialization error (%s). Running in degraded mode.", e)
            return None

    return _ocr_engines.get(paddle_lang)


# ---------------------------------------------------------------------------
# Document Classification Gate (Score-Based)
# ---------------------------------------------------------------------------

INCOME_CERT_KEYWORDS = {
    "income": 1.0,
    "certificate": 1.0,
    "annual": 0.5,
    "rupees": 0.5,
    "tehsildar": 1.0,
    "revenue": 0.8,
    "government": 0.5,
    "office": 0.2,
    "praman": 0.8,  # Hindi for certificate
    "patra": 0.8,
    "aay": 1.0,     # Hindi for income
}


def _score_document_classification(text_blocks: list[str]) -> tuple[bool, float]:
    """
    Score-based classification to ensure the uploaded document is an income certificate.
    Returns: (passed, score)
    """
    full_text = " ".join(text_blocks).lower()
    score = 0.0

    for kw, weight in INCOME_CERT_KEYWORDS.items():
        if kw in full_text:
            score += weight

    threshold = 2.0
    passed = score >= threshold
    return passed, score


# ---------------------------------------------------------------------------
# Field Extraction
# ---------------------------------------------------------------------------

def _extract_income_amount(text_blocks: list[str], confidences: list[float]) -> Optional[tuple[str, float, float]]:
    """
    Heuristic extraction for Annual Income.
    Returns (value, ocr_confidence, extraction_confidence)
    """
    full_text = " ".join(text_blocks).lower()
    match = re.search(r'(?:rs\.?|inr|₹)?\s*([\d,]+)(?:\/-|\.00|\s)?', full_text)

    if not match:
        return None

    extracted_val = match.group(1).replace(",", "")

    try:
        float(extracted_val)
    except ValueError:
        return None

    ocr_conf = 0.5
    for block, conf in zip(text_blocks, confidences):
        if match.group(1) in block:
            ocr_conf = conf
            break

    ext_conf = 0.6
    if "income" in full_text or "aay" in full_text:
        ext_conf = 0.85

    return extracted_val, ocr_conf, ext_conf


# ---------------------------------------------------------------------------
# OCR Service
# ---------------------------------------------------------------------------

class OcrService:
    @staticmethod
    async def process_income_certificate(
        image_bytes: bytes,
        language: str = "en"
    ) -> OcrExtractionResult:
        """
        Extract text and fields from an income certificate image entirely locally.
        PaddleOCR is lazy-loaded on the first invocation.
        """
        engine = _get_ocr_engine(language)
        if not engine:
            raise RuntimeError("OCR Engine (PaddleOCR) is not available.")

        try:
            result = engine.ocr(image_bytes, cls=True)
        except Exception as e:
            logger.error("PaddleOCR processing failed: %s", e)
            raise RuntimeError("Failed to process image with OCR engine.")

        text_blocks = []
        confidences = []

        if result and len(result) > 0 and result[0] is not None:
            for line in result[0]:
                if len(line) == 2:
                    _, (text, score) = line
                    text_blocks.append(text)
                    confidences.append(score)

        classification_passed, classification_score = _score_document_classification(text_blocks)
        raw_text = " ".join(text_blocks)
        preview = regex_sanitize(raw_text[:300]) + ("..." if len(raw_text) > 300 else "")

        extracted_fields = {}
        if classification_passed:
            income_result = _extract_income_amount(text_blocks, confidences)
            if income_result:
                val, ocr_conf, ext_conf = income_result
                extracted_fields["annual_income"] = OcrField(
                    field_name="annual_income",
                    extracted_value=val,
                    ocr_confidence=ocr_conf,
                    extraction_confidence=ext_conf,
                    validation_status="needs_confirmation"
                )

        token = str(uuid.uuid4())

        return OcrExtractionResult(
            document_type="income_certificate",
            document_classification_passed=classification_passed,
            document_classification_score=classification_score,
            extracted_fields=extracted_fields,
            raw_text_preview=preview,
            requires_user_confirmation=True,
            confirmation_token=token,
            status="pending_confirmation"
        )


async def process_document(file_bytes: bytes) -> str:
    """
    Run OCR on raw document bytes and return PII-masked plain text string.
    Used by pdf_extractor for scanned PDFs.
    """
    try:
        import cv2
        import numpy as np
        from app.services.privacy import mask_pii

        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return ""

        engine = _get_ocr_engine("en")
        if not engine:
            return ""

        result = engine.ocr(img, cls=True)
        if not result or not result[0]:
            return ""

        lines = [line[1][0] for line in result[0] if line and len(line) > 1]
        raw_text = "\n".join(lines)
        return mask_pii(raw_text)
    except Exception as exc:
        logger.warning("Error in process_document OCR helper: %s", exc)
        return ""


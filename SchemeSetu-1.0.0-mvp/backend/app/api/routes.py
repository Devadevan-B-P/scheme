"""
API routes for SchemeSetu.

Exposes:
  POST /admin/seed          — seed the DB with a sample scheme
  POST /chat/{beneficiary_id} — conversational intake + eligibility evaluation
"""

from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models.beneficiary import BeneficiaryProfile
from app.models.scheme import Scheme
from app.models.eligibility import EligibilityRule, EligibilityResult, ReasonCode
from app.services.ai_extractor import extract_entities_from_message
from app.services.rule_engine import evaluate_eligibility
from app.services.ai_responder import generate_conversational_reply
from app.services.ocr_service import process_document
from app.services.privacy import mask_pii

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


# ── Hardcoded demo rules (no DB yet) ─────────────────────────────────────────

def _build_demo_rules(scheme_id: str) -> list[EligibilityRule]:
    """Return a minimal set of demo eligibility rules for testing."""
    return [
        EligibilityRule(
            rule_id="R001",
            scheme_id=scheme_id,
            field="annual_income",
            operator="<=",
            value=800_000.0,
            reason_code_on_fail=ReasonCode.INCOME_EXCEEDED,
        ),
        EligibilityRule(
            rule_id="R002",
            scheme_id=scheme_id,
            field="category",
            operator="in",
            value=["sc", "st", "obc", "ews"],
            reason_code_on_fail=ReasonCode.CATEGORY_NOT_ELIGIBLE,
        ),
        EligibilityRule(
            rule_id="R003",
            scheme_id=scheme_id,
            field="age",
            operator=">=",
            value=18,
            reason_code_on_fail=ReasonCode.RULE_VIOLATED_OTHER,
        ),
    ]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/admin/seed")
async def seed_schemes() -> dict:
    """
    Seed the database with a sample scheme for development / testing.
    Idempotent: returns early if schemes already exist.
    """
    count = await Scheme.find_all().count()
    if count > 0:
        return {"msg": "Already seeded", "scheme_count": count}

    scheme = Scheme(
        scheme_id="MOSJEBIZ-001",
        name="MoSJE Business Loan",
        ministry="Ministry of Social Justice and Empowerment",
        category_eligibility=["sc", "st", "obc", "ews"],
        income_ceiling=800_000.0,
        project_cost_range={"min": 50_000.0, "max": 1_000_000.0},
        loan_limit=500_000.0,
        subsidy_pct=25.0,
        margin_money_pct=5.0,
        interest_rate_range={"min": 6.0, "max": 9.0},
        tenure_months=60,
        moratorium_months=6,
        required_documents=["aadhaar", "pan", "income_certificate", "caste_certificate"],
        rule_version="1.0.0",
        last_updated=datetime.now(timezone.utc),
        source_url="https://socialjustice.gov.in/schemes",
    )
    await scheme.insert()

    demo_rules = _build_demo_rules(scheme.scheme_id)

    return {
        "msg": "Seeded successfully",
        "scheme_id": scheme.scheme_id,
        "scheme_name": scheme.name,
        "demo_rules": [r.model_dump() for r in demo_rules],
    }


@router.post("/chat/{beneficiary_id}")
async def chat(beneficiary_id: str, request: ChatRequest) -> dict:
    """
    Core conversational intake endpoint.

    1. Fetch or create the beneficiary profile.
    2. Extract entities from the user message via Gemini.
    3. Merge extracted fields into the profile and persist.
    4. Run the eligibility rule engine against all known schemes.
    5. Return the updated profile + eligibility results.
    """
    # Accept a valid UUID string, or generate a deterministic uuid5 from
    # any arbitrary string (e.g. "test-user-123") so development testing
    # works without pre-generating a UUID.
    try:
        ben_uuid = UUID(beneficiary_id)
    except ValueError:
        ben_uuid = uuid5(NAMESPACE_URL, beneficiary_id)

    profile = await BeneficiaryProfile.find_one(
        BeneficiaryProfile.beneficiary_id == ben_uuid
    )

    if profile is None:
        profile = BeneficiaryProfile(beneficiary_id=ben_uuid)
        await profile.insert()

    # ── Immediately sanitize incoming text for PII masking ──────────────────
    sanitized_message = mask_pii(request.message)

    # ── 2. Extract entities from message ─────────────────────────────────────
    extraction = await extract_entities_from_message(
        user_message=sanitized_message,
        current_state=profile.model_dump(mode="json", exclude_none=True),
    )
    # ── 3. Merge non-None extracted fields into the profile ───────────────────
    extracted = extraction.model_dump(exclude_none=True)
    # Remove beneficiary_id — never overwrite the identity field from extraction
    extracted.pop("beneficiary_id", None)

    for field, value in extracted.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)

    # Recalculate completeness: count non-None fields out of the 12 tracked fields
    tracked = [
        "channel", "language", "category", "gender", "age",
        "location", "annual_income", "education_level",
        "business_type", "project_cost", "loan_required",
    ]
    filled = sum(1 for f in tracked if getattr(profile, f) is not None)
    profile.profile_completeness_pct = round((filled / len(tracked)) * 100)

    await profile.save()

    # ── 4. Evaluate eligibility against all schemes ───────────────────────────
    schemes = await Scheme.find_all().to_list()

    eligibility_results: list[dict] = []
    for scheme in schemes:
        rules = _build_demo_rules(scheme.scheme_id)
        result: EligibilityResult = evaluate_eligibility(profile, scheme, rules)
        eligibility_results.append(result.model_dump())

    # ── 5. Generate conversational reply ──────────────────────────────────────
    reply_text = await generate_conversational_reply(
        user_message=sanitized_message,
        profile_state=profile.model_dump(mode="json", exclude={"id"}),
        eligibility_results=eligibility_results
    )

    # ── 6. Return response ────────────────────────────────────────────────────
    return {
        "reply": reply_text,
        "beneficiary_id": str(profile.beneficiary_id),
        "profile_completeness_pct": profile.profile_completeness_pct,
        "extracted_this_turn": extracted,
        "profile": profile.model_dump(mode="json", exclude={"id"}),
        "eligibility_results": eligibility_results,
    }

@router.post("/chat/{beneficiary_id}/document")
async def upload_document(beneficiary_id: str, file: UploadFile = File(...)):
    """
    Upload a document (e.g. Aadhaar card) for OCR processing and PII masking.
    Currently returns the masked text directly.
    """
    file_bytes = await file.read()
    
    # Process the document with OCR and mask PII
    masked_text = await process_document(file_bytes)
    
    return {
        "message": "Document processed",
        "extracted_text": masked_text
    }

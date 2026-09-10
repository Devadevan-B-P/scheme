"""
Conversational Orchestrator.

Implements the central Two-Tiered Reasoning Workflow:
  1. Privacy Layer: Redacts PII before context touches Gemini or history.
  2. Gemini Agent: Extracts structured entities and language intent only.
  3. Deterministic Engine: Evaluates scheme eligibility without AI hallucination.
  4. Next-Best-Question Discriminator: Selects the single best question when info is missing.
  5. Financial Simulator: Computes EMI, subsidy, and margin money on eligible outcomes.
  6. Partner Routing: Attaches nearest active SCAs/Banks/CSCs (no dead ends).
"""

import uuid
from typing import Optional
from app.models.contracts import (
    ChatRequest,
    ChatResponse,
    Decision,
    FinancialSummary,
    PartnerInfo,
)
from app.models.user import (
    UserSession,
    ConversationMessage,
    ConversationRole,
)
from app.agent.pii_pipeline import sanitize_text_pipeline
from app.agent.gemini_client import gemini_agent
from app.services.scheme_service import SchemeService
from app.services.partner_service import PartnerService
from app.repositories.session_repository import session_repository
from app.engine.eligibility import check_all_schemes, select_next_question
from app.engine.financial import generate_financial_summary


async def get_or_create_session(session_id: Optional[str], language: str = "en") -> UserSession:
    """Retrieve existing session from repository or instantiate a new one."""
    if session_id:
        existing = await session_repository.get_session(session_id)
        if existing:
            return existing

    new_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
    session = UserSession(session_id=new_id, language=language)
    await session_repository.save_session(session)
    return session


async def handle_chat_message(request: ChatRequest) -> ChatResponse:
    """
    Core conversational turn handler.
    """
    session = await get_or_create_session(request.session_id, request.language)

    # Step 1: Privacy Sanitization (two-pass: regex + DLP)
    sanitized_context = await sanitize_text_pipeline(request.message)
    sanitized_input = sanitized_context.sanitized_text

    # Store sanitized message in conversation history
    session.conversation_history.append(
        ConversationMessage(
            role=ConversationRole.USER,
            content=sanitized_input,
            language=request.language,
        )
    )

    # Step 2: Gemini Entity Extraction
    extracted = await gemini_agent.extract_entities(
        sanitized_user_message=sanitized_input,
        conversation_history=session.conversation_history,
        target_language=request.language,
    )

    # Step 3: Update Profile
    profile = session.profile
    if extracted.age is not None:
        profile.age = extracted.age
    if extracted.annual_income is not None:
        profile.annual_income = extracted.annual_income
    if extracted.category is not None:
        profile.category = extracted.category
    if extracted.gender is not None:
        profile.gender = extracted.gender
    if extracted.business_type is not None:
        profile.business_type = extracted.business_type
    if extracted.location is not None:
        profile.location = extracted.location
    if extracted.state is not None:
        profile.state = extracted.state
    if extracted.disability_status is not None:
        profile.disability_status = extracted.disability_status

    # Step 4: Deterministic Eligibility Evaluation
    active_schemes = await SchemeService.get_active_schemes()
    eligibility_results = check_all_schemes(active_schemes, profile)

    candidates_missing = [r for r in eligibility_results if r.decision == Decision.MISSING_INFORMATION]
    eligible_schemes = [r for r in eligibility_results if r.decision == Decision.ELIGIBLE]
    ineligible_schemes = [r for r in eligibility_results if r.decision == Decision.INELIGIBLE]

    response_text = ""
    financial_summaries: Optional[list[FinancialSummary]] = None
    partner_list: Optional[list[PartnerInfo]] = None

    # Step 5: Orchestrate Response Based on State
    if candidates_missing and len(eligible_schemes) == 0:
        winning_next_question = select_next_question(eligibility_results)
        ack = extracted.friendly_acknowledgment or "Got it."
        response_text = f"{ack} {winning_next_question}"

    elif len(eligible_schemes) > 0:
        financial_summaries = []
        for el in eligible_schemes:
            scheme_obj = next((s for s in active_schemes if s.scheme_id == el.scheme_id), None)
            if scheme_obj:
                fin = generate_financial_summary(scheme_obj)
                financial_summaries.append(fin)

        user_lat = profile.latitude or 26.8467
        user_lng = profile.longitude or 80.9462
        first_eligible_id = eligible_schemes[0].scheme_id
        partner_list = await PartnerService.get_nearest_partners(
            user_lat=user_lat,
            user_lng=user_lng,
            scheme_id=first_eligible_id,
            limit=3,
        )

        scheme_names = ", ".join([el.scheme_id.replace("_", " ").upper() for el in eligible_schemes])
        response_text = (
            f"Great news! Based on your verified details, you qualify for {len(eligible_schemes)} government scheme(s): "
            f"{scheme_names}. We have calculated your EMI, subsidy, and identified your nearest channelizing partner branch."
        )

    else:
        user_lat = profile.latitude or 26.8467
        user_lng = profile.longitude or 80.9462
        partner_list = await PartnerService.get_nearest_partners(
            user_lat=user_lat,
            user_lng=user_lng,
            limit=2,
        )

        reasons = []
        for inel in ineligible_schemes:
            for f in inel.failed_rules:
                if f.explanation:
                    reasons.append(f.explanation)

        distinct_reasons = list(dict.fromkeys(reasons))[:2]
        reasons_summary = " ".join(distinct_reasons)

        response_text = (
            f"We evaluated the standard central MoSJE schemes against your profile. "
            f"Currently, you do not meet the specific criteria: {reasons_summary} "
            f"Do not worry! We have mapped you to the nearest Common Service Centre (CSC) "
            f"where an assisted operator can guide you to alternative state schemes or special exemption categories."
        )

    # Store assistant response in sanitized conversation history
    session.conversation_history.append(
        ConversationMessage(
            role=ConversationRole.ASSISTANT,
            content=response_text,
            language=request.language,
        )
    )

    await session_repository.save_session(session)

    extracted_dict = {
        k: v for k, v in extracted.model_dump().items()
        if v is not None and k not in ("language", "friendly_acknowledgment")
    }

    return ChatResponse(
        session_id=session.session_id,
        response_text=response_text,
        language=request.language,
        extracted_entities=extracted_dict,
        profile_completeness=profile.completeness(),
        extraction_mode=extracted.extraction_mode,
        sanitizer_mode=sanitized_context.sanitizer_mode,
        eligibility_results=eligibility_results,
        financial_summaries=financial_summaries,
        partner_list=partner_list,
    )

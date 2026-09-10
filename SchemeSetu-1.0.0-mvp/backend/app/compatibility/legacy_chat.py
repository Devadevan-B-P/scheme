"""
Legacy Chat Compatibility Adapter.
Maps legacy POST /chat/{beneficiary_id} to unified ChatService.

DIRECTIVE: beneficiary_id is strictly treated as an unauthenticated
session/correlation identifier, not an authenticated user identity.
"""

from fastapi import APIRouter, Response
from pydantic import BaseModel
from app.models.contracts import ChatRequest
from app.services.chat_service import chat_service

router = APIRouter(tags=["Legacy Compatibility"])


class LegacyChatRequest(BaseModel):
    message: str


@router.post("/chat/{beneficiary_id}")
async def legacy_chat_adapter(
    beneficiary_id: str,
    request: LegacyChatRequest,
    response: Response,
) -> dict:
    """
    Deprecated compatibility route for /chat/{beneficiary_id}.
    Adapts legacy payload to unified ChatService and returns expected legacy envelope.
    """
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Deprecation-Notice"] = "Use POST /api/v1/chat with {message, session_id}"

    # Treat beneficiary_id strictly as correlation / session identifier
    modern_request = ChatRequest(
        session_id=beneficiary_id,
        message=request.message,
        language="en",
    )

    chat_resp = await chat_service.process_chat_turn(modern_request)

    # Convert to legacy response shape
    return {
        "reply": chat_resp.response_text,
        "beneficiary_id": beneficiary_id,
        "profile_completeness_pct": round(chat_resp.profile_completeness * 100),
        "extracted_this_turn": chat_resp.extracted_entities,
        "eligibility_results": [
            res.model_dump() for res in (chat_resp.eligibility_results or [])
        ],
    }

"""
Chat Router — Primary conversational interface endpoint.
"""

from fastapi import APIRouter
from app.models.contracts import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.agent.conversation import get_or_create_session
from app.models.user import UserSession

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Multilingual conversational intake & reasoning endpoint.
    Performs PII redaction, entity extraction, deterministic eligibility evaluation,
    and returns conversational responses with full financial & partner context.
    """
    return await chat_service.process_chat_turn(request)


@router.get("/session/{session_id}", response_model=UserSession)
async def get_session_endpoint(session_id: str):
    """Get active session details including sanitized conversation history and profile."""
    return await get_or_create_session(session_id)

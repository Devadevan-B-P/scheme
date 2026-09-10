"""
Chat Service — Orchestrator for conversational turns.
Encapsulates intake, sanitization, entity extraction, rule evaluation,
financial summaries, and partner recommendations.
"""

import logging
from app.models.contracts import ChatRequest, ChatResponse
from app.agent.conversation import handle_chat_message

logger = logging.getLogger(__name__)


class ChatService:
    @staticmethod
    async def process_chat_turn(request: ChatRequest) -> ChatResponse:
        """
        Execute a conversational turn and return full ChatResponse contract.
        """
        return await handle_chat_message(request)


chat_service = ChatService()

"""
Consent Service — DPDP Act 2023 Compliance.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request
from pymongo.collection import ReturnDocument

from app.core.database import get_database
from app.models.consent import ConsentRecord, ConsentResponse
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


class ConsentService:
    async def grant_consent(self, session_id: str, consent_type: str, request: Optional[Request] = None) -> ConsentResponse:
        """Grant consent for data processing."""
        db = get_database()
        if db is None:
            raise RuntimeError("Database connection not initialized")

        col = db["consents"]
        now = datetime.now(timezone.utc).isoformat()

        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        record = await col.find_one_and_update(
            {"session_id": session_id, "consent_type": consent_type},
            {"$set": {
                "status": "granted",
                "granted_at": now,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "withdrawn_at": None,
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        await audit_service.append_event(
            event_type="CONSENT_GRANTED",
            payload={"consent_type": consent_type, "ip_address": ip_address},
            session_id=session_id,
        )

        logger.info("Consent granted for session %s (type: %s)", session_id, consent_type)
        return ConsentResponse(**record)

    async def withdraw_consent(self, session_id: str, consent_type: str, request: Optional[Request] = None) -> ConsentResponse:
        """Withdraw consent and trigger PII cleanup."""
        db = get_database()
        if db is None:
            raise RuntimeError("Database connection not initialized")

        col = db["consents"]
        now = datetime.now(timezone.utc).isoformat()

        ip_address = request.client.host if request and request.client else None

        record = await col.find_one_and_update(
            {"session_id": session_id, "consent_type": consent_type},
            {"$set": {
                "status": "withdrawn",
                "withdrawn_at": now,
                "ip_address": ip_address,
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        # Truncate session memory due to withdrawn consent (DPDP Act requirement)
        sessions_col = db["sessions"]
        await sessions_col.update_one(
            {"session_id": session_id},
            {"$set": {"conversation_history": [], "profile": {}, "withdrawn": True}},
        )

        await audit_service.append_event(
            event_type="CONSENT_WITHDRAWN",
            payload={"consent_type": consent_type, "action": "deleted_session_pii", "ip_address": ip_address},
            session_id=session_id,
        )

        logger.info("Consent withdrawn for session %s (type: %s). Memory cleared.", session_id, consent_type)
        return ConsentResponse(**record)

    async def get_consent_status(self, session_id: str, consent_type: str = "global") -> ConsentResponse:
        """Check current consent status."""
        db = get_database()
        if db is None:
            raise RuntimeError("Database connection not initialized")

        col = db["consents"]
        record = await col.find_one({"session_id": session_id, "consent_type": consent_type})

        if not record:
            return ConsentResponse(session_id=session_id, status="pending")

        return ConsentResponse(**record)


consent_service = ConsentService()

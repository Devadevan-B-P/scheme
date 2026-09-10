"""
Session Repository — Data Access Layer for User Sessions.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timezone
from app.core.database import get_database
from app.models.user import UserSession

logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self):
        self.collection_name = "sessions"
        # In-memory store for fast fallback or offline test mode
        self.memory_store: Dict[str, UserSession] = {}

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Fetch session from memory or MongoDB."""
        if session_id in self.memory_store:
            return self.memory_store[session_id]

        db = get_database()
        if db is not None:
            try:
                doc = await db[self.collection_name].find_one({"session_id": session_id})
                if doc:
                    doc.pop("_id", None)
                    session = UserSession.model_validate(doc)
                    self.memory_store[session_id] = session
                    return session
            except Exception as err:
                logger.warning("Error fetching session %s from DB: %s", session_id, err)

        return None

    async def save_session(self, session: UserSession) -> None:
        """Persist session state to memory and MongoDB."""
        session.updated_at = datetime.now(timezone.utc)
        self.memory_store[session.session_id] = session

        db = get_database()
        if db is not None:
            try:
                await db[self.collection_name].replace_one(
                    {"session_id": session.session_id},
                    session.model_dump(mode="json"),
                    upsert=True,
                )
            except Exception as err:
                logger.warning("Error saving session %s to DB: %s", session.session_id, err)


session_repository = SessionRepository()

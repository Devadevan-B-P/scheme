"""
Consent Repository — Data Access Layer for User Consents (DPDP Act 2023).
"""

import logging
from typing import Optional
from app.core.database import get_database
from app.models.consent import ConsentRecord

logger = logging.getLogger(__name__)


class ConsentRepository:
    def __init__(self):
        self.collection_name = "consent_records"

    async def get_by_session_id(self, session_id: str) -> Optional[ConsentRecord]:
        """Fetch active consent record for session."""
        db = get_database()
        if db is None:
            return None

        doc = await db[self.collection_name].find_one({"session_id": session_id})
        if doc:
            doc.pop("_id", None)
            return ConsentRecord.model_validate(doc)
        return None

    async def save_consent(self, record: ConsentRecord) -> None:
        """Upsert consent record."""
        db = get_database()
        if db is None:
            return

        await db[self.collection_name].replace_one(
            {"session_id": record.session_id},
            record.model_dump(),
            upsert=True,
        )


consent_repository = ConsentRepository()

"""
Scheme Repository — Data Access Layer for Schemes.
"""

import logging
from typing import List, Optional
from app.core.database import get_database
from app.models.scheme import Scheme, SchemeStatus

logger = logging.getLogger(__name__)


class SchemeRepository:
    def __init__(self):
        self.collection_name = "schemes"

    async def get_active_schemes(self) -> List[Scheme]:
        """Fetch all active schemes excluding draft/suspended ones."""
        db = get_database()
        if db is None:
            return []

        cursor = db[self.collection_name].find({"status": SchemeStatus.ACTIVE.value})
        schemes = []
        async for doc in cursor:
            doc.pop("_id", None)
            schemes.append(Scheme.model_validate(doc))
        return schemes

    async def get_all_schemes(self) -> List[Scheme]:
        """Fetch all schemes in database."""
        db = get_database()
        if db is None:
            return []

        cursor = db[self.collection_name].find({})
        schemes = []
        async for doc in cursor:
            doc.pop("_id", None)
            schemes.append(Scheme.model_validate(doc))
        return schemes

    async def get_by_id(self, scheme_id: str) -> Optional[Scheme]:
        """Fetch single scheme by ID."""
        db = get_database()
        if db is None:
            return None

        doc = await db[self.collection_name].find_one({"scheme_id": scheme_id})
        if doc:
            doc.pop("_id", None)
            return Scheme.model_validate(doc)
        return None

    async def upsert_scheme(self, scheme: Scheme) -> None:
        """Upsert scheme by scheme_id."""
        db = get_database()
        if db is None:
            return

        doc = scheme.model_dump(mode="json")
        await db[self.collection_name].replace_one(
            {"scheme_id": scheme.scheme_id},
            doc,
            upsert=True,
        )

    async def count(self) -> int:
        """Count total schemes."""
        db = get_database()
        if db is None:
            return 0
        return await db[self.collection_name].count_documents({})


scheme_repository = SchemeRepository()

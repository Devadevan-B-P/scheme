"""
Partner Repository — Data Access Layer for Channel Partners (SCAs, Banks, CSCs).
"""

import logging
from typing import List, Optional, Dict, Any
from app.core.database import get_database
from app.models.partner import Partner

logger = logging.getLogger(__name__)


class PartnerRepository:
    def __init__(self):
        self.collection_name = "partners"

    async def get_all_active_partners(self) -> List[Partner]:
        """Fetch all active partners."""
        db = get_database()
        if db is None:
            return []

        cursor = db[self.collection_name].find({"active": True})
        partners = []
        async for doc in cursor:
            doc.pop("_id", None)
            partners.append(Partner.model_validate(doc))
        return partners

    async def get_candidate_partners(self, scheme_id: Optional[str] = None) -> List[Partner]:
        """Fetch candidate partners compatible with scheme_id if given."""
        db = get_database()
        if db is None:
            return []

        query: Dict[str, Any] = {"active": True}
        if scheme_id:
            query["schemes_served"] = scheme_id

        cursor = db[self.collection_name].find(query)
        partners = []
        async for doc in cursor:
            doc.pop("_id", None)
            partners.append(Partner.model_validate(doc))
        return partners

    async def upsert_partner(self, partner: Partner) -> None:
        """Upsert partner with location GeoJSON point."""
        db = get_database()
        if db is None:
            return

        doc = partner.model_dump(mode="json")
        doc["location"] = {
            "type": "Point",
            "coordinates": [partner.longitude, partner.latitude],
        }

        await db[self.collection_name].replace_one(
            {"partner_id": partner.partner_id},
            doc,
            upsert=True,
        )

    async def count(self) -> int:
        """Count total partners."""
        db = get_database()
        if db is None:
            return 0
        return await db[self.collection_name].count_documents({})


partner_repository = PartnerRepository()

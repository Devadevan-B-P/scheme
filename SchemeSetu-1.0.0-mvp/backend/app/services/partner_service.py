"""
Partner Service — Channelizing agency (SCA/Bank/CSC) search & routing.
Uses Haversine distance with partner_repository.
"""

from typing import List, Optional
from app.models.partner import Partner
from app.models.contracts import PartnerInfo
from app.routing.haversine import haversine_distance
from app.repositories.partner_repository import partner_repository


class PartnerService:
    @staticmethod
    async def get_all_partners() -> List[Partner]:
        """Fetch all registered active partners."""
        partners = await partner_repository.get_all_active_partners()
        if partners:
            return partners

        from app.seed.seed_data import VERIFIED_PARTNERS
        return [p for p in VERIFIED_PARTNERS if p.active]

    @staticmethod
    async def get_nearest_partners(
        user_lat: float,
        user_lng: float,
        scheme_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[PartnerInfo]:
        """
        Find nearest active channelizing partners using Haversine distance.
        Filters by served scheme if specified.
        """
        partners = await PartnerService.get_all_partners()

        results: list[PartnerInfo] = []
        for p in partners:
            if scheme_id and scheme_id not in p.schemes_served:
                continue

            dist = haversine_distance(user_lat, user_lng, p.latitude, p.longitude)
            results.append(
                PartnerInfo(
                    partner_id=p.partner_id,
                    name=p.name,
                    type=p.type.value if hasattr(p.type, "value") else str(p.type),
                    address=p.address,
                    phone=p.phone,
                    distance_km=dist,
                    schemes_served=p.schemes_served,
                )
            )

        results.sort(key=lambda x: x.distance_km)
        return results[:limit]

    @staticmethod
    async def seed_partners(force: bool = False) -> int:
        """Seed verified partners into MongoDB."""
        from app.seed.seed_data import VERIFIED_PARTNERS
        count = await partner_repository.count()
        if count == 0 or force:
            for p in VERIFIED_PARTNERS:
                await partner_repository.upsert_partner(p)
            return len(VERIFIED_PARTNERS)
        return count


partner_service = PartnerService()

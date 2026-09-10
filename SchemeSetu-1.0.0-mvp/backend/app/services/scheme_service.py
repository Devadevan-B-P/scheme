"""
Scheme Service — Data retrieval for verified government schemes.
Enforces workflow constraint: Draft schemes are strictly excluded from eligibility matching.
"""

from typing import Optional, List
from app.models.scheme import Scheme, SchemeStatus
from app.repositories.scheme_repository import scheme_repository


class SchemeService:
    @staticmethod
    async def get_active_schemes() -> List[Scheme]:
        """
        Return all active verified schemes from repository.
        Draft schemes are excluded from eligibility matching.
        """
        schemes = await scheme_repository.get_active_schemes()
        if schemes:
            return schemes

        # Fallback to verified in-memory seed dataset if DB is offline
        from app.seed.seed_data import VERIFIED_SCHEMES
        return [s for s in VERIFIED_SCHEMES if s.status == SchemeStatus.ACTIVE]

    @staticmethod
    async def get_all_schemes() -> List[Scheme]:
        """Fetch all schemes."""
        schemes = await scheme_repository.get_all_schemes()
        if schemes:
            return schemes

        from app.seed.seed_data import VERIFIED_SCHEMES
        return VERIFIED_SCHEMES

    @staticmethod
    async def get_scheme_by_id(scheme_id: str) -> Optional[Scheme]:
        """Fetch a specific scheme by ID."""
        scheme = await scheme_repository.get_by_id(scheme_id)
        if scheme:
            return scheme

        from app.seed.seed_data import VERIFIED_SCHEMES
        for s in VERIFIED_SCHEMES:
            if s.scheme_id == scheme_id:
                return s
        return None

    @staticmethod
    async def seed_schemes(force: bool = False) -> int:
        """Seed verified schemes into MongoDB."""
        from app.seed.seed_data import VERIFIED_SCHEMES
        count = await scheme_repository.count()
        if count == 0 or force:
            for s in VERIFIED_SCHEMES:
                await scheme_repository.upsert_scheme(s)
            return len(VERIFIED_SCHEMES)
        return count


scheme_service = SchemeService()

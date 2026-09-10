"""
Beanie document model for a beneficiary profile.
"""

from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field


class BeneficiaryProfile(Document):
    """
    Represents a beneficiary's profile collected via the conversational intake flow.
    Stored as a single document in the `beneficiary_profiles` MongoDB collection.
    """

    beneficiary_id: UUID = Field(default_factory=uuid4)
    channel: str | None = None          # e.g., "whatsapp", "web", "ivr"
    language: str | None = None         # e.g., "en", "hi", "mr"
    category: str | None = None         # e.g., "sc", "st", "obc", "general"
    gender: str | None = None           # e.g., "male", "female", "other"
    age: int | None = None
    location: dict | None = None        # {"state": ..., "district": ..., "pincode": ...}
    annual_income: float | None = None
    education_level: str | None = None  # e.g., "illiterate", "primary", "graduate"
    disability_status: bool = False
    business_type: str | None = None    # e.g., "manufacturing", "service", "trading"
    project_cost: float | None = None
    loan_required: float | None = None
    documents: list[dict] = Field(default_factory=list)
    # Each dict expected shape: {"type": str, "status": str, "ocr_confidence": float}
    profile_completeness_pct: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "beneficiary_profiles"

"""
User profile and session models.

PRIVACY DIRECTIVE:
  - UserProfile stores only demographic/business facts needed for scheme matching:
    (age, annual_income, category, gender, business_type, location, state, etc.)
  - High-risk PII (Aadhaar, PAN, phone, bank account) is NEVER stored in UserProfile
    or in conversation_history.
  - UserSession.conversation_history stores the SANITIZED version of messages only.
  - Retention: Absolute 24 hours. expires_at is set to created_at + 24 hours.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from uuid import UUID, uuid4
from beanie import Document
from pydantic import BaseModel, Field


class User(Document):
    """
    Represents a registered beneficiary user in the MongoDB database.
    """

    user_id: UUID = Field(default_factory=uuid4)
    email: str
    password_hash: str
    full_name: str
    phone_number: str | None = None
    category: str = "SC"
    state: str = "Kerala"
    district: str = "Thiruvananthapuram"
    role: str = "beneficiary"  # 'beneficiary' | 'admin'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """
    A single message in conversation history.
    Content is ALWAYS the sanitized version.
    """
    role: ConversationRole
    content: str = Field(
        ...,
        description="SANITIZED message content. PII patterns replaced with "
        "[AADHAAR_REDACTED], [PAN_REDACTED], [PHONE_REDACTED], [ACCOUNT_REDACTED].",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = Field(default="en")


class UserProfile(BaseModel):
    """
    The beneficiary profile, built incrementally through conversation.
    Demographic & financial eligibility attributes only.
    """
    age: Optional[int] = Field(None, ge=0, le=120)
    annual_income: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(
        None, description="SC, ST, OBC, General, etc."
    )
    gender: Optional[str] = Field(None, description="Male, Female, Other")
    business_type: Optional[str] = Field(
        None, description="Type of business/activity the user wants to start or runs"
    )
    location: Optional[str] = Field(None, description="City or district name")
    state: Optional[str] = Field(None, description="Indian state or UT")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    disability_status: Optional[bool] = Field(None)
    education: Optional[str] = Field(None)
    existing_business: Optional[bool] = Field(None)

    def filled_fields(self) -> list[str]:
        """Return names of fields that have values."""
        return [
            name
            for name, value in self.model_dump().items()
            if value is not None
        ]

    def missing_fields(self) -> list[str]:
        """Return names of fields that are still None."""
        engine_fields = [
            "age", "annual_income", "category", "gender",
            "business_type", "location", "state",
        ]
        return [
            name for name in engine_fields
            if getattr(self, name) is None
        ]

    def completeness(self) -> float:
        """Return 0.0-1.0 indicating how complete the profile is."""
        engine_fields = [
            "age", "annual_income", "category", "gender",
            "business_type", "location", "state",
        ]
        filled = sum(1 for f in engine_fields if getattr(self, f) is not None)
        return filled / len(engine_fields) if engine_fields else 0.0


def default_expiry() -> datetime:
    """Default absolute expiration 24 hours from creation."""
    return datetime.now(timezone.utc) + timedelta(hours=24)


class UserSession(BaseModel):
    """
    Tracks a beneficiary's conversation session.
    Features absolute 24-hour retention via expires_at TTL.
    """
    session_id: str
    profile: UserProfile = Field(default_factory=UserProfile)
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
        description="SANITIZED conversation messages. Raw PII never stored here.",
    )
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=default_expiry)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

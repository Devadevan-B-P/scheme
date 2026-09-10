"""
Partner model — SCA, Bank, and CSC locations.
Supports both primary Partner and teammate ChannelPartner contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from beanie import Document
from pydantic import BaseModel, Field


class PartnerType(str, Enum):
    SCA = "SCA"  # State Channelizing Agency
    BANK = "Bank"
    CSC = "CSC"  # Common Service Centre


class FundStatus(str, Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    DEPLETED = "depleted"


class Partner(BaseModel):
    """
    An SCA, Bank, or CSC partner that can process scheme applications.
    Location stored as lat/lng for Haversine distance calculation.
    """
    partner_id: str
    name: str
    type: PartnerType
    address: str
    city: str
    state: str
    district: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    schemes_served: list[str] = Field(
        default_factory=list,
        description="scheme_ids this partner can process",
    )
    active: bool = True
    fund_status: FundStatus = FundStatus.AVAILABLE
    rating: float = 4.5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChannelPartner(Document):
    """
    ChannelPartner model for compatibility with recent additions and Beanie.
    """
    partner_id: str
    name: str
    type: str  # e.g., "SCA", "Bank", "NBFC", "CSC"
    compatible_schemes: list[str] = Field(default_factory=list)
    latitude: float
    longitude: float
    address: str
    district: Optional[str] = None
    state: str = ""
    contact_phone: Optional[str] = None
    fund_availability_status: str = "available"
    rating: float = 4.5

    class Settings:
        name = "channel_partners"

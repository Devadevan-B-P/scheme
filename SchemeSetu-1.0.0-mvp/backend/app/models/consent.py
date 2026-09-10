"""
Consent models for DPDP Act 2023 compliance.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ConsentRequest(BaseModel):
    session_id: str = Field(..., description="The user's active session ID")
    consent_type: str = Field(default="global", description="Type of consent, e.g., 'global' or 'ocr'")


class ConsentResponse(BaseModel):
    session_id: str
    status: str = Field(..., description="Current status: 'granted', 'withdrawn', or 'pending'")
    granted_at: Optional[str] = None
    withdrawn_at: Optional[str] = None


class ConsentRecord(BaseModel):
    session_id: str
    status: str
    consent_type: str
    granted_at: Optional[str] = None
    withdrawn_at: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

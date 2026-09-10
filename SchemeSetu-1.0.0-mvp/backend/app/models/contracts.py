"""
Step 0 — Fixed JSON Contracts

These Pydantic models ARE the system's source of truth.
Frontend and backend build against them. Every API response validates against these shapes.

Four contracts:
  - RuleResult: individual rule evaluation outcome
  - EligibilityResult: full eligibility decision (eligible/ineligible/missing_information)
  - FinancialSummary: loan/subsidy/EMI breakdown
  - ChatRequest + ChatResponse: conversational API surface
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RuleStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class Decision(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    MISSING_INFORMATION = "missing_information"


# ---------------------------------------------------------------------------
# RuleResult — individual rule evaluation outcome
# ---------------------------------------------------------------------------


class RuleResult(BaseModel):
    """One rule applied to one value. Always includes human-readable context."""
    rule: str = Field(..., description="Rule identifier, e.g. 'category', 'annual_income'")
    value: Optional[str | int | float] = Field(
        None, description="The user's actual value for this field"
    )
    requirement: str = Field(
        ..., description="Human-readable requirement, e.g. 'SC/ST', '<=300000', '18-55'"
    )
    status: RuleStatus
    explanation: Optional[str] = Field(
        None,
        description="Human-readable explanation, populated on failure.",
    )


# ---------------------------------------------------------------------------
# EligibilityResult — per-scheme eligibility decision
# ---------------------------------------------------------------------------


class EligibilityResult(BaseModel):
    """
    Per-scheme eligibility result. One of three states:
      - eligible:            all rules passed
      - ineligible:          at least one rule failed
      - missing_information: some rules could not be evaluated (fields missing)
    """
    scheme_id: str
    scheme_version: str = Field(
        ...,
        description="Version of the scheme content (loan limits, docs, etc.).",
    )
    rule_version: str = Field(
        ...,
        description="Version of the rule evaluation logic.",
    )
    decision: Decision
    decision_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp. Always UTC, never local.",
    )
    passed_rules: list[RuleResult] = Field(
        default_factory=list,
        description="Rules that passed. MUST be populated even on eligible decisions.",
    )
    failed_rules: list[RuleResult] = Field(default_factory=list)
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields the user hasn't provided yet. Empty on final decisions.",
    )
    next_question: Optional[str] = Field(
        None,
        description="Per-scheme next question. Only present when decision == missing_information.",
    )

    @field_validator("decision_timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            raise ValueError("decision_timestamp must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)

    @field_validator("next_question", mode="after")
    @classmethod
    def next_question_only_when_missing(cls, v: Optional[str], info) -> Optional[str]:
        decision = info.data.get("decision")
        if decision != Decision.MISSING_INFORMATION and v is not None:
            raise ValueError(
                "next_question must be None when decision is not 'missing_information'"
            )
        return v


# ---------------------------------------------------------------------------
# FinancialSummary — loan/subsidy/EMI breakdown
# ---------------------------------------------------------------------------


class FinancialSummary(BaseModel):
    """Complete financial breakdown for an eligible scheme + applicant."""
    scheme_id: str
    scheme_version: str
    loan_amount: float = Field(..., ge=0)
    subsidy_amount: float = Field(..., ge=0)
    subsidy_percentage: float = Field(..., ge=0, le=100)
    margin_money: float = Field(..., ge=0)
    margin_money_percentage: float = Field(..., ge=0, le=100)
    bank_loan: float = Field(
        ..., ge=0, description="loan_amount - subsidy_amount - margin_money"
    )
    interest_rate: float = Field(..., ge=0, description="Annual interest rate in %")
    tenure_months: int = Field(..., gt=0)
    emi: float = Field(..., ge=0)
    total_repayment: float = Field(..., ge=0)
    total_interest: float = Field(..., ge=0)
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# ChatRequest — inbound message
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Inbound message from the user to the chat API."""
    session_id: Optional[str] = Field(
        None, description="Existing session ID. None to create a new session."
    )
    message: str = Field(..., min_length=1, description="User's text message")
    language: str = Field(
        default="en",
        description="ISO 639-1 language code. e.g. 'en', 'hi', 'ta'",
    )


# ---------------------------------------------------------------------------
# PartnerInfo — partner with distance
# ---------------------------------------------------------------------------


class PartnerInfo(BaseModel):
    """Partner summary for display in chat results."""
    partner_id: str
    name: str
    type: str = Field(..., description="SCA, Bank, or CSC")
    address: str
    phone: Optional[str] = None
    distance_km: float = Field(..., ge=0, description="Haversine distance from user")
    schemes_served: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ChatResponse — conversational API response
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Outbound response from the chat API."""
    session_id: str
    response_text: str = Field(
        ...,
        description="The single message to display to the user.",
    )
    language: str
    extracted_entities: dict = Field(
        default_factory=dict,
        description="Entities extracted from this message turn.",
    )
    profile_completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0.0 to 1.0 — how complete the user profile is.",
    )
    extraction_mode: str = Field(
        default="gemini",
        description="'gemini' when model extracted entities, or 'fallback' when offline regex parser was active.",
    )
    sanitizer_mode: str = Field(
        default="regex_only",
        description="'regex+dlp' when Cloud DLP was active, 'regex_only' when DLP was disabled or degraded.",
    )
    eligibility_results: Optional[list[EligibilityResult]] = None
    financial_summaries: Optional[list[FinancialSummary]] = None
    partner_list: Optional[list[PartnerInfo]] = None

"""
Scheme and SchemeRule models.

scheme_version and rule_version are INDEPENDENT fields:
  - scheme_version changes when MoSJE updates the scheme content
    (loan limits, income ceilings, subsidy %, required documents)
  - rule_version changes when the evaluation logic is fixed/updated
    (how rules are applied, bug fixes in comparison logic)

They must never be collapsed into one field — the audit trail depends on
knowing exactly which version of what produced each decision.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


class SchemeStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"  # Unverified data — excluded from eligibility matching
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class RuleOperator(str, Enum):
    """Operators for rule evaluation."""
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    EQUAL = "eq"
    IN = "in"  # value must be in a list
    BETWEEN = "between"  # value between [min, max]


class SchemeRule(BaseModel):
    """
    A single eligibility rule for a scheme.
    The engine evaluates: user_profile[field] <operator> value
    """
    field: str = Field(
        ..., description="User profile field to check, e.g. 'annual_income', 'age', 'category'"
    )
    operator: RuleOperator
    value: str | int | float | list = Field(
        ..., description="The threshold/set to compare against"
    )
    explanation_template: str = Field(
        ...,
        description="Human-readable template for failure. "
        "Use {value} for user's value, {requirement} for the rule's threshold. "
        "E.g. 'Your annual income of ₹{value} exceeds the limit of ₹{requirement}.'",
    )
    requirement_display: str = Field(
        ...,
        description="Human-readable requirement for display. E.g. '<=300000', 'SC/ST', '18-55'",
    )


class SubsidyConfig(BaseModel):
    """How subsidy is calculated for this scheme."""
    percentage: float = Field(..., ge=0, le=100)
    max_amount: Optional[float] = Field(None, ge=0)


class MarginMoneyConfig(BaseModel):
    """Margin money (beneficiary's own contribution) configuration."""
    percentage: float = Field(..., ge=0, le=100)


class LoanLimits(BaseModel):
    """Loan amount boundaries."""
    min_amount: float = Field(0, ge=0)
    max_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0, description="Annual interest rate in %")
    max_tenure_months: int = Field(..., gt=0)


class SchemeProvenance(BaseModel):
    """
    Source attribution for scheme data.
    """
    source_name: str = Field(
        ..., description="Name of the official government authority or portal"
    )
    source_url: Optional[str] = Field(
        None, description="Direct URL to the official scheme document/guideline"
    )
    source_document: str = Field(
        ..., description="Official circular, policy manual, or gazette notification"
    )
    effective_date: str = Field(
        ..., description="Date from which these guidelines became effective (YYYY-MM-DD)"
    )
    last_verified_at: datetime = Field(
        ..., description="ISO 8601 UTC timestamp of last human verification"
    )
    verified_by: Optional[str] = Field(
        default="MoSJE Policy Desk",
        description="Official verifier or verification authority"
    )


class Scheme(BaseModel):
    """
    A government financial scheme.
    scheme_version and rule_version are INDEPENDENT.
    If unverified, set status='draft' — engine will exclude from matching.
    """
    scheme_id: str = Field(..., description="Unique identifier, e.g. 'nsfdc_term_loan'")
    name: str
    description: str = ""
    organization: str = Field(
        default="", description="Implementing organization: NSFDC, NSKFDC, NHFDC, NBCFDC"
    )
    ministry: Optional[str] = None
    target_category: list[str] = Field(
        default_factory=list, description="Target beneficiary categories: SC, ST, OBC, Disabled, Women, etc."
    )
    category_eligibility: list[str] = Field(default_factory=list)
    income_ceiling: Optional[float] = None
    project_cost_range: Optional[dict] = None
    loan_limit: Optional[float] = None
    subsidy_pct: Optional[float] = None
    margin_money_pct: Optional[float] = None
    interest_rate_range: Optional[dict] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    source_url: Optional[str] = None
    last_updated: Optional[datetime] = None
    scheme_version: str = Field(
        default="1.0.0",
        description="Version of the scheme content. Changes when MoSJE updates "
        "loan limits, income ceilings, subsidy %, etc.",
    )
    rule_version: str = Field(
        default="1.0.0",
        description="Version of the rule evaluation logic. Changes when a bug is "
        "fixed in how rules are applied, independent of scheme content.",
    )
    rules: list[SchemeRule] = Field(
        default_factory=list, description="Eligibility rules for this scheme"
    )
    loan_limits: Optional[LoanLimits] = None
    subsidy_config: Optional[SubsidyConfig] = None
    margin_money_config: Optional[MarginMoneyConfig] = None
    required_documents: list[str] = Field(default_factory=list)
    geographic_scope: Optional[list[str]] = Field(
        None, description="Allowed states/UTs. None = nationwide."
    )
    status: SchemeStatus = SchemeStatus.ACTIVE
    provenance: Optional[SchemeProvenance] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "schemes"

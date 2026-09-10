"""
Pydantic schemas and enums for the eligibility rule engine.
These are pure data-transfer / configuration models — not Beanie documents.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ReasonCode(str, Enum):
    """Standardised codes that describe why a rule failed."""

    INCOME_EXCEEDED = "INCOME_EXCEEDED"
    CATEGORY_NOT_ELIGIBLE = "CATEGORY_NOT_ELIGIBLE"
    DOCUMENT_MISSING = "DOCUMENT_MISSING"
    PROJECT_COST_OUT_OF_RANGE = "PROJECT_COST_OUT_OF_RANGE"
    RULE_VIOLATED_OTHER = "RULE_VIOLATED_OTHER"


class EligibilityRule(BaseModel):
    """
    A single declarative rule that the rule engine evaluates against a
    BeneficiaryProfile.

    Supported operators: ``<=``, ``>=``, ``==``, ``in``
    """

    rule_id: str
    scheme_id: str
    field: str                   # attribute name on BeneficiaryProfile
    operator: str                # "<=", ">=", "==", "in"
    value: Any                   # threshold or set to compare against
    reason_code_on_fail: ReasonCode


class RuleFailureReason(BaseModel):
    """Human-readable explanation attached to a failed rule."""

    code: ReasonCode
    detail: str


class EligibilityResult(BaseModel):
    """
    Full output of a single eligibility evaluation run.
    Produced by the rule engine and returned to the caller.
    """

    beneficiary_id: str
    scheme_id: str
    eligible: bool
    match_score: float           # fraction of rules passed (0.0 – 1.0)
    passed_rules: list[str]
    failed_rules: list[str]
    reasons: list[RuleFailureReason]
    rule_engine_version: str

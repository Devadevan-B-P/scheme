"""
Deterministic Eligibility Engine.

Evaluates user profile against verified schemes.
Strictly pure functions — zero probabilistic reasoning, zero AI.
Returns standardized EligibilityResult contracts.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Optional, List

from app.models.contracts import (
    EligibilityResult,
    Decision,
    RuleResult,
    RuleStatus,
)
from app.models.scheme import Scheme, SchemeStatus
from app.models.user import UserProfile
from app.engine.rules import evaluate_rule

# Vernacular-friendly field prompts for next-best-question
FIELD_QUESTION_TEMPLATES = {
    "annual_income": "What is your approximate yearly family income?",
    "category": "Which social category do you belong to (e.g. SC, ST, OBC, or General)?",
    "age": "What is your current age?",
    "gender": "Are you applying as a woman entrepreneur or male applicant?",
    "business_type": "What kind of small business or activity do you plan to start or expand?",
    "location": "Which city or district are you located in?",
    "state": "Which state do you reside in?",
    "disability_status": "Do you have a certified disability of 40% or more (PwD/Divyangjan)?",
    "education": "What is your highest educational qualification?",
    "existing_business": "Do you already have an existing business, or are you starting a new one?",
}


def check_scheme_eligibility(scheme: Scheme, profile: UserProfile) -> EligibilityResult:
    """
    Deterministically evaluate a single scheme against a user's profile.
    """
    if scheme.status != SchemeStatus.ACTIVE:
        raise ValueError(
            f"Cannot evaluate eligibility for scheme '{scheme.scheme_id}' with status '{scheme.status.value}'. "
            "Only active, verified schemes can be evaluated."
        )

    passed_rules: list[RuleResult] = []
    failed_rules: list[RuleResult] = []
    missing_fields: list[str] = []

    profile_dict = profile.model_dump()

    for rule in scheme.rules:
        field_name = rule.field
        user_val = profile_dict.get(field_name)

        if user_val is None:
            missing_fields.append(field_name)
        else:
            rule_result = evaluate_rule(rule, user_val)
            if rule_result.status == RuleStatus.PASSED:
                passed_rules.append(rule_result)
            else:
                failed_rules.append(rule_result)

    now_utc = datetime.now(timezone.utc)

    # Ineligible if ANY rule failed
    if len(failed_rules) > 0:
        return EligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_version=scheme.scheme_version,
            rule_version=scheme.rule_version,
            decision=Decision.INELIGIBLE,
            decision_timestamp=now_utc,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            missing_fields=[],
            next_question=None,
        )

    # Missing Information if no rule failed, but required fields are uncollected
    if len(missing_fields) > 0:
        first_missing = missing_fields[0]
        per_scheme_question = FIELD_QUESTION_TEMPLATES.get(
            first_missing, f"Please provide your {first_missing}."
        )
        return EligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_version=scheme.scheme_version,
            rule_version=scheme.rule_version,
            decision=Decision.MISSING_INFORMATION,
            decision_timestamp=now_utc,
            passed_rules=passed_rules,
            failed_rules=[],
            missing_fields=missing_fields,
            next_question=per_scheme_question,
        )

    # Fully Eligible
    return EligibilityResult(
        scheme_id=scheme.scheme_id,
        scheme_version=scheme.scheme_version,
        rule_version=scheme.rule_version,
        decision=Decision.ELIGIBLE,
        decision_timestamp=now_utc,
        passed_rules=passed_rules,
        failed_rules=[],
        missing_fields=[],
        next_question=None,
    )


def check_all_schemes(schemes: list[Scheme], profile: UserProfile) -> list[EligibilityResult]:
    """
    Evaluate all active schemes against user profile.
    Ignores draft or suspended schemes.
    """
    active_schemes = [s for s in schemes if s.status == SchemeStatus.ACTIVE]
    results: list[EligibilityResult] = []

    for s in active_schemes:
        result = check_scheme_eligibility(s, profile)
        results.append(result)

    return results


def select_next_question(results: list[EligibilityResult]) -> Optional[str]:
    """
    Next-Best-Question Arbitrator across candidate schemes.
    """
    candidates = [r for r in results if r.decision == Decision.MISSING_INFORMATION]
    if not candidates:
        return None

    field_counter = Counter()
    for c in candidates:
        for f in c.missing_fields:
            field_counter[f] += 1

    if not field_counter:
        return None

    winning_field, _ = field_counter.most_common(1)[0]
    return FIELD_QUESTION_TEMPLATES.get(
        winning_field, f"Could you please share your approximate {winning_field.replace('_', ' ')}?"
    )

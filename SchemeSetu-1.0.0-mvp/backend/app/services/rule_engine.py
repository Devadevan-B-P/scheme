"""
Deterministic eligibility rule engine for SchemeSetu.

Evaluates a list of :class:`EligibilityRule` objects against a
:class:`BeneficiaryProfile` and produces an :class:`EligibilityResult`.

All logic is pure and stateless — no database calls occur here.
"""

import operator as _op
from typing import Any

from app.models.beneficiary import BeneficiaryProfile
from app.models.scheme import Scheme
from app.models.eligibility import (
    EligibilityRule,
    EligibilityResult,
    RuleFailureReason,
)

_RULE_ENGINE_VERSION = "1.0.0"

# Map operator strings to callables
_OPERATOR_MAP: dict[str, Any] = {
    "<=": _op.le,
    ">=": _op.ge,
    "==": _op.eq,
    "in": lambda field_val, rule_val: field_val in rule_val,
}


def _get_field_value(profile: BeneficiaryProfile, field: str) -> Any:
    """
    Retrieve a field value from the profile.
    Supports top-level attributes and one level of nested dict access
    using dot notation (e.g. ``"location.state"``).
    """
    if "." in field:
        parent, child = field.split(".", 1)
        parent_val = getattr(profile, parent, None)
        if isinstance(parent_val, dict):
            return parent_val.get(child)
        return None
    return getattr(profile, field, None)


def evaluate_eligibility(
    profile: BeneficiaryProfile,
    scheme: Scheme,
    rules: list[EligibilityRule],
) -> EligibilityResult:
    """
    Evaluate whether a beneficiary is eligible for a scheme.

    Parameters
    ----------
    profile: The beneficiary's collected profile data.
    scheme:  The scheme being evaluated against.
    rules:   Ordered list of declarative eligibility rules for this scheme.

    Returns
    -------
    :class:`EligibilityResult` — fully populated result object.
    """
    passed_rules: list[str] = []
    failed_rules: list[str] = []
    reasons: list[RuleFailureReason] = []

    for rule in rules:
        compare_fn = _OPERATOR_MAP.get(rule.operator)
        if compare_fn is None:
            # Unknown operator — treat as a failure to avoid silent mismatches
            failed_rules.append(rule.rule_id)
            reasons.append(
                RuleFailureReason(
                    code=rule.reason_code_on_fail,
                    detail=(
                        f"Rule '{rule.rule_id}': unsupported operator "
                        f"'{rule.operator}'."
                    ),
                )
            )
            continue

        field_value = _get_field_value(profile, rule.field)

        # A missing (None) field always fails the rule
        if field_value is None:
            failed_rules.append(rule.rule_id)
            reasons.append(
                RuleFailureReason(
                    code=rule.reason_code_on_fail,
                    detail=(
                        f"Rule '{rule.rule_id}': field '{rule.field}' is "
                        f"missing from the beneficiary profile."
                    ),
                )
            )
            continue

        try:
            rule_passed: bool = compare_fn(field_value, rule.value)
        except TypeError:
            rule_passed = False

        if rule_passed:
            passed_rules.append(rule.rule_id)
        else:
            failed_rules.append(rule.rule_id)
            reasons.append(
                RuleFailureReason(
                    code=rule.reason_code_on_fail,
                    detail=(
                        f"Rule '{rule.rule_id}': '{rule.field}' value "
                        f"'{field_value}' did not satisfy "
                        f"'{rule.operator} {rule.value}'."
                    ),
                )
            )

    total_rules = len(rules)
    match_score: float = (
        round(len(passed_rules) / total_rules, 4) if total_rules > 0 else 0.0
    )
    eligible: bool = len(failed_rules) == 0

    return EligibilityResult(
        beneficiary_id=str(profile.beneficiary_id),
        scheme_id=scheme.scheme_id,
        eligible=eligible,
        match_score=match_score,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        reasons=reasons,
        rule_engine_version=_RULE_ENGINE_VERSION,
    )

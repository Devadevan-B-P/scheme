"""
Deterministic Rule Evaluators.

Pure functions that compare a user's profile value against a scheme rule.
No AI, no probabilistic reasoning. Returns RuleResult with status and explanation.
"""

from typing import Any
from app.models.contracts import RuleResult, RuleStatus
from app.models.scheme import SchemeRule, RuleOperator


def evaluate_rule(rule: SchemeRule, user_value: Any) -> RuleResult:
    """
    Evaluate a single SchemeRule against a user-provided value.
    Assumes user_value is not None.
    """
    op = rule.operator
    threshold = rule.value
    passed = False

    try:
        if op == RuleOperator.EQUAL:
            if isinstance(user_value, str) and isinstance(threshold, str):
                passed = user_value.strip().lower() == threshold.strip().lower()
            else:
                passed = user_value == threshold

        elif op == RuleOperator.IN:
            if isinstance(threshold, list):
                if isinstance(user_value, str):
                    passed = any(
                        user_value.strip().lower() == str(item).strip().lower()
                        for item in threshold
                    )
                else:
                    passed = user_value in threshold
            else:
                passed = user_value == threshold

        elif op == RuleOperator.LESS_THAN:
            passed = float(user_value) < float(threshold)

        elif op == RuleOperator.LESS_THAN_OR_EQUAL:
            passed = float(user_value) <= float(threshold)

        elif op == RuleOperator.GREATER_THAN:
            passed = float(user_value) > float(threshold)

        elif op == RuleOperator.GREATER_THAN_OR_EQUAL:
            passed = float(user_value) >= float(threshold)

        elif op == RuleOperator.BETWEEN:
            if isinstance(threshold, list) and len(threshold) == 2:
                val = float(user_value)
                passed = float(threshold[0]) <= val <= float(threshold[1])
            else:
                passed = False
    except (ValueError, TypeError):
        passed = False

    if passed:
        return RuleResult(
            rule=rule.field,
            value=user_value,
            requirement=rule.requirement_display,
            status=RuleStatus.PASSED,
            explanation=None,
        )
    else:
        explanation = _format_explanation(rule.explanation_template, user_value, rule.requirement_display, threshold)
        return RuleResult(
            rule=rule.field,
            value=user_value,
            requirement=rule.requirement_display,
            status=RuleStatus.FAILED,
            explanation=explanation,
        )


def _format_explanation(template: str, user_val: Any, requirement_display: str, raw_threshold: Any) -> str:
    """Format explanation template safely with user and rule values."""
    try:
        return template.format(
            value=user_val,
            requirement=raw_threshold if isinstance(raw_threshold, (int, float)) else requirement_display,
        )
    except Exception:
        return f"Requirement '{requirement_display}' was not met (reported value: {user_val})."

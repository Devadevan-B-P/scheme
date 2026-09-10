"""
Deterministic Financial Engine.

Pure Python calculations for:
  - Capital & interest subsidy
  - Beneficiary margin money (promoter contribution)
  - Equated Monthly Installment (EMI)
  - Total interest & repayment schedule

Returns standardized FinancialSummary contracts.
Zero AI, zero hallucination.
"""

from datetime import datetime, timezone
from typing import Optional
from app.models.contracts import FinancialSummary
from app.models.scheme import Scheme, SubsidyConfig, MarginMoneyConfig


def calculate_subsidy(
    loan_amount: float, subsidy_config: Optional[SubsidyConfig]
) -> tuple[float, float]:
    """
    Calculate subsidy amount and effective percentage.
    Returns: (subsidy_amount, subsidy_percentage)
    """
    if not subsidy_config or subsidy_config.percentage <= 0:
        return 0.0, 0.0

    raw_subsidy = (loan_amount * subsidy_config.percentage) / 100.0
    if subsidy_config.max_amount is not None:
        subsidy_amount = min(raw_subsidy, subsidy_config.max_amount)
    else:
        subsidy_amount = raw_subsidy

    effective_pct = (subsidy_amount / loan_amount * 100.0) if loan_amount > 0 else 0.0
    return round(subsidy_amount, 2), round(effective_pct, 2)


def calculate_margin_money(
    loan_amount: float, margin_config: Optional[MarginMoneyConfig]
) -> tuple[float, float]:
    """
    Calculate margin money (beneficiary's own contribution).
    Returns: (margin_money_amount, margin_money_percentage)
    """
    if not margin_config or margin_config.percentage <= 0:
        return 0.0, 0.0

    pct = margin_config.percentage
    amount = (loan_amount * pct) / 100.0
    return round(amount, 2), round(pct, 2)


def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """
    Calculate Equated Monthly Installment (EMI) using reducing balance method.
    Formula:
      EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
      where r = monthly interest rate, n = tenure in months.
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0

    if annual_rate_pct <= 0:
        return round(principal / tenure_months, 2)

    monthly_rate = (annual_rate_pct / 100.0) / 12.0
    numerator = principal * monthly_rate * ((1.0 + monthly_rate) ** tenure_months)
    denominator = ((1.0 + monthly_rate) ** tenure_months) - 1.0

    emi = numerator / denominator
    return round(emi, 2)


def generate_financial_summary(
    scheme: Scheme,
    requested_loan_amount: Optional[float] = None,
    requested_tenure_months: Optional[int] = None,
) -> FinancialSummary:
    """
    Generate complete financial breakdown for an eligible scheme.
    Caps requested amount to scheme min/max limits.
    """
    limits = scheme.loan_limits

    # Determine loan amount within permissible scheme limits
    if requested_loan_amount is None:
        loan_amount = limits.max_amount
    else:
        loan_amount = max(limits.min_amount, min(requested_loan_amount, limits.max_amount))

    # Determine tenure within permissible scheme limits
    if requested_tenure_months is None:
        tenure_months = limits.max_tenure_months
    else:
        tenure_months = min(requested_tenure_months, limits.max_tenure_months)

    subsidy_amount, subsidy_pct = calculate_subsidy(loan_amount, scheme.subsidy_config)
    margin_amount, margin_pct = calculate_margin_money(loan_amount, scheme.margin_money_config)

    # Net principal financed by the bank/SCA
    bank_loan = max(0.0, loan_amount - subsidy_amount - margin_amount)

    rate = limits.interest_rate
    emi = calculate_emi(bank_loan, rate, tenure_months)

    total_repayment = round(emi * tenure_months, 2)
    total_interest = round(max(0.0, total_repayment - bank_loan), 2)

    return FinancialSummary(
        scheme_id=scheme.scheme_id,
        scheme_version=scheme.scheme_version,
        loan_amount=round(loan_amount, 2),
        subsidy_amount=subsidy_amount,
        subsidy_percentage=subsidy_pct,
        margin_money=margin_amount,
        margin_money_percentage=margin_pct,
        bank_loan=round(bank_loan, 2),
        interest_rate=rate,
        tenure_months=tenure_months,
        emi=emi,
        total_repayment=total_repayment,
        total_interest=total_interest,
        calculated_at=datetime.now(timezone.utc),
    )

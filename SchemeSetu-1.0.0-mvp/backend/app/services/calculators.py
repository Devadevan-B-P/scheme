"""
Pure financial calculator for government scheme loan products.

All functions are stateless and side-effect-free — safe to call from
synchronous or asynchronous contexts without any database I/O.
"""


def calculate_financial_plan(
    project_cost: float,
    subsidy_pct: float,
    margin_money_pct: float,
    annual_interest_rate: float,
    tenure_months: int,
    moratorium_months: int = 0,
) -> dict:
    """
    Compute the full financial breakdown for a scheme application.

    Parameters
    ----------
    project_cost:        Total project cost (₹).
    subsidy_pct:         Subsidy as a percentage of project cost (e.g. 25 → 25%).
    margin_money_pct:    Promoter's margin money as % of project cost.
    annual_interest_rate: Nominal annual interest rate (e.g. 9.5 → 9.5% p.a.).
    tenure_months:       Total repayment period in months.
    moratorium_months:   Initial interest-free / repayment-free period in months.

    Returns
    -------
    dict with all computed values, each rounded to 2 decimal places.
    """
    # ── Primary split ────────────────────────────────────────────────────────
    subsidy_amount: float = project_cost * (subsidy_pct / 100)
    margin_money_amount: float = project_cost * (margin_money_pct / 100)
    loan_amount: float = project_cost - subsidy_amount - margin_money_amount

    # Clamp to zero if rounding pushes below 0
    loan_amount = max(loan_amount, 0.0)

    # ── EMI (reducing-balance) ────────────────────────────────────────────────
    # Effective repayment installments after moratorium
    n_installments: int = tenure_months - moratorium_months

    if loan_amount == 0 or annual_interest_rate == 0:
        # No interest or nothing to repay
        monthly_emi: float = (
            loan_amount / n_installments if n_installments > 0 else 0.0
        )
        total_interest: float = 0.0
    else:
        monthly_rate: float = annual_interest_rate / 12 / 100  # R
        # Standard formula: EMI = P * R * (1+R)^N / ((1+R)^N - 1)
        compound_factor: float = (1 + monthly_rate) ** n_installments
        monthly_emi = (
            loan_amount * monthly_rate * compound_factor / (compound_factor - 1)
        )
        total_interest = (monthly_emi * n_installments) - loan_amount

    total_repayment: float = loan_amount + total_interest

    return {
        "project_cost": round(project_cost, 2),
        "subsidy_amount": round(subsidy_amount, 2),
        "margin_money_amount": round(margin_money_amount, 2),
        "loan_amount": round(loan_amount, 2),
        "annual_interest_rate_pct": round(annual_interest_rate, 2),
        "tenure_months": tenure_months,
        "moratorium_months": moratorium_months,
        "effective_repayment_months": n_installments,
        "monthly_emi": round(monthly_emi, 2),
        "total_interest": round(total_interest, 2),
        "total_repayment": round(total_repayment, 2),
    }

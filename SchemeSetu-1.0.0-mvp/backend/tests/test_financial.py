"""
Unit & Integration Tests for Deterministic Financial Engine.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.engine.financial import (
    calculate_emi,
    calculate_subsidy,
    calculate_margin_money,
    generate_financial_summary,
)
from app.models.scheme import SubsidyConfig, MarginMoneyConfig
from app.seed.seed_data import VERIFIED_SCHEMES
from app.main import app


def test_calculate_emi_standard():
    # 1 Lakh principal, 12% p.a., 12 months tenure
    # Monthly rate = 1%
    # EMI = 100000 * 0.01 * (1.01)^12 / ((1.01)^12 - 1) = 8884.88
    emi = calculate_emi(100000.0, 12.0, 12)
    assert abs(emi - 8884.88) < 0.1


def test_calculate_emi_zero_interest():
    # 12,000 principal, 0% interest, 12 months tenure -> 1000.0 per month
    emi = calculate_emi(12000.0, 0.0, 12)
    assert emi == 1000.0


def test_calculate_subsidy_percentage_and_cap():
    config = SubsidyConfig(percentage=50.0, max_amount=50000.0)

    # 80,000 project cost -> 50% is 40,000 (below cap of 50,000)
    amt, pct = calculate_subsidy(80000.0, config)
    assert amt == 40000.0
    assert pct == 50.0

    # 1,20,000 project cost -> 50% is 60,000, capped at 50,000
    amt_capped, pct_effective = calculate_subsidy(120000.0, config)
    assert amt_capped == 50000.0
    assert abs(pct_effective - 41.67) < 0.1


def test_calculate_margin_money():
    config = MarginMoneyConfig(percentage=5.0)
    amt, pct = calculate_margin_money(1500000.0, config)
    assert amt == 75000.0
    assert pct == 5.0


def test_generate_financial_summary_nsfdc():
    scheme = next(s for s in VERIFIED_SCHEMES if s.scheme_id == "nsfdc_term_loan")
    summary = generate_financial_summary(scheme, requested_loan_amount=1500000.0)

    assert summary.scheme_id == "nsfdc_term_loan"
    assert summary.loan_amount == 1500000.0
    assert summary.subsidy_amount == 0.0
    assert summary.margin_money == 150000.0  # 10%
    assert summary.bank_loan == 1350000.0  # 15L - 150K
    assert summary.interest_rate == 8.0
    assert summary.tenure_months == 84
    assert summary.emi > 0
    assert summary.total_repayment > summary.bank_loan
    assert summary.total_interest == round(summary.total_repayment - summary.bank_loan, 2)


def test_generate_financial_summary_mahila_samriddhi():
    scheme = next(s for s in VERIFIED_SCHEMES if s.scheme_id == "nskfdc_mahila_samriddhi")
    summary = generate_financial_summary(scheme, requested_loan_amount=100000.0)

    assert summary.scheme_id == "nskfdc_mahila_samriddhi"
    assert summary.loan_amount == 100000.0
    assert summary.subsidy_amount == 50000.0  # 50% cap
    assert summary.margin_money == 0.0  # 0%
    assert summary.bank_loan == 50000.0  # 100K - 50K
    assert summary.interest_rate == 4.0
    assert summary.tenure_months == 36
    assert summary.emi > 0


@pytest.mark.asyncio
async def test_financial_simulate_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "scheme_id": "nsfdc_term_loan",
            "loan_amount": 500000.0,
            "tenure_months": 60,
        }
        resp = await client.post("/api/v1/financial/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["scheme_id"] == "nsfdc_term_loan"
        assert data["loan_amount"] == 500000.0
        assert data["margin_money"] == 50000.0  # 10% of 500k
        assert data["bank_loan"] == 450000.0
        assert data["emi"] > 0
        assert data["total_repayment"] > data["bank_loan"]

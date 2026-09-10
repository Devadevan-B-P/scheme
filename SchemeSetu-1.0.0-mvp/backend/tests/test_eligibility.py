"""
Unit & Integration Tests for Deterministic Eligibility Engine.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.contracts import Decision, RuleStatus
from app.models.user import UserProfile
from app.engine.eligibility import (
    check_scheme_eligibility,
    check_all_schemes,
    select_next_question,
)
from app.seed.seed_data import VERIFIED_SCHEMES
from app.main import app


@pytest.fixture
def nsfdc_scheme():
    return next(s for s in VERIFIED_SCHEMES if s.scheme_id == "nsfdc_term_loan")


@pytest.fixture
def nskfdc_scheme():
    return next(s for s in VERIFIED_SCHEMES if s.scheme_id == "nskfdc_mahila_samriddhi")


def test_exact_match_eligible(nsfdc_scheme):
    profile = UserProfile(
        category="SC",
        annual_income=250000.0,
        age=30,
        business_type="tailoring",
        location="Lucknow",
    )
    res = check_scheme_eligibility(nsfdc_scheme, profile)

    assert res.decision == Decision.ELIGIBLE
    assert len(res.passed_rules) == 3
    assert len(res.failed_rules) == 0
    assert res.missing_fields == []
    assert res.next_question is None

    # Verify every passed rule has status=passed
    for r in res.passed_rules:
        assert r.status == RuleStatus.PASSED


def test_boundary_conditions_income(nsfdc_scheme):
    # Exactly on ceiling (500,000) -> should pass (lte)
    profile_at_limit = UserProfile(category="SC", annual_income=500000.0, age=30)
    res_at_limit = check_scheme_eligibility(nsfdc_scheme, profile_at_limit)
    assert res_at_limit.decision == Decision.ELIGIBLE

    # Just above ceiling (500,001) -> should fail
    profile_above_limit = UserProfile(category="SC", annual_income=500001.0, age=30)
    res_above = check_scheme_eligibility(nsfdc_scheme, profile_above_limit)
    assert res_above.decision == Decision.INELIGIBLE
    assert len(res_above.failed_rules) == 1
    assert res_above.failed_rules[0].rule == "annual_income"
    assert "exceeds" in res_above.failed_rules[0].explanation


def test_boundary_conditions_age(nsfdc_scheme):
    # Exactly 18 -> pass
    res_18 = check_scheme_eligibility(nsfdc_scheme, UserProfile(category="SC", annual_income=200000.0, age=18))
    assert res_18.decision == Decision.ELIGIBLE

    # Exactly 55 -> pass
    res_55 = check_scheme_eligibility(nsfdc_scheme, UserProfile(category="SC", annual_income=200000.0, age=55))
    assert res_55.decision == Decision.ELIGIBLE

    # 17 -> fail
    res_17 = check_scheme_eligibility(nsfdc_scheme, UserProfile(category="SC", annual_income=200000.0, age=17))
    assert res_17.decision == Decision.INELIGIBLE

    # 56 -> fail
    res_56 = check_scheme_eligibility(nsfdc_scheme, UserProfile(category="SC", annual_income=200000.0, age=56))
    assert res_56.decision == Decision.INELIGIBLE


def test_ineligible_category(nsfdc_scheme):
    profile = UserProfile(category="General", annual_income=150000.0, age=25)
    res = check_scheme_eligibility(nsfdc_scheme, profile)
    assert res.decision == Decision.INELIGIBLE
    assert any(f.rule == "category" for f in res.failed_rules)


def test_gender_restriction(nskfdc_scheme):
    # Male applicant for Mahila Samriddhi -> should fail
    male_profile = UserProfile(gender="Male", annual_income=100000.0, age=30)
    res = check_scheme_eligibility(nskfdc_scheme, male_profile)
    assert res.decision == Decision.INELIGIBLE
    assert any(f.rule == "gender" for f in res.failed_rules)

    # Female applicant -> passes
    female_profile = UserProfile(gender="Female", annual_income=100000.0, age=30)
    res_female = check_scheme_eligibility(nskfdc_scheme, female_profile)
    assert res_female.decision == Decision.ELIGIBLE


def test_partial_profile_missing_information(nsfdc_scheme):
    # Only category provided
    profile = UserProfile(category="SC")
    res = check_scheme_eligibility(nsfdc_scheme, profile)

    assert res.decision == Decision.MISSING_INFORMATION
    assert len(res.passed_rules) == 1  # category passed
    assert len(res.failed_rules) == 0
    assert set(res.missing_fields) == {"annual_income", "age"}
    assert res.next_question is not None


def test_empty_profile():
    empty_profile = UserProfile()
    results = check_all_schemes(VERIFIED_SCHEMES, empty_profile)

    # All active schemes should return missing_information
    for r in results:
        assert r.decision == Decision.MISSING_INFORMATION
        assert len(r.missing_fields) > 0


def test_select_next_question_discriminator():
    # User provided only category="SC"
    profile = UserProfile(category="SC")
    results = check_all_schemes(VERIFIED_SCHEMES, profile)

    question = select_next_question(results)
    assert question is not None
    # annual_income is required by both NSFDC and NBCFDC / NSKFDC, so it should be prioritized
    assert "income" in question.lower() or "age" in question.lower()


@pytest.mark.asyncio
async def test_eligibility_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "category": "SC",
            "annual_income": 200000.0,
            "age": 32,
            "business_type": "handicrafts",
            "location": "Lucknow",
        }
        resp = await client.post("/api/v1/eligibility/check", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3

        # NSFDC should be eligible
        nsfdc_res = next(r for r in data if r["scheme_id"] == "nsfdc_term_loan")
        assert nsfdc_res["decision"] == "eligible"
        assert len(nsfdc_res["passed_rules"]) >= 3
        assert nsfdc_res["failed_rules"] == []

"""
Step 0 Contract Validation Tests

Verifies that the four core contracts:
1. RuleResult
2. EligibilityResult (with passed_rules, failed_rules, missing_fields, next_question, UTC timestamps)
3. FinancialSummary
4. ChatRequest and ChatResponse

strictly enforce the agreed-upon JSON schema and business rules.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models.contracts import (
    RuleStatus,
    Decision,
    RuleResult,
    EligibilityResult,
    FinancialSummary,
    ChatRequest,
    ChatResponse,
    PartnerInfo,
)
from app.models.scheme import Scheme, SchemeRule, RuleOperator, LoanLimits, SchemeProvenance, SchemeStatus
from app.models.user import UserProfile, UserSession, ConversationRole, ConversationMessage


def test_rule_result_passed():
    rule = RuleResult(
        rule="category",
        value="SC",
        requirement="SC/ST",
        status=RuleStatus.PASSED,
    )
    assert rule.status == RuleStatus.PASSED
    assert rule.explanation is None


def test_rule_result_failed_with_explanation():
    rule = RuleResult(
        rule="annual_income",
        value=500000,
        requirement="<=300000",
        status=RuleStatus.FAILED,
        explanation="Your annual income of ₹5,00,000 exceeds the scheme limit of ₹3,00,000.",
    )
    assert rule.status == RuleStatus.FAILED
    assert rule.explanation is not None


def test_eligibility_result_eligible():
    now_utc = datetime.now(timezone.utc)
    res = EligibilityResult(
        scheme_id="nsfdc_term_loan",
        scheme_version="2026.09",
        rule_version="1.0.0",
        decision=Decision.ELIGIBLE,
        decision_timestamp=now_utc,
        passed_rules=[
            RuleResult(rule="category", value="SC", requirement="SC/ST", status=RuleStatus.PASSED),
            RuleResult(rule="annual_income", value=280000, requirement="<=300000", status=RuleStatus.PASSED),
            RuleResult(rule="age", value=28, requirement="18-55", status=RuleStatus.PASSED),
        ],
        failed_rules=[],
        missing_fields=[],
    )
    assert res.decision == Decision.ELIGIBLE
    assert len(res.passed_rules) == 3
    assert res.missing_fields == []
    assert res.next_question is None
    assert res.decision_timestamp.tzinfo == timezone.utc


def test_eligibility_result_ineligible_with_failed_rules():
    now_utc = datetime.now(timezone.utc)
    res = EligibilityResult(
        scheme_id="nsfdc_term_loan",
        scheme_version="2026.09",
        rule_version="1.0.0",
        decision=Decision.INELIGIBLE,
        decision_timestamp=now_utc,
        passed_rules=[
            RuleResult(rule="category", value="SC", requirement="SC/ST", status=RuleStatus.PASSED),
        ],
        failed_rules=[
            RuleResult(
                rule="annual_income",
                value=500000,
                requirement="<=300000",
                status=RuleStatus.FAILED,
                explanation="Your annual income of ₹5,00,000 exceeds the scheme limit of ₹3,00,000.",
            )
        ],
        missing_fields=[],
    )
    assert res.decision == Decision.INELIGIBLE
    assert len(res.passed_rules) == 1
    assert len(res.failed_rules) == 1
    assert res.next_question is None


def test_eligibility_result_missing_information():
    now_utc = datetime.now(timezone.utc)
    res = EligibilityResult(
        scheme_id="nsfdc_term_loan",
        scheme_version="2026.09",
        rule_version="1.0.0",
        decision=Decision.MISSING_INFORMATION,
        decision_timestamp=now_utc,
        passed_rules=[
            RuleResult(rule="category", value="SC", requirement="SC/ST", status=RuleStatus.PASSED),
        ],
        failed_rules=[],
        missing_fields=["annual_income", "age"],
        next_question="What is your approximate yearly family income?",
    )
    assert res.decision == Decision.MISSING_INFORMATION
    assert res.missing_fields == ["annual_income", "age"]
    assert res.next_question == "What is your approximate yearly family income?"


def test_eligibility_result_rejects_next_question_on_eligible():
    now_utc = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        EligibilityResult(
            scheme_id="nsfdc_term_loan",
            scheme_version="2026.09",
            rule_version="1.0.0",
            decision=Decision.ELIGIBLE,
            decision_timestamp=now_utc,
            passed_rules=[],
            failed_rules=[],
            missing_fields=[],
            next_question="Invalid question for eligible",
        )


def test_eligibility_result_rejects_naive_timestamp():
    naive_dt = datetime(2026, 9, 10, 14, 30, 0)
    with pytest.raises(ValidationError):
        EligibilityResult(
            scheme_id="nsfdc_term_loan",
            scheme_version="2026.09",
            rule_version="1.0.0",
            decision=Decision.ELIGIBLE,
            decision_timestamp=naive_dt,
            passed_rules=[],
        )


def test_financial_summary_contract():
    now_utc = datetime.now(timezone.utc)
    fin = FinancialSummary(
        scheme_id="nsfdc_term_loan",
        scheme_version="2026.09",
        loan_amount=1500000.0,
        subsidy_amount=0.0,
        subsidy_percentage=0.0,
        margin_money=75000.0,
        margin_money_percentage=5.0,
        bank_loan=1425000.0,
        interest_rate=6.0,
        tenure_months=120,
        emi=15819.0,
        total_repayment=1898280.0,
        total_interest=473280.0,
        calculated_at=now_utc,
    )
    assert fin.bank_loan == 1425000.0
    assert fin.emi == 15819.0


def test_chat_request_and_response_contracts():
    req = ChatRequest(
        session_id="sess_123",
        message="I want to start a tailoring shop in Lucknow",
        language="en",
    )
    assert req.message == "I want to start a tailoring shop in Lucknow"

    partner = PartnerInfo(
        partner_id="p1",
        name="UP SC Finance Corp",
        type="SCA",
        address="Hazratganj, Lucknow",
        phone="0522-123456",
        distance_km=4.2,
        schemes_served=["nsfdc_term_loan"],
    )

    resp = ChatResponse(
        session_id="sess_123",
        response_text="What is your approximate yearly family income?",
        language="en",
        extracted_entities={"business_type": "tailoring", "location": "Lucknow"},
        profile_completeness=0.3,
        partner_list=[partner],
    )
    assert resp.profile_completeness == 0.3
    assert len(resp.partner_list) == 1
    assert resp.partner_list[0].distance_km == 4.2


def test_scheme_model_independent_versions():
    now_utc = datetime.now(timezone.utc)
    scheme = Scheme(
        scheme_id="nsfdc_term_loan",
        name="Term Loan Scheme",
        description="Term loan for SC entrepreneurs",
        organization="NSFDC",
        target_category=["SC"],
        scheme_version="2026.09",
        rule_version="1.0.0",
        rules=[
            SchemeRule(
                field="annual_income",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=300000,
                explanation_template="Your annual income of ₹{value} exceeds ₹{requirement}.",
                requirement_display="<=300000",
            )
        ],
        loan_limits=LoanLimits(
            min_amount=50000,
            max_amount=1500000,
            interest_rate=6.0,
            max_tenure_months=120,
        ),
        provenance=SchemeProvenance(
            source_name="Ministry of Social Justice and Empowerment / NSFDC",
            source_url="https://nsfdc.nic.in/en/term-loan-scheme",
            source_document="NSFDC Operational Guidelines 2026, Circular No. 11014/01/2021-SCD-I",
            effective_date="2024-04-01",
            last_verified_at=now_utc,
        ),
        status=SchemeStatus.ACTIVE,
    )
    assert scheme.scheme_version == "2026.09"
    assert scheme.rule_version == "1.0.0"
    assert scheme.status == SchemeStatus.ACTIVE
    assert scheme.provenance.source_name == "Ministry of Social Justice and Empowerment / NSFDC"
    assert scheme.provenance.source_url == "https://nsfdc.nic.in/en/term-loan-scheme"
    assert scheme.provenance.effective_date == "2024-04-01"
    assert scheme.provenance.last_verified_at == now_utc



def test_user_session_sanitized_conversation_history():
    profile = UserProfile(
        age=28,
        annual_income=250000.0,
        category="SC",
        business_type="tailoring",
    )
    msg = ConversationMessage(
        role=ConversationRole.USER,
        content="My Aadhaar is [AADHAAR_REDACTED] and I want a loan",
    )
    session = UserSession(
        session_id="sess_abc",
        profile=profile,
        conversation_history=[msg],
    )
    assert "[AADHAAR_REDACTED]" in session.conversation_history[0].content
    assert session.profile.age == 28
    assert session.profile.completeness() > 0.0

"""
Unit Tests for Deterministic Regex Entity Extraction Fallback.

Ensures the offline/resilience extractor accurately parses demographic variables
when Gemini is offline, unreachable, or in test environments.
"""

from app.agent.gemini_client import gemini_agent


def test_fallback_extract_age():
    # Keyword formats
    e1 = gemini_agent._local_fallback_extract("I am 28 years old from Lucknow", "en")
    assert e1.age == 28
    assert e1.extraction_mode == "fallback"

    e2 = gemini_agent._local_fallback_extract("Meri umr 35 saal hai", "hi")
    assert e2.age == 35

    # Standalone two-digit age
    e3 = gemini_agent._local_fallback_extract("Age 42, female", "en")
    assert e3.age == 42


def test_fallback_extract_income():
    # Lakh expression
    e1 = gemini_agent._local_fallback_extract("My annual income is 2.5 lakh", "en")
    assert e1.annual_income == 250000.0

    e2 = gemini_agent._local_fallback_extract("Family income 3 lacs per year", "en")
    assert e2.annual_income == 300000.0

    # Direct digits
    e3 = gemini_agent._local_fallback_extract("Income 180000 annually", "en")
    assert e3.annual_income == 180000.0


def test_fallback_extract_category():
    e_sc = gemini_agent._local_fallback_extract("I belong to SC category", "en")
    assert e_sc.category == "SC"

    e_st = gemini_agent._local_fallback_extract("Applicant from Scheduled Tribe community", "en")
    assert e_st.category == "ST"

    e_obc = gemini_agent._local_fallback_extract("OBC non creamy layer", "en")
    assert e_obc.category == "OBC"

    e_gen = gemini_agent._local_fallback_extract("General category applicant", "en")
    assert e_gen.category == "General"


def test_fallback_extract_gender():
    e_fem = gemini_agent._local_fallback_extract("I am a woman entrepreneur seeking a loan", "en")
    assert e_fem.gender == "Female"

    e_mahila = gemini_agent._local_fallback_extract("Mahila self help group member", "hi")
    assert e_mahila.gender == "Female"

    e_male = gemini_agent._local_fallback_extract("Male applicant, age 30", "en")
    assert e_male.gender == "Male"


def test_fallback_extract_business_and_location():
    e = gemini_agent._local_fallback_extract(
        "I want to open a tailoring shop and boutique in Lucknow, Uttar Pradesh", "en"
    )
    assert e.business_type == "tailoring"
    assert e.location == "Lucknow"


def test_fallback_extract_disability_affirmative_and_negative():
    # Affirmative
    e_pos = gemini_agent._local_fallback_extract("I am a disabled applicant (40% loco-motor disability)", "en")
    assert e_pos.disability_status is True

    # Negative
    e_neg1 = gemini_agent._local_fallback_extract("I have no disability", "en")
    assert e_neg1.disability_status is False

    e_neg2 = gemini_agent._local_fallback_extract("No, I am not disabled", "en")
    assert e_neg2.disability_status is False

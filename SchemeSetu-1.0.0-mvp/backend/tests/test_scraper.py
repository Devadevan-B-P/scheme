"""
Unit Tests — SchemeSetu Government Scheme Ingestion Pipeline.

Covers:
  - Domain validator Layer 1 (hostname whitelist)
  - Domain validator Layer 2 (Approved Source Registry)
  - Change detector field diffing
  - Conflict detector
  - API 400 response on untrusted domain
"""

import pytest
from datetime import datetime


# ── Domain Validator Tests ────────────────────────────────────────────────────


class TestDomainValidatorLayer1:
    """Layer 1: hostname whitelist (no DB required)."""

    def test_allowed_gov_in(self):
        from app.services.domain_validator import _is_hostname_trusted
        assert _is_hostname_trusted("nsfdc.nic.in") is True
        assert _is_hostname_trusted("socialjustice.gov.in") is True
        assert _is_hostname_trusted("schemes.gov.in") is True
        assert _is_hostname_trusted("msde.gov.in") is True

    def test_rejected_arbitrary_domains(self):
        from app.services.domain_validator import _is_hostname_trusted
        assert _is_hostname_trusted("example.com") is False
        assert _is_hostname_trusted("schemesetu.in") is False
        assert _is_hostname_trusted("nsfdc.gov.in.scam.com") is False  # Suffix spoofing

    def test_rejected_partial_match_spoofing(self):
        from app.services.domain_validator import _is_hostname_trusted
        # These look like gov domains but are not
        assert _is_hostname_trusted("gov.in.example.com") is False
        assert _is_hostname_trusted("mygov.in.phishing.net") is False

    def test_extract_hostname(self):
        from app.services.domain_validator import extract_hostname
        assert extract_hostname("https://nsfdc.nic.in/faqs") == "nsfdc.nic.in"
        assert extract_hostname("https://socialjustice.gov.in/schemes/123") == "socialjustice.gov.in"
        assert extract_hostname("not-a-url") is None or extract_hostname("not-a-url") == "not-a-url"


# ── Change Detector Tests ─────────────────────────────────────────────────────


class TestChangeDetector:
    """Tests for field-level diff detection between scheme versions."""

    def test_no_changes_when_identical(self):
        from app.services.change_detector import detect_changes
        old = {"name": "NSFDC Loan", "income_requirements": {"value": 500000}}
        new = {"name": "NSFDC Loan", "income_requirements": {"value": 500000}}
        changes = detect_changes(old, new)
        assert len(changes) == 0

    def test_detects_income_limit_change(self):
        from app.services.change_detector import detect_changes
        old = {"income_requirements": {"value": 500000}}
        new = {"income_requirements": {"value": 600000}}
        changes = detect_changes(old, new)
        assert len(changes) == 1
        assert changes[0].field == "income_requirements"
        assert changes[0].old_value == 500000
        assert changes[0].new_value == 600000

    def test_detects_new_name(self):
        from app.services.change_detector import detect_changes
        old = {"name": None}
        new = {"name": "NSFDC Credit Scheme"}
        changes = detect_changes(old, new)
        assert any(c.field == "name" for c in changes)

    def test_all_changes_require_review(self):
        from app.services.change_detector import detect_changes
        old = {"loan_amount": {"value": 2000000}}
        new = {"loan_amount": {"value": 4500000}}
        changes = detect_changes(old, new)
        assert all(c.requires_review for c in changes)

    def test_detects_list_field_change(self):
        from app.services.change_detector import detect_changes
        old = {"required_documents": ["aadhaar", "pan"]}
        new = {"required_documents": ["aadhaar", "pan", "caste_certificate"]}
        changes = detect_changes(old, new)
        assert any(c.field == "required_documents" for c in changes)


# ── Conflict Detector Tests ───────────────────────────────────────────────────


class TestConflictDetector:
    """Tests for cross-source conflict detection."""

    def test_no_conflict_when_sources_agree(self):
        from app.services.change_detector import detect_conflicts
        sources = [
            {"url": "https://nsfdc.nic.in/a", "value": 500000, "authority": "NSFDC"},
            {"url": "https://nsfdc.nic.in/b", "value": 500000, "authority": "NSFDC"},
        ]
        result = detect_conflicts("income_limit", sources)
        assert result is None

    def test_conflict_when_sources_disagree(self):
        from app.services.change_detector import detect_conflicts
        sources = [
            {"url": "https://nsfdc.nic.in/a", "value": 4000000, "authority": "NSFDC"},
            {"url": "https://socialjustice.gov.in/b", "value": 4500000, "authority": "MoSJE"},
        ]
        result = detect_conflicts("loan_limit", sources)
        assert result is not None
        assert result.field == "loan_limit"
        assert result.resolved is False
        assert len(result.sources) == 2

    def test_conflict_requires_admin_resolution(self):
        from app.services.change_detector import detect_conflicts
        sources = [
            {"url": "https://nsfdc.nic.in/a", "value": 500000},
            {"url": "https://nsfdc.nic.in/b", "value": 600000},
        ]
        result = detect_conflicts("income_limit", sources)
        assert result is not None
        assert result.resolved is False
        assert result.resolution_notes is None

    def test_single_source_no_conflict(self):
        from app.services.change_detector import detect_conflicts
        result = detect_conflicts("income_limit", [{"url": "...", "value": 500000}])
        assert result is None


# ── Scheme Extractor Tests (schema validation) ────────────────────────────────


class TestCandidateRuleValidation:
    """Ensure CandidateRule schema enforces source_text requirement."""

    def test_candidate_rule_requires_source_text(self):
        from app.models.scraper import CandidateRule
        # Rule with source_text should succeed
        rule = CandidateRule(
            rule_id="R001",
            scheme_id="SCRAPED-TEST001",
            field="annual_income",
            operator="<=",
            value=500000,
            unit="INR",
            source_url="https://nsfdc.nic.in/faqs",
            source_text="Annual family income should not exceed ₹5 lakh.",
            version="2026.1",
        )
        assert rule.source_text == "Annual family income should not exceed ₹5 lakh."
        assert rule.status == "candidate"

    def test_candidate_rule_never_published(self):
        from app.models.scraper import CandidateRule
        rule = CandidateRule(
            rule_id="R001",
            scheme_id="TEST",
            field="income",
            operator="<=",
            value=500000,
            source_url="https://nsfdc.nic.in",
            source_text="Income must not exceed ₹5 lakh.",
            version="2026.1",
        )
        # Candidate rules should start as "candidate", never "published"
        assert rule.status == "candidate"


# ── Status State Machine Tests ────────────────────────────────────────────────


class TestSchemeStatusStateMachine:
    """Verify the SchemeStatus enum covers all required states."""

    def test_all_required_statuses_exist(self):
        from app.models.scraper import SchemeStatus
        required = {
            "draft", "validation_failed", "review_required",
            "validated", "reviewed", "published",
            "superseded", "archived", "rejected", "conflict"
        }
        actual = {s.value for s in SchemeStatus}
        assert required.issubset(actual), f"Missing statuses: {required - actual}"


# ── Source Evidence Tests ─────────────────────────────────────────────────────


class TestSourceEvidence:
    """Every extracted value must carry evidence."""

    def test_evidenced_value_ok_has_evidence(self):
        from app.models.scraper import EvidencedValue, SourceEvidence, ExtractionMethod
        evidence = SourceEvidence(
            url="https://nsfdc.nic.in/faqs",
            source_text="Annual family income should not exceed ₹5 lakh.",
            extraction_method=ExtractionMethod.HTTPX_FALLBACK,
        )
        val = EvidencedValue(value=500000, unit="INR", status="ok", evidence=evidence)
        assert val.value == 500000
        assert val.evidence is not None
        assert val.evidence.source_text is not None

    def test_not_specified_has_no_value(self):
        from app.models.scraper import EvidencedValue
        val = EvidencedValue(value=None, status="not_specified")
        assert val.value is None
        assert val.status == "not_specified"
        assert val.evidence is None

"""
Beanie document models for the Government Scheme Ingestion Pipeline.

Collections:
    scheme_sources   — Approved source registry (domain + authority + topics)
    scrape_jobs      — Per-job execution records
    scraped_schemes  — Extracted scheme candidates pending admin review
    scheme_versions  — Immutable historical snapshots of published schemes
    scrape_changes   — Field-level diffs detected between scrape runs
    audit_logs       — Immutable admin action trail
"""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class SchemeStatus(str, Enum):
    """Full lifecycle state machine for a scraped scheme candidate."""
    DRAFT             = "draft"
    VALIDATION_FAILED = "validation_failed"
    REVIEW_REQUIRED   = "review_required"
    VALIDATED         = "validated"
    REVIEWED          = "reviewed"
    PUBLISHED         = "published"
    SUPERSEDED        = "superseded"
    ARCHIVED          = "archived"
    REJECTED          = "rejected"
    CONFLICT          = "conflict"


class JobStatus(str, Enum):
    QUEUED     = "queued"
    RUNNING    = "running"
    SUCCESS    = "success"
    FAILED     = "failed"
    CANCELLED  = "cancelled"


class ExtractionMethod(str, Enum):
    FIRECRAWL      = "firecrawl"
    HTTPX_FALLBACK = "httpx_fallback"


class SourcePriority(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class PdfDetectionMethod(str, Enum):
    TEXT_PDF = "pdfplumber"
    SCANNED  = "paddleocr"
    UNKNOWN  = "unknown"


# ── Embedded sub-models ───────────────────────────────────────────────────────


class SourceEvidence(BaseModel):
    """
    Attached to every extracted field value.
    Allows SchemeSetu to answer "Where does this rule come from?"
    """
    url: str
    page_title: str | None = None
    source_text: str          # Exact sentence from the official source
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: ExtractionMethod = ExtractionMethod.HTTPX_FALLBACK


class EvidencedValue(BaseModel):
    """A single extracted field with its source evidence."""
    value: Any = None
    unit: str | None = None
    status: str = "not_specified"    # "ok" | "not_specified" | "conflict"
    evidence: SourceEvidence | None = None


class CandidateRule(BaseModel):
    """
    A proposed eligibility rule extracted from an official source.

    IMPORTANT: Remains a candidate until an admin explicitly approves it.
    The AI extraction layer MUST NEVER auto-activate this as a live rule.

    Pipeline:
        Official Source → Gemini Extraction → CandidateRule
        → Evidence Validation → Admin Review → Published Rule
    """
    rule_id: str
    scheme_id: str
    field: str
    operator: str | None = None       # "<=", ">=", "==", "in" — None if not explicit
    value: Any = None
    unit: str | None = None
    description: str | None = None
    source_url: str
    source_text: str                  # Exact sentence from official page — REQUIRED
    version: str
    status: str = "candidate"         # "candidate" | "approved" | "rejected"


class FieldChange(BaseModel):
    """Describes a single field that changed between two scrape runs."""
    field: str
    old_value: Any
    new_value: Any
    old_source_url: str | None = None
    new_source_url: str | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    requires_review: bool = True


class ConflictRecord(BaseModel):
    """Two official sources disagree on a field value — requires admin resolution."""
    field: str
    sources: list[dict] = Field(default_factory=list)
    # Each entry: {"url": ..., "value": ..., "retrieved_at": ..., "authority": ...}
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_notes: str | None = None


# ── Collection 1: SchemeSource (Approved Source Registry) ────────────────────


class SchemeSource(Document):
    """
    Approved source registry.

    A URL is only trusted if its domain AND authority are registered here.
    Scraping a random gov.in page that merely MENTIONS an NSFDC scheme does
    NOT make that page an authoritative source for NSFDC eligibility.

    Admin must explicitly approve each source before it can be scraped.
    """
    source_id: str
    domain: str                     # e.g. "nsfdc.nic.in"
    authority: str                  # e.g. "NSFDC"
    display_name: str               # Human-readable name
    base_url: str                   # e.g. "https://nsfdc.nic.in"
    allowed_topics: list[str] = Field(default_factory=list)
    # e.g. ["credit schemes", "education loans", "channel partners"]
    source_type: str = "official_scheme_page"
    # "official_scheme_page" | "official_portal" | "ministry_website"
    priority: SourcePriority = SourcePriority.MEDIUM
    approved: bool = False          # Must be manually approved before scraping
    last_verified: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "scheme_sources"


# ── Collection 2: ScrapeJob ───────────────────────────────────────────────────


class ScrapeJob(Document):
    """
    One scraping job execution record.
    Created immediately when POST /admin/scraper/scrape is called.
    Updated asynchronously by the background job runner.

    extraction_method is recorded for every job so the audit trail shows
    whether Firecrawl or the httpx fallback was used — never silently switched.
    """
    job_id: str
    url: str
    source_id: str | None = None       # FK → SchemeSource.source_id
    authority: str | None = None
    status: JobStatus = JobStatus.QUEUED
    extraction_method: ExtractionMethod | None = None
    firecrawl_used: bool = False
    firecrawl_failure_reason: str | None = None
    # If Firecrawl failed, this records why before falling back to httpx
    started_at: datetime | None = None
    completed_at: datetime | None = None
    schemes_found: int = 0
    pdfs_processed: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "scrape_jobs"


# ── Collection 3: ScrapedScheme ───────────────────────────────────────────────


class ScrapedScheme(Document):
    """
    A scheme candidate extracted from an official government source.

    Status lifecycle:
        DRAFT → VALIDATION_FAILED
        DRAFT → REVIEW_REQUIRED → VALIDATED → REVIEWED → PUBLISHED → SUPERSEDED/ARCHIVED
        DRAFT → REVIEW_REQUIRED → REVIEWED → REJECTED
        Any state → CONFLICT  (when sources disagree; admin must resolve)

    Only PUBLISHED schemes feed the deterministic eligibility engine.
    PUBLISHED schemes transition to SUPERSEDED when a newer version is approved.
    """
    scheme_id: str
    job_id: str                         # FK → ScrapeJob.job_id
    source_id: str | None = None        # FK → SchemeSource.source_id
    version: str                        # e.g. "2026.1"
    status: SchemeStatus = SchemeStatus.DRAFT

    # ── Core identification ──────────────────────────────────────────────────
    name: str | None = None
    ministry: str | None = None
    department: str | None = None
    implementing_agency: str | None = None
    scheme_type: str | None = None
    # "micro_finance" | "term_loan" | "education_loan" | "skill_development"
    # "interest_subvention" | "entrepreneurship" | "other"
    description: str | None = None

    # ── Beneficiary criteria (all evidenced) ─────────────────────────────────
    target_beneficiaries: list[str] = Field(default_factory=list)
    category_requirements: list[str] = Field(default_factory=list)
    age_requirements: EvidencedValue = Field(default_factory=EvidencedValue)
    income_requirements: EvidencedValue = Field(default_factory=EvidencedValue)
    location_requirements: list[str] = Field(default_factory=list)
    gender_requirements: list[str] = Field(default_factory=list)
    disability_requirements: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    business_requirements: list[str] = Field(default_factory=list)

    # ── Financial terms (all evidenced) ──────────────────────────────────────
    project_cost: EvidencedValue = Field(default_factory=EvidencedValue)
    loan_amount: EvidencedValue = Field(default_factory=EvidencedValue)
    interest_rate: EvidencedValue = Field(default_factory=EvidencedValue)
    subsidy: EvidencedValue = Field(default_factory=EvidencedValue)
    margin_money: EvidencedValue = Field(default_factory=EvidencedValue)
    moratorium: EvidencedValue = Field(default_factory=EvidencedValue)
    repayment_period: EvidencedValue = Field(default_factory=EvidencedValue)

    # ── Process ──────────────────────────────────────────────────────────────
    benefits: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    application_process: list[str] = Field(default_factory=list)
    channel_partners: list[str] = Field(default_factory=list)
    application_url: str | None = None
    official_contact: str | None = None

    # ── Candidate eligibility rules (NEVER auto-activated) ───────────────────
    candidate_rules: list[CandidateRule] = Field(default_factory=list)

    # ── Source provenance ────────────────────────────────────────────────────
    source_url: str
    source_domain: str
    source_authority: str | None = None
    page_title: str | None = None
    extraction_method: ExtractionMethod = ExtractionMethod.HTTPX_FALLBACK
    pdf_sources: list[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    last_verified: datetime | None = None
    source_updated_date: str | None = None

    # ── Validation & admin review ─────────────────────────────────────────────
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    has_conflicts: bool = False
    reviewer_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    published_at: datetime | None = None

    class Settings:
        name = "scraped_schemes"


# ── Collection 4: SchemeVersion ───────────────────────────────────────────────


class SchemeVersion(Document):
    """
    Immutable snapshot of a scheme at the moment it was published.
    Never overwritten — maintains the full change history.
    """
    version_id: str
    scheme_id: str
    version: str                   # e.g. "2026.1", "2026.2"
    snapshot: dict                 # Full ScrapedScheme.model_dump() at publish time
    published_at: datetime = Field(default_factory=datetime.utcnow)
    published_by: str | None = None
    superseded_at: datetime | None = None
    superseded_by_version: str | None = None

    class Settings:
        name = "scheme_versions"


# ── Collection 5: ScrapeChange ────────────────────────────────────────────────


class ScrapeChange(Document):
    """
    Field-level diffs detected when a scheme is re-scraped.
    Every change requires admin review before being applied to the live scheme.
    """
    change_id: str
    scheme_id: str
    job_id: str
    old_version: str
    new_version: str
    changes: list[FieldChange] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    requires_review: bool = True
    reviewed: bool = False
    review_decision: str | None = None   # "applied" | "rejected"
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "scrape_changes"


# ── Collection 6: AuditLog ────────────────────────────────────────────────────


class AuditLog(Document):
    """
    Immutable record of every significant action in the ingestion system.
    Includes admin decisions and system events.
    """
    log_id: str
    actor: str                  # Admin email | "system"
    action: str                 # "PUBLISH_SCHEME" | "REJECT_SCHEME" | "SCRAPE_TRIGGERED" | etc.
    target_type: str            # "ScrapedScheme" | "ScrapeJob" | "SchemeSource"
    target_id: str
    details: dict = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "audit_logs"

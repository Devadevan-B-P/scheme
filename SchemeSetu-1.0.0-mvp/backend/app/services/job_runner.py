"""
Job Runner — Background scrape job execution.

Design decisions:
  - Uses FastAPI BackgroundTasks for the current MVP (no Redis/Celery needed).
  - run_scrape_job() is fully isolated — the API layer just calls it via
    background_tasks.add_task(run_scrape_job, ...) and returns 202 immediately.
  - To migrate to Celery/RQ later, only this file needs to change. The API
    routes and scraper services remain unchanged.

Pipeline per job:
    Domain validation (Layer 1 + Layer 2)
        ↓
    Firecrawl / httpx fallback (extraction_method recorded explicitly)
        ↓
    PDF detection & extraction (text PDF → pdfplumber | scanned → PaddleOCR)
        ↓
    Gemini extraction (structured + candidate rules)
        ↓
    Change detection (vs existing published scheme if re-scrape)
        ↓
    Conflict detection
        ↓
    Validation
        ↓
    Save ScrapedScheme with status = DRAFT or REVIEW_REQUIRED
        ↓
    Update ScrapeJob status = SUCCESS or FAILED
        ↓
    Append AuditLog
"""

import logging
import uuid
from datetime import datetime, timezone

from app.models.scraper import (
    ScrapeJob,
    ScrapedScheme,
    SchemeVersion,
    AuditLog,
    JobStatus,
    SchemeStatus,
    ExtractionMethod,
    EvidencedValue,
    CandidateRule,
    ConflictRecord,
)
from app.services.domain_validator import validate_government_url
from app.services.firecrawl_service import scrape_url, crawl_scheme_source, PageContent
from app.services.pdf_extractor import extract_pdf_text
from app.services.scheme_extractor import extract_scheme_data
from app.services.change_detector import detect_changes, create_scrape_change_record

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _generate_scheme_id(name: str | None, authority: str | None) -> str:
    """Generate a clean, deterministic scheme_id slug."""
    base = name or "UNKNOWN_SCHEME"
    slug = base.upper().replace(" ", "_").replace("-", "_")
    clean = "".join(c for c in slug if c.isalnum() or c == "_")[:24]
    auth_prefix = (authority or "GOV").upper()[:6]
    return f"{auth_prefix}_{clean}"


def _validate_extracted_scheme(data: dict) -> tuple[list[str], list[str]]:
    """
    Run baseline validation on extracted scheme data.
    Returns (errors, warnings).
    Errors block publication. Warnings require reviewer attention.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Hard requirements for a scheme to ever be published
    if not data.get("scheme_name"):
        errors.append("Scheme name was not found in the official source text.")

    if not data.get("target_beneficiaries") and not data.get("category_requirements"):
        warnings.append("No explicit beneficiary or category criteria found.")

    # Check that financial fields have evidence if values are present
    financial_fields = ["loan_amount", "interest_rate", "income_ceiling", "subsidy"]
    for f in financial_fields:
        val = data.get(f)
        if isinstance(val, EvidencedValue) and val.value is not None:
            if not val.evidence or not val.evidence.source_text:
                errors.append(f"Financial field '{f}' has a value but no source_text evidence.")

    # Candidate rules check
    candidate_rules: list[CandidateRule] = data.get("candidate_rules", [])
    for rule in candidate_rules:
        if not rule.source_text:
            errors.append(f"Candidate rule '{rule.field}' has no source_text evidence.")

    return errors, warnings


def _determine_initial_status(
    errors: list[str],
    warnings: list[str],
    conflicts: list[ConflictRecord],
) -> SchemeStatus:
    """Determine the initial lifecycle status of a newly extracted candidate."""
    if conflicts:
        return SchemeStatus.CONFLICT
    if errors:
        return SchemeStatus.VALIDATION_FAILED
    if warnings:
        return SchemeStatus.REVIEW_REQUIRED
    return SchemeStatus.DRAFT


def _build_scraped_scheme(
    extracted: dict,
    job: ScrapeJob,
    page_content: PageContent,
    version: str,
    validation_errors: list[str],
    validation_warnings: list[str],
    conflicts: list[ConflictRecord],
    pdf_sources: list[str],
) -> ScrapedScheme:
    """Construct a ScrapedScheme Beanie document from extraction results."""
    scheme_id = _generate_scheme_id(
        extracted.get("scheme_name"),
        job.authority,
    )
    status = _determine_initial_status(validation_errors, validation_warnings, conflicts)

    return ScrapedScheme(
        scheme_id=scheme_id,
        job_id=job.job_id,
        source_id=job.source_id,
        version=version,
        status=status,
        name=extracted.get("scheme_name"),
        ministry=extracted.get("ministry"),
        department=extracted.get("department"),
        implementing_agency=extracted.get("implementing_agency"),
        scheme_type=extracted.get("scheme_type"),
        description=extracted.get("description"),
        target_beneficiaries=extracted.get("target_beneficiaries", []),
        category_requirements=extracted.get("category_requirements", []),
        age_requirements=extracted.get("age_requirements", EvidencedValue()),
        income_requirements=extracted.get("income_requirements", EvidencedValue()),
        location_requirements=extracted.get("location_requirements", []),
        gender_requirements=extracted.get("gender_requirements", []),
        disability_requirements=extracted.get("disability_requirements", []),
        education_requirements=extracted.get("education_requirements", []),
        business_requirements=extracted.get("business_requirements", []),
        project_cost=extracted.get("project_cost", EvidencedValue()),
        loan_amount=extracted.get("loan_amount", EvidencedValue()),
        interest_rate=extracted.get("interest_rate", EvidencedValue()),
        subsidy=extracted.get("subsidy", EvidencedValue()),
        margin_money=extracted.get("margin_money", EvidencedValue()),
        moratorium=extracted.get("moratorium", EvidencedValue()),
        repayment_period=extracted.get("repayment_period", EvidencedValue()),
        benefits=extracted.get("benefits", []),
        required_documents=extracted.get("required_documents", []),
        application_process=extracted.get("application_process", []),
        channel_partners=extracted.get("channel_partners", []),
        application_url=extracted.get("application_url"),
        official_contact=extracted.get("official_contact"),
        candidate_rules=extracted.get("candidate_rules", []),
        source_url=page_content.url,
        source_domain=page_content.hostname,
        source_authority=job.authority,
        page_title=page_content.page_title,
        extraction_method=page_content.extraction_method,
        pdf_sources=pdf_sources,
        scraped_at=datetime.now(timezone.utc),
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        conflicts=conflicts,
        has_conflicts=len(conflicts) > 0,
    )


# ── Main Entry Point ──────────────────────────────────────────────────────────


async def run_scrape_job(job_id: str) -> None:
    """
    Main background job execution loop.

    Steps:
    1. Load ScrapeJob from MongoDB.
    2. Validate URL (two-layer check).
    3. Scrape page (Firecrawl → httpx fallback).
    4. Process any linked official PDFs.
    5. Extract structured scheme data with Gemini.
    6. Run change & conflict detection vs existing published schemes.
    7. Validate extracted fields.
    8. Save ScrapedScheme (status = DRAFT / REVIEW_REQUIRED / CONFLICT).
    9. Update ScrapeJob (SUCCESS / FAILED).
    10. Write AuditLog entry.
    """
    logger.info(f"[job_runner] Starting scrape job {job_id}")

    job = await ScrapeJob.find_one(ScrapeJob.job_id == job_id)
    if not job:
        logger.error(f"[job_runner] Job {job_id} not found in database.")
        return

    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    await job.save()

    all_errors: list[str] = []
    all_warnings: list[str] = []
    scraped_schemes: list[ScrapedScheme] = []

    try:
        # ── Step 1: URL Validation ───────────────────────────────────────────
        validation = await validate_government_url(job.url)
        if not validation.allowed:
            job.status = JobStatus.FAILED
            job.errors.append(f"Domain validation failed: {validation.rejection_reason}")
            job.completed_at = datetime.now(timezone.utc)
            await job.save()
            logger.warning(f"[job_runner] Job {job_id} failed URL validation: {validation.rejection_reason}")
            return

        if validation.source_record:
            job.source_id = validation.source_record.source_id
            job.authority = validation.authority

        # ── Step 2: Scrape main page ─────────────────────────────────────────
        logger.info(f"[job_runner] Scraping {job.url} for job {job_id}")
        page_content = await scrape_url(job.url)

        job.extraction_method = page_content.extraction_method
        job.firecrawl_used = page_content.firecrawl_used
        job.firecrawl_failure_reason = page_content.firecrawl_failure_reason
        await job.save()

        # Combine page content for extraction
        combined_text = page_content.markdown_text
        pdf_sources_used: list[str] = []

        # ── Step 3: Process linked official PDFs ──────────────────────────────
        for pdf_url in page_content.pdf_links[:3]:  # Cap at 3 PDFs per job
            try:
                logger.info(f"[job_runner] Extracting linked PDF: {pdf_url}")
                pdf_result = await extract_pdf_text(pdf_url)
                if pdf_result.extracted_text:
                    job.pdfs_processed += 1
                    pdf_sources_used.append(pdf_url)
                    combined_text += (
                        f"\n\n--- CONTENT FROM OFFICIAL PDF ({pdf_url}) ---\n"
                        f"{pdf_result.extracted_text}"
                    )
            except Exception as exc:
                all_warnings.append(f"Could not process linked PDF {pdf_url}: {exc}")

        # ── Step 4: Extract with Gemini ──────────────────────────────────────
        version = f"{datetime.now(timezone.utc).year}.1"
        extracted = await extract_scheme_data(
            content=combined_text,
            source_url=job.url,
            page_title=page_content.page_title,
            extraction_method=page_content.extraction_method,
            version=version,
        )

        if "error" in extracted and not extracted.get("scheme_name"):
            all_errors.append(f"Extraction error: {extracted['error']}")

        # ── Step 5: Change & Conflict Detection ──────────────────────────────
        conflicts: list[ConflictRecord] = []
        if extracted.get("scheme_name"):
            # Check if this scheme was already published
            existing = await ScrapedScheme.find_one(
                ScrapedScheme.name == extracted.get("scheme_name"),
                ScrapedScheme.status == SchemeStatus.PUBLISHED,
            )
            if existing:
                changes = detect_changes(
                    old_data=existing.model_dump(),
                    new_data=extracted,
                    old_source_url=existing.source_url,
                    new_source_url=job.url,
                )
                if changes:
                    await create_scrape_change_record(
                        scheme_id=existing.scheme_id,
                        job_id=job.job_id,
                        old_version=existing.version,
                        new_version=version,
                        changes=changes,
                        conflicts=[],
                    )
                    all_warnings.append(
                        f"Detected {len(changes)} changed fields compared to published version {existing.version}."
                    )

        # ── Step 6: Validate extracted fields ────────────────────────────────
        v_errors, v_warnings = _validate_extracted_scheme(extracted)
        all_errors.extend(v_errors)
        all_warnings.extend(v_warnings)

        # ── Step 7: Build and save ScrapedScheme ──────────────────────────────
        scraped_scheme = _build_scraped_scheme(
            extracted=extracted,
            job=job,
            page_content=page_content,
            version=version,
            validation_errors=all_errors,
            validation_warnings=all_warnings,
            conflicts=conflicts,
            pdf_sources=pdf_sources_used,
        )
        await scraped_scheme.insert()
        scraped_schemes.append(scraped_scheme)
        job.schemes_found = len(scraped_schemes)

        # ── Step 8: Update job status ────────────────────────────────────────
        job.status = JobStatus.SUCCESS if not all_errors else JobStatus.FAILED
        job.errors = all_errors
        job.warnings = all_warnings
        job.completed_at = datetime.now(timezone.utc)
        await job.save()

        # ── Step 9: Audit Log ────────────────────────────────────────────────
        audit = AuditLog(
            log_id=str(uuid.uuid4()),
            actor="system",
            action="SCRAPE_JOB_COMPLETED",
            target_type="ScrapeJob",
            target_id=job.job_id,
            details={
                "url": job.url,
                "status": job.status.value,
                "extraction_method": job.extraction_method.value if job.extraction_method else None,
                "firecrawl_used": job.firecrawl_used,
                "schemes_found": job.schemes_found,
                "pdfs_processed": job.pdfs_processed,
                "errors_count": len(all_errors),
                "warnings_count": len(all_warnings),
            },
            created_at=datetime.now(timezone.utc),
        )
        await audit.insert()

        logger.info(
            f"[job_runner] Job {job_id} completed with status {job.status.value}. "
            f"Method: {job.extraction_method.value if job.extraction_method else 'none'}, "
            f"Schemes: {job.schemes_found}"
        )

    except Exception as exc:
        logger.exception(f"[job_runner] Unhandled exception in job {job_id}: {exc}")
        job.status = JobStatus.FAILED
        job.errors.append(f"Unexpected runner error: {exc}")
        job.completed_at = datetime.now(timezone.utc)
        await job.save()

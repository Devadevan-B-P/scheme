"""
Admin Scraper API Routes.

All routes require admin role (enforced by convention — add JWT middleware later).

POST /admin/scraper/scrape          → 202 Accepted + job_id (non-blocking)
GET  /admin/scraper/jobs            → list all jobs
GET  /admin/scraper/jobs/{job_id}   → single job detail
GET  /admin/scraper/schemes         → list scraped schemes (filterable by status)
GET  /admin/scraper/schemes/{id}    → single scheme detail
GET  /admin/scraper/schemes/{id}/versions → version history
POST /admin/scraper/schemes/{id}/publish  → admin publish
POST /admin/scraper/schemes/{id}/reject   → admin reject
GET  /admin/scraper/changes         → pending field changes
POST /admin/sources                 → register a new approved source
GET  /admin/sources                 → list all sources
PATCH /admin/sources/{id}/approve   → approve a source for scraping
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from app.models.scraper import (
    ScrapeJob,
    ScrapedScheme,
    SchemeSource,
    SchemeVersion,
    ScrapeChange,
    AuditLog,
    JobStatus,
    SchemeStatus,
    SourcePriority,
)
from app.services.domain_validator import validate_government_url
from app.services.job_runner import run_scrape_job

router = APIRouter(tags=["Admin Scraper"])


# ── Request / Response schemas ────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    url: str
    actor: str = "admin"   # Who triggered the scrape


class PublishRequest(BaseModel):
    reviewer_notes: str | None = None
    actor: str = "admin"


class RejectRequest(BaseModel):
    reason: str
    actor: str = "admin"


class RegisterSourceRequest(BaseModel):
    domain: str
    authority: str
    display_name: str
    base_url: str
    allowed_topics: list[str] = []
    source_type: str = "official_scheme_page"
    priority: SourcePriority = SourcePriority.MEDIUM
    notes: str | None = None


# ── Helper ────────────────────────────────────────────────────────────────────


async def _audit(actor: str, action: str, target_type: str, target_id: str, details: dict = {}) -> None:
    log = AuditLog(
        log_id=str(uuid.uuid4()),
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        created_at=datetime.now(timezone.utc),
    )
    await log.insert()


# ── Source Registry ───────────────────────────────────────────────────────────


@router.post("/sources", status_code=201)
async def register_source(request: RegisterSourceRequest) -> dict:
    """
    Register a new government domain in the Approved Source Registry.
    Source is created with approved=False — an admin must explicitly approve it
    before it can be scraped.
    """
    existing = await SchemeSource.find_one(SchemeSource.domain == request.domain)
    if existing:
        raise HTTPException(status_code=400, detail=f"Domain '{request.domain}' is already registered.")

    source = SchemeSource(
        source_id=str(uuid.uuid4()),
        domain=request.domain,
        authority=request.authority,
        display_name=request.display_name,
        base_url=request.base_url,
        allowed_topics=request.allowed_topics,
        source_type=request.source_type,
        priority=request.priority,
        approved=False,     # Must be explicitly approved before scraping
        notes=request.notes,
        created_at=datetime.now(timezone.utc),
    )
    await source.insert()
    return {"message": "Source registered. Approve it before it can be scraped.", "source_id": source.source_id}


@router.get("/sources")
async def list_sources() -> list[dict]:
    """List all registered government sources."""
    sources = await SchemeSource.find_all().to_list()
    return [s.model_dump(mode="json", exclude={"id"}) for s in sources]


@router.patch("/sources/{source_id}/approve")
async def approve_source(source_id: str, actor: str = "admin") -> dict:
    """Approve a registered source, allowing it to be scraped."""
    source = await SchemeSource.find_one(SchemeSource.source_id == source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")

    source.approved = True
    source.last_verified = datetime.now(timezone.utc)
    await source.save()

    await _audit(actor, "SOURCE_APPROVED", "SchemeSource", source_id, {"domain": source.domain})
    return {"message": f"Source '{source.domain}' approved for scraping.", "source_id": source_id}


# ── Scrape Job Endpoints ──────────────────────────────────────────────────────


@router.post("/scraper/scrape", status_code=202)
async def trigger_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Trigger a government page scrape.

    Returns 202 Accepted immediately with a job_id.
    The scrape runs in the background via FastAPI BackgroundTasks.
    (Can be swapped to Celery without changing this endpoint.)
    """
    url = request.url.strip()

    # Quick Layer 1 check before even queuing
    from app.services.domain_validator import _is_hostname_trusted, extract_hostname
    hostname = extract_hostname(url) or ""
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: no hostname found.")
    if not _is_hostname_trusted(hostname):
        raise HTTPException(
            status_code=400,
            detail=f"Domain '{hostname}' is not a trusted government domain. "
                   "Only .gov.in and .nic.in domains are permitted.",
        )

    # Create job record
    job_id = str(uuid.uuid4())
    job = ScrapeJob(
        job_id=job_id,
        url=url,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
    )
    await job.insert()

    # Audit log
    await _audit(request.actor, "SCRAPE_TRIGGERED", "ScrapeJob", job_id, {"url": url})

    # Hand off to background task
    background_tasks.add_task(run_scrape_job, job_id, url)

    return {
        "status": "queued",
        "job_id": job_id,
        "url": url,
        "message": "Scrape job queued. Poll GET /admin/scraper/jobs/{job_id} for status.",
    }


@router.get("/scraper/jobs")
async def list_jobs(
    limit: int = Query(default=50, le=200),
    status: Optional[str] = None,
) -> list[dict]:
    """List scrape jobs, optionally filtered by status."""
    query = ScrapeJob.find_all()
    jobs = await query.to_list()
    result = [j.model_dump(mode="json", exclude={"id"}) for j in jobs]
    if status:
        result = [j for j in result if j.get("status") == status]
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]


@router.get("/scraper/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    """Get a single scrape job with full detail."""
    job = await ScrapeJob.find_one(ScrapeJob.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    job_data = job.model_dump(mode="json", exclude={"id"})

    # Include schemes found in this job
    schemes = await ScrapedScheme.find(ScrapedScheme.job_id == job_id).to_list()
    job_data["schemes"] = [
        {
            "scheme_id": s.scheme_id,
            "name": s.name,
            "status": s.status,
            "version": s.version,
            "has_conflicts": s.has_conflicts,
        }
        for s in schemes
    ]

    return job_data


# ── Scheme Registry Endpoints ─────────────────────────────────────────────────


@router.get("/scraper/schemes")
async def list_scraped_schemes(
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500),
) -> list[dict]:
    """
    List all scraped scheme candidates.
    Filter by status: draft | validation_failed | review_required |
                      validated | reviewed | published | superseded | rejected | conflict
    """
    all_schemes = await ScrapedScheme.find_all().to_list()
    result = [
        {
            "scheme_id": s.scheme_id,
            "name": s.name,
            "ministry": s.ministry,
            "status": s.status,
            "version": s.version,
            "source_url": s.source_url,
            "source_authority": s.source_authority,
            "extraction_method": s.extraction_method,
            "has_conflicts": s.has_conflicts,
            "candidate_rules_count": len(s.candidate_rules),
            "validation_errors": s.validation_errors,
            "validation_warnings": s.validation_warnings,
            "scraped_at": s.scraped_at.isoformat() if s.scraped_at else None,
            "published_at": s.published_at.isoformat() if s.published_at else None,
        }
        for s in all_schemes
    ]
    if status:
        result = [s for s in result if s.get("status") == status]
    return result[:limit]


@router.get("/scraper/schemes/{scheme_id}")
async def get_scraped_scheme(scheme_id: str) -> dict:
    """Get full detail of a scraped scheme candidate."""
    scheme = await ScrapedScheme.find_one(ScrapedScheme.scheme_id == scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")
    return scheme.model_dump(mode="json", exclude={"id"})


@router.get("/scraper/schemes/{scheme_id}/versions")
async def get_scheme_versions(scheme_id: str) -> list[dict]:
    """Get the full version history of a scheme."""
    versions = await SchemeVersion.find(SchemeVersion.scheme_id == scheme_id).to_list()
    return [v.model_dump(mode="json", exclude={"id"}) for v in versions]


@router.post("/scraper/schemes/{scheme_id}/publish")
async def publish_scheme(scheme_id: str, request: PublishRequest) -> dict:
    """
    Admin publishes a scraped scheme candidate.
    """
    scheme = await ScrapedScheme.find_one(ScrapedScheme.scheme_id == scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    if scheme.status in (SchemeStatus.PUBLISHED, SchemeStatus.ARCHIVED):
        raise HTTPException(status_code=400, detail=f"Scheme is already {scheme.status}.")

    if scheme.status == SchemeStatus.VALIDATION_FAILED and scheme.validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish: scheme has validation errors: {scheme.validation_errors}",
        )

    if scheme.has_conflicts:
        raise HTTPException(
            status_code=400,
            detail="Cannot publish: scheme has unresolved conflicts. Resolve them first.",
        )

    # Supersede any previously published version
    prev_published = await ScrapedScheme.find(
        ScrapedScheme.name == scheme.name,
        ScrapedScheme.status == SchemeStatus.PUBLISHED,
        ScrapedScheme.scheme_id != scheme_id,
    ).to_list()
    for prev in prev_published:
        prev.status = SchemeStatus.SUPERSEDED
        prev.published_at = None
        await prev.save()

    # Publish
    scheme.status = SchemeStatus.PUBLISHED
    scheme.published_at = datetime.now(timezone.utc)
    scheme.reviewed_by = request.actor
    scheme.reviewed_at = datetime.now(timezone.utc)
    scheme.reviewer_notes = request.reviewer_notes
    await scheme.save()

    # Create immutable version snapshot
    version_record = SchemeVersion(
        version_id=str(uuid.uuid4()),
        scheme_id=scheme_id,
        version=scheme.version,
        snapshot=scheme.model_dump(mode="json", exclude={"id"}),
        published_at=datetime.now(timezone.utc),
        published_by=request.actor,
    )
    await version_record.insert()

    await _audit(
        request.actor, "PUBLISH_SCHEME", "ScrapedScheme", scheme_id,
        {"scheme_name": scheme.name, "version": scheme.version, "source_url": scheme.source_url},
    )

    return {
        "message": f"Scheme '{scheme.name}' published successfully.",
        "scheme_id": scheme_id,
        "version": scheme.version,
        "status": "published",
    }


@router.post("/scraper/schemes/{scheme_id}/reject")
async def reject_scheme(scheme_id: str, request: RejectRequest) -> dict:
    """Admin rejects a scraped scheme candidate."""
    scheme = await ScrapedScheme.find_one(ScrapedScheme.scheme_id == scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    if scheme.status == SchemeStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Cannot reject a published scheme. Archive it instead.")

    scheme.status = SchemeStatus.REJECTED
    scheme.reviewer_notes = request.reason
    scheme.reviewed_by = request.actor
    scheme.reviewed_at = datetime.now(timezone.utc)
    await scheme.save()

    await _audit(
        request.actor, "REJECT_SCHEME", "ScrapedScheme", scheme_id,
        {"scheme_name": scheme.name, "reason": request.reason},
    )

    return {"message": f"Scheme '{scheme.name}' rejected.", "scheme_id": scheme_id, "status": "rejected"}


# ── Change Detection Endpoints ────────────────────────────────────────────────


@router.get("/scraper/changes")
async def list_pending_changes() -> list[dict]:
    """List all pending field change records that require admin review."""
    changes = await ScrapeChange.find(ScrapeChange.reviewed == False).to_list()  # noqa: E712
    return [c.model_dump(mode="json", exclude={"id"}) for c in changes]


# ── Audit Log Endpoint ────────────────────────────────────────────────────────


@router.get("/scraper/audit-logs")
async def list_audit_logs(limit: int = Query(default=100, le=500)) -> list[dict]:
    """List audit logs for the scraper system."""
    logs = await AuditLog.find_all().to_list()
    result = [log.model_dump(mode="json", exclude={"id"}) for log in logs]
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

"""
Change Detector — Field-level diff and conflict detection.

When a scheme is re-scraped:
  1. Compare newly extracted data against the stored version.
  2. Identify fields that have changed.
  3. Detect conflicts when two sources disagree on the same field.
  4. Create ScrapeChange records — admin must review before changes are applied.

RULE: Changes are NEVER automatically applied.
      Conflicts are NEVER automatically resolved.
      Admin review is ALWAYS required.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.scraper import FieldChange, ConflictRecord, ScrapeChange

logger = logging.getLogger(__name__)

# Fields tracked for change detection
TRACKED_FIELDS = [
    "name",
    "ministry",
    "scheme_type",
    "description",
    "category_requirements",
    "income_requirements",
    "age_requirements",
    "loan_amount",
    "interest_rate",
    "subsidy",
    "margin_money",
    "moratorium",
    "repayment_period",
    "project_cost",
    "required_documents",
    "application_process",
    "channel_partners",
    "target_beneficiaries",
]


def _normalize_value(value: Any) -> Any:
    """Normalize values for comparison (handles EvidencedValue dicts)."""
    if isinstance(value, dict):
        # For EvidencedValue-like dicts, compare only the value field
        return value.get("value")
    if isinstance(value, list):
        return sorted([str(v) for v in value])
    return value


def _values_differ(old: Any, new: Any) -> bool:
    """Return True if two field values are meaningfully different."""
    old_norm = _normalize_value(old)
    new_norm = _normalize_value(new)

    # If both are None or empty, they don't differ
    if old_norm is None and new_norm is None:
        return False
    if old_norm == "" and new_norm is None:
        return False
    if old_norm is None and new_norm == "":
        return False
    if old_norm == [] and new_norm == []:
        return False

    return old_norm != new_norm


def detect_changes(
    old_data: dict,
    new_data: dict,
    old_source_url: str | None = None,
    new_source_url: str | None = None,
) -> list[FieldChange]:
    """
    Compare old and new scheme data dicts field-by-field.
    Returns a list of FieldChange objects for all fields where values differ.
    """
    changes: list[FieldChange] = []

    for field_name in TRACKED_FIELDS:
        old_val = old_data.get(field_name)
        new_val = new_data.get(field_name)

        if _values_differ(old_val, new_val):
            logger.info(f"[change_detector] Change detected in '{field_name}': {old_val} → {new_val}")
            changes.append(
                FieldChange(
                    field=field_name,
                    old_value=_normalize_value(old_val),
                    new_value=_normalize_value(new_val),
                    old_source_url=old_source_url,
                    new_source_url=new_source_url,
                    detected_at=datetime.now(timezone.utc),
                    requires_review=True,
                )
            )

    return changes


def detect_conflicts(
    arg1: Any,
    arg2: Any = None,
    new_source_url: str | None = None,
    new_authority: str | None = None,
) -> Any:
    """
    Detect conflicts when multiple sources report different values for the same field.
    Supports two calling signatures:
      1. detect_conflicts(field_name: str, sources: list[dict]) -> ConflictRecord | None
      2. detect_conflicts(existing_schemes: list[dict], new_data: dict, ...) -> list[ConflictRecord]
    """
    # Signature 1: direct (field, sources)
    if isinstance(arg1, str) and isinstance(arg2, list):
        field_name = arg1
        sources = arg2
        if len(sources) < 2:
            return None
        first_val = sources[0].get("value")
        if any(_values_differ(first_val, s.get("value")) for s in sources[1:]):
            return ConflictRecord(
                field=field_name,
                sources=sources,
                detected_at=datetime.now(timezone.utc),
                resolved=False,
            )
        return None

    # Signature 2: scheme comparison
    existing_schemes = arg1 if isinstance(arg1, list) else []
    new_data = arg2 if isinstance(arg2, dict) else {}
    conflicts: list[ConflictRecord] = []

    for existing in existing_schemes:
        existing_url = existing.get("source_url", "")
        existing_authority = existing.get("source_authority", "")

        # Skip comparing a source to itself
        if existing_url == new_source_url:
            continue

        for field_name in ["loan_amount", "interest_rate", "income_requirements", "subsidy"]:
            old_val = existing.get(field_name)
            new_val = new_data.get(field_name)

            if _values_differ(old_val, new_val) and old_val is not None and new_val is not None:
                logger.warning(
                    f"[change_detector] CONFLICT detected for '{field_name}': "
                    f"{existing_url} ({old_val}) vs {new_source_url} ({new_val})"
                )
                conflicts.append(
                    ConflictRecord(
                        field=field_name,
                        sources=[
                            {
                                "url": existing_url,
                                "value": old_val,
                                "authority": existing_authority,
                                "retrieved_at": existing.get("scraped_at", datetime.now(timezone.utc).isoformat()),
                            },
                            {
                                "url": new_source_url or "",
                                "value": new_val,
                                "authority": new_authority,
                                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                            },
                        ],
                        detected_at=datetime.now(timezone.utc),
                        resolved=False,
                    )
                )

    return conflicts



async def create_scrape_change_record(
    scheme_id: str,
    job_id: str,
    old_version: str,
    new_version: str,
    changes: list[FieldChange],
    conflicts: list[ConflictRecord],
) -> ScrapeChange:
    """
    Persist a ScrapeChange document to MongoDB.
    An admin must review this record before changes take effect.
    """
    import uuid

    record = ScrapeChange(
        change_id=f"CHG_{uuid.uuid4().hex[:8].upper()}",
        scheme_id=scheme_id,
        job_id=job_id,
        old_version=old_version,
        new_version=new_version,
        changes=changes,
        conflicts=conflicts,
        requires_review=len(changes) > 0 or len(conflicts) > 0,
        reviewed=False,
        detected_at=datetime.now(timezone.utc),
    )
    await record.insert()
    return record

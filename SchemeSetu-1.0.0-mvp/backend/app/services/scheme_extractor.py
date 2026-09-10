"""
Scheme Extractor — Gemini-powered extraction with strict anti-hallucination rules.

CRITICAL RULE (enforced by prompt):
    If a value is NOT explicitly stated in the official source text:
        → value = null, status = "not_specified"
    NEVER invent or infer a value from context.

Every non-null field carries:
    evidence.source_text = exact sentence from the official page
    evidence.url = source URL

This makes SchemeSetu explainable:
    "Why is this rule this value?"
    → "Because the official NSFDC page at <url> states: '<source_text>'"

Pipeline enforced here:
    Official Source
        ↓
    Gemini extraction (extraction assistant only)
        ↓
    Structured CandidateRule (never auto-activated)
        ↓
    Evidence validation
        ↓
    Human admin review
        ↓
    Published deterministic rule
"""

import json
import logging
import re
from datetime import datetime, timezone

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.scraper import (
    EvidencedValue,
    SourceEvidence,
    CandidateRule,
    ExtractionMethod,
)

logger = logging.getLogger(__name__)


# ── Extraction prompt ─────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """
You are a structured data extraction assistant for SchemeSetu, a government scheme eligibility system.

Your ONLY job is to extract scheme information that is EXPLICITLY STATED in the provided official government source text.

STRICT RULES — THESE ARE ABSOLUTE:
1. If a piece of information is NOT explicitly written in the text, set its value to null and status to "not_specified".
2. NEVER invent, infer, assume, or guess any value.
3. NEVER use your training knowledge to fill gaps — only extract what the provided text says.
4. For every field where you find a value, provide the EXACT sentence from the text as evidence.source_text.
5. If a field is not mentioned, evidence must be null.
6. The output must be PURE JSON matching the requested schema. No conversational preamble, no markdown backticks.

CRITICAL: You are an extraction assistant only. You are NOT deciding eligibility.
The rules you extract will be reviewed by human administrators before being activated.
"""

EXTRACTION_USER_TEMPLATE = """
Extract all scheme information from this official government page into the JSON schema below.

SOURCE URL: {source_url}
PAGE TITLE: {page_title}
RETRIEVED AT: {retrieved_at}

PAGE TEXT:
---
{content}
---

Return JSON with exactly this structure:
{{
  "scheme_name": "exact name from page or null",
  "ministry": "ministry name or null",
  "department": "department name or null",
  "implementing_agency": "e.g. NSFDC, NBCFDC, or null",
  "scheme_type": "micro_finance | term_loan | education_loan | skill_development | interest_subvention | entrepreneurship | other",
  "description": "brief 1-2 sentence description from page or null",

  "target_beneficiaries": ["list of beneficiary groups explicitly mentioned"],
  "category_requirements": ["SC", "ST", "OBC", "General", etc. — only if explicitly stated],

  "income_ceiling": {{
    "value": 300000.0,
    "unit": "INR/year",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating the income limit",
      "url": "{source_url}"
    }}
  }},

  "age_requirements": {{
    "value": {{"min": 18, "max": 50}},
    "unit": "years",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating age requirements",
      "url": "{source_url}"
    }}
  }},

  "loan_amount": {{
    "value": {{"min": 50000, "max": 500000}},
    "unit": "INR",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating the loan limit",
      "url": "{source_url}"
    }}
  }},

  "interest_rate": {{
    "value": 6.0,
    "unit": "% p.a.",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating interest rate",
      "url": "{source_url}"
    }}
  }},

  "subsidy": {{
    "value": 10.0,
    "unit": "%",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating subsidy percentage or amount",
      "url": "{source_url}"
    }}
  }},

  "margin_money": {{
    "value": 5.0,
    "unit": "%",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating margin money requirement",
      "url": "{source_url}"
    }}
  }},

  "moratorium": {{
    "value": 6,
    "unit": "months",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating moratorium period",
      "url": "{source_url}"
    }}
  }},

  "repayment_period": {{
    "value": 60,
    "unit": "months",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating repayment tenure",
      "url": "{source_url}"
    }}
  }},

  "project_cost": {{
    "value": {{"min": null, "max": 500000}},
    "unit": "INR",
    "status": "ok | not_specified",
    "evidence": {{
      "source_text": "Exact sentence stating project cost limits",
      "url": "{source_url}"
    }}
  }},

  "location_requirements": ["state or region restrictions, or empty list if pan-India"],
  "gender_requirements": ["women only, etc., or empty list if all"],
  "disability_requirements": ["disability % requirement or empty list"],
  "education_requirements": ["minimum education or empty list"],
  "business_requirements": ["manufacturing, services, trading etc. or empty list"],

  "required_documents": ["list of required documents explicitly named in the text"],
  "application_process": ["step 1", "step 2", "etc."],
  "channel_partners": ["SCA", "Bank names", "CSC", etc. explicitly named as channel partners"],
  "application_url": "portal URL if mentioned, else null",
  "official_contact": "helpline or email if mentioned, else null",

  "candidate_rules": [
    {{
      "rule_id": "auto_generated",
      "field": "annual_income | age | category | state | business_type | project_cost",
      "operator": "<= | >= | == | in",
      "value": "extracted threshold value",
      "unit": "unit if applicable",
      "description": "Human readable rule description",
      "source_text": "Exact sentence from text that defines this rule",
      "status": "candidate"
    }}
  ]
}}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _clean_llm_json(raw_text: str) -> dict:
    """Strip markdown code fence blocks if LLM returned them despite instructions."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


def _parse_evidenced_value(
    raw: dict | None,
    source_url: str,
    method: ExtractionMethod,
) -> EvidencedValue:
    """Parse a raw JSON dict into a typed EvidencedValue."""
    if not raw or not isinstance(raw, dict):
        return EvidencedValue()

    evidence = None
    evidence_raw = raw.get("evidence")
    if evidence_raw and isinstance(evidence_raw, dict) and evidence_raw.get("source_text"):
        evidence = SourceEvidence(
            url=evidence_raw.get("url", source_url),
            page_title=evidence_raw.get("page_title"),
            source_text=evidence_raw["source_text"],
            extraction_method=method,
        )

    return EvidencedValue(
        value=raw.get("value"),
        unit=raw.get("unit"),
        status=raw.get("status", "ok") if raw.get("value") is not None else "not_specified",
        evidence=evidence,
    )


# ── Public API ────────────────────────────────────────────────────────────────


async def extract_scheme_data(
    content: str,
    source_url: str,
    page_title: str,
    extraction_method: ExtractionMethod = ExtractionMethod.HTTPX_FALLBACK,
    version: str | None = None,
) -> dict:
    """
    Use Gemini to extract structured scheme data from official government text.

    Returns a dict with all extracted fields. Every non-null value includes
    source_text evidence from the original page.

    IMPORTANT: Candidate rules in the output are NEVER auto-published.
    They must go through Admin Review → Published Rule.
    """
    if not version:
        version = f"{datetime.now(timezone.utc).year}.1"

    # Truncate very long content to avoid token limit issues
    MAX_CONTENT_CHARS = 8000
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "\n... [content truncated for length]"
        logger.info(f"[scheme_extractor] Content truncated to {MAX_CONTENT_CHARS} chars for {source_url}")

    user_message = EXTRACTION_USER_TEMPLATE.format(
        source_url=source_url,
        page_title=page_title,
        content=content,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        version=version,
    )

    if not settings.GEMINI_API_KEY:
        logger.warning("[scheme_extractor] GEMINI_API_KEY is not configured; cannot extract scheme data.")
        return {"error": "GEMINI_API_KEY not configured", "source_url": source_url}

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL or "gemini-3.8-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        raw_data = _clean_llm_json(response.text)
    except json.JSONDecodeError as exc:
        logger.error(f"[scheme_extractor] JSON parse error for {source_url}: {exc}")
        return {"error": f"LLM returned non-JSON output: {exc}", "source_url": source_url}
    except Exception as exc:
        logger.error(f"[scheme_extractor] Gemini call failed for {source_url}: {exc}")
        return {"error": str(exc), "source_url": source_url}

    # ── Parse EvidencedValue fields ────────────────────────────────────────────
    evidenced_fields = [
        "income_ceiling",
        "age_requirements",
        "loan_amount",
        "interest_rate",
        "subsidy",
        "margin_money",
        "moratorium",
        "repayment_period",
        "project_cost",
    ]

    for field_name in evidenced_fields:
        raw_data[field_name] = _parse_evidenced_value(
            raw_data.get(field_name),
            source_url=source_url,
            method=extraction_method,
        )

    # ── Parse CandidateRule items ──────────────────────────────────────────────
    raw_rules = raw_data.get("candidate_rules", [])
    candidate_rules: list[CandidateRule] = []

    for i, rule in enumerate(raw_rules):
        if not isinstance(rule, dict):
            continue
        # Candidate rule must have a source_text evidence sentence
        source_text = rule.get("source_text", "").strip()
        if not source_text:
            logger.warning(
                f"[scheme_extractor] Candidate rule {rule.get('field')} has no source_text evidence. Skipped."
            )
            continue

        rule_id = f"RULE_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{i + 1:03d}"
        candidate_rules.append(
            CandidateRule(
                rule_id=rule_id,
                scheme_id=raw_data.get("scheme_name", "UNKNOWN"),
                field=rule.get("field", "unknown"),
                operator=rule.get("operator"),
                value=rule.get("value"),
                unit=rule.get("unit"),
                description=rule.get("description"),
                source_url=source_url,
                source_text=source_text,
                version=version,
                status="candidate",  # Always candidate — NEVER auto-activate
            )
        )

    raw_data["candidate_rules"] = candidate_rules
    return raw_data

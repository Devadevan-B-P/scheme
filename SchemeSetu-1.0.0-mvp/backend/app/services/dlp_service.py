"""
Cloud DLP Service — Defense-in-Depth PII Sanitizer (Tier 2).

Architecture:
  raw_input → regex pre-filter (fast, local) → Cloud DLP (authoritative) → sanitized context

Mock-first design:
  - DLP_ENABLED=False (default): Uses MockDlpClient that catches common PII regex misses
    (full names, email addresses) using local heuristics. Same API shape as real client.
  - DLP_ENABLED=True: Uses google.cloud.dlp_v2.DlpServiceAsyncClient with verified infoTypes.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Union

from app.core.config import settings

logger = logging.getLogger(__name__)

# Verified Google DLP infoType identifiers
DLP_INFO_TYPES = [
    "INDIA_AADHAAR_INDIVIDUAL",
    "INDIA_PAN_INDIVIDUAL",
    "PHONE_NUMBER",
    "CREDIT_CARD_NUMBER",
    "INDIA_GST_INDIVIDUAL",
    "EMAIL_ADDRESS",
    "PERSON_NAME",
]


@dataclass
class DlpResult:
    """Result of DLP inspection + deidentification."""
    sanitized_text: str
    findings_count: int = 0
    finding_types: list[str] = field(default_factory=list)
    dlp_available: bool = True


# ---------------------------------------------------------------------------
# Mock DLP Client (default when DLP_ENABLED=False)
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

NAME_PREFIX_PATTERN = re.compile(
    r"\b(?:Mr|Mrs|Ms|Shri|Smt|Dr|Sri|Kumari|Sh)\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
)

GST_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[A-Z]{1}\d{1}\b")


class MockDlpClient:
    """
    Local heuristic DLP that catches PII patterns the regex sanitizer misses.
    Same API surface as the real DLP client wrapper.
    """
    async def inspect_and_deidentify(self, text: str) -> DlpResult:
        """Apply heuristic PII detection for patterns regex misses."""
        sanitized = text
        findings: list[str] = []

        if EMAIL_PATTERN.search(sanitized):
            sanitized = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", sanitized)
            findings.append("EMAIL_ADDRESS")

        if NAME_PREFIX_PATTERN.search(sanitized):
            sanitized = NAME_PREFIX_PATTERN.sub("[NAME_REDACTED]", sanitized)
            findings.append("PERSON_NAME")

        if GST_PATTERN.search(sanitized):
            sanitized = GST_PATTERN.sub("[GST_REDACTED]", sanitized)
            findings.append("INDIA_GST_INDIVIDUAL")

        return DlpResult(
            sanitized_text=sanitized,
            findings_count=len(findings),
            finding_types=findings,
            dlp_available=True,
        )


# ---------------------------------------------------------------------------
# Real DLP Client (when DLP_ENABLED=True + GOOGLE_CLOUD_PROJECT set)
# ---------------------------------------------------------------------------


class CloudDlpClient:
    """
    Google Cloud DLP client for authoritative PII detection and deidentification.
    Uses DlpServiceAsyncClient with Indian-specific infoTypes and ADC credentials.
    """
    def __init__(self, project_id: str, timeout: float):
        from google.cloud import dlp_v2

        self._client = dlp_v2.DlpServiceAsyncClient()
        self._project_id = project_id
        self._timeout = timeout
        self._parent = f"projects/{project_id}"

        self._inspect_config = dlp_v2.InspectConfig(
            info_types=[
                dlp_v2.InfoType(name=name) for name in DLP_INFO_TYPES
            ],
            min_likelihood=dlp_v2.Likelihood.POSSIBLE,
        )

        self._deidentify_config = dlp_v2.DeidentifyConfig(
            info_type_transformations=dlp_v2.InfoTypeTransformations(
                transformations=[
                    dlp_v2.InfoTypeTransformations.InfoTypeTransformation(
                        primitive_transformation=dlp_v2.PrimitiveTransformation(
                            replace_with_info_type_config=dlp_v2.ReplaceWithInfoTypeConfig(),
                        ),
                    ),
                ],
            ),
        )

    async def inspect_and_deidentify(self, text: str) -> DlpResult:
        """Call Cloud DLP to inspect and deidentify text."""
        from google.cloud import dlp_v2

        try:
            request = dlp_v2.DeidentifyContentRequest(
                parent=self._parent,
                inspect_config=self._inspect_config,
                deidentify_config=self._deidentify_config,
                item=dlp_v2.ContentItem(value=text),
            )

            response = await asyncio.wait_for(
                self._client.deidentify_content(request=request),
                timeout=self._timeout,
            )

            sanitized_text = response.item.value
            finding_types = []
            if response.overview and response.overview.transformation_summaries:
                for summary in response.overview.transformation_summaries:
                    if summary.info_type:
                        finding_types.append(summary.info_type.name)

            return DlpResult(
                sanitized_text=sanitized_text,
                findings_count=len(finding_types),
                finding_types=finding_types,
                dlp_available=True,
            )
        except asyncio.TimeoutError:
            logger.warning("Cloud DLP timed out after %.1fs. Falling back to regex-only sanitization.", self._timeout)
            return DlpResult(
                sanitized_text=text,
                findings_count=0,
                finding_types=[],
                dlp_available=False,
            )
        except Exception as exc:
            logger.warning("Cloud DLP API error: %s. Falling back to regex-only sanitization.", exc)
            return DlpResult(
                sanitized_text=text,
                findings_count=0,
                finding_types=[],
                dlp_available=False,
            )


def _create_dlp_client() -> Union[MockDlpClient, CloudDlpClient]:
    """Create DLP client based on configuration."""
    if settings.DLP_ENABLED and settings.GOOGLE_CLOUD_PROJECT:
        try:
            client = CloudDlpClient(
                project_id=settings.GOOGLE_CLOUD_PROJECT,
                timeout=settings.DLP_TIMEOUT_SECONDS,
            )
            logger.info(
                "Cloud DLP client initialized for project '%s' (timeout: %.1fs)",
                settings.GOOGLE_CLOUD_PROJECT,
                settings.DLP_TIMEOUT_SECONDS,
            )
            return client
        except Exception as exc:
            logger.warning("Failed to initialize Cloud DLP client: %s. Using mock DLP.", exc)
            return MockDlpClient()
    else:
        logger.info("DLP_ENABLED=False or GOOGLE_CLOUD_PROJECT not set. Using mock DLP client.")
        return MockDlpClient()


dlp_client = _create_dlp_client()

"""
Government Domain Validator — Two-Layer Trust System.

Layer 1: Hostname whitelist (technical filter)
    The hostname must end with a known government TLD.

Layer 2: Approved Source Registry (authority filter)
    The domain + authority must be registered and approved in the
    scheme_sources MongoDB collection.

A random .gov.in page that merely *mentions* an NSFDC scheme is NOT
automatically treated as an authoritative source for NSFDC eligibility.
Both layers must pass for a URL to be scrapeable.
"""

from urllib.parse import urlparse
from dataclasses import dataclass

from app.models.scraper import SchemeSource


# ── Layer 1: Hostname whitelist ───────────────────────────────────────────────
# These are the technical domain suffixes we accept at all.
# Domain must END with one of these (proper suffix check, not simple string match).

TRUSTED_TLD_SUFFIXES: list[str] = [
    ".gov.in",
    ".nic.in",
]

# Additional exact hostnames trusted without the suffix list above.
TRUSTED_EXACT_HOSTNAMES: list[str] = [
    "nsfdc.nic.in",
    "socialjustice.gov.in",
    "msde.gov.in",
    "tribal.gov.in",
    "minorityaffairs.gov.in",
    "wcd.nic.in",
    "handicrafts.nic.in",
    "kvic.gov.in",
]


@dataclass
class ValidationResult:
    allowed: bool
    source_record: SchemeSource | None = None
    rejection_reason: str | None = None
    hostname: str | None = None
    authority: str | None = None


def _is_hostname_trusted(hostname: str) -> bool:
    """
    Layer 1: strict hostname check.
    Uses proper suffix matching — not a simple ``url.endswith(".gov.in")`` check.
    """
    # Exact match
    if hostname in TRUSTED_EXACT_HOSTNAMES:
        return True
    # Suffix match — hostname must end with one of the trusted TLD suffixes
    for suffix in TRUSTED_TLD_SUFFIXES:
        if hostname == suffix.lstrip(".") or hostname.endswith(suffix):
            return True
    return False


async def validate_government_url(url: str) -> ValidationResult:
    """
    Full two-layer URL validation.

    Returns a ValidationResult with:
        allowed=True  + source_record  → URL is cleared for scraping
        allowed=False + rejection_reason → URL is rejected

    Layer 1 — Hostname whitelist check (synchronous, no DB).
    Layer 2 — Approved Source Registry lookup (async MongoDB query).
    """
    # Parse URL
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if not hostname:
            return ValidationResult(
                allowed=False,
                rejection_reason="URL has no valid hostname.",
            )
    except Exception as exc:
        return ValidationResult(
            allowed=False,
            rejection_reason=f"Invalid URL format: {exc}",
        )

    # ── Layer 1 ───────────────────────────────────────────────────────────────
    if not _is_hostname_trusted(hostname):
        return ValidationResult(
            allowed=False,
            hostname=hostname,
            rejection_reason=(
                f"Domain '{hostname}' is not in the trusted government domain list. "
                "Only official Indian Government domains (.gov.in, .nic.in) are permitted."
            ),
        )

    # ── Layer 2 ───────────────────────────────────────────────────────────────
    # Find an approved source whose base domain matches the hostname.
    # We match on the registered domain field (not just any substring).
    source = await SchemeSource.find_one(
        SchemeSource.domain == hostname,
        SchemeSource.approved == True,  # noqa: E712
    )

    if source is None:
        # Domain passes Layer 1 but is not yet registered as an approved source.
        # An admin must register it in the Source Registry before scraping.
        return ValidationResult(
            allowed=False,
            hostname=hostname,
            rejection_reason=(
                f"Domain '{hostname}' passes the government domain check but is not "
                "registered in the Approved Source Registry. "
                "Please add and approve it via POST /api/admin/sources first."
            ),
        )

    return ValidationResult(
        allowed=True,
        source_record=source,
        hostname=hostname,
        authority=source.authority,
    )


def extract_hostname(url: str) -> str | None:
    """Utility: safely extract the hostname from a URL string."""
    try:
        return urlparse(url).hostname
    except Exception:
        return None

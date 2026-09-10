"""
Firecrawl Service — Page scraping with explicit fallback tracking.

When Firecrawl is available (API key set), it is used first.
If Firecrawl fails for any reason:
  1. The failure is EXPLICITLY RECORDED (reason, timestamp).
  2. The system falls back to httpx + BeautifulSoup.
  3. extraction_method is set to "httpx_fallback" — never silently switched.

The database records which method was used for every single scrape job,
making it auditable: "Was this scheme data obtained via Firecrawl or fallback?"
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.scraper import ExtractionMethod
from app.services.domain_validator import extract_hostname, _is_hostname_trusted

logger = logging.getLogger(__name__)

# ── Rate-limiting constants ───────────────────────────────────────────────────
REQUEST_DELAY_SECONDS = 1.0     # Polite crawl delay between requests
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0        # Exponential: 2s, 4s, 8s
REQUEST_TIMEOUT = 30.0          # Seconds
MAX_CRAWL_PAGES = 10            # Max pages per crawl_scheme_source() call

# Keywords indicating a page is relevant to scheme information
SCHEME_RELEVANT_KEYWORDS = [
    "scheme", "eligibility", "loan", "credit", "benefit", "subsidy",
    "beneficiar", "guideline", "circular", "notification", "application",
    "interest", "repayment", "moratorium", "income", "documents required",
    "who can apply", "how to apply",
]


@dataclass
class PageContent:
    """Result of scraping a single government page."""
    url: str
    hostname: str
    page_title: str
    raw_html: str
    markdown_text: str
    extraction_method: ExtractionMethod
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    firecrawl_used: bool = False
    firecrawl_failure_reason: str | None = None
    pdf_links: list[str] = field(default_factory=list)
    scheme_links: list[str] = field(default_factory=list)
    http_status: int | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _extract_pdf_and_scheme_links(html: str, base_url: str) -> tuple[list[str], list[str]]:
    """Extract PDF links and potentially relevant sub-page links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    pdf_links: list[str] = []
    scheme_links: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # PDF check
        if parsed.path.lower().endswith(".pdf"):
            if _is_hostname_trusted(parsed.hostname or ""):
                pdf_links.append(full_url)
            continue

        # Sub-page check — must be on same host and look scheme-relevant
        if parsed.hostname == urlparse(base_url).hostname:
            link_text = a_tag.get_text(strip=True).lower()
            url_lower = full_url.lower()
            if any(k in link_text or k in url_lower for k in SCHEME_RELEVANT_KEYWORDS):
                scheme_links.append(full_url)

    # Deduplicate preserving order
    return list(dict.fromkeys(pdf_links)), list(dict.fromkeys(scheme_links))


def _html_to_markdown_simple(html: str) -> tuple[str, str]:
    """Basic HTML to readable plain text (used by httpx fallback)."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse excess blank lines
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines), title


# ── Scraper 1: Firecrawl ───────────────────────────────────────────────────────


async def _scrape_with_firecrawl(url: str) -> PageContent:
    """
    Scrape a single URL using the official Firecrawl API.
    Raises an exception if Firecrawl is not configured or fails.
    """
    api_key = settings.FIRECRAWL_API_KEY
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY is not set in environment.")

    # Firecrawl-py SDK wrapper
    from firecrawl import FirecrawlApp
    app = FirecrawlApp(api_key=api_key)

    # Run in a thread pool since firecrawl-py synchronous client is blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: app.scrape_url(url, params={"formats": ["markdown", "html"]}),
    )

    if not result:
        raise RuntimeError("Firecrawl returned an empty response.")

    markdown = result.get("markdown", "")
    html = result.get("html", "")
    metadata = result.get("metadata", {})
    title = metadata.get("title", "")

    pdf_links, scheme_links = _extract_pdf_and_scheme_links(html, url)

    return PageContent(
        url=url,
        hostname=extract_hostname(url) or "",
        page_title=title,
        raw_html=html,
        markdown_text=markdown,
        extraction_method=ExtractionMethod.FIRECRAWL,
        firecrawl_used=True,
        pdf_links=pdf_links,
        scheme_links=scheme_links,
        http_status=200,
    )


# ── Scraper 2: HTTPX Fallback ─────────────────────────────────────────────────


async def _scrape_with_httpx(url: str, failure_reason: str | None = None) -> PageContent:
    """
    Robust fallback scraper using httpx + BeautifulSoup.
    Implements exponential backoff retry.
    Explicitly tags extraction_method = ExtractionMethod.HTTPX_FALLBACK.
    """
    last_error: Exception | None = None

    headers = {
        "User-Agent": (
            "SchemeSetu-GovBot/1.0 (+https://schemesetu.gov.in; "
            "contact: admin@schemesetu.gov.in; Indian Government Scheme Ingestion)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    }

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                backoff = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"Retrying {url} (attempt {attempt + 1}/{MAX_RETRIES}) after {backoff}s backoff")
                await asyncio.sleep(backoff)

            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=REQUEST_TIMEOUT) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                html = resp.text
                text, title = _html_to_markdown_simple(html)
                pdf_links, scheme_links = _extract_pdf_and_scheme_links(html, url)

                return PageContent(
                    url=url,
                    hostname=extract_hostname(url) or "",
                    page_title=title,
                    raw_html=html,
                    markdown_text=text,
                    extraction_method=ExtractionMethod.HTTPX_FALLBACK,
                    firecrawl_used=False,
                    firecrawl_failure_reason=failure_reason,
                    pdf_links=pdf_links,
                    scheme_links=scheme_links,
                    http_status=resp.status_code,
                )

        except httpx.HTTPStatusError as exc:
            last_error = exc
            logger.error(f"HTTP {exc.response.status_code} error fetching {url}: {exc}")
            if exc.response.status_code in (404, 403, 401):
                # Permanent errors — do not retry
                break
        except Exception as exc:
            last_error = exc
            logger.error(f"Network error fetching {url} on attempt {attempt + 1}: {exc}")

    # If we get here, all retries failed
    raise RuntimeError(f"httpx fallback failed for {url} after {MAX_RETRIES} attempts. Last error: {last_error}")


# ── Public API ────────────────────────────────────────────────────────────────


async def scrape_url(url: str) -> PageContent:
    """
    Scrape a single government URL.
    Attempts Firecrawl first. On failure (or if key unset), falls back to httpx.
    Records which method was used in PageContent.extraction_method.
    """
    firecrawl_failure: str | None = None

    # Try Firecrawl first if API key is present
    if settings.FIRECRAWL_API_KEY:
        try:
            logger.info(f"Attempting Firecrawl scrape for {url}")
            return await _scrape_with_firecrawl(url)
        except Exception as exc:
            firecrawl_failure = f"Firecrawl error: {exc}"
            logger.warning(
                f"Firecrawl failed for {url} ({exc}). "
                "Falling back to httpx — extraction_method will be recorded as 'httpx_fallback'."
            )
    else:
        firecrawl_failure = "FIRECRAWL_API_KEY is not configured; using default httpx fallback."
        logger.info(f"No Firecrawl key configured. Using httpx fallback for {url}")

    # Fallback to httpx
    return await _scrape_with_httpx(url, failure_reason=firecrawl_failure)


async def crawl_scheme_source(base_url: str, max_pages: int = MAX_CRAWL_PAGES) -> list[PageContent]:
    """
    Politely crawl a government source starting at base_url.
    Respects polite crawl delay (REQUEST_DELAY_SECONDS) between requests.
    Stops at max_pages.
    """
    visited: set[str] = set()
    to_visit: list[str] = [base_url]
    results: list[PageContent] = []

    while to_visit and len(results) < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            content = await scrape_url(current_url)
            results.append(content)

            # Add discovered sub-page links that haven't been visited yet
            for link in content.scheme_links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)

            # Polite crawl delay
            await asyncio.sleep(REQUEST_DELAY_SECONDS)

        except Exception as exc:
            logger.error(f"Error crawling {current_url}: {exc}")

    return results

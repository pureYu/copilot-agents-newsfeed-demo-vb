"""robots.txt compliance checker for the scrape ingestion pipeline.

Compliance assumptions:
- A 404 on robots.txt is treated as no restrictions (standard convention).
- Any other HTTP error or network failure is logged and treated as allowed so
  that transient infra problems do not permanently block ingestion.
- We check against our declared user-agent "newsfeed-bot/0.1".
- Only scrape sources call this module; RSS feeds are not subject to robots.txt.
"""
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
import structlog

from app.core.config import settings

_USER_AGENT = "newsfeed-bot/0.1"
_TIMEOUT = httpx.Timeout(10.0)

logger = structlog.get_logger(__name__)


async def _fetch_robots_content(robots_url: str) -> tuple[int, str]:
    """Fetch raw robots.txt content.  Returns (status_code, body_text)."""
    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
        verify=settings.ssl_verify,
    ) as client:
        response = await client.get(robots_url)
        return response.status_code, response.text


async def is_url_allowed(url: str) -> bool:
    """Return True if our bot is permitted to fetch *url* per that site's robots.txt.

    Decision logic:
    - Network / timeout error  → log warning, return True (optimistic)
    - HTTP 404                 → return True (no restrictions)
    - Other HTTP error         → log warning, return True (optimistic)
    - Disallow rule matched    → return False
    - No matching rule         → return True
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        status, text = await _fetch_robots_content(robots_url)
    except Exception as exc:
        logger.warning("robots.fetch_error", robots_url=robots_url, error=str(exc))
        return True

    if status == 404:
        return True  # absent robots.txt → no restrictions

    if status >= 400:
        logger.warning(
            "robots.unexpected_status",
            robots_url=robots_url,
            status=status,
        )
        return True  # treat non-404 errors optimistically

    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.parse(text.splitlines())
    allowed = rp.can_fetch(_USER_AGENT, url)
    if not allowed:
        logger.info("robots.disallowed", robots_url=robots_url, url=url)
    return allowed

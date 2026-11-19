"""Scrape ingestion service.

Fetches an HTML index page, extracts article links using configurable CSS
selectors, deduplicates against existing database records, and persists new
articles.  robots.txt is checked before any request is made to the source URL.

Source.config keys (all optional):
    article_selector  CSS selector for individual article containers
                      default: "article, .article, .post"
    title_selector    CSS selector for the title element within each container
                      default: "h1 a, h2 a, h3 a, h1, h2, h3, .title a"
    summary_selector  CSS selector for the summary element within each container
                      default: "p, .summary, .excerpt"
"""
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import asyncio
import httpx
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Article, IngestionError, IngestionRun, IngestionStatus, Source
from app.services.robots import is_url_allowed

_FETCH_TIMEOUT = httpx.Timeout(30.0)
_USER_AGENT = "newsfeed-bot/0.1"
_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException)
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.5

_DEFAULT_ARTICLE_SELECTOR = "article, .article, .post"
_DEFAULT_TITLE_SELECTOR = "h1 a, h2 a, h3 a, h1, h2, h3, .title a"
_DEFAULT_SUMMARY_SELECTOR = "p, .summary, .excerpt"

logger = structlog.get_logger(__name__)


async def _fetch_page(url: str) -> str:
    """Fetch raw HTML from a URL, retrying on transient connection errors."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=_FETCH_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
                follow_redirects=True,
                verify=settings.ssl_verify,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except _RETRYABLE as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "fetch.retry",
                    url=url,
                    attempt=attempt,
                    delay=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)
    raise last_exc


def _extract_articles(html: str, base_url: str, config: dict) -> list[dict]:
    """Parse *html* and return a list of article dicts (url, title, summary).

    Relative hrefs are resolved against *base_url*.  Duplicate URLs and
    non-HTTP(S) URLs are silently dropped.
    """
    soup = BeautifulSoup(html, "lxml")

    article_sel = config.get("article_selector", _DEFAULT_ARTICLE_SELECTOR)
    title_sel = config.get("title_selector", _DEFAULT_TITLE_SELECTOR)
    summary_sel = config.get("summary_selector", _DEFAULT_SUMMARY_SELECTOR)

    containers = soup.select(article_sel)
    results: list[dict] = []
    seen_urls: set[str] = set()

    for container in containers:
        title_el = container.select_one(title_sel)
        if title_el is None:
            continue

        # Resolve article URL from the title element or any link in the container
        if title_el.name == "a" and title_el.get("href"):
            href = title_el["href"]
        else:
            inner_link = title_el.find("a", href=True)
            href = inner_link["href"] if inner_link else None

        if not href:
            fallback = container.find("a", href=True)
            href = fallback["href"] if fallback else None

        if not href:
            continue

        url = urljoin(base_url, href)
        if urlparse(url).scheme not in ("http", "https"):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = title_el.get_text(strip=True) or "Untitled"

        summary_el = container.select_one(summary_sel)
        summary = summary_el.get_text(strip=True) if summary_el else None

        results.append({"url": url, "title": title, "summary": summary or None})

    return results


async def ingest_source(session: AsyncSession, source: Source) -> IngestionRun:
    """Fetch and ingest articles from a scrape source.

    Checks robots.txt compliance before making any request to the source URL.
    If disallowed the run is recorded as failed immediately.  Otherwise fetches
    the HTML, extracts article candidates, deduplicates by URL, and persists
    new articles.  Returns the committed IngestionRun.
    """
    # Refresh source in case a previous rollback expired it in the session.
    await session.refresh(source)
    source_id: int = source.id
    source_url: str = source.url
    source_config: dict = source.config or {}

    run = IngestionRun(source_id=source_id)
    session.add(run)
    await session.flush()  # assigns run.id
    await session.commit()  # commit run immediately so its ID survives any later rollback
    await session.refresh(run)
    run_id: int = run.id

    log = logger.bind(source_id=source_id, source_url=source_url, run_id=run_id)
    log.info("ingestion.start", source_type="scrape")

    try:
        if not await is_url_allowed(source_url):
            log.warning("ingestion.robots_blocked", url=source_url)
            run.status = IngestionStatus.failed
            run.completed_at = datetime.now(timezone.utc)
            session.add(IngestionError(
                source_id=source_id,
                run_id=run_id,
                error_message=f"robots.txt disallows scraping {source_url}",
                error_type="RobotsBlocked",
            ))
        else:
            html = await _fetch_page(source_url)
            items = _extract_articles(html, source_url, source_config)

            run.articles_found = len(items)
            log.debug("ingestion.page_parsed", items_found=len(items))

            inserted = 0
            for item in items:
                existing = await session.execute(
                    select(Article.id).where(Article.url == item["url"])
                )
                if existing.scalar_one_or_none() is not None:
                    log.debug("ingestion.article_duplicate", url=item["url"])
                    continue

                session.add(Article(
                    source_id=source_id,
                    title=item["title"],
                    url=item["url"],
                    canonical_url=item["url"],
                    summary=item["summary"],
                    tags=[],
                ))
                inserted += 1

            await session.flush()  # flush inside try so IntegrityError is caught here
            run.articles_inserted = inserted
            run.status = IngestionStatus.success
            run.completed_at = datetime.now(timezone.utc)
            log.info(
                "ingestion.complete",
                status=run.status.value,
                articles_found=run.articles_found,
                articles_inserted=run.articles_inserted,
            )

    except Exception as exc:
        # Roll back any unflushed work. Then use raw SQL to record the failure
        # so we never touch potentially-expired ORM objects.
        await session.rollback()
        now = datetime.now(timezone.utc)
        await session.execute(
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(status=IngestionStatus.failed, completed_at=now)
        )
        await session.execute(
            insert(IngestionError).values(
                source_id=source_id,
                run_id=run_id,
                error_message=str(exc),
                error_type=type(exc).__name__,
            )
        )
        log.error("ingestion.failed", error=str(exc), exc_info=True)

    await session.commit()
    await session.refresh(run)
    return run

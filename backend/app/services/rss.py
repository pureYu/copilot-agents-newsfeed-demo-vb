import asyncio
import calendar
from datetime import datetime, timezone

import feedparser
import httpx
import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Article, IngestionError, IngestionRun, IngestionStatus, Source

_FETCH_TIMEOUT = httpx.Timeout(30.0)
_USER_AGENT = "newsfeed-bot/0.1"
_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException)
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.5  # seconds; doubled on each attempt

logger = structlog.get_logger(__name__)


async def _fetch_feed_content(url: str) -> str:
    """Fetch raw feed XML from a URL, retrying on transient connection errors."""
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


def _parse_date(struct_time) -> datetime | None:
    """Convert a feedparser struct_time tuple to an aware UTC datetime."""
    if struct_time is None:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc)
    except Exception:
        return None


def _get_content(entry) -> str | None:
    """Extract the first content block value from a feedparser entry."""
    content_list = entry.get("content")
    if content_list:
        return content_list[0].get("value")
    return None


def _normalize_entry(entry, source_id: int) -> Article | None:
    """Convert a feedparser entry dict to an Article ORM instance.

    Returns None if the entry has no usable URL (the record cannot be stored).
    """
    url = entry.get("link") or entry.get("id")
    if not url:
        return None

    raw_title = (entry.get("title") or "").strip()
    tags = [t.term for t in entry.get("tags", []) if hasattr(t, "term")]

    return Article(
        source_id=source_id,
        title=raw_title or "Untitled",
        url=url,
        canonical_url=entry.get("link"),
        author=entry.get("author") or None,
        published_at=_parse_date(
            entry.get("published_parsed") or entry.get("updated_parsed")
        ),
        summary=entry.get("summary") or None,
        content=_get_content(entry),
        tags=tags,
    )


async def ingest_source(session: AsyncSession, source: Source) -> IngestionRun:
    """Fetch and ingest new articles from an RSS source.

    Creates an IngestionRun record, fetches the feed URL, normalises each
    entry, deduplicates by article URL, persists new articles, and marks the
    run complete.  Returns the persisted IngestionRun.
    """
    # Refresh source in case a previous rollback expired it in the session.
    await session.refresh(source)
    source_id: int = source.id
    source_url: str = source.url

    run = IngestionRun(source_id=source_id)
    session.add(run)
    await session.flush()  # assigns run.id
    await session.commit()  # commit run immediately so its ID survives any later rollback
    await session.refresh(run)
    run_id: int = run.id

    log = logger.bind(source_id=source_id, source_url=source_url, run_id=run_id)
    log.info("ingestion.start")

    entry_errors = 0
    try:
        raw = await _fetch_feed_content(source_url)

        # feedparser is synchronous; run in a thread to avoid blocking the loop.
        parsed = await asyncio.to_thread(feedparser.parse, raw)

        entries = parsed.entries
        run.articles_found = len(entries)
        log.debug("ingestion.feed_parsed", entries=len(entries))

        inserted = 0
        seen_urls: set[str] = set()  # within-batch dedup prevents IntegrityError on flush
        for entry in entries:
            article = _normalize_entry(entry, source_id)
            if article is None:
                log.warning("ingestion.entry_skipped", reason="no_url")
                session.add(IngestionError(
                    source_id=source_id,
                    run_id=run_id,
                    error_message="Entry skipped: no URL found",
                    error_type="MissingURL",
                ))
                entry_errors += 1
                continue

            if article.url in seen_urls:
                log.debug("ingestion.article_duplicate_in_batch", url=article.url)
                continue
            seen_urls.add(article.url)

            # Deduplicate: skip URLs already in the database.
            existing = await session.execute(
                select(Article.id).where(Article.url == article.url)
            )
            if existing.scalar_one_or_none() is not None:
                log.debug("ingestion.article_duplicate", url=article.url)
                continue

            session.add(article)
            inserted += 1

        await session.flush()
        run.articles_inserted = inserted
        run.status = (
            IngestionStatus.partial if entry_errors > 0 else IngestionStatus.success
        )
        run.completed_at = datetime.now(timezone.utc)
        log.info(
            "ingestion.complete",
            status=run.status.value,
            articles_found=run.articles_found,
            articles_inserted=run.articles_inserted,
            entry_errors=entry_errors,
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

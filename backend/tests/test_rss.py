import textwrap
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Article, IngestionError, IngestionRun, IngestionStatus, Source, SourceType
from app.services.rss import _normalize_entry, _parse_date, ingest_source

# ---------------------------------------------------------------------------
# Feed fixtures
# ---------------------------------------------------------------------------

SAMPLE_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Tech Blog</title>
        <link>https://techblog.example.com</link>
        <description>Tech news and tutorials</description>
        <item>
          <title>Python Tips</title>
          <link>https://techblog.example.com/python-tips</link>
          <description>Useful tips for Python developers</description>
          <pubDate>Thu, 10 Jul 2026 12:00:00 +0000</pubDate>
          <author>alice@example.com (Alice Smith)</author>
          <category>python</category>
          <category>tips</category>
        </item>
        <item>
          <title>FastAPI Guide</title>
          <link>https://techblog.example.com/fastapi</link>
          <description>Learn FastAPI from scratch</description>
          <pubDate>Thu, 10 Jul 2026 14:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
""")

EMPTY_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Empty Blog</title>
        <link>https://empty.example.com</link>
        <description>No content yet</description>
      </channel>
    </rss>
""")


@pytest.fixture
async def rss_source(session) -> Source:
    """Persists an RSS source in the shared test session and returns its ORM instance."""
    src = Source(
        name="Tech Blog",
        url="https://techblog.example.com/feed",
        source_type=SourceType.rss,
    )
    session.add(src)
    await session.flush()  # assigns src.id; ingest_source will commit
    return src


# ---------------------------------------------------------------------------
# Unit tests — _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_returns_none_for_none(self):
        assert _parse_date(None) is None

    def test_converts_struct_time_to_utc_datetime(self):
        st = time.strptime("2026-07-10 12:00:00", "%Y-%m-%d %H:%M:%S")
        result = _parse_date(st)
        assert result is not None
        assert result.year == 2026
        assert result.month == 7
        assert result.day == 10
        assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# Unit tests — _normalize_entry  (no DB; plain dicts as entries)
# ---------------------------------------------------------------------------

class TestNormalizeEntry:
    def test_returns_none_when_no_url(self):
        assert _normalize_entry({"title": "No link"}, source_id=1) is None

    def test_minimal_entry(self):
        entry = {"title": "Hello", "link": "https://example.com/1"}
        article = _normalize_entry(entry, source_id=5)
        assert article is not None
        assert article.title == "Hello"
        assert article.url == "https://example.com/1"
        assert article.source_id == 5
        assert article.tags == []

    def test_empty_title_becomes_untitled(self):
        article = _normalize_entry({"title": "  ", "link": "https://example.com/2"}, source_id=1)
        assert article.title == "Untitled"

    def test_missing_title_becomes_untitled(self):
        article = _normalize_entry({"link": "https://example.com/3"}, source_id=1)
        assert article.title == "Untitled"

    def test_falls_back_to_id_when_no_link(self):
        article = _normalize_entry({"id": "urn:uuid:abc", "title": "By ID"}, source_id=1)
        assert article is not None
        assert article.url == "urn:uuid:abc"

    def test_extracts_tags_via_term_attribute(self):
        tags = [SimpleNamespace(term="python"), SimpleNamespace(term="tips")]
        entry = {"link": "https://example.com/4", "title": "Tagged", "tags": tags}
        article = _normalize_entry(entry, source_id=1)
        assert article.tags == ["python", "tips"]

    def test_objects_without_term_are_skipped(self):
        # A tag object with no .term attribute should be silently dropped
        tags = [SimpleNamespace(term="ok"), {"no_term": True}]
        entry = {"link": "https://example.com/5", "title": "Mixed", "tags": tags}
        article = _normalize_entry(entry, source_id=1)
        assert article.tags == ["ok"]

    def test_published_at_set_from_published_parsed(self):
        st = time.strptime("2026-07-10 12:00:00", "%Y-%m-%d %H:%M:%S")
        entry = {"link": "https://example.com/6", "title": "Dated", "published_parsed": st}
        article = _normalize_entry(entry, source_id=1)
        assert article.published_at is not None
        assert article.published_at.year == 2026

    def test_author_none_when_empty_string(self):
        entry = {"link": "https://example.com/7", "title": "No author", "author": ""}
        article = _normalize_entry(entry, source_id=1)
        assert article.author is None

    def test_summary_none_when_absent(self):
        entry = {"link": "https://example.com/8", "title": "No summary"}
        article = _normalize_entry(entry, source_id=1)
        assert article.summary is None


# ---------------------------------------------------------------------------
# Integration tests — ingest_source
# ---------------------------------------------------------------------------

class TestIngestSource:
    async def test_inserts_new_articles(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            await ingest_source(session, rss_source)

        result = await session.execute(
            select(Article).where(Article.source_id == rss_source.id)
        )
        assert len(list(result.scalars().all())) == 2

    async def test_run_status_is_success(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            run = await ingest_source(session, rss_source)
        assert run.status == IngestionStatus.success

    async def test_run_counts_are_correct(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            run = await ingest_source(session, rss_source)
        assert run.articles_found == 2
        assert run.articles_inserted == 2

    async def test_run_has_completed_at(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            run = await ingest_source(session, rss_source)
        assert run.completed_at is not None

    async def test_normalizes_published_date(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            await ingest_source(session, rss_source)

        result = await session.execute(
            select(Article).where(Article.title == "Python Tips")
        )
        article = result.scalar_one()
        assert article.published_at is not None
        assert article.published_at.year == 2026

    async def test_normalizes_author(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            await ingest_source(session, rss_source)

        result = await session.execute(
            select(Article).where(Article.title == "Python Tips")
        )
        article = result.scalar_one()
        # feedparser normalises RSS <author> to "name (email)" or just the email
        assert article.author is not None

    async def test_deduplication_second_run_inserts_zero(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            await ingest_source(session, rss_source)
            run2 = await ingest_source(session, rss_source)
        assert run2.articles_inserted == 0

    async def test_deduplication_does_not_duplicate_articles(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=SAMPLE_RSS)):
            await ingest_source(session, rss_source)
            await ingest_source(session, rss_source)

        result = await session.execute(
            select(Article).where(Article.source_id == rss_source.id)
        )
        assert len(list(result.scalars().all())) == 2

    async def test_empty_feed_is_success_with_zero_counts(self, session, rss_source):
        with patch("app.services.rss._fetch_feed_content", new=AsyncMock(return_value=EMPTY_RSS)):
            run = await ingest_source(session, rss_source)
        assert run.status == IngestionStatus.success
        assert run.articles_found == 0
        assert run.articles_inserted == 0

    async def test_http_failure_marks_run_failed(self, session, rss_source):
        with patch(
            "app.services.rss._fetch_feed_content",
            new=AsyncMock(side_effect=httpx.HTTPError("Connection refused")),
        ):
            run = await ingest_source(session, rss_source)
        assert run.status == IngestionStatus.failed
        assert run.completed_at is not None

    async def test_http_failure_creates_ingestion_error(self, session, rss_source):
        with patch(
            "app.services.rss._fetch_feed_content",
            new=AsyncMock(side_effect=httpx.HTTPError("Connection refused")),
        ):
            run = await ingest_source(session, rss_source)

        result = await session.execute(
            select(IngestionError).where(IngestionError.run_id == run.id)
        )
        errors = list(result.scalars().all())
        assert len(errors) == 1
        assert "HTTPError" in errors[0].error_type

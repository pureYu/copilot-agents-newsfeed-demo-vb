"""Tests for the scrape ingestion service.

Unit tests cover _extract_articles (pure function, no DB).
Integration tests cover ingest_source with patched network calls.
"""
import textwrap
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Article, IngestionError, IngestionRun, IngestionStatus, Source, SourceType
from app.services.scrape import _extract_articles, ingest_source

# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

BASE_URL = "https://techblog.example.com"

SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <article>
      <h2><a href="/news/python-tips">Python Tips</a></h2>
      <p>Useful tips for Python developers</p>
    </article>
    <article>
      <h2><a href="/news/fastapi-guide">FastAPI Guide</a></h2>
      <p>Learn FastAPI from scratch</p>
    </article>
    <article>
      <h2><a href="/news/no-summary">No Summary Article</a></h2>
    </article>
    </body></html>
""")


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def scrape_source(session) -> Source:
    """Persists a scrape source in the shared test session and returns its ORM instance."""
    src = Source(
        name="Tech Blog",
        url=BASE_URL,
        source_type=SourceType.scrape,
    )
    session.add(src)
    await session.flush()  # assigns src.id; ingest_source will commit
    return src


# ---------------------------------------------------------------------------
# Unit tests — _extract_articles  (no DB, no network)
# ---------------------------------------------------------------------------

class TestExtractArticles:
    def test_extracts_all_articles(self):
        results = _extract_articles(SAMPLE_HTML, BASE_URL, {})
        assert len(results) == 3

    def test_title_and_summary_extracted(self):
        results = _extract_articles(SAMPLE_HTML, BASE_URL, {})
        assert results[0]["title"] == "Python Tips"
        assert results[0]["summary"] == "Useful tips for Python developers"

    def test_relative_url_resolved_to_absolute(self):
        results = _extract_articles(SAMPLE_HTML, BASE_URL, {})
        assert results[0]["url"] == f"{BASE_URL}/news/python-tips"
        for r in results:
            assert r["url"].startswith("https://")

    def test_absolute_external_url_preserved(self):
        html = (
            "<html><body><article>"
            "<h2><a href='https://external.com/post'>External</a></h2>"
            "</article></body></html>"
        )
        results = _extract_articles(html, BASE_URL, {})
        assert results[0]["url"] == "https://external.com/post"

    def test_summary_is_none_when_no_p_tag(self):
        results = _extract_articles(SAMPLE_HTML, BASE_URL, {})
        # Third article has no <p>
        assert results[2]["summary"] is None

    def test_untitled_when_anchor_has_no_text(self):
        html = (
            "<html><body><article>"
            "<h2><a href='/news/1'></a></h2>"
            "</article></body></html>"
        )
        results = _extract_articles(html, BASE_URL, {})
        assert results[0]["title"] == "Untitled"

    def test_duplicate_urls_deduplicated(self):
        html = textwrap.dedent("""\
            <html><body>
            <article><h2><a href="/news/1">Article One</a></h2></article>
            <article><h2><a href="/news/1">Duplicate</a></h2></article>
            </body></html>
        """)
        results = _extract_articles(html, BASE_URL, {})
        assert len(results) == 1

    def test_custom_selectors_respected(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="news-item">
              <h3 class="headline"><a href="/story/1">Custom Headline</a></h3>
              <div class="snippet">A custom snippet</div>
            </div>
            </body></html>
        """)
        config = {
            "article_selector": ".news-item",
            "title_selector": ".headline",
            "summary_selector": ".snippet",
        }
        results = _extract_articles(html, BASE_URL, config)
        assert len(results) == 1
        assert results[0]["title"] == "Custom Headline"
        assert results[0]["summary"] == "A custom snippet"

    def test_non_http_urls_skipped(self):
        html = (
            "<html><body><article>"
            "<h2><a href='mailto:foo@bar.com'>Mail</a></h2>"
            "</article></body></html>"
        )
        assert _extract_articles(html, BASE_URL, {}) == []

    def test_empty_page_returns_empty_list(self):
        assert _extract_articles("<html><body></body></html>", BASE_URL, {}) == []


# ---------------------------------------------------------------------------
# Integration tests — ingest_source  (real DB, patched network)
# ---------------------------------------------------------------------------

class TestIngestSource:
    async def test_robots_blocked_returns_failed_run(self, session, scrape_source):
        with patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=False)):
            run = await ingest_source(session, scrape_source)

        assert run.status == IngestionStatus.failed
        errors = (
            await session.execute(
                select(IngestionError).where(IngestionError.run_id == run.id)
            )
        ).scalars().all()
        assert len(errors) == 1
        assert "robots" in errors[0].error_message.lower()
        assert errors[0].error_type == "RobotsBlocked"

    async def test_successful_scrape_inserts_articles(self, session, scrape_source):
        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value=SAMPLE_HTML)),
        ):
            run = await ingest_source(session, scrape_source)

        assert run.status == IngestionStatus.success
        assert run.articles_found == 3
        assert run.articles_inserted == 3

    async def test_deduplication_skips_existing_article(self, session, scrape_source):
        # Pre-insert one article with a URL that appears in SAMPLE_HTML
        session.add(Article(
            source_id=scrape_source.id,
            title="Python Tips",
            url=f"{BASE_URL}/news/python-tips",
            tags=[],
        ))
        await session.flush()

        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value=SAMPLE_HTML)),
        ):
            run = await ingest_source(session, scrape_source)

        assert run.articles_found == 3
        assert run.articles_inserted == 2

    async def test_fetch_error_returns_failed_run_with_error_record(self, session, scrape_source):
        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(side_effect=Exception("connection timeout"))),
        ):
            run = await ingest_source(session, scrape_source)

        assert run.status == IngestionStatus.failed
        errors = (
            await session.execute(
                select(IngestionError).where(IngestionError.run_id == run.id)
            )
        ).scalars().all()
        assert len(errors) == 1
        assert "connection timeout" in errors[0].error_message

    async def test_empty_page_succeeds_with_zero_inserted(self, session, scrape_source):
        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value="<html><body></body></html>")),
        ):
            run = await ingest_source(session, scrape_source)

        assert run.status == IngestionStatus.success
        assert run.articles_found == 0
        assert run.articles_inserted == 0

    async def test_custom_config_selectors_used(self, session):
        """Source with config selectors correctly extracts from non-standard HTML."""
        src = Source(
            name="Custom Site",
            url="https://custom.example.com",
            source_type=SourceType.scrape,
            config={
                "article_selector": ".news-item",
                "title_selector": ".headline",
                "summary_selector": ".snippet",
            },
        )
        session.add(src)
        await session.flush()

        custom_html = textwrap.dedent("""\
            <html><body>
            <div class="news-item">
              <h3 class="headline"><a href="/story/1">Custom Headline</a></h3>
              <div class="snippet">Snippet text</div>
            </div>
            </body></html>
        """)
        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value=custom_html)),
        ):
            run = await ingest_source(session, src)

        assert run.status == IngestionStatus.success
        assert run.articles_inserted == 1
        articles = (
            await session.execute(select(Article).where(Article.source_id == src.id))
        ).scalars().all()
        assert articles[0].title == "Custom Headline"
        assert articles[0].summary == "Snippet text"

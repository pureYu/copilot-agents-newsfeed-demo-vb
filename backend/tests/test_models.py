from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Article, IngestionError, IngestionRun, IngestionStatus, Source, SourceType


async def _make_source(
    session, *, name: str, url: str, source_type: SourceType = SourceType.rss
) -> Source:
    source = Source(name=name, url=url, source_type=source_type)
    session.add(source)
    await session.flush()
    return source


class TestSource:
    async def test_create_rss_source(self, session):
        source = await _make_source(
            session, name="BBC News", url="https://feeds.bbci.co.uk/news/rss.xml"
        )
        await session.commit()
        await session.refresh(source)

        assert source.id is not None
        assert source.enabled is True
        assert source.source_type == SourceType.rss
        assert source.config == {}

    async def test_create_scrape_source(self, session):
        source = await _make_source(
            session,
            name="Example Blog",
            url="https://example.com/blog",
            source_type=SourceType.scrape,
        )
        await session.commit()
        await session.refresh(source)

        assert source.source_type == SourceType.scrape

    async def test_source_url_must_be_unique(self, session):
        await _make_source(session, name="Feed A", url="https://duplicate.example.com/feed")
        # Use session.add (no flush) so the violation is caught at commit, matching
        # the same pattern as test_article_url_must_be_unique.
        session.add(Source(name="Feed B", url="https://duplicate.example.com/feed", source_type=SourceType.rss))

        with pytest.raises(IntegrityError):
            await session.commit()

    async def test_source_disabled_by_config(self, session):
        source = Source(
            name="Disabled",
            url="https://disabled.example.com/feed",
            source_type=SourceType.rss,
            enabled=False,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        assert source.enabled is False


class TestArticle:
    async def test_create_article_minimal_fields(self, session):
        source = await _make_source(session, name="Minimal", url="https://minimal.example.com/feed")
        article = Article(
            source_id=source.id, title="Hello World", url="https://minimal.example.com/1"
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        assert article.id is not None
        assert article.tags == []
        assert article.author is None
        assert article.published_at is None
        assert article.canonical_url is None

    async def test_create_article_all_fields(self, session):
        source = await _make_source(session, name="Full", url="https://full.example.com/feed")
        article = Article(
            source_id=source.id,
            title="Full Article",
            url="https://full.example.com/article/42",
            canonical_url="https://full.example.com/article/42",
            author="Jane Smith",
            published_at=datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc),
            summary="A concise summary.",
            content="Full article body text.",
            image_url="https://full.example.com/img.jpg",
            tags=["tech", "news"],
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        assert article.tags == ["tech", "news"]
        assert article.author == "Jane Smith"
        assert article.published_at is not None

    async def test_article_url_must_be_unique(self, session):
        source = await _make_source(session, name="Dup", url="https://dup.example.com/feed")
        session.add(Article(source_id=source.id, title="A", url="https://dup.example.com/article"))
        await session.flush()
        session.add(Article(source_id=source.id, title="B", url="https://dup.example.com/article"))

        with pytest.raises(IntegrityError):
            await session.commit()

    async def test_article_tags_default_to_empty_list(self, session):
        source = await _make_source(session, name="Tags", url="https://tags.example.com/feed")
        article = Article(source_id=source.id, title="T", url="https://tags.example.com/1")
        session.add(article)
        await session.commit()
        await session.refresh(article)

        assert isinstance(article.tags, list)
        assert len(article.tags) == 0


class TestIngestionRun:
    async def test_default_status_is_running(self, session):
        source = await _make_source(session, name="Run1", url="https://run1.example.com/feed")
        run = IngestionRun(source_id=source.id)
        session.add(run)
        await session.commit()
        await session.refresh(run)

        assert run.status == IngestionStatus.running
        assert run.articles_found == 0
        assert run.articles_inserted == 0
        assert run.completed_at is None

    async def test_mark_run_success(self, session):
        source = await _make_source(session, name="Run2", url="https://run2.example.com/feed")
        run = IngestionRun(source_id=source.id)
        session.add(run)
        await session.flush()

        run.status = IngestionStatus.success
        run.articles_found = 10
        run.articles_inserted = 8
        run.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run)

        assert run.status == IngestionStatus.success
        assert run.articles_found == 10
        assert run.articles_inserted == 8
        assert run.completed_at is not None

    async def test_mark_run_partial(self, session):
        source = await _make_source(session, name="Run3", url="https://run3.example.com/feed")
        run = IngestionRun(source_id=source.id)
        session.add(run)
        await session.flush()

        run.status = IngestionStatus.partial
        run.articles_found = 5
        run.articles_inserted = 3
        await session.commit()
        await session.refresh(run)

        assert run.status == IngestionStatus.partial


class TestIngestionError:
    async def test_error_without_run(self, session):
        source = await _make_source(session, name="Err1", url="https://err1.example.com/feed")
        error = IngestionError(
            source_id=source.id,
            error_message="Connection refused",
            error_type="NetworkError",
            url="https://err1.example.com/feed",
        )
        session.add(error)
        await session.commit()
        await session.refresh(error)

        assert error.id is not None
        assert error.run_id is None

    async def test_error_linked_to_run(self, session):
        source = await _make_source(session, name="Err2", url="https://err2.example.com/feed")
        run = IngestionRun(source_id=source.id)
        session.add(run)
        await session.flush()

        error = IngestionError(
            source_id=source.id,
            run_id=run.id,
            error_message="Malformed XML at line 42",
            error_type="ParseError",
        )
        session.add(error)
        await session.commit()
        await session.refresh(error)

        assert error.run_id == run.id

    async def test_error_without_url(self, session):
        source = await _make_source(session, name="Err3", url="https://err3.example.com/feed")
        error = IngestionError(
            source_id=source.id,
            error_message="Source config missing selector",
            error_type="ConfigError",
        )
        session.add(error)
        await session.commit()
        await session.refresh(error)

        assert error.url is None

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Article, Source, SourceType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def source(engine) -> Source:
    """Persists one RSS source directly and returns its ORM instance."""
    _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _factory() as s:
        src = Source(name="Tech Blog", url="https://techblog.example.com/feed", source_type=SourceType.rss)
        s.add(src)
        await s.commit()
        await s.refresh(src)
    return src


@pytest.fixture
async def articles(engine, source) -> list[dict]:
    """Inserts three articles with varied metadata and returns their basic info."""
    now = datetime.now(timezone.utc)
    _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _factory() as s:
        rows = [
            Article(
                source_id=source.id,
                title="Python Tips",
                url="https://techblog.example.com/python-tips",
                summary="Useful tips for Python developers",
                tags=["python", "tips"],
                published_at=now - timedelta(hours=3),
            ),
            Article(
                source_id=source.id,
                title="FastAPI Tutorial",
                url="https://techblog.example.com/fastapi",
                summary="Learn FastAPI, a Python web framework, from scratch",
                tags=["python", "fastapi"],
                published_at=now - timedelta(hours=2),
            ),
            Article(
                source_id=source.id,
                title="Database Design Patterns",
                url="https://techblog.example.com/database",
                summary="Relational database patterns",
                tags=["database", "architecture"],
                published_at=now - timedelta(hours=1),
            ),
        ]
        for row in rows:
            s.add(row)
        await s.commit()
    return [{"title": r.title, "url": r.url, "tags": r.tags} for r in rows]


# ---------------------------------------------------------------------------
# GET /articles — basic listing
# ---------------------------------------------------------------------------

class TestListArticlesEmpty:
    async def test_empty_database_returns_empty_list(self, client: AsyncClient):
        response = await client.get("/articles")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20


class TestListArticles:
    async def test_returns_all_articles(self, client: AsyncClient, articles):
        response = await client.get("/articles")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_response_includes_source_summary(self, client: AsyncClient, articles):
        response = await client.get("/articles")
        item = response.json()["items"][0]
        assert "source" in item
        assert item["source"]["name"] == "Tech Blog"
        assert item["source"]["source_type"] == "rss"

    async def test_ordered_by_ingested_at_descending(self, client: AsyncClient, articles):
        response = await client.get("/articles")
        items = response.json()["items"]
        ingested_dates = [item["ingested_at"] for item in items]
        assert ingested_dates == sorted(ingested_dates, reverse=True)

    async def test_response_contains_expected_fields(self, client: AsyncClient, articles):
        item = (await client.get("/articles")).json()["items"][0]
        for field in ("id", "source_id", "source", "title", "url", "tags", "ingested_at"):
            assert field in item


# ---------------------------------------------------------------------------
# GET /articles — pagination
# ---------------------------------------------------------------------------

class TestPagination:
    async def test_page_size_limits_results(self, client: AsyncClient, articles):
        response = await client.get("/articles?page_size=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["page_size"] == 2

    async def test_second_page_returns_remaining(self, client: AsyncClient, articles):
        response = await client.get("/articles?page=2&page_size=2")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 2

    async def test_page_beyond_results_returns_empty(self, client: AsyncClient, articles):
        response = await client.get("/articles?page=99&page_size=20")
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 3

    async def test_invalid_page_returns_422(self, client: AsyncClient):
        response = await client.get("/articles?page=0")
        assert response.status_code == 422

    async def test_page_size_above_max_returns_422(self, client: AsyncClient):
        response = await client.get("/articles?page_size=101")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /articles — source filter
# ---------------------------------------------------------------------------

class TestSourceFilter:
    async def test_filter_by_valid_source_id(self, client: AsyncClient, articles, source):
        response = await client.get(f"/articles?source_id={source.id}")
        data = response.json()
        assert data["total"] == 3

    async def test_filter_by_unknown_source_id_returns_empty(self, client: AsyncClient, articles):
        response = await client.get("/articles?source_id=99999")
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


# ---------------------------------------------------------------------------
# GET /articles — search
# ---------------------------------------------------------------------------

class TestSearch:
    async def test_search_by_title_keyword(self, client: AsyncClient, articles):
        response = await client.get("/articles?search=FastAPI")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "FastAPI Tutorial"

    async def test_search_is_case_insensitive(self, client: AsyncClient, articles):
        response = await client.get("/articles?search=python")
        data = response.json()
        assert data["total"] == 2

    async def test_search_matches_summary(self, client: AsyncClient, articles):
        response = await client.get("/articles?search=Relational")
        data = response.json()
        assert data["total"] == 1
        assert "Database" in data["items"][0]["title"]

    async def test_search_no_match_returns_empty(self, client: AsyncClient, articles):
        response = await client.get("/articles?search=kubernetes")
        data = response.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /articles — tag filter
# ---------------------------------------------------------------------------

class TestTagFilter:
    async def test_filter_by_existing_tag(self, client: AsyncClient, articles):
        response = await client.get("/articles?tag=python")
        data = response.json()
        assert data["total"] == 2

    async def test_filter_by_unique_tag(self, client: AsyncClient, articles):
        response = await client.get("/articles?tag=fastapi")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "FastAPI Tutorial"

    async def test_filter_by_nonexistent_tag_returns_empty(self, client: AsyncClient, articles):
        response = await client.get("/articles?tag=rust")
        data = response.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /articles/{id}
# ---------------------------------------------------------------------------

class TestGetArticle:
    async def test_get_existing_article(self, client: AsyncClient, articles, engine):
        # Retrieve id of the first article from the DB
        from sqlalchemy import select as sa_select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with _factory() as s:
            result = await s.execute(sa_select(Article).limit(1))
            article_id = result.scalar_one().id

        response = await client.get(f"/articles/{article_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert "source" in data
        assert data["source"]["name"] == "Tech Blog"

    async def test_get_article_returns_all_fields(self, client: AsyncClient, articles, engine):
        from sqlalchemy import select as sa_select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with _factory() as s:
            result = await s.execute(sa_select(Article).limit(1))
            article_id = result.scalar_one().id

        data = (await client.get(f"/articles/{article_id}")).json()
        for field in ("id", "source_id", "source", "title", "url", "tags",
                      "summary", "content", "author", "published_at", "image_url", "ingested_at"):
            assert field in data

    async def test_get_nonexistent_article_returns_404(self, client: AsyncClient):
        response = await client.get("/articles/99999")
        assert response.status_code == 404

import textwrap
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient

# Minimal two-item RSS feed used for all ingest tests.
_SAMPLE_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Feed</title>
        <link>https://feed.example.com</link>
        <description>Test</description>
        <item>
          <title>Article One</title>
          <link>https://feed.example.com/1</link>
          <description>First article</description>
        </item>
        <item>
          <title>Article Two</title>
          <link>https://feed.example.com/2</link>
          <description>Second article</description>
        </item>
      </channel>
    </rss>
""")

_PATCH = "app.services.rss._fetch_feed_content"


# ---------------------------------------------------------------------------
# POST /ingest/{source_id}
# ---------------------------------------------------------------------------

class TestIngestSingle:
    async def test_returns_200_with_run(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Feed", "url": "https://feed.example.com/rss", "source_type": "rss",
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post(f"/ingest/{source_id}")

        assert response.status_code == 200
        assert response.json()["source_id"] == source_id

    async def test_run_status_is_success(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "FeedS", "url": "https://feeds.example.com/rss", "source_type": "rss",
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post(f"/ingest/{source_id}")

        assert response.json()["status"] == "success"

    async def test_run_counts_articles(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "FeedC", "url": "https://feedc.example.com/rss", "source_type": "rss",
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post(f"/ingest/{source_id}")

        data = response.json()
        assert data["articles_found"] == 2
        assert data["articles_inserted"] == 2

    async def test_response_has_all_fields(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "FeedF", "url": "https://feedf.example.com/rss", "source_type": "rss",
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post(f"/ingest/{source_id}")

        data = response.json()
        for field in ("id", "source_id", "status", "articles_found",
                      "articles_inserted", "started_at", "completed_at"):
            assert field in data

    async def test_unknown_source_returns_404(self, client: AsyncClient):
        response = await client.post("/ingest/99999")
        assert response.status_code == 404

    async def test_disabled_source_can_still_be_ingested(self, client: AsyncClient):
        """Manual trigger should work regardless of the enabled flag."""
        create = await client.post("/sources", json={
            "name": "Off", "url": "https://off.example.com/rss",
            "source_type": "rss", "enabled": False,
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post(f"/ingest/{source_id}")

        assert response.status_code == 200

    async def test_http_error_returns_failed_status(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Broken", "url": "https://broken.example.com/rss", "source_type": "rss",
        })
        source_id = create.json()["id"]

        with patch(_PATCH, new=AsyncMock(side_effect=httpx.HTTPError("timeout"))):
            response = await client.post(f"/ingest/{source_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# POST /ingest
# ---------------------------------------------------------------------------

class TestIngestAll:
    async def test_no_sources_returns_empty_list(self, client: AsyncClient):
        response = await client.post("/ingest")
        assert response.status_code == 200
        assert response.json() == []

    async def test_ingests_all_enabled_sources(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "A", "url": "https://a.example.com/rss", "source_type": "rss",
        })
        await client.post("/sources", json={
            "name": "B", "url": "https://b.example.com/rss", "source_type": "rss",
        })

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post("/ingest")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_skips_disabled_sources(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "On", "url": "https://on.example.com/rss",
            "source_type": "rss", "enabled": True,
        })
        await client.post("/sources", json={
            "name": "Off", "url": "https://off2.example.com/rss",
            "source_type": "rss", "enabled": False,
        })

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post("/ingest")

        runs = response.json()
        assert len(runs) == 1

    async def test_each_run_has_success_status(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "Src", "url": "https://src.example.com/rss", "source_type": "rss",
        })

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            response = await client.post("/ingest")

        assert response.json()[0]["status"] == "success"

    async def test_second_ingest_shows_zero_new_inserts(self, client: AsyncClient):
        """Deduplication should be preserved across requests."""
        await client.post("/sources", json={
            "name": "Dedup", "url": "https://dedup.example.com/rss", "source_type": "rss",
        })

        with patch(_PATCH, new=AsyncMock(return_value=_SAMPLE_RSS)):
            await client.post("/ingest")
            response = await client.post("/ingest")

        assert response.json()[0]["articles_inserted"] == 0


# ---------------------------------------------------------------------------
# Source-type dispatch
# ---------------------------------------------------------------------------

_SCRAPE_HTML = """\
<html><body>
<article>
  <h2><a href="/news/test-article">Test Article</a></h2>
  <p>A test summary</p>
</article>
</body></html>
"""


class TestIngestDispatch:
    async def test_scrape_source_uses_scrape_service(self, client: AsyncClient):
        """A scrape-type source is routed to the scrape service, not the RSS service."""
        create = await client.post("/sources", json={
            "name": "Scrape Site",
            "url": "https://scrape.example.com",
            "source_type": "scrape",
        })
        source_id = create.json()["id"]

        with (
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value=_SCRAPE_HTML)),
        ):
            response = await client.post(f"/ingest/{source_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["articles_inserted"] == 1

    async def test_ingest_all_handles_mixed_source_types(self, client: AsyncClient):
        """POST /ingest dispatches RSS and scrape sources to their respective services."""
        await client.post("/sources", json={
            "name": "RSS Mix", "url": "https://mix-rss.example.com/rss", "source_type": "rss",
        })
        await client.post("/sources", json={
            "name": "Scrape Mix", "url": "https://mix-scrape.example.com", "source_type": "scrape",
        })

        with (
            patch("app.services.rss._fetch_feed_content", AsyncMock(return_value=_SAMPLE_RSS)),
            patch("app.services.scrape.is_url_allowed", AsyncMock(return_value=True)),
            patch("app.services.scrape._fetch_page", AsyncMock(return_value=_SCRAPE_HTML)),
        ):
            response = await client.post("/ingest")

        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 2
        statuses = {r["status"] for r in runs}
        assert statuses == {"success"}

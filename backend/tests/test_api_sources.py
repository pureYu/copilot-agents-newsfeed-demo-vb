import pytest
from httpx import AsyncClient


class TestCreateSource:
    async def test_create_rss_source(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "name": "BBC News",
            "url": "https://feeds.bbci.co.uk/news/rss.xml",
            "source_type": "rss",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == "BBC News"
        assert data["source_type"] == "rss"
        assert data["enabled"] is True
        assert data["config"] == {}
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_scrape_source_with_config(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "name": "Example Blog",
            "url": "https://blog.example.com/",
            "source_type": "scrape",
            "config": {"title_selector": "h1", "content_selector": "article"},
        })
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "scrape"
        assert data["config"]["title_selector"] == "h1"

    async def test_create_source_disabled_by_default_override(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "name": "Paused Feed",
            "url": "https://paused.example.com/feed",
            "source_type": "rss",
            "enabled": False,
        })
        assert response.status_code == 201
        assert response.json()["enabled"] is False

    async def test_create_source_rejects_invalid_url(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "name": "Bad URL",
            "url": "not-a-url",
            "source_type": "rss",
        })
        assert response.status_code == 422

    async def test_create_source_rejects_missing_name(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "url": "https://example.com/feed",
            "source_type": "rss",
        })
        assert response.status_code == 422

    async def test_create_source_rejects_invalid_source_type(self, client: AsyncClient):
        response = await client.post("/sources", json={
            "name": "Feed",
            "url": "https://example.com/feed",
            "source_type": "twitter",
        })
        assert response.status_code == 422

    async def test_create_duplicate_url_returns_409(self, client: AsyncClient):
        payload = {
            "name": "Feed",
            "url": "https://dup.example.com/feed",
            "source_type": "rss",
        }
        first = await client.post("/sources", json=payload)
        assert first.status_code == 201
        second = await client.post("/sources", json=payload)
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"]


class TestListSources:
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_lists_all_sources(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "Feed A", "url": "https://a.example.com/feed", "source_type": "rss",
        })
        await client.post("/sources", json={
            "name": "Feed B", "url": "https://b.example.com/feed", "source_type": "rss",
        })
        response = await client.get("/sources")
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_filter_enabled_true(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "On", "url": "https://on.example.com/feed", "source_type": "rss", "enabled": True,
        })
        await client.post("/sources", json={
            "name": "Off", "url": "https://off.example.com/feed", "source_type": "rss", "enabled": False,
        })
        response = await client.get("/sources?enabled=true")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "On"

    async def test_filter_enabled_false(self, client: AsyncClient):
        await client.post("/sources", json={
            "name": "Active", "url": "https://active.example.com/feed", "source_type": "rss",
        })
        await client.post("/sources", json={
            "name": "Paused", "url": "https://paused2.example.com/feed", "source_type": "rss", "enabled": False,
        })
        response = await client.get("/sources?enabled=false")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Paused"


class TestGetSource:
    async def test_get_existing_source(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "My Source", "url": "https://my.example.com/feed", "source_type": "rss",
        })
        source_id = create.json()["id"]
        response = await client.get(f"/sources/{source_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "My Source"

    async def test_get_nonexistent_returns_404(self, client: AsyncClient):
        response = await client.get("/sources/99999")
        assert response.status_code == 404


class TestUpdateSource:
    async def test_disable_source(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Toggle", "url": "https://toggle.example.com/feed", "source_type": "rss",
        })
        source_id = create.json()["id"]
        response = await client.patch(f"/sources/{source_id}", json={"enabled": False})
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    async def test_re_enable_source(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Reenable", "url": "https://re.example.com/feed", "source_type": "rss", "enabled": False,
        })
        source_id = create.json()["id"]
        response = await client.patch(f"/sources/{source_id}", json={"enabled": True})
        assert response.json()["enabled"] is True

    async def test_update_name(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Old Name", "url": "https://rename.example.com/feed", "source_type": "rss",
        })
        source_id = create.json()["id"]
        response = await client.patch(f"/sources/{source_id}", json={"name": "New Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_update_config(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Scraper", "url": "https://scraper.example.com/", "source_type": "scrape",
        })
        source_id = create.json()["id"]
        response = await client.patch(
            f"/sources/{source_id}", json={"config": {"title_selector": "h2"}},
        )
        assert response.status_code == 200
        assert response.json()["config"]["title_selector"] == "h2"

    async def test_partial_update_preserves_other_fields(self, client: AsyncClient):
        create = await client.post("/sources", json={
            "name": "Partial",
            "url": "https://partial.example.com/feed",
            "source_type": "rss",
            "config": {"key": "value"},
        })
        source_id = create.json()["id"]
        response = await client.patch(f"/sources/{source_id}", json={"name": "Updated"})
        data = response.json()
        assert data["name"] == "Updated"
        assert data["config"] == {"key": "value"}

    async def test_update_nonexistent_returns_404(self, client: AsyncClient):
        response = await client.patch("/sources/99999", json={"enabled": False})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# SSRF guard
# ---------------------------------------------------------------------------

class TestSourceUrlSsrfGuard:
    """POST /sources must reject URLs that point to private or internal addresses."""

    async def _post(self, client: AsyncClient, url: str) -> int:
        response = await client.post("/sources", json={
            "name": "Test", "url": url, "source_type": "rss",
        })
        return response.status_code

    async def test_localhost_url_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://localhost/feed") == 422

    async def test_loopback_ip_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://127.0.0.1/feed") == 422

    async def test_private_class_a_ip_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://10.0.0.1/feed") == 422

    async def test_private_class_c_ip_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://192.168.1.1/feed") == 422

    async def test_link_local_ip_rejected(self, client: AsyncClient):
        # 169.254.x.x is used for AWS instance metadata
        assert await self._post(client, "http://169.254.169.254/latest/meta-data/") == 422

    async def test_dot_local_domain_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://myserver.local/feed") == 422

    async def test_dot_internal_domain_rejected(self, client: AsyncClient):
        assert await self._post(client, "http://api.internal/feed") == 422

    async def test_public_url_still_accepted(self, client: AsyncClient):
        assert await self._post(client, "https://example.com/feed") == 201

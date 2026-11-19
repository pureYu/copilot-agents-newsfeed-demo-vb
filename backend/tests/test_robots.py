"""Unit tests for the robots.txt compliance checker.

All tests patch _fetch_robots_content to avoid real network calls.
Tests that verify RobotFileParser decisions mock the parser itself so
the tests are independent of CPython internals that vary across versions.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.robots import is_url_allowed


class TestIsUrlAllowed:
    async def test_404_means_no_restrictions(self):
        """A 404 on robots.txt means the site has no restrictions."""
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(404, ""))):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_disallow_all_blocks_url(self):
        """Disallow: / blocks every path."""
        robots_txt = "User-agent: *\nDisallow: /"
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))):
            assert await is_url_allowed("http://example.com/news") is False

    async def test_allow_all_permits_url(self):
        """Explicit Allow: / permits every path."""
        robots_txt = "User-agent: *\nAllow: /"
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_specific_path_blocked(self):
        """Disallow: /private/ blocks URLs under that prefix."""
        robots_txt = "User-agent: *\nDisallow: /private/"
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))):
            assert await is_url_allowed("http://example.com/private/article") is False

    async def test_unblocked_path_allowed(self):
        """Disallow: /private/ does not block paths outside that prefix."""
        robots_txt = "User-agent: *\nDisallow: /private/"
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))):
            assert await is_url_allowed("http://example.com/news/article") is True

    async def test_server_error_allows_access_optimistically(self):
        """Non-404 HTTP errors are treated optimistically (proceed with logged warning)."""
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(503, ""))):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_network_error_allows_access_optimistically(self):
        """Network failures are treated optimistically so transient errors don't block ingestion."""
        with patch(
            "app.services.robots._fetch_robots_content",
            AsyncMock(side_effect=Exception("connection refused")),
        ):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_our_specific_user_agent_blocked(self):
        """When RobotFileParser.can_fetch returns False we return False, and we
        pass our declared _USER_AGENT constant — not a hardcoded string."""
        robots_txt = "User-agent: *\nDisallow: /"
        mock_rp = MagicMock()
        mock_rp.can_fetch.return_value = False

        with (
            patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))),
            patch("app.services.robots.RobotFileParser", return_value=mock_rp),
        ):
            result = await is_url_allowed("http://example.com/news")

        mock_rp.can_fetch.assert_called_once_with("newsfeed-bot/0.1", "http://example.com/news")
        assert result is False

    async def test_other_agent_blocked_does_not_affect_us(self):
        """A rule for a different user-agent does not restrict our bot."""
        robots_txt = "User-agent: Googlebot\nDisallow: /"
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, robots_txt))):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_empty_robots_allows_access(self):
        """An empty robots.txt file imposes no restrictions."""
        with patch("app.services.robots._fetch_robots_content", AsyncMock(return_value=(200, ""))):
            assert await is_url_allowed("http://example.com/news") is True

    async def test_robots_url_constructed_from_domain_root(self):
        """The robots.txt URL is always fetched from the domain root."""
        captured: list[str] = []

        async def _mock_fetch(url: str) -> tuple[int, str]:
            captured.append(url)
            return (200, "")

        with patch("app.services.robots._fetch_robots_content", _mock_fetch):
            await is_url_allowed("https://news.example.com/category/tech/article-1")

        assert captured == ["https://news.example.com/robots.txt"]

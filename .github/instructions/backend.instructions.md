---
applyTo: "backend/**"
---

# Backend Instructions

## Architecture
- Prefer clear separation between source management, ingestion, normalization, persistence, and API layers.
- Keep parsing and normalization logic modular and testable.
- Favor explicit data contracts over implicit transformations.

## Ingestion
- Support both RSS and scrape-based sources through source-specific configuration.
- Treat malformed feeds, unreachable pages, invalid source configuration, and extraction failures as expected operational cases.
- Add structured logs for ingestion start, success, deduplication outcomes, and failures.
- Support scheduled and manually triggered ingestion paths where practical.

## Scraping and compliance
- Respect robots.txt, rate limits, site terms, and access restrictions.
- Do not implement paywall bypasses, account automation, or anti-bot circumvention.
- Record compliance assumptions in docs or source configuration notes when adding a scraping source.

## Data and API
- Normalize articles into a canonical model.
- Preserve source attribution, article URL, publication metadata, and ingestion history.
- Support filtering, searching, and article detail retrieval through clear API endpoints.
- Design for deduplication by URL, canonical URL, source identifier, or title similarity where needed.

## Stack
The backend uses the following tooling. Follow these choices consistently:
- **Framework**: FastAPI (Python)
- **Database**: SQLite for development and demo; SQLAlchemy 2 async for ORM; Alembic for migrations
- **RSS parsing**: feedparser
- **HTTP client**: httpx (async)
- **HTML parsing**: BeautifulSoup4
- **Structured logging**: structlog with JSON output
- **Scheduling**: APScheduler (in-process)
- **Testing**: pytest, pytest-asyncio, httpx AsyncClient
- **Package management**: pyproject.toml with pip or uv

## Quality
- Add tests for feed parsing, normalization, deduplication, and error handling.
- Use environment variables for secrets and runtime configuration.
- Prefer structured logging and explicit error reporting over silent failure.
# Application Architecture Overview

## Purpose
This document describes the architecture of the news reader demonstration system and the supporting AI-assisted delivery workflow.

## Objectives
- Keep the solution understandable and demo-friendly.
- Support RSS and scrape-based ingestion.
- Normalize articles into a canonical data model.
- Expose data through backend APIs.
- Provide a frontend for browsing and reading articles.
- Preserve traceability of AI-assisted delivery decisions.

## Proposed high-level components
### Backend
- source registry/configuration
- RSS ingestion service
- scrape ingestion service
- normalization and deduplication layer
- persistence layer
- API layer
- ingestion history and error reporting
- structured logging

### Frontend
- article list view
- article detail view
- search and filtering UI
- source and category/tag filters
- loading, empty, and error states
- refresh/sync interaction where supported

### Documentation and AI workflow
- repository-wide instructions
- path-specific instructions
- custom agents
- reusable skills
- APM-managed packages
- MCP integrations
- execution and evidence logs

## Data model areas
At minimum, the system should model:
- sources
- source type
- source configuration
- articles
- article metadata
- ingestion history
- ingestion errors

## Key design decisions

### Backend framework: FastAPI (Python)
Decided on 2026-07-11.

FastAPI was selected for the backend API and ingestion services.

Reasons:
- Async-native using Python `asyncio`, which aligns with concurrent RSS feed fetching and scrape requests.
- Built-in OpenAPI/Swagger documentation at `/docs` — useful for demo walkthroughs without a separate API client.
- Pydantic v2 models provide data validation and serialization at the boundary with no boilerplate.
- Type annotations throughout make the codebase readable without additional documentation.
- Lightweight enough to keep the demo understandable; no hidden framework magic.

### Database: SQLite (development and demo)
Decided on 2026-07-11.

SQLite was selected for the demonstration scope.

Reasons:
- Zero setup — no external database process required to run or reproduce the demo.
- File-based — the database travels with the project and can be reset easily between demo runs.
- Fully supported by SQLAlchemy; migration to PostgreSQL would require only a connection string change.

Limitation: SQLite serialises writes, so it is not suitable for production-scale concurrent ingestion. Acceptable for demo purposes.

### ORM and migrations: SQLAlchemy 2 (async) + Alembic
Decided on 2026-07-11.

SQLAlchemy 2's async session model aligns with FastAPI's async request handling. Alembic provides schema migration management. Tortoise ORM was considered but rejected: SQLAlchemy has a larger ecosystem, better documentation, and is more widely recognised in a demonstration context.

### RSS parsing: feedparser
Decided on 2026-07-11.

feedparser is the de facto Python RSS/Atom library. It handles feed format variations, malformed entries, and encoding issues without custom parsing logic.

### HTTP client and scraping: httpx + BeautifulSoup4
Decided on 2026-07-11.

httpx was selected over requests because it is async-native and compatible with the FastAPI/asyncio runtime. BeautifulSoup4 provides HTML parsing for scrape-based ingestion. lxml is available as a faster parser back-end when needed.

### Structured logging: structlog
Decided on 2026-07-11.

structlog produces JSON-formatted, context-bound log output. It satisfies the structured logging requirement for ingestion, scraping, API operations, and failures. The standard library `logging` module was rejected because JSON formatting requires non-trivial configuration and context binding is manual.

### Task scheduling: APScheduler
Decided on 2026-07-11.

APScheduler runs in-process alongside FastAPI and supports interval and cron-style schedules. Celery was considered and rejected: it requires a separate broker (Redis or RabbitMQ) which adds setup complexity inconsistent with a demo-portable project.

### Testing: pytest + pytest-asyncio + httpx (AsyncClient)
Decided on 2026-07-11.

pytest with the asyncio plugin enables async test functions that match the async application code. httpx's `AsyncClient` is used as the test HTTP client against the FastAPI app directly.

### Frontend framework
Deferred to milestone M3 (task G-1). Decision will be recorded here when made.

## Tradeoffs and alternatives

| Decision | Chosen | Rejected | Reason rejected |
|---|---|---|---|
| Backend framework | FastAPI | Flask | No async; no built-in validation or docs |
| Backend framework | FastAPI | Django REST Framework | Excessive for a demo-scale app; steeper setup |
| Database | SQLite | PostgreSQL | Requires external process; adds setup friction for a portable demo |
| ORM | SQLAlchemy 2 async | Tortoise ORM | Smaller ecosystem; less familiar to reviewers |
| HTTP client | httpx | requests | requests is sync-only; incompatible with async ingestion |
| Structured logging | structlog | stdlib logging | stdlib requires manual JSON formatter and context binding |
| Scheduling | APScheduler | Celery | Celery requires a broker; disproportionate for demo scope |

## Validation approach
Expected validation areas:
- RSS ingestion
- scrape ingestion with allowed sources
- normalization and deduplication
- backend API behavior
- frontend browsing and reading flows
- documentation completeness for the AI demonstration
# Code Review Implementation Plan

**Source:** [docs/code-review-report.md](code-review-report.md)  
**Date:** 2026-07-13  
**Status:** Pending  

This plan converts all findings from the 2026-07-13 code review into actionable implementation phases. Each phase maps to one GitHub issue. Phases are ordered by severity: blocking first, then non-blocking by backend/frontend/infra grouping, then suggestions.

---

## Phase 1: Fix Blocking Startup Crash and SSL Security Misconfiguration

**Template:** `chore_request.yml`  
**Category:** configuration  
**Labels:** chore  

### Description

Two blocking issues must be resolved before the next deployment.

**BLOCKING-1 — SQLAlchemy startup crash (`models.py`)**  
`IngestionError` is missing its `source` and `run` relationship attributes. `Source.ingestion_errors` and `IngestionRun.errors` both declare `back_populates` pointing at `IngestionError`, but `IngestionError` defines neither side. SQLAlchemy 2.0 raises `ArgumentError` during mapper configuration — the application cannot start and the full test suite fails.

**BLOCKING-2 — SSL verification disabled in production (`docker-compose.yml`)**  
`SSL_VERIFY: "false"` disables TLS certificate validation for all outbound HTTPS requests (RSS fetches, robots.txt checks, and scrape requests), making every feed endpoint vulnerable to a machine-in-the-middle attack that could inject arbitrary article content. The setting defaults to `True` in `core/config.py` and must not be forced to `false` in the compose file.

### Requirements reference

Sections 3.1 and 4 of `docs/REQUIREMENTS_SUMMARY.md` — working backend API and ingestion services; no hardcoded or insecure configuration values.

### Acceptance criteria

- [ ] `IngestionError` has a `source: Mapped["Source"]` relationship attribute with `back_populates="ingestion_errors"` and `lazy="noload"`.
- [ ] `IngestionError` has a `run: Mapped["IngestionRun | None"]` relationship attribute with `back_populates="errors"` and `lazy="noload"`.
- [ ] The full backend test suite passes (`pytest`).
- [ ] `SSL_VERIFY: "false"` is removed from `docker-compose.yml`.
- [ ] `.env.example` documents `SSL_VERIFY=false` with a note that it is only for corporate proxy environments and must never be set in production.
- [ ] Application starts successfully via `docker compose up`.

### Notes and dependencies

Files changed: `backend/app/models.py`, `docker-compose.yml`, `.env.example`.  
No dependencies on other phases.

---

## Phase 2: Add Structured Logging to Articles and Sources API Routers

**Template:** `chore_request.yml`  
**Category:** refactoring  
**Labels:** chore  

### Description

`copilot-instructions.md` and `backend.instructions.md` both require structured logging for all API operations. The `ingest.py` router logs correctly with `structlog`, but `articles.py` and `sources.py` have no logging at all. The following events are currently silent:

- 404 responses (article not found, source not found)
- Article list/search/filter executions (query params, result count)
- Source creation, update, and deletion
- Duplicate-URL rejection on source creation

### Requirements reference

`docs/REQUIREMENTS_SUMMARY.md` section 3.1 — structured logging for API operations and failures.  
`.github/instructions/backend.instructions.md` — every router must use `structlog`.

### Acceptance criteria

- [ ] `articles.py` imports and uses `structlog` at module level.
- [ ] `sources.py` imports and uses `structlog` at module level.
- [ ] 404 responses in both routers emit a structured log event with article/source ID.
- [ ] Article list endpoint logs query parameters and result count at `INFO` level.
- [ ] Source create endpoint logs the new source URL and whether the URL was rejected as a duplicate.
- [ ] Source update and delete endpoints log the source ID and outcome.
- [ ] No `print()` statements introduced.

### Notes and dependencies

Files changed: `backend/app/api/articles.py`, `backend/app/api/sources.py`.  
No dependencies on other phases.

---

## Phase 3: Add Frontend Test Infrastructure (Vitest + React Testing Library)

**Template:** `chore_request.yml`  
**Category:** infrastructure  
**Labels:** chore  

### Description

The frontend has zero test coverage. No test framework, no test scripts, and no test files exist. `frontend.instructions.md` explicitly requires tests for critical rendering and interaction flows. The following components and pages have no coverage: `ArticleCard`, `ErrorMessage`, `LoadingSpinner`, `ArticlesPage`, `ArticleDetailPage`, and the API client in `src/api/`.

### Requirements reference

`docs/REQUIREMENTS_SUMMARY.md` section 3.1 — include tests for critical flows.  
`.github/instructions/frontend.instructions.md` — Vitest + React Testing Library required.

### Acceptance criteria

- [ ] `vitest`, `@testing-library/react`, `@testing-library/user-event`, and `@testing-library/jest-dom` are added to `devDependencies` in `frontend/package.json`.
- [ ] A `test` script is added to `package.json` (e.g. `vitest run`).
- [ ] `vitest.config.ts` (or config merged into `vite.config.ts`) is present with jsdom environment.
- [ ] At minimum one test file exists per required item:
  - `ArticleCard` renders title, source name, and publication date.
  - `ErrorMessage` renders the provided message text.
  - `ArticlesPage` renders a loading spinner while fetching, then article cards.
- [ ] `npm test` exits with code 0.
- [ ] Tests are added to the CI pipeline if one exists.

### Notes and dependencies

Files changed: `frontend/package.json`, `frontend/vite.config.ts` or new `frontend/vitest.config.ts`, new files under `frontend/src/__tests__/` or co-located `.test.tsx` files.  
No dependencies on other phases.

---

## Phase 4: Centralise `_USER_AGENT` and `_FETCH_TIMEOUT` in Core Config

**Template:** `chore_request.yml`  
**Category:** refactoring  
**Labels:** chore  

### Description

Both `backend/app/services/rss.py` and `backend/app/services/scrape.py` independently hard-code `_FETCH_TIMEOUT = httpx.Timeout(30.0)` and `_USER_AGENT = "newsfeed-bot/0.1"`. A change to either value in one file does not propagate to the other. `_USER_AGENT` is also referenced directly in tests, meaning test breakage if the string changes in one service but not the other. These should be centralised in `core/config.py` as `Settings` fields with environment-variable overrides.

### Requirements reference

`.github/instructions/backend.instructions.md` — configuration via `pydantic-settings`; no hardcoded values.

### Acceptance criteria

- [ ] `Settings` in `core/config.py` gains `user_agent: str = "newsfeed-bot/0.1"` and `fetch_timeout_seconds: float = 30.0`.
- [ ] `rss.py` and `scrape.py` read these values from `settings` instead of local constants.
- [ ] Tests that assert on the user-agent string reference `settings.user_agent`.
- [ ] Both values are documented in `.env.example`.
- [ ] No functional behaviour changes.

### Notes and dependencies

Files changed: `backend/app/core/config.py`, `backend/app/services/rss.py`, `backend/app/services/scrape.py`, relevant test files, `.env.example`.  
No dependencies on other phases.

---

## Phase 5: Improve Ingest Error Reporting in `ingest_all` Response

**Template:** `feature_request.yml`  
**Labels:** enhancement  

### Description

When `_dispatch_ingest` raises an unhandled exception before a run record is created, that source is silently dropped from the returned `runs` list. Callers cannot distinguish "zero sources were enabled" from "one source crashed before a run was created". The response should always account for every enabled source — either with a run entry or with an error summary entry.

### Requirements reference

`docs/REQUIREMENTS_SUMMARY.md` section 3.1 — structured logging for ingestion and failures.  
`.github/instructions/backend.instructions.md` — ingestion errors must be surfaced.

### Acceptance criteria

- [ ] Every enabled source processed by `ingest_all` is represented in the response, whether it succeeded or failed early.
- [ ] Sources that fail before a run is created appear as an error entry containing the source ID and a reason string.
- [ ] The response schema (`schemas/ingest.py`) is updated to accommodate both run entries and error entries, or a separate `errors` field is added.
- [ ] A structured log event is emitted for each pre-run failure.
- [ ] Existing tests are updated; at least one new test covers the pre-run failure path.

### Notes and dependencies

Files changed: `backend/app/api/ingest.py`, `backend/app/schemas/ingest.py`, `backend/tests/test_api_ingest.py`.  
No dependencies on other phases.

---

## Phase 6: Implement APScheduler for Periodic Background Ingestion

**Template:** `feature_request.yml`  
**Labels:** enhancement  

### Description

`apscheduler>=3.10.0` is declared as a dependency in `pyproject.toml` and `backend.instructions.md` requires it for scheduled ingestion, but no scheduler is configured anywhere in the application. The lifespan handler in `main.py` does not start a scheduler. Periodic ingestion never runs; the dependency adds image weight with no effect.

This phase initialises APScheduler in the FastAPI lifespan handler to run ingestion on a configurable interval.

### Requirements reference

`docs/REQUIREMENTS_SUMMARY.md` section 3.1 — RSS and scrape-based source ingestion must be supported.  
`.github/instructions/backend.instructions.md` — APScheduler for scheduled ingestion.

### Acceptance criteria

- [ ] `AsyncIOScheduler` (or `BackgroundScheduler`) is started in the lifespan `startup` block and stopped in `shutdown`.
- [ ] A job is registered that calls the ingest-all logic on a configurable interval (default 60 minutes).
- [ ] The interval is controlled by a `Settings` field (e.g. `ingest_interval_minutes: int = 60`) backed by an environment variable.
- [ ] The interval is documented in `.env.example`.
- [ ] Structured log events are emitted at scheduler start, stop, and each job execution.
- [ ] The manual `POST /ingest/` endpoint continues to work independently.
- [ ] At least one test confirms the scheduler is registered at startup (can use a mock/spy).

### Notes and dependencies

Files changed: `backend/app/main.py`, `backend/app/core/config.py`, `.env.example`, `backend/tests/`.  
No dependencies on other phases, but integrates with Phase 5 (ingest error reporting).

---

## Phase 7: Initialise Alembic and Create Baseline Database Migration

**Template:** `chore_request.yml`  
**Category:** infrastructure  
**Labels:** chore  

### Description

`alembic>=1.13.0` is declared as a dependency and `backend.instructions.md` specifies Alembic for schema migrations, but no `alembic/` directory, `alembic.ini`, or migration history exists. The schema is managed entirely via `Base.metadata.create_all`, which cannot safely apply changes to existing databases and will silently leave columns missing on upgrade. This phase bootstraps Alembic with a baseline migration that reflects the current schema.

### Requirements reference

`.github/instructions/backend.instructions.md` — Alembic for database migrations.

### Acceptance criteria

- [ ] `alembic init alembic` has been run and the resulting `alembic/` directory is committed.
- [ ] `alembic.ini` references the `DATABASE_URL` environment variable (not a hardcoded path).
- [ ] `alembic/env.py` imports `Base` and uses `target_metadata = Base.metadata`.
- [ ] A baseline migration exists that creates all current tables (`articles`, `sources`, `ingestion_runs`, `ingestion_errors`).
- [ ] `alembic upgrade head` runs without errors against a fresh SQLite database.
- [ ] The `entrypoint.sh` script runs `alembic upgrade head` before starting the application.
- [ ] `Base.metadata.create_all` is removed from the startup path.

### Notes and dependencies

Files changed: new `backend/alembic/` directory, `backend/alembic.ini`, `backend/entrypoint.sh`, `backend/app/database.py` or `main.py`.  
Depends on Phase 1 (startup crash fix) — the models must be correct before a migration is generated.

---

## Phase 8: Fix Frontend Silent Error Handling and Input Guard

**Template:** `chore_request.yml`  
**Category:** refactoring  
**Labels:** chore  

### Description

Two frontend issues silently fail in ways that harm UX and debuggability.

**NON-BLOCKING-7 — Source list error swallowed in `ArticlesPage`**  
`getSources().then(...).catch(() => {})` silently discards errors. If the sources endpoint fails, the filter dropdown is empty with no user feedback and no console warning.

**SUGGESTION-2 — Non-numeric article ID not guarded before `Number()` conversion**  
In `ArticleDetailPage.tsx`, `getArticle(Number(id))` converts a non-numeric path segment to `NaN`, producing a `/articles/NaN` API request and a confusing 422 response. A guard should catch this before the request is made.

### Requirements reference

`.github/instructions/frontend.instructions.md` — all error states must be handled and visible to the user.

### Acceptance criteria

- [ ] In `ArticlesPage`, the `catch` block in the sources fetch logs a `console.warn` and sets a visible UI message (e.g. "Could not load sources for filtering").
- [ ] In `ArticleDetailPage`, a guard checks `!id || isNaN(Number(id))` before calling `getArticle`. If triggered, a "Not found" or error state is shown to the user without making a network request.
- [ ] No new `console.error` calls are silently swallowed.
- [ ] Existing rendering behaviour for valid inputs is unchanged.

### Notes and dependencies

Files changed: `frontend/src/pages/ArticlesPage.tsx`, `frontend/src/pages/ArticleDetailPage.tsx`.  
No dependencies on other phases.

---

## Phase 9: Content Quality and Code Clarity Improvements

**Template:** `chore_request.yml`  
**Category:** refactoring  
**Labels:** chore  

### Description

Three small improvements to content handling and code clarity identified during the code review.

**SUGGESTION-1 — RSS HTML content rendered as escaped plain text**  
RSS `<content:encoded>` typically contains HTML markup. React escapes JSX string children, so users see raw tags as plain text (e.g. `<p>text</p>`). The recommended fix is to strip HTML server-side in `rss.py` before storing the content field.

**SUGGESTION-3 — `json_each` SQLite dependency undocumented**  
The tag filter in `articles.py` uses SQLite's `json_each` table-valued function. This does not exist in PostgreSQL or MySQL. A code comment noting the SQLite requirement prevents a silent failure if the database is ever swapped.

**SUGGESTION-4 — Articles sorted by `ingested_at` instead of `published_at`**  
After a bulk ingest, all articles share nearly identical `ingested_at` timestamps, making ordering meaningless. Sorting by `published_at DESC NULLS LAST, ingested_at DESC` produces a more useful chronological feed.

### Requirements reference

`docs/REQUIREMENTS_SUMMARY.md` section 3.1 — article normalisation into a canonical model; basic article browsing flows.

### Acceptance criteria

- [ ] `rss.py` strips HTML from the article content/description field before storing (e.g. using `bleach.clean` with no allowed tags, or a simple regex/html.parser strip).
- [ ] A comment in `articles.py` near the `json_each` call notes: "SQLite-specific — replace with a JSON operator or normalised tags table for PostgreSQL/MySQL".
- [ ] The default article list query orders by `published_at DESC NULLS LAST, ingested_at DESC`.
- [ ] Existing tests pass; update any test that asserts on article ordering.

### Notes and dependencies

Files changed: `backend/app/services/rss.py`, `backend/app/api/articles.py`.  
No dependencies on other phases, but consider doing after Phase 1 (stable startup) so manual testing is possible.

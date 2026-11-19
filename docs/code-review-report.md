# Code Review Report

**Date:** 2026-07-13
**Reviewer:** code-review agent
**Scope:** Full codebase — `backend/app/`, `backend/tests/`, `frontend/src/`

---

## Summary

**Status: NEEDS CHANGES**

The codebase is well-structured and follows most project conventions. SSRF protection, robots.txt compliance, and ingestion deduplication are solid. However, one startup-blocking SQLAlchemy configuration bug and one production-level security misconfiguration must be resolved before the next deployment. Structured logging is missing from two API routers despite being an explicit project requirement, and the frontend has no test coverage.

---

## Findings

### Blocking

---

**[BLOCKING-1] SQLAlchemy startup crash — missing `back_populates` on `IngestionError`**
- **File:** `backend/app/models.py`
- **Severity:** Blocking
- **Description:** `Source.ingestion_errors` declares `back_populates="source"` and `IngestionRun.errors` declares `back_populates="run"`, but `IngestionError` defines neither relationship attribute. SQLAlchemy 2.0 raises `ArgumentError` during mapper configuration — the app cannot start and the full test suite fails.
- **Fix:** Add to `IngestionError`:
  ```python
  source: Mapped["Source"] = relationship("Source", back_populates="ingestion_errors", lazy="noload")
  run: Mapped["IngestionRun | None"] = relationship("IngestionRun", back_populates="errors", lazy="noload")
  ```

---

**[BLOCKING-2] SSL verification disabled in production Docker image**
- **File:** `docker-compose.yml`
- **Severity:** Blocking
- **Description:** `SSL_VERIFY: "false"` disables TLS certificate validation for all outbound HTTPS requests — RSS fetches, robots.txt checks, and scrape requests — making every feed endpoint vulnerable to a machine-in-the-middle attack that could inject arbitrary article content.
- **Fix:** Remove `SSL_VERIFY: "false"` from `docker-compose.yml`. The setting defaults to `True` in `core/config.py`. Document it in `.env.example` for operators who need it for corporate proxy environments.

---

### Non-Blocking

---

**[NON-BLOCKING-1] Structured logging absent from `articles` and `sources` API routers**
- **Files:** `backend/app/api/articles.py`, `backend/app/api/sources.py`
- **Severity:** Non-blocking
- **Description:** `copilot-instructions.md` and `backend.instructions.md` both require structured logging for API operations. `ingest.py` logs correctly. Neither `articles.py` nor `sources.py` imports or uses `structlog`. 404 responses, search/filter executions, source creation/update, and duplicate-URL rejections are all silent.

---

**[NON-BLOCKING-2] No frontend test framework or tests**
- **Files:** `frontend/package.json`, `frontend/src/`
- **Severity:** Non-blocking
- **Description:** No `test` script and no testing framework (Vitest, Jest, React Testing Library) is installed. `frontend.instructions.md` requires tests for critical rendering and interaction flows. `ArticlesPage`, `ArticleDetailPage`, `ArticleCard`, and the API client have zero coverage.

---

**[NON-BLOCKING-3] `_USER_AGENT` and `_FETCH_TIMEOUT` duplicated across services**
- **Files:** `backend/app/services/rss.py`, `backend/app/services/scrape.py`
- **Severity:** Non-blocking
- **Description:** Both files independently hard-code `_FETCH_TIMEOUT = httpx.Timeout(30.0)` and `_USER_AGENT = "newsfeed-bot/0.1"`. A change in one place does not propagate. `_USER_AGENT` is also referenced in tests. These should be centralised in `core/config.py`.

---

**[NON-BLOCKING-4] Failed sources silently omitted from `ingest_all` response**
- **File:** `backend/app/api/ingest.py`
- **Severity:** Non-blocking
- **Description:** When `_dispatch_ingest` raises an unhandled exception before a run is created, that source is skipped with no entry in the returned `runs` list. Callers cannot distinguish "0 sources enabled" from "1 source crashed before creating a run".

---

**[NON-BLOCKING-5] APScheduler declared as dependency but never initialised**
- **File:** `backend/pyproject.toml`, `backend/app/main.py`
- **Severity:** Non-blocking
- **Description:** `apscheduler>=3.10.0` is listed as a dependency and `backend.instructions.md` requires it for scheduled ingestion. No scheduler is configured in the lifespan handler. Scheduled ingestion never runs; the dependency adds image weight with no effect.

---

**[NON-BLOCKING-6] Alembic declared as dependency but no migrations exist**
- **File:** `backend/pyproject.toml`
- **Severity:** Non-blocking
- **Description:** `alembic>=1.13.0` is declared and `backend.instructions.md` specifies Alembic for migrations. Schema is managed entirely via `Base.metadata.create_all`, which cannot safely apply changes to existing databases. No `alembic/` directory, `alembic.ini`, or migration history exists.

---

**[NON-BLOCKING-7] Source list fetch error silently swallowed in `ArticlesPage`**
- **File:** `frontend/src/pages/ArticlesPage.tsx`
- **Severity:** Non-blocking
- **Description:** `getSources().then(...).catch(() => {})` silently discards errors. If the sources endpoint fails, the filter dropdown is empty with no user feedback.

---

### Suggestions

---

**[SUGGESTION-1] RSS article HTML content rendered as escaped plain text**
- **File:** `frontend/src/pages/ArticleDetailPage.tsx`
- **Description:** RSS `<content:encoded>` typically contains HTML. React escapes JSX string children, so users see raw tags as plain text. Options: strip server-side before storing (recommended), or render via `dangerouslySetInnerHTML` after sanitisation with `bleach`.

---

**[SUGGESTION-2] Non-numeric article ID not guarded before `Number()` conversion**
- **File:** `frontend/src/pages/ArticleDetailPage.tsx`
- **Description:** `getArticle(Number(id))` converts a non-numeric path segment to `NaN`, producing a `/articles/NaN` request and a confusing 422 error. Add a guard: `if (!id || isNaN(Number(id))) { /* show not found */ }`.

---

**[SUGGESTION-3] `json_each` tag filter is SQLite-specific and undocumented**
- **File:** `backend/app/api/articles.py`
- **Description:** The tag query uses SQLite's `json_each` table-valued function, which does not exist in PostgreSQL or MySQL. A code comment noting the SQLite dependency would prevent a silent failure if the database is swapped.

---

**[SUGGESTION-4] Articles sorted by `ingested_at` instead of `published_at`**
- **File:** `backend/app/api/articles.py`
- **Description:** After a bulk ingest all articles share nearly identical `ingested_at` timestamps. Sorting by `published_at DESC NULLS LAST, ingested_at DESC` would produce a more useful chronological feed.

---

## Positive Findings

- **SSRF mitigation is thorough** — `SourceCreate.url_must_be_public` validates IPs and hostnames; `TestSourceUrlSsrfGuard` covers loopback, private ranges, link-local (169.254.x.x), `.local`, and `.internal`.
- **robots.txt compliance is solid** — 404 → allowed; non-404 errors → optimistic allow + warn; delegates to stdlib `RobotFileParser`; exhaustive unit tests.
- **Ingestion error handling survives session corruption** — raw DML after rollback safely records failures without touching expired ORM objects.
- **Two-layer deduplication** — in-batch `seen_urls` set plus pre-insert DB lookup; both tested.
- **Async correctness** — `feedparser.parse` via `asyncio.to_thread`; `expire_on_commit=False` and `lazy="noload"` throughout.
- **React UX quality** — loading, empty, and error states on all pages; `useEffect` cancelled-flag prevents stale updates; `rel="noopener noreferrer"` on all external links; `role="alert"` and `aria-label` present.
- **No hardcoded secrets** — all config via `pydantic-settings`; seed script is secret-free.

---

## Required Actions

| ID | Severity | Action | File(s) |
|----|----------|--------|---------|
| BLOCKING-1 | Blocking | Add `source` and `run` relationship attributes to `IngestionError` | `backend/app/models.py` |
| BLOCKING-2 | Blocking | Remove `SSL_VERIFY: "false"` from docker-compose; move to `.env.example` | `docker-compose.yml` |
| NON-BLOCKING-1 | Non-blocking | Add `structlog` logging to `articles.py` and `sources.py` | `backend/app/api/articles.py`, `backend/app/api/sources.py` |
| NON-BLOCKING-2 | Non-blocking | Add Vitest + React Testing Library; write smoke tests for `ArticleCard`, `ErrorMessage`, and one page render | `frontend/` |
| NON-BLOCKING-3 | Non-blocking | Extract `_USER_AGENT` and `_FETCH_TIMEOUT` to `core/config.py` | `backend/app/services/rss.py`, `backend/app/services/scrape.py`, `backend/app/core/config.py` |
| NON-BLOCKING-4 | Non-blocking | Include failed-source entries or a summary count in `ingest_all` response | `backend/app/api/ingest.py` |
| NON-BLOCKING-5 | Non-blocking | Initialise APScheduler for periodic ingestion in lifespan, or remove the dependency | `backend/app/main.py`, `backend/pyproject.toml` |
| NON-BLOCKING-6 | Non-blocking | Initialise Alembic with a baseline migration, or remove the dependency | `backend/pyproject.toml` |
| NON-BLOCKING-7 | Non-blocking | Surface source list fetch error in the filter dropdown with a console warning or UI message | `frontend/src/pages/ArticlesPage.tsx` |
| SUGGESTION-1 | Suggestion | Strip or sanitise HTML from RSS `content` before display | `backend/app/services/rss.py` or `frontend/src/pages/ArticleDetailPage.tsx` |
| SUGGESTION-2 | Suggestion | Guard non-numeric `id` param before `Number()` conversion | `frontend/src/pages/ArticleDetailPage.tsx` |
| SUGGESTION-3 | Suggestion | Add comment noting `json_each` is SQLite-specific | `backend/app/api/articles.py` |
| SUGGESTION-4 | Suggestion | Change default article sort to `published_at DESC NULLS LAST, ingested_at DESC` | `backend/app/api/articles.py` |

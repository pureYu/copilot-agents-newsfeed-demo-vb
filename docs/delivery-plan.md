# Delivery Plan

## Deliverable Distinction

| Label | Deliverable | What it is |
|---|---|---|
| [P] | Primary | Copilot AI workflow evidence: agents, skills, MCP, APM, logs, docs |
| [S] | Secondary | Working news reader application: backend + frontend |

Most milestones require tasks from both labels. Evidence tasks must accompany every application task.

---

## Epics

### Epic A — AI Workflow Foundation [P]
Establish all Copilot AI infrastructure: agent definitions, skills, instructions, APM packages, MCP integrations.

### Epic B — APM Asset Management [P]
Install, version, and inventory AI packages from `github/awesome-copilot`. Produce a reproducible setup path.

### Epic C — Delivery Evidence & Documentation [P]
Populate `agent-execution-log.md`, `copilot-usage-guide.md`, `demo-script.md`, and `mcp-integration-summary.md` as work progresses.

### Epic D — Backend Data & API [S]
Canonical data model, persistence layer, and REST API for sources and articles.

### Epic E — RSS Ingestion [S]
Fetch, parse, normalize, and deduplicate articles from RSS/Atom feeds.

### Epic F — Scrape Ingestion [S]
Per-source scraping with `robots.txt` compliance, rate limits, and error capture.

### Epic G — Frontend [S]
Article list, detail, search, filter, source selector, and all auxiliary states.

### Epic H — Testing & Validation [P+S]
Tests for critical flows; validation evidence for the AI demonstration.

---

## Milestones

| # | Name | Epics covered | Primary signal |
|---|---|---|---|
| M1 | AI Workflow Infrastructure Ready | A, B | All agents defined, APM populated, MCPs configured |
| M2 | Backend + RSS MVP | C, D, E | API serves articles ingested from at least one real RSS feed |
| M3 | Full Stack Integration | C, G | Frontend renders live articles from backend |
| M4 | Scrape Ingestion + Compliance | C, F | At least one scrape source working with `robots.txt` validation |
| M5 | Tested, Evidenced, Demo-Ready | C, H | Tests pass; all evidence docs complete; demo script runnable |

---

## Issue-Sized Tasks, Acceptance Criteria & Dependencies

## M1 — AI Workflow Infrastructure Ready

### A-1 [P] Define missing agent roles
Add agent entries for:
- executor
- research
- code-review
- security-review
- qa

Each file must declare:
- name
- description
- tools
- model
- responsibilities

**Depends on:** nothing

**Acceptance Criteria**
- 5 new agent files exist and are readable by Copilot
- `agent-execution-log.md` updated with this task

---

### A-2 [P] Select and install APM packages from `github/awesome-copilot`
Identify 2–4 packages relevant to:
- planning
- code review
- documentation
- testing

Run:
```text
copilot plugin marketplace add github/awesome-copilot
copilot plugin install <name>@awesome-copilot
```

**Depends on:** A-1

**Acceptance Criteria**
- `apm-inventory.md` has ≥ 2 rows with:
  - name
  - version
  - source
  - purpose
  - usage evidence
- installation commands recorded

---

### A-3 [P] Configure MCP integrations
Enable GitHub MCP (repo/issue/PR context).

Evaluate and configure one additional MCP:
- Browser/Playwright, or
- search

**Depends on:** nothing

**Acceptance Criteria**
- `mcp-integration-summary.md` has ≥ 2 rows
- each row has:
  - setup status
  - purpose
  - one concrete usage example

---

### A-4 [P] Extend path-specific Copilot instructions
Verify `backend.instructions.md` and `frontend.instructions.md` are complete.

Confirm they cover:
- logging conventions
- error handling
- testing expectations
- security constraints

**Depends on:** nothing

**Acceptance Criteria**
- both instruction files reviewed
- gaps filled
- `agent-execution-log.md` updated

---

## M2 — Backend + RSS MVP

### D-1 [S] Choose and document backend tech stack
Evaluate:
- Python/FastAPI
- Node/Express
- or equivalent

Record decision, rationale, and tradeoffs in `architecture-overview.md`.

**Depends on:** A-4

**Acceptance Criteria**
- `architecture-overview.md` has a **Key design decisions** section with stack choice rationale
- `agent-execution-log.md` updated with research agent output

---

### D-2 [S] Implement canonical data models
Models:
- **Source** (`id`, `name`, `type`, `config`, `enabled`, `created_at`)
- **Article** (`id`, `source_id`, `title`, `url`, `canonical_url`, `author`, `published_at`, `summary`, `content`, `image_url`, `tags`, `created_at`)
- **IngestionRun** (`id`, `source_id`, `started_at`, `completed_at`, `status`, `articles_found`, `articles_inserted`)
- **IngestionError** (`id`, `source_id`, `run_id`, `error_message`, `occurred_at`)

**Depends on:** D-1

**Acceptance Criteria**
- models are defined in code
- migrations or schema scripts exist and run without error
- unit tests cover model validation

---

### D-3 [S] Implement source management API
Endpoints:
- `POST /sources` — register a new source
- `GET /sources` — list all sources
- `PATCH /sources/{id}` — update source config or enabled flag

**Depends on:** D-2

**Acceptance Criteria**
- endpoints respond correctly
- request validation rejects invalid source type or missing URL
- tests exist for happy path and validation errors

---

### D-4 [S] Implement articles API
Endpoints:
- `GET /articles` — list with pagination, source filter, tag filter, search query
- `GET /articles/{id}` — single article detail

**Depends on:** D-2

**Acceptance Criteria**
- filtering and search work for at least source and keyword
- pagination returns correct total and page metadata
- tests exist

---

### E-1 [S] Implement RSS ingestion service
Requirements:
- fetch and parse RSS/Atom feeds for registered sources
- extract:
  - title
  - url
  - author
  - `published_at`
  - summary
  - content
  - `image_url`
  - tags
- normalize into `Article` model
- deduplicate by URL or canonical URL
- report malformed feeds as `IngestionError` records

**Depends on:** D-2

**Acceptance Criteria**
- given one real RSS feed URL, ingestion creates ≥ 1 article in the database
- duplicate run does not create duplicate articles
- malformed feed logs an error record

---

### E-2 [S] Implement ingestion trigger endpoint
Endpoints:
- `POST /ingest/{source_id}` — manually trigger ingestion for one source
- `POST /ingest` — trigger all enabled sources

**Depends on:** E-1, D-3

**Acceptance Criteria**
- trigger runs ingestion synchronously or returns job id
- ingestion run record is created
- errors are captured

---

### E-3 [S] Implement structured logging
Logging requirements:
- log ingestion start, completion, article counts, and errors at `INFO`/`ERROR` level
- log API requests at `DEBUG` level with method and path
- use structured format (JSON preferred)

**Depends on:** D-1

**Acceptance Criteria**
- log output is parseable
- ingestion events are identifiable without reading source code

---

### C-1 [P] Agent execution log — M2 entries
Record executor agent usage for:
- D-1 through E-3

Record research agent input/output for:
- tech stack choice

**Depends on:** D-1, E-1

**Acceptance Criteria**
- `agent-execution-log.md` has ≥ 4 new rows covering M2 work

---

## M3 — Full Stack Integration

### G-1 [S] Choose and document frontend tech stack
Evaluate:
- React + Vite
- Next.js
- or equivalent

Record decision in `architecture-overview.md`.

**Depends on:** D-4 (API contract known)

**Acceptance Criteria**
- frontend framework chosen
- entry in `architecture-overview.md`
- `agent-execution-log.md` updated

---

### G-2 [S] Scaffold frontend project
Initialize project in `frontend`.

Set up:
- dev server
- routing
- API client pointing to backend

**Depends on:** G-1

**Acceptance Criteria**
- `npm run dev` (or equivalent) starts without errors
- dev server reaches backend health endpoint

---

### G-3 [S] Implement article list view
Requirements:
- fetch and render articles from `GET /articles`
- show:
  - title
  - source
  - publication time
  - summary

**Depends on:** G-2, D-4

**Acceptance Criteria**
- list renders real articles
- loading and empty states are visible
- no console errors on happy path

---

### G-4 [S] Implement search and filter UI
Requirements:
- source filter (dropdown or chips)
- keyword search input with debounce
- tag/category filter when metadata exists

**Depends on:** G-3

**Acceptance Criteria**
- changing filter triggers new API call with correct query params
- results update without full page reload

---

### G-5 [S] Implement article detail view
Route:
- `/articles/:id` renders full article from `GET /articles/{id}`

Show all fields:
- title
- author
- source
- `published_at`
- content
- image
- tags
- original URL link

**Depends on:** G-2, D-4

**Acceptance Criteria**
- detail view loads for any article id
- source attribution and original link are always visible

---

### G-6 [S] Implement refresh/sync action and error states
Requirements:
- sync button calls `POST /ingest` and shows progress or result
- article list shows error state if API is unreachable

**Depends on:** G-3, E-2

**Acceptance Criteria**
- sync button produces visible feedback
- error state does not show raw error objects to the user

---

### C-2 [P] Agent execution log — M3 entries
Record executor and review agent usage for frontend work.

**Depends on:** G-1 through G-6

**Acceptance Criteria**
- `agent-execution-log.md` updated with M3 entries

---

## M4 — Scrape Ingestion + Compliance

### F-1 [S] Implement `robots.txt` check
Before any scrape request:
- fetch and parse `robots.txt` for the domain
- disallow configured paths
- log a compliance skip if disallowed

**Depends on:** E-1 (ingestion infrastructure exists)

**Acceptance Criteria**
- scrape of a disallowed URL produces an `IngestionError` with reason `"robots.txt disallowed"`
- no HTTP request is made to that URL

---

### F-2 [S] Implement scrape ingestion service
Requirements:
- per-source scrape configuration (CSS selectors or XPath for title, body, author, date, image)
- rate-limited polite requests (configurable delay between requests)
- article extraction and normalization using same `Article` model

**Depends on:** F-1, D-2

**Acceptance Criteria**
- given one allowed scrape source, ingestion extracts ≥ 1 article
- delay between requests is enforced
- `robots.txt` is checked first

---

### F-3 [S] Scrape error capture and reporting
Record:
- network failures
- parse failures
- missing required fields

As `IngestionError`.

Error detail includes:
- URL
- error type
- timestamp

**Depends on:** F-2

**Acceptance Criteria**
- simulated network failure produces `IngestionError` record
- API exposes ingestion error list per source

---

### C-3 [P] Document scraping compliance decisions
Update:
- `copilot-usage-guide.md` with compliance rationale
- `architecture-overview.md` with scraping design decisions

**Depends on:** F-1, F-2

**Acceptance Criteria**
- compliance behavior traceable in documentation

---

## M5 — Tested, Evidenced, Demo-Ready

### H-1 [S] Backend test suite
Unit tests:
- normalization
- deduplication
- `robots.txt` check
- data model validation

Integration tests:
- API endpoints with a test database

**Depends on:** E-1, F-2, D-3, D-4

**Acceptance Criteria**
- `pytest` (or equivalent) passes
- coverage ≥ 70% on ingestion and API modules

---

### H-2 [S] Frontend test suite
Tests:
- component tests for article list, detail, and filter
- at least one end-to-end test:
  - load app
  - see articles
  - filter by source

**Depends on:** G-3, G-4, G-5

**Acceptance Criteria**
- test runner passes
- E2E test runs against dev backend with seeded data

---

### C-4 [P] Complete `copilot-usage-guide.md`
Required sections:
- agents used (role, work delegated, evidence)
- skills used
- MCPs used
- APM packages

Must be completable by a reviewer without reading any source code.

**Depends on:** all prior C tasks

**Acceptance Criteria**
- every agent, skill, and MCP referenced in the log has an entry in the guide

---

### C-5 [P] Complete `demo-script.md`
Create a step-by-step script a presenter can follow to show the Copilot AI delivery story.

Include:
- which agent produced which artifact
- how to trigger ingestion
- how to read the evidence docs

**Depends on:** C-4, H-1, H-2

**Acceptance Criteria**
- a new reader can follow the script without additional instruction

---

### C-6 [P] Security review pass
Security review agent audits:
- secrets in env vars
- scraping not bypassing auth
- no PII stored
- OWASP Top 10 check on API

**Depends on:** D-3, D-4, F-2

**Acceptance Criteria**
- security review findings documented
- any HIGH findings remediated before demo
- `agent-execution-log.md` updated

---

## Recommended First Thin Vertical Slice

**Goal:** prove the full chain — AI-assisted planning → backend → frontend — in one small PR, producing both a working feature and traceable evidence.

### Scope
- register one real RSS source (e.g. BBC News RSS)
- `POST /ingest/{source_id}` fetches and stores ≥ 1 article
- `GET /articles` returns the article
- frontend list view renders it
- `agent-execution-log.md` records the executor agent session that implemented it

### Why this slice
- touches every layer (data model → ingestion → API → frontend)
- produces Copilot evidence alongside working code
- avoids scraping compliance risk entirely (RSS only)
- can be reviewed in a single PR with clear before/after
- unblocks all subsequent M2 and M3 tasks

### Tasks required for this slice (in order)
- D-1
- D-2 (Source + Article models only)
- E-1 (RSS only, one source)
- E-2 (manual trigger)
- D-4 (articles list endpoint)
- G-1
- G-2
- G-3
- C-1 (log the session)

---

## Open Questions & Risks

| # | Item | Risk level | Notes |
|---|---|---|---|
| R1 | Backend tech stack not yet chosen | Medium | Blocks D-2 onward; resolve at D-1 |
| R2 | Frontend tech stack not yet chosen | Medium | Blocks G-2 onward; resolve at G-1 |
| R3 | APM packages not yet selected or installed | Medium | `apm-inventory.md` is empty; must choose real packages from `github/awesome-copilot` before M1 is complete |
| R4 | MCP integrations not yet configured | Medium | `mcp-integration-summary.md` is empty; GitHub MCP setup should be first |
| R5 | Scraping compliance is source-dependent | High | Each scrape source needs manual `robots.txt` and terms review before F-2; do not batch scrape sources without review |
| R6 | Deduplication strategy needs definition | Low-Medium | URL-based deduplication is straightforward; title-similarity deduplication is ambiguous — define scope at D-2 |
| R7 | Ingestion scheduling mechanism | Low | Requirements say "scheduled or manually triggered" — manual trigger is sufficient for MVP; scheduled jobs can be M4/M5 scope |
| R8 | Evidence completeness is hard to validate | Medium | Define a review checklist in `copilot-usage-guide.md` so evidence quality is measurable |

---

## Recommended Implementation Order Summary

Every [S] task must be accompanied by an `agent-execution-log.md` entry. Every architectural decision must appear in `architecture-overview.md`. The primary deliverable is built incrementally alongside the application — it is not a post-hoc write-up.
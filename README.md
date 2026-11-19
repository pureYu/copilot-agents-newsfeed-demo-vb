# Copilot Agents Newsfeed Demo

A demonstration of how GitHub Copilot AI technologies can drive the full software delivery lifecycle — from requirements and planning through implementation, review, testing, and documentation.

> **Primary deliverable:** the AI-assisted delivery process and its evidence.
> **Secondary deliverable:** a working news reader application with RSS and web scraping ingestion.

---

## Contents

- [Project overview](#project-overview)
- [AI workflow infrastructure](#ai-workflow-infrastructure)
- [Application architecture](#application-architecture)
- [Getting started](#getting-started)
- [Running tests](#running-tests)
- [Project structure](#project-structure)
- [Documentation](#documentation)

---

## Project overview

This repository demonstrates how GitHub Copilot App can coordinate application delivery through:

- **Custom agents** — orchestrator, planner, executor, research, code-review, security-review, QA
- **Reusable skills** — local and marketplace-managed, versioned via an Agent Package Manager (APM)
- **MCP integrations** — GitHub, filesystem, Playwright, Context7
- **Structured evidence** — execution logs, decision records, and a repeatable demo script

The news reader application (FastAPI backend + React frontend) serves as proof that a Copilot-driven workflow can produce a practical software product end to end.

---

## AI workflow infrastructure

```
.github/
├── copilot-instructions.md      # always-on repository guidance
├── agents/                      # 7 custom agent definitions
│   ├── orchestrator.agent.md
│   ├── planner.agent.md
│   ├── executor.agent.md
│   ├── research.agent.md
│   ├── code-review.agent.md
│   ├── security-review.agent.md
│   └── qa.agent.md
├── instructions/                # path-specific instructions
│   ├── backend.instructions.md
│   └── frontend.instructions.md
├── skills/                      # 6 skills (3 local, 3 marketplace)
├── workflows/                   # GitHub Actions CI workflows
│   └── pr-tests.yml             # runs backend + frontend tests on every PR
└── ISSUE_TEMPLATE/              # structured GitHub issue templates
```

See [docs/copilot-usage-guide.md](docs/copilot-usage-guide.md) for the full capability inventory and workflow.

---

## Application architecture

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.11+) |
| Database | SQLite (dev/demo) via SQLAlchemy 2 async + Alembic |
| RSS ingestion | feedparser |
| Web scraping | httpx + BeautifulSoup4 + robots.txt compliance |
| Logging | structlog (structured JSON) |
| Frontend | React 18 + TypeScript + Vite |
| Routing | react-router-dom v6 |

### Key design decisions

- **SQLite** for zero-setup local development; swap to PostgreSQL by changing `DATABASE_URL`.
- **FastAPI** for async-native ingestion, auto-generated `/docs` (Swagger), and Pydantic v2 validation.
- **robots.txt compliance** is enforced before every scrape request.
- Secrets are read from environment variables — never hardcoded.

Full architecture rationale: [docs/architecture-overview.md](docs/architecture-overview.md).

---

## Getting started

### Option A — Docker (one-command startup)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin).

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

The backend seeds example RSS sources automatically on first startup. The SQLite database is stored in a named Docker volume (`db_data`) and survives container restarts.

To stop and remove containers (data volume is preserved):
```bash
docker compose down
```

To also delete the database volume:
```bash
docker compose down -v
```

---

### Option B — Local development

#### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd backend

# Copy and configure environment variables
cp .env.example .env

# Install dependencies (editable mode)
pip install -e .[dev]

# Apply database migrations
alembic upgrade head

# Seed example RSS sources (optional)
python seed_sources.py

# Start the development server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.
Interactive API docs: `http://localhost:8000/docs`.
Health check: `http://localhost:8000/health`.

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend runs at `http://localhost:5173`. The Vite dev server proxies `/api` to the backend.

---

## Running tests

### Backend

```bash
cd backend
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

The test suite covers:

| File | Area |
|------|------|
| `test_api_articles.py` | Articles API endpoints |
| `test_api_sources.py` | Sources API endpoints + SSRF validation |
| `test_api_ingest.py` | Ingest API endpoints |
| `test_models.py` | SQLAlchemy models |
| `test_rss.py` | RSS ingestion service |
| `test_scrape.py` | Scrape service |
| `test_robots.py` | robots.txt compliance |

### Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run all tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

The test suite uses [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/react) with a jsdom environment.

| Directory | Area |
|-----------|------|
| `src/api/__tests__/` | API client, articles, sources, ingest modules |
| `src/components/__tests__/` | ArticleCard, ErrorMessage, Layout, LoadingSpinner |
| `src/pages/__tests__/` | ArticlesPage, ArticleDetailPage, SourcesPage |

---

## Project structure

```
.
├── .github/                     # Copilot agents, skills, instructions, workflows, issue templates
├── .vscode/
│   └── mcp.json                 # MCP server configuration (GitHub, filesystem, Playwright, Context7)
├── apm/                         # Agent Package Manager inventory
│   ├── inventory.json
│   └── README.md
├── docker-compose.yml           # One-command local startup (backend + frontend)
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routers (articles, sources, ingest)
│   │   ├── core/                # Configuration, logging
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # RSS, scrape, robots.txt services
│   │   ├── database.py
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── main.py
│   ├── tests/                   # 80+ unit and integration tests
│   ├── .env.example
│   ├── Dockerfile
│   ├── entrypoint.sh            # Seeds DB then starts uvicorn
│   ├── pyproject.toml
│   └── seed_sources.py
├── docs/
│   ├── REQUIREMENTS_SUMMARY.md
│   ├── architecture-overview.md
│   ├── delivery-plan.md
│   ├── copilot-usage-guide.md
│   ├── agent-execution-log.md
│   ├── mcp-integration-summary.md
│   ├── apm-inventory.md
│   └── demo-script.md
└── frontend/
    ├── src/
    │   ├── api/                 # Typed API client (articles, sources, ingest)
    │   ├── components/          # ArticleCard, Layout, LoadingSpinner, ErrorMessage
    │   ├── pages/               # ArticlesPage, ArticleDetailPage, SourcesPage
    │   └── types/               # Shared TypeScript types
    ├── index.html
    ├── nginx.conf               # Docker: SPA serve + /api proxy to backend
    ├── Dockerfile
    └── package.json
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/REQUIREMENTS_SUMMARY.md](docs/REQUIREMENTS_SUMMARY.md) | Project objectives, scope, and deliverable definitions |
| [docs/architecture-overview.md](docs/architecture-overview.md) | Stack choices, data model, design tradeoffs |
| [docs/delivery-plan.md](docs/delivery-plan.md) | Epics, milestones, tasks, and acceptance criteria |
| [docs/copilot-usage-guide.md](docs/copilot-usage-guide.md) | Agents, skills, MCPs, and AI workflow patterns |
| [docs/agent-execution-log.md](docs/agent-execution-log.md) | Per-session AI execution evidence |
| [docs/mcp-integration-summary.md](docs/mcp-integration-summary.md) | MCP server setup and usage |
| [docs/apm-inventory.md](docs/apm-inventory.md) | APM-managed skills, agents, and packages |
| [docs/demo-script.md](docs/demo-script.md) | Repeatable 25-minute demo walkthrough |

---

## Known gaps

- Alembic initial migration — the migration directory exists but the first migration script has not been generated.

---

## Compliance notes

- **robots.txt** is fetched and respected before every scrape request.
- Sources are only added by explicit configuration; no automated crawling occurs.
- No secrets or credentials are hardcoded; all configuration is via environment variables.
- The `.env` file is excluded from source control via `.gitignore`.

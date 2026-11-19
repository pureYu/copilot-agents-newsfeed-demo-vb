# Demo Script

## Purpose
A repeatable, step-by-step script for demonstrating both:

1. The GitHub Copilot AI-assisted delivery workflow (primary deliverable)
2. The working news reader application (secondary deliverable)

**Audience:** Reviewers assessing how Copilot App, agents, skills, MCPs, and APM were used across the full software delivery lifecycle.

**Duration:** ~25 minutes (application walkthrough only: ~10 minutes)

---

## Pre-demo setup

Run these commands before presenting. Both services must be running.

```bash
# Terminal 1 — backend
cd backend
pip install -e .[dev]          # first time only
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install                    # first time only
npm run dev
```

Verify:
- Backend health: `curl http://localhost:8000/health` → `{"status":"ok"}`
- Frontend: open `http://localhost:5173` in browser

---

## Part 1: Project context (3 min)

**Open:** [`docs/REQUIREMENTS_SUMMARY.md`](REQUIREMENTS_SUMMARY.md)

Key points to make:
- The **primary deliverable** is the AI-assisted delivery process and its evidence — not the app.
- The **secondary deliverable** is a working news reader with RSS + scrape ingestion.
- The demo proves a Copilot-driven workflow can produce a practical software product end to end.

**Open:** [`docs/architecture-overview.md`](architecture-overview.md)

Point to the stack decision rationale and explain that the technology choices were documented before any code was written.

---

## Part 2: Copilot AI infrastructure (5 min)

### Custom agents
**Open:** `.github/agents/` directory

Show each agent file and call out:
- `orchestrator.agent.md` — coordinates planning, implementation, validation, and docs
- `planner.agent.md` — decomposes requirements into epics, milestones, and tasks
- `executor.agent.md` — implements tasks and writes tests
- `research.agent.md` — investigates libraries and compliance constraints
- `code-review.agent.md` — reviews code against path-specific instructions
- `security-review.agent.md` — performs OWASP Top 10 analysis
- `qa.agent.md` — validates acceptance criteria and identifies test gaps

Point out the `model`, `tools`, and `description` fields. Explain that each agent has a narrowly defined role and that the orchestrator delegates to them.

### Reusable skills
**Open:** `.github/skills/` directory

Show that marketplace skills (from APM) are installed alongside custom local skills. Point to `SKILL.md` files and explain skills are versioned and reproducible.

### Path-specific instructions
**Open:** `.github/instructions/backend.instructions.md`

Highlight how instructions declare the tech stack, ingestion compliance rules, and quality expectations. These apply automatically when Copilot edits files matching the `applyTo` pattern.

### APM inventory
**Open:** [`apm/inventory.json`](../apm/inventory.json) and [`docs/apm-inventory.md`](apm-inventory.md)

Show the installed packages, their tree SHAs, and install commands. Explain this makes the AI toolchain reproducible.

### MCP integrations
**Open:** [`docs/mcp-integration-summary.md`](mcp-integration-summary.md)

Walk through the four MCP servers (GitHub, filesystem, Playwright, Context7) and their roles.

---

## Part 3: Planning workflow evidence (4 min)

**Open:** [`docs/agent-execution-log.md`](agent-execution-log.md)

Walk the log chronologically. For each milestone row, show:
- which agent was invoked
- what inputs it received
- what outputs it produced
- which files changed

Key rows to highlight:
- **Planner row** — 5 epics, 5 milestones, 23 tasks produced before a single line of code was written
- **D-2 row** — data models and 16 tests generated together in one executor session
- **E-3 row** — structured logging added as a cross-cutting concern after core features were done
- **M4 row** — robots.txt compliance check implemented before scraping was wired up

Ask: *"What other process produces this kind of traceable, agent-attributed delivery log?"*

---

## Part 4: Application walkthrough (8 min)

### Step 1: Add an RSS source

Open `http://localhost:5173/sources` → click **+ Add Source**.

Fill in:
- Name: `Hacker News RSS`
- URL: `https://news.ycombinator.com/rss`
- Type: `RSS`
- Enabled: ✓

Click **Save Source**. Confirm the source appears in the table with status **Enabled**.

### Step 2: Add a scrape source

Click **+ Add Source** again.

Fill in:
- Name: `BBC News`
- URL: `https://www.bbc.com/news`
- Type: `Scrape`

Click **Save Source**.

*Aside for reviewers:* Before fetching, the scrape service checks `https://www.bbc.com/robots.txt` and only proceeds if our user-agent `newsfeed-bot/0.1` is not blocked. This is logged to stdout as structured JSON.

### Step 3: Trigger ingestion

Click **↻ Sync All** on the Sources page. Watch the per-row Ingest buttons and the bulk sync message.

Switch to Terminal 1 and show the structured JSON log output:
```json
{"event": "ingestion.start", "source_id": 1, "source_url": "...", "run_id": 1, ...}
{"event": "ingestion.complete", "status": "success", "articles_found": 30, "articles_inserted": 30, ...}
```

Point out: every ingestion event is timestamped, correlated by `run_id`, and structured for log aggregation.

### Step 4: Browse articles

Navigate to `http://localhost:5173/`.

Show:
- Article cards with source badge, date, truncated summary, and tag pills
- **Apply** filters: type "python" in the search box, click Apply
- Source dropdown: filter to Hacker News only
- **Reset** to clear filters

### Step 5: Article detail

Click any article title.

Show:
- Source and type badges
- Publication date and author
- Full summary
- **Read original article ↗** button linking back to canonical URL

### Step 6: Deduplication

Return to Sources → click **Ingest** on the RSS source.

Show the per-row status updates to `0 new · success`. Explain:
- Articles are deduplicated by URL before insert
- The second run returns `articles_inserted = 0` with status `success` — not an error

### Step 7: Source toggle

Click the **Enabled** toggle button on the scrape source to disable it.

Click **↻ Sync All** again — the disabled source is skipped. Only enabled sources run in bulk ingestion.

---

## Part 5: Validation evidence (3 min)

### Test suite

Run in Terminal 1:
```bash
cd backend && pytest --tb=short -q
```

Expected output: all tests passing across 7 test files (100+ test cases).

Call out specific suites:
- `test_models.py` — ORM constraints and uniqueness rules
- `test_api_sources.py` — includes 8 SSRF guard tests rejecting private IP ranges
- `test_robots.py` — 11 unit tests for robots.txt compliance logic
- `test_scrape.py` — 10 unit + 6 integration tests for the scrape service

### Security review highlights

Point to the SSRF guard in `backend/app/schemas/sources.py`:
- Rejects `http://localhost`, `http://127.0.0.1`, `http://10.x.x.x`, `http://192.168.x.x`
- Rejects link-local range `169.254.x.x` (AWS metadata endpoint)
- Rejects `.local`, `.internal`, `.corp` domain patterns

Explain this was identified and implemented as part of the security review phase (M5) — a deliberate, documented step in the workflow, not a reactive fix.

### API validation

Run in Terminal 1:
```bash
curl -s http://localhost:8000/docs | head -5
```

Or open `http://localhost:8000/docs` to show auto-generated OpenAPI documentation.

---

## Part 6: Reproducibility (2 min)

**Open:** [`docs/copilot-usage-guide.md`](copilot-usage-guide.md)

Walk through the installed agents, skills, MCPs, and APM packages. Explain:

1. Any developer can `git clone` this repository and the entire AI workflow is ready:
   - agents in `.github/agents/`
   - skills in `.github/skills/`
   - instructions in `.github/instructions/`
   - MCPs configured in `.vscode/mcp.json`
   - APM packages listed in `apm/inventory.json` with install commands

2. The agent execution log provides a replay of every AI decision:
   - which agent was used
   - what prompts were given
   - what files were produced
   - how validation was performed

3. The delivery can be extended to M6, M7, etc. by following the same workflow pattern.

---

## Demo checklist

Before presenting, confirm each item:

- [ ] `uvicorn app.main:app --reload` running on port 8000
- [ ] `npm run dev` running on port 5173
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] At least one RSS source created and ingested
- [ ] `pytest` passes with no failures
- [ ] Agent execution log open and readable
- [ ] REQUIREMENTS_SUMMARY.md open
- [ ] Browser tabs: localhost:5173, localhost:5173/sources, localhost:8000/docs

## Presenter notes

- Lead with the process, not the app. The app is evidence that the process works.
- When showing the execution log, pause on each row and name the agent and what decision it made.
- If live ingestion is slow (robots.txt check + HTTP fetch), explain it — don't treat it as a bug.
- The structured logs in Terminal 1 are a deliberate feature. Point to them actively.
- If asked about production-readiness: acknowledge it's a demo; point to authentication, rate limiting, and scheduled ingestion as planned M6 extensions.

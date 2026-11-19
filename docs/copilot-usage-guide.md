# Copilot AI Usage Guide

## Purpose
This document explains how GitHub Copilot AI technologies are used throughout the delivery lifecycle of this repository.

## Goals
- Make AI-assisted delivery understandable to a reviewer.
- Show which Copilot features were used and why.
- Provide a repeatable workflow for future contributors.

## Copilot capability categories
### 1. Repository instructions
Always-on guidance is stored in `.github/copilot-instructions.md`. It applies to every Copilot interaction in this repository and covers:
- project purpose and primary/secondary deliverable distinction
- delivery priorities (clarity, reproducibility, traceability)
- technical expectations (backend, frontend, ingestion, security, logging, testing)
- implementation behaviour (plan before coding, compliance assumptions, modular architecture)
- required documentation (which docs to keep current)

### 2. Path-specific instructions
Targeted instructions under `.github/instructions/` apply only to matching file paths.

| File | Applies To | Key rules |
|---|---|---|
| `backend.instructions.md` | `backend/**` | Stack (FastAPI, SQLAlchemy 2, SQLite, feedparser, httpx, structlog, APScheduler, pytest); separation of layers; treat ingestion failures as expected; robots.txt compliance; env vars for secrets |
| `frontend.instructions.md` | `frontend/**` | Demo-clarity over complexity; article list + detail views; loading/empty/error states; search + filter; sync action; accessibility basics; small testable components |

### 3. Custom agents
All agent definitions live in `.github/agents/`.

| Agent | Purpose | When Used | Tools | Outputs |
|---|---|---|---|---|
| `orchestrator` | Coordinates planning, implementation, validation, and documentation across agents | During every significant delivery session | read, search, edit, agent | implementation plans, progress summaries, evidence alignment, next-action directives |
| `planner` | Breaks requirements into epics, milestones, tasks, and acceptance criteria | Before implementation starts; when scope changes | read, search, edit | epics, milestones, issue-sized tasks, dependency graph, thin vertical slice recommendation |
| `executor` | Implements tasks from planner output; writes code and configuration | When a task has clear acceptance criteria and is ready for coding | read, search, edit | source files, test files, updated docs |
| `research` | Investigates libraries, compliance requirements, robots.txt, and technical approaches | Before choosing a library or adding a scrape source | read, search | structured findings report with recommendation and confidence level |
| `code-review` | Reviews code changes against path instructions and acceptance criteria | After executor completes a task; before merge | read, search | review report (approved / needs changes / blocked) with per-finding severity |
| `security-review` | OWASP Top 10 audit, secrets check, scraping compliance, data privacy | After significant API or ingestion work; before demo | read, search | security findings report with HIGH/MEDIUM/LOW verdicts and remediation guidance |
| `qa` | Validates features against acceptance criteria; runs or inspects tests | After implementation; generates evidence for execution log | read, search, edit | validation report mapping each AC to test coverage status; evidence summary |

### 4. Skills
All skill definitions live in `.github/skills/`. Marketplace skills carry a `github-tree-sha` in their frontmatter.

| Skill | Source | Purpose | Typical Inputs | Typical Outputs |
|---|---|---|---|---|
| `requirements-analyst` | local | Converts requirements into epics, milestones, tasks, and ACs; maintains primary/secondary deliverable distinction | `docs/REQUIREMENTS_SUMMARY.md` | backlog, milestone breakdown, acceptance criteria, dependency analysis |
| `architecture-writer` | local | Proposes and documents system architecture with tradeoff recording | requirements, design constraints | `docs/architecture-overview.md` sections; tradeoff tables |
| `demo-evidence-recorder` | local | Captures Copilot AI workflow evidence after each meaningful activity | prompts, outputs, changed artifacts | `docs/agent-execution-log.md` rows; updates to copilot-usage-guide, mcp-integration-summary, demo-script |
| `review-and-refactor` | github/awesome-copilot (`1c31b702`) | Reviews all code against path instructions; refactors for quality and maintainability | changed source files, `.github/instructions/*.md` | clean, refactored code consistent with project standards |
| `documentation-writer` | github/awesome-copilot (`016d8040`) | Produces Diátaxis-structured documentation | document type + audience + scope | tutorial, how-to, reference, or explanation document |
| `create-github-issues-feature-from-implementation-plan` | github/awesome-copilot (`e9c8ec75`) | Creates GitHub Issues from implementation plan phases | implementation plan file path | one GitHub Issue per phase using `feature_request.yml` or `chore_request.yml` template |

### 5. MCP integrations
All MCPs are declared in `.vscode/mcp.json`. See `docs/mcp-integration-summary.md` for full setup details.

| MCP | Transport | Used By | Purpose |
|---|---|---|---|
| `github` | HTTP (Copilot auth) | orchestrator, create-github-issues skill | Issue/PR/repo context; issue creation from plan phases |
| `filesystem` | stdio/npx | executor, orchestrator | Scoped file read/write within `${workspaceFolder}` |
| `playwright` | stdio/npx | qa agent (M3+) | Browser-based UI validation of frontend views |
| `context7` | stdio/npx | research agent | Live library documentation lookup (FastAPI, SQLAlchemy, feedparser, etc.) |

### 6. APM-managed assets
Full inventory is in `apm/inventory.json` and `docs/apm-inventory.md`.

**Marketplace** (`github/awesome-copilot`):
- `review-and-refactor` — tree SHA `1c31b702`
- `documentation-writer` — tree SHA `016d8040`
- `create-github-issues-feature-from-implementation-plan` — tree SHA `e9c8ec75`

**Custom local skills** (committed to `.github/skills/`):
- `requirements-analyst`, `architecture-writer`, `demo-evidence-recorder`

To reproduce: `copilot plugin marketplace add github/awesome-copilot` then install each marketplace package. See `apm/README.md` for the full step-by-step.

## Standard workflow
1. Review requirements and project instructions.
2. Use the planner agent to decompose work.
3. Use the orchestrator to coordinate implementation.
4. Apply skills for requirements, architecture, and evidence capture.
5. Validate code and behavior.
6. Update documentation and evidence artifacts.

## Prompting guidance
Recommended prompt qualities:
- explicit objective
- scope boundaries
- required outputs
- acceptance criteria
- evidence expectations

## Review and verification
Document how outputs from Copilot are checked before being accepted:
- human review
- tests
- manual validation
- documentation completeness checks

## Change log
| Date | Change | Notes |
|---|---|---|
| 2026-07-10 | Initial guide created | Starter template |
| 2026-07-11 | All sections populated | 7 agents, 6 skills, 4 MCPs, APM inventory, path instructions documented |
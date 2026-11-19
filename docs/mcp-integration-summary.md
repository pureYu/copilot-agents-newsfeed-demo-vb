# MCP Integration Summary

## Purpose
This document summarizes Model Context Protocol integrations used by the repository and the decisions or workflows they enabled.

## MCP inventory

| MCP Name | Purpose | Setup Status | Used For | Evidence | Notes |
|---|---|---|---|---|---|
| `github` | Repository, issue, PR, and code context via GitHub Copilot API | configured | Creating GitHub Issues from plan phases; reading repo and PR context during code review; querying issue status | agent-execution-log.md | HTTP transport; auth via Copilot session — no separate token required |
| `filesystem` | Controlled read/write access to the workspace folder | configured | Agent file operations scoped to project; used by executor and orchestrator for file reads without IDE dependency | agent-execution-log.md | Scoped to `${workspaceFolder}` only; cannot access paths outside the project |
| `playwright` | Browser automation for UI validation and E2E testing | configured | Frontend validation in M3+: article list renders, filter interactions, error states, sync button behaviour | agent-execution-log.md | Requires frontend dev server running on localhost; used by qa agent for M3–M5 validation |
| `context7` | Live library documentation lookup | configured | Research agent queries for FastAPI, SQLAlchemy, feedparser, httpx, BeautifulSoup4, structlog API docs during implementation | agent-execution-log.md | Requires internet access; resolves library docs by name — avoids stale cached documentation |

## Configuration

All MCPs are declared in `.vscode/mcp.json`. This file is committed to the repository so the configuration is reproducible.

```json
{
  "servers": {
    "github":     { "type": "http", "url": "https://api.githubcopilot.com/mcp/" },
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "${workspaceFolder}"] },
    "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@latest"] },
    "context7":   { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] }
  }
}
```

## Setup details per MCP

### github
- **Transport**: HTTP
- **URL**: `https://api.githubcopilot.com/mcp/`
- **Authentication**: GitHub Copilot session — no separate token or environment variable required
- **Key capabilities**: list/create/update issues, read PRs, search code, get file contents
- **Agent usage**: orchestrator uses it to track tasks; `create-github-issues-feature-from-implementation-plan` skill depends on it; code-review agent reads PR diff context
- **Write operations**: issue creation and PR comments require human confirmation before execution
- **Limitations**: scoped to the authenticated user's accessible repositories

### filesystem
- **Transport**: stdio (npx)
- **Package**: `@modelcontextprotocol/server-filesystem`
- **Scope**: `${workspaceFolder}` — the repository root only
- **Key capabilities**: read file, write file, list directory, search files
- **Agent usage**: executor agent uses it for file reads during implementation; orchestrator uses it for evidence document updates
- **Security**: hard-scoped to workspace; requests for paths outside the project folder will be rejected by the server
- **Prerequisites**: Node.js and npx available on PATH

### playwright
- **Transport**: stdio (npx)
- **Package**: `@playwright/mcp@latest`
- **Key capabilities**: navigate URL, click, fill form, screenshot, assert element visibility
- **Agent usage**: qa agent uses it in M3–M5 to validate frontend views against acceptance criteria (article list renders, filter changes update results, error state appears on API failure)
- **Prerequisites**: Playwright browsers installed (`npx playwright install`); frontend dev server running
- **Lifecycle**: not used until M3 (frontend scaffold complete)

### context7
- **Transport**: stdio (npx)
- **Package**: `@upstash/context7-mcp`
- **Key capabilities**: resolve library documentation by name and version, return API reference and usage examples
- **Agent usage**: research agent uses it to fetch accurate FastAPI, SQLAlchemy 2, feedparser, httpx, BeautifulSoup4, structlog, and APScheduler documentation during implementation planning
- **Prerequisites**: internet access; no API key required for public library docs
- **Rationale**: prevents executor from working from stale or hallucinated library APIs

## Evaluation criteria applied

| Criterion | Assessment |
|---|---|
| Usefulness for workflow | All 4 MCPs address concrete workflow needs (issue tracking, file ops, UI validation, library docs) |
| Setup complexity | Low — `mcp.json` is committed; npx handles package resolution; github MCP requires no separate auth |
| Reproducibility | High — `.vscode/mcp.json` is version-controlled; any collaborator opens the repo and gets the same MCPs |
| Security | filesystem scoped to workspace; playwright limited to localhost during dev; no credentials stored in config |
| Evidence value | Each MCP usage is loggable in `agent-execution-log.md` with the operation performed and output produced |
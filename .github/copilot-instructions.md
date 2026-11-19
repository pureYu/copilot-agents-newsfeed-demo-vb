# Copilot Instructions for Newsfeed Demo

## Project purpose
This repository demonstrates how GitHub Copilot AI technologies can drive the software delivery lifecycle for a news reader application. The primary deliverable is the explainable AI-assisted delivery process and evidence. The application is a secondary deliverable used as proof.

## Delivery priorities
1. Prefer clarity, reproducibility, and explainability over cleverness.
2. Keep all AI-assisted work traceable through docs, issues, PRs, logs, and commit history.
3. Whenever implementing functionality, also update the relevant documentation evidence.
4. Break work into small, reviewable steps with explicit acceptance criteria.

## Technical expectations
- Build both frontend and backend.
- Support RSS ingestion and allowed scrape-based ingestion.
- Normalize articles into a canonical model.
- Respect robots.txt, publisher terms, and access restrictions.
- Do not hardcode secrets; use environment variables.
- Add structured logging for ingestion, scraping, API operations, and failures.
- Include tests for critical flows.

## Implementation behavior
- Before coding, propose a plan.
- Before scraping logic, confirm compliance assumptions from source configuration.
- Prefer simple, modular architecture.
- Document tradeoffs when choosing libraries or frameworks.
- For every major change, identify:
  - files changed
  - tests added/updated
  - docs updated
  - evidence produced for the Copilot demonstration

## Documentation requirements
Always keep these documents current when relevant:
- docs/copilot-usage-guide.md
- docs/apm-inventory.md
- docs/agent-execution-log.md
- docs/mcp-integration-summary.md
- docs/architecture-overview.md
- docs/demo-script.md

## Output style
- Be explicit and step-by-step.
- When suggesting changes, include rationale.
- When creating plans, map them back to the project requirements.
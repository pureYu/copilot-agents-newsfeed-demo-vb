# Requirements Summary: Copilot AI Demonstration News Reader App

## 1. Purpose

This document defines the requirements for creating a news reader application that demonstrates the practical use of GitHub Copilot AI technologies across the software delivery lifecycle.

The **primary deliverable** is not the news reader application itself. The primary deliverable is the explanation, evidence, and repeatable usage model showing how Copilot AI technologies can plan, design, implement, review, test, document, and manage delivery of the application.

The **secondary deliverable** is a working frontend and backend news reader app that reads news from multiple sources using RSS feeds and web scraping methodologies.

## 2. Project Objectives

1. Demonstrate how GitHub Copilot App can coordinate application delivery through AI-assisted workflows.
2. Demonstrate the usage of Copilot skills, agents, MCP servers, and package-managed AI capabilities.
3. Use an Agent Package Manager (APM) to install, version, manage, and reuse skills, agents, MCP integrations, and related AI workflow assets.
4. Produce a working news reader app as evidence that the Copilot AI delivery process can generate a practical software product.
5. Capture the AI workflow decisions, prompts, tool usage, verification steps, and delivery outputs as the main project artifact.

## 3. Scope

### 3.1 In Scope

- Frontend news reader interface.
- Backend API and ingestion services.
- RSS-based source ingestion.
- Web scraping-based source ingestion.
- Source management for multiple publishers or websites.
- Article normalization into a common data model.
- Basic article browsing, filtering, searching, and reading flows.
- Demonstration of Copilot AI-assisted SDLC activities.
- Demonstration of APM-managed skills, agents, and MCP integrations.
- Documentation explaining how Copilot AI technologies were used.

### 3.2 Out of Scope

- Becoming a production-grade commercial news platform.
- Paid publisher integrations unless explicitly needed for the demonstration.
- Full editorial workflow, moderation, or content syndication.
- Mobile native applications.
- Advanced recommendation engines beyond simple filters or categories.
- Circumventing publisher access restrictions, paywalls, robots.txt rules, or terms of service.

## 4. Primary Deliverable: Copilot AI Technology Demonstration

The project must explain and evidence how Copilot AI technologies were used. The demonstration must include:

### 4.1 GitHub Copilot App Usage

The project must show how the GitHub Copilot App is used to:

- Create and coordinate delivery sessions.
- Route work to specialized agents.
- Maintain task context and execution history.
- Generate planning, implementation, review, QA, and documentation outputs.
- Support human oversight and approval points.

### 4.2 Skills Usage

The project must use Copilot skills to structure lifecycle work. Candidate skill categories include:

- Analysis and requirements production.
- Architecture and design.
- Implementation planning.
- Test-driven development or QA execution.
- Documentation generation.
- Deployment planning.
- Security and non-functional requirement review.

The final documentation must state which skills were used, why they were selected, what inputs they received, and what outputs they produced.

### 4.3 Agents Usage

The project must demonstrate specialized agents for different responsibilities, such as:

- Planner agent for decomposing work.
- Executor agent for implementation tasks.
- Research agent for technology and library investigation.
- Code review agent for implementation review.
- Security review agent for security-focused inspection.
- QA or testing agent for validation support.

The final documentation must explain the role of each agent, the work delegated to it, and the evidence produced by the agent.

### 4.4 MCP Usage

The project must use Model Context Protocol integrations where useful. Candidate MCP integrations include:

- GitHub MCP for repository, issue, pull request, and code context.
- Browser or Playwright MCP for UI validation.
- Documentation/search MCPs for technology research.
- Filesystem or local tooling MCPs for controlled project operations.
- Custom MCPs if a specific project workflow requires them.

The final documentation must identify each MCP integration, its purpose, and the decisions or outputs it enabled.

### 4.5 Agent Package Manager Usage

The project must use an Agent Package Manager (APM) to manage AI delivery assets.

APM requirements:

- Install reusable skills, agents, and MCP packages.
- Track package names, versions, sources, and configuration.
- Support updating or replacing packages.
- Record which packages were used during the project.
- Provide a repeatable setup path for another user to reproduce the AI workflow.
- Use `https://github.com/github/awesome-copilot` as a reference marketplace/source for predefined Copilot customizations, including agents, instructions, skills, hooks, workflows, plugins, MCP servers, and developer tooling.

The final documentation must include an APM inventory and setup instructions.

Recommended APM/Copilot marketplace setup template:

```text
copilot plugin marketplace add github/awesome-copilot
copilot plugin install <plugin-name>@awesome-copilot
```

These commands are templates because the exact package names must be selected during project setup. For environments where the Awesome Copilot marketplace is already registered, only the install command is required. Every installed package from this source must be listed in the APM inventory with package name, version or revision when available, source repository, purpose, and usage evidence.

## 5. Secondary Deliverable: News Reader Application

The app must include a frontend and backend that demonstrate real ingestion and reading flows.

### 5.1 Backend Requirements

The backend must provide:

- Source registration for RSS and scrape-based sources.
- RSS feed fetching and parsing.
- Web scraping for configured pages where scraping is allowed.
- Article extraction for title, URL, author, publication date, summary, content, source, image URL, and tags when available.
- Article normalization into one canonical model.
- Deduplication by URL, canonical URL, title similarity, or source-specific identifiers.
- API endpoints for listing sources, listing articles, filtering articles, searching articles, and reading article details.
- Scheduled or manually triggered ingestion jobs.
- Error reporting for failed feeds, invalid pages, unreachable sources, and malformed content.
- Structured logging for ingestion, scraping, API operations, and failures.

### 5.2 Frontend Requirements

The frontend must provide:

- Article list view.
- Article detail view.
- Source filter.
- Search input.
- Category or tag filter when metadata exists.
- Clear indication of source and publication time.
- Refresh or sync action for triggering ingestion where supported.
- User-friendly empty, loading, and error states.

### 5.3 Data Requirements

The application must store:

- News sources.
- Source type: RSS or scrape.
- Source configuration.
- Articles.
- Article metadata.
- Ingestion history.
- Ingestion errors.

### 5.4 Web Scraping Requirements

Scraping must:

- Respect robots.txt, site terms, and access restrictions.
- Use source-specific configuration rather than brittle global assumptions.
- Avoid bypassing paywalls, authentication, or anti-bot controls.
- Use rate limits and polite request behavior.
- Capture scraping failures with clear error details.

### 5.5 RSS Requirements

RSS ingestion must:

- Support multiple RSS or Atom feeds.
- Handle feed metadata and article entries.
- Preserve source attribution.
- Detect unchanged feeds where possible.
- Report malformed feeds as ingestion errors.

## 6. Non-Functional Requirements

### 6.1 Explainability

The project must make the AI-assisted delivery process understandable. A reviewer must be able to trace how Copilot technologies contributed to requirements, design, implementation, testing, review, and documentation.

### 6.2 Reproducibility

The project must document enough setup and execution detail for another user to reproduce the Copilot AI workflow and run the app demonstration.

### 6.3 Security

The app must avoid storing secrets in source code. Configuration must use environment variables or equivalent secure configuration. Scraping must not collect credentials or private user data.

### 6.4 Compliance and Ethics

The project must respect publisher rules, robots.txt, content ownership, and legal restrictions. The app must display source attribution and link back to original articles.

### 6.5 Observability

The backend must provide structured logs for source ingestion, scraping, deduplication, API requests, and operational failures.

### 6.6 Testability

The project must include evidence that critical ingestion, normalization, API, and frontend flows were validated.

## 7. Required Documentation Deliverables

The project must produce:

1. Requirements summary.
2. Copilot AI usage guide.
3. APM package inventory.
4. Agent and skill execution log.
5. MCP integration summary.
6. Application architecture overview.
7. Frontend and backend setup instructions.
8. Test and validation evidence.
9. Demo script showing the app and the Copilot AI workflow.

## 8. Acceptance Criteria

The project is accepted when:

1. The documentation clearly proves that Copilot AI technologies were the main delivery mechanism.
2. The APM-managed skills, agents, and MCPs are listed with their purpose and usage.
3. The news reader app has a working frontend and backend.
4. The backend can ingest at least one RSS source and one allowed scrape-based source.
5. Articles are normalized and available through backend APIs.
6. The frontend can display, filter, search, and open articles.
7. The project includes evidence of AI-assisted planning, implementation, review, testing, and documentation.
8. The project includes setup instructions that allow the app and AI workflow to be reproduced.

## 9. Success Measure

The main success measure is the quality and clarity of the Copilot AI technology demonstration. The app is successful if it provides enough functionality to prove that Copilot-assisted delivery can produce a real frontend/backend product while keeping the AI workflow, package management, agent orchestration, and MCP usage visible and explainable.

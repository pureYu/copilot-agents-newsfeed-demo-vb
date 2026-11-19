# APM Inventory

## Purpose
This document records Agent Package Manager assets used in the repository so another user can reproduce the AI workflow setup.

## Marketplace/source reference
Reference source:
- `github/awesome-copilot`

Recommended setup template:
```text
copilot plugin marketplace add github/awesome-copilot
copilot plugin install <plugin-name>@awesome-copilot
```

## Inventory

### Marketplace packages (github/awesome-copilot)

| Package | Tree SHA | Source | Type | Purpose | Installed By | Used In | Evidence |
|---|---|---|---|---|---|---|---|
| `review-and-refactor` | `1c31b702` | github/awesome-copilot | skill | Reviews code against path instructions; refactors for quality and maintainability | orchestrator | M2–M5 implementation tasks; post-executor quality pass | agent-execution-log.md |
| `documentation-writer` | `016d8040` | github/awesome-copilot | skill | Diátaxis-structured documentation for copilot-usage-guide.md and demo-script.md | orchestrator | docs/copilot-usage-guide.md, docs/demo-script.md | agent-execution-log.md |
| `create-github-issues-feature-from-implementation-plan` | `e9c8ec75` | github/awesome-copilot | skill | Creates GitHub Issues from implementation plan phases using feature/chore templates | orchestrator | Milestone planning; GitHub Issues task tracking | agent-execution-log.md |

### Custom local skills

| Package | Version | Source | Type | Purpose | Installed By | Used In | Evidence |
|---|---|---|---|---|---|---|---|
| `requirements-analyst` | local | local | skill | Converts requirements into epics, milestones, tasks, AC, and dependency analysis | orchestrator | REQUIREMENTS_SUMMARY.md analysis; M1–M5 planning | agent-execution-log.md 2026-07-10 |
| `architecture-writer` | local | local | skill | Proposes and documents system architecture with tradeoff recording | orchestrator | docs/architecture-overview.md | architecture-overview.md Key design decisions |
| `demo-evidence-recorder` | local | local | skill | Records Copilot AI workflow evidence after each meaningful activity | orchestrator | agent-execution-log.md; copilot-usage-guide.md; mcp-integration-summary.md; demo-script.md | Applied on every task completion |

## Installation notes

### Marketplace setup
```text
copilot plugin marketplace add github/awesome-copilot
```

### Package installation commands
```text
copilot plugin install review-and-refactor@awesome-copilot
copilot plugin install documentation-writer@awesome-copilot
copilot plugin install create-github-issues-feature-from-implementation-plan@awesome-copilot
```

### Package selection rationale
- **review-and-refactor**: selected to ensure executor output is reviewed against path-specific instructions before merge; avoids manual review overhead during demo sessions.
- **documentation-writer**: selected to produce structured, Diátaxis-compliant documentation for `copilot-usage-guide.md` and `demo-script.md` — the primary deliverable's facing documents.
- **create-github-issues-feature-from-implementation-plan**: selected to convert the planner's milestone output into trackable GitHub Issues, demonstrating end-to-end Copilot-assisted project management.

### Configuration after installation
No post-installation configuration is required for any marketplace package. Skills are available immediately after the install command completes.

### Machine-readable record
See `apm/inventory.json` for the complete record including full tree SHAs, install commands, and usage context.

## Reproducibility checklist
- [x] marketplace/source registered (`github/awesome-copilot`)
- [x] installed packages listed with install commands
- [x] versions captured (tree SHA for marketplace packages)
- [x] configuration steps documented (none required)
- [x] usage evidence recorded in `docs/agent-execution-log.md`
- [x] machine-readable inventory in `apm/inventory.json`
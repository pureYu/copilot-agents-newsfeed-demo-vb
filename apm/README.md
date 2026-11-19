# APM — Agent Package Manager Setup

This directory contains the machine-readable inventory of AI delivery assets used in this repository.

## Reproducing the AI workflow setup

### Step 1 — Register the marketplace

```text
copilot plugin marketplace add github/awesome-copilot
```

Only required once per environment. If `github/awesome-copilot` is already registered, skip this step.

### Step 2 — Install marketplace packages

```text
copilot plugin install review-and-refactor@awesome-copilot
copilot plugin install documentation-writer@awesome-copilot
copilot plugin install create-github-issues-feature-from-implementation-plan@awesome-copilot
```

Each command installs the skill's `SKILL.md` into `.github/skills/<name>/`.

### Step 3 — Verify custom local skills

Three skills in this repository are custom (not from the marketplace):
- `.github/skills/requirements-analyst/SKILL.md`
- `.github/skills/architecture-writer/SKILL.md`
- `.github/skills/demo-evidence-recorder/SKILL.md`

These are committed to the repository and require no installation command.

### Step 4 — Verify agent definitions

Confirm all agent files exist in `.github/agents/`:
- `orchestrator.agent.md`
- `planner.agent.md`
- `executor.agent.md`
- `research.agent.md`
- `code-review.agent.md`
- `security-review.agent.md`
- `qa.agent.md`

## inventory.json

`inventory.json` is the authoritative record of all installed packages with version (tree SHA), source, purpose, and usage evidence. Update it whenever a package is added, removed, or upgraded.

---
applyTo: "frontend/**"
---

# Frontend Instructions

## UI priorities
- Optimize for a clear demo experience rather than visual complexity.
- Make article browsing, filtering, searching, and reading easy to understand.
- Prefer simple composition and readable state management.

## Required UX behavior
- Provide article list and article detail views.
- Clearly show source attribution and publication time.
- Include loading, empty, and error states.
- Include source filtering and search.
- Include category or tag filtering when metadata exists.
- Provide a refresh or sync action where backend support exists.

## Implementation guidance
- Keep components small and testable.
- Avoid premature abstraction for a demo-oriented app.
- Use consistent naming and explicit props/contracts.
- Handle slow or failing API responses gracefully.

## Quality
- Add tests for critical rendering and interaction flows where practical.
- Ensure accessibility basics for forms, buttons, loading states, and navigation.
- Document key UI assumptions in architecture or demo docs when relevant.
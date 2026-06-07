# Exec Plan

## Goal

Add the next React vertical slice: consent-gated patient session lifecycle UI.

## Scope

In scope:

- Harness story and durable proof records.
- React route guard and consent gate polish.
- React patient session list, start, detail, and close UI.
- Frontend API client types for existing session endpoints.

Out of scope:

- Backend API changes.
- Database migrations.
- Streamlit removal.
- Chat messages or AI orchestration.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Public contracts.
- Existing behavior.
- Multi-domain.

Hard gates:

- Auth.
- Authorization.

## Work Phases

1. Record story and intake.
2. Add frontend session API types.
3. Refactor React auth and consent app state.
4. Add patient session workspace.
5. Verify backend and frontend checks.
6. Update Harness proof and trace.

## Stop Conditions

Pause for human confirmation if:

- Backend endpoint behavior must change.
- A migration becomes necessary.
- Validation requirements need to be weakened.
- The React UI needs doctor/admin behavior in this story.

# Exec Plan

## Goal

Add persisted patient message transcripts inside React patient sessions.

## Scope

In scope:

- Message sender type migration.
- Patient message read/create API.
- React transcript list and message composer.
- Backend and frontend validation.

Out of scope:

- AI-generated messages.
- Doctor/admin messaging surfaces.
- Safety classifier and crisis routing.
- Streamlit removal.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Data model.
- Public contracts.
- Existing behavior.
- Multi-domain.

Hard gates:

- Auth.
- Authorization.
- Data migration.

## Work Phases

1. Record HR-003 story and intake.
2. Add migration and seed updates.
3. Implement backend message API and service.
4. Add backend tests.
5. Add React transcript UI and API methods.
6. Validate and record Harness proof.

## Stop Conditions

Pause for human confirmation if:

- Message schema needs more fields.
- Doctor/assistant writes become required in this story.
- Existing production data has role values outside `user/assistant/system`.

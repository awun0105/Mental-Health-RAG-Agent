# Design

## Domain Model

`chat_messages.role` becomes the transcript sender type. Allowed values are
`patient`, `assistant`, `system`, and `doctor`. HR-003 only creates `patient`
messages through the public browser API.

## Application Flow

React loads messages after a session is selected. Patients submit message text
inside an active session. FastAPI validates ownership and session status, saves
the message, and returns the updated transcript data.

## Interface Contract

New FastAPI endpoints:

- `GET /api/v1/sessions/{session_id}/messages`
- `POST /api/v1/sessions/{session_id}/messages`

The POST request accepts `{ "content": "..." }` and always stores role
`patient`. Calls use the existing HTTP-only cookie session.

## Data Model

A migration updates the message role check constraint and backfills any legacy
`user` role rows to `patient`. RBAC seed data adds `message:create` and
`message:read` permissions for patients.

## UI / Platform Impact

The React session detail panel gains a transcript list and a message composer.
Closed sessions keep their transcript visible but disable new patient messages.

## Observability

No new audit action is added in HR-003. Existing session ownership and message
persistence tests provide proof.

## Alternatives Considered

1. Add AI replies in the same story. Rejected to keep transcript persistence
   stable before adding agent orchestration.

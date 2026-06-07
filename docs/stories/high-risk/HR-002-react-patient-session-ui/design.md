# Design

## Domain Model

The story uses existing backend session models only: a patient session has an id,
owner user id, status, start/end timestamps, and JSON metadata. Backend services
continue to enforce patient role, consent, ownership, and active-session rules.

## Application Flow

React boots by calling `/auth/me`. Authenticated users then call
`/consent/status`. Missing consent routes to the consent page; valid consent
routes to the patient session workspace.

## Interface Contract

React calls existing FastAPI endpoints with `credentials: "include"`:

- `GET /api/v1/consent/status`
- `POST /api/v1/consent/accept`
- `GET /api/v1/sessions/me`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `POST /api/v1/sessions/{session_id}/close`

## Data Model

No database migration is required. Session rows, consent rows, RBAC roles, and
audit records remain owned by the backend.

## UI / Platform Impact

The React shell gains explicit app states for anonymous, consent-required, and
ready users. The patient workspace lists sessions, starts a new session, shows a
selected session, and closes active sessions.

## Observability

No new log or audit contract is added. Existing backend audit behavior records
session start and close events.

## Alternatives Considered

1. Keep session UI deferred until chat messages exist. Rejected because the
   backend session lifecycle is already implemented and needed for React parity.

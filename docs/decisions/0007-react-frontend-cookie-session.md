# 0007 React Frontend And Cookie Session

Date: 2026-06-06

## Status

Accepted

## Context

The Streamlit frontend stores JWT state in process/session memory and is weak
for browser-native OAuth redirects, persistent login, route guards, and future
doctor/patient application workflows. The project needs a production-oriented
browser app foundation before implementing patient chat, doctor dashboard, and
copilot flows.

## Decision

Use React + Vite + TypeScript for the replacement frontend and add an
HTTP-only cookie session contract to the FastAPI backend. The backend remains
the only browser-facing auth authority; the React app will not call Supabase
directly.

## Alternatives Considered

1. Keep Streamlit and patch session behavior.
2. Store JWTs in browser localStorage.
3. Use Supabase JS directly from the frontend.

## Consequences

Positive:

- Browser reloads can preserve authenticated state.
- OAuth redirect handling becomes simpler and more reliable.
- The future patient/doctor UI can use normal SPA routing and route guards.
- Existing Bearer token clients can continue working during transition.

Tradeoffs:

- Cookie/CORS behavior must be tested carefully.
- The frontend stack expands beyond the current Python-only workspace.
- Deployment needs frontend build/runtime configuration.

## Follow-Up

- Add backend cookie auth tests.
- Scaffold React app.
- Keep Streamlit until React reaches functional parity for auth/consent/profile.

# Exec Plan

## Goal

Create the authentication foundation needed for replacing Streamlit with a
React frontend: backend cookie sessions, logout, safe CORS settings, and a
React auth shell.

## Scope

In scope:

- Add backend cookie settings.
- Set auth cookies on local password login and Google auth-code exchange.
- Allow `GET /auth/me` to resolve identity from Bearer token or cookie.
- Add logout endpoint that clears the cookie.
- Add tests for cookie login, cookie `/me`, Bearer compatibility, logout, and
  Google exchange cookie behavior.
- Scaffold a React + TypeScript frontend app with auth/consent/profile routes.

Out of scope:

- Removing Streamlit.
- Implementing patient chat, RAG, LangGraph agents, or doctor dashboards.
- Using Supabase JS directly in the browser.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Public contracts.
- Cross-platform browser behavior.
- Existing behavior.

Hard gates:

- Auth.
- Authorization.

## Work Phases

1. Backend cookie contract.
2. Backend auth tests.
3. React frontend scaffold.
4. React auth shell and protected routes.
5. Validation: backend tests, lint/type checks, and frontend build.
6. Harness trace/update.

## Stop Conditions

Pause for human confirmation if:

- Cookie behavior requires breaking Bearer token compatibility.
- CORS must be loosened for production in an unsafe way.
- A database migration becomes necessary.
- Validation cannot run locally.

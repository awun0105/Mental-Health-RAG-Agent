# Validation

## Proof Strategy

Use existing backend tests for session lifecycle and RBAC. Prove the React slice
with TypeScript, production build, and browser smoke against local backend and
frontend.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Existing backend session and consent tests pass. |
| Integration | React API client calls cookie-auth protected endpoints. |
| E2E | Login, reload, consent gate, start/list/detail/close session. |
| Platform | Backend on `8001`, React on `5173`, loopback CORS works. |
| Performance | No dedicated performance proof in this story. |
| Logs/Audit | Existing session start/close audit tests pass. |

## Fixtures

- Existing local/Supabase user with patient role.
- Accepted current consent policy for session start, or consent screen for
  missing consent.

## Commands

```text
make check
make typecheck-web
make build-web
```

## Acceptance Evidence

- `make typecheck-web` passed.
- `make build-web` passed.
- `make check` passed: Ruff, Mypy, and 114 backend tests.
- `make validate` passed: backend checks, React production build, and
  pre-commit hooks.
- Human-confirmed browser smoke passed for Google login, consent gate, session
  start/list/detail/close, and reload persistence.

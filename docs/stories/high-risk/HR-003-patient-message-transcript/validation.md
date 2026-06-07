# Validation

## Proof Strategy

Use backend tests to prove RBAC, ownership, active-session write rules, and
message ordering. Use React typecheck/build to prove the transcript UI compiles.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Message repository stores and lists sender roles. |
| Integration | Patient can list/create own session messages; strangers and closed sessions are rejected. |
| E2E | Browser smoke: send message, reload, transcript persists. |
| Platform | Backend `8001`, React `5173`, cookie auth. |
| Performance | No dedicated performance proof. |
| Logs/Audit | No new audit action in HR-003. |

## Fixtures

- Patient with accepted consent and active session.
- Closed session for write rejection.
- Stranger patient for ownership rejection.

## Commands

```text
make check
make typecheck-web
make build-web
make validate
```

## Acceptance Evidence

- Focused backend message tests passed: 8 tests.
- `make validate` passed: Ruff, Mypy, 119 backend tests, React production
  build, and pre-commit hooks.
- Manual browser E2E remains pending for send/reload transcript persistence.

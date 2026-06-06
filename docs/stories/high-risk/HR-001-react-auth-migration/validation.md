# Validation

## Backend

- `make check`
- Tests for:
  - Login sets cookie.
  - Google exchange sets cookie.
  - `/auth/me` accepts auth cookie.
  - `/auth/me` still accepts Bearer token.
  - Logout clears cookie.

## Frontend

- Install/build succeeds.
- TypeScript check succeeds.
- React app can call backend with `credentials: "include"`.
- Auth route guard handles loading, authenticated, and unauthenticated states.

## Manual Smoke

- Start backend.
- Start React frontend.
- Login locally.
- Reload browser.
- Confirm `/auth/me` still resolves through cookie.

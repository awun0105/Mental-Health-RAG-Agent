# Design

## Backend Contract

- `POST /api/v1/auth/login` returns the existing token response and sets an
  HTTP-only auth cookie.
- `POST /api/v1/auth/google/exchange` returns the existing token response and
  sets the same cookie.
- `GET /api/v1/auth/me` accepts either `Authorization: Bearer <jwt>` or the auth
  cookie.
- `POST /api/v1/auth/logout` clears the auth cookie.

## Cookie Policy

- Cookie name is configurable.
- Cookie max age follows JWT expiration.
- `HttpOnly` is always true.
- `SameSite` is configurable for local vs deployed environments.
- `Secure` is configurable and should be true in HTTPS deployments.

## Frontend Contract

- React talks only to FastAPI, not directly to Supabase.
- Browser API calls use `credentials: "include"`.
- Local token storage is avoided for cookie-auth paths.
- Route guards call `/auth/me`.

## Compatibility

- Existing Bearer token clients keep working.
- Streamlit can continue using bearer tokens during the transition.
- The cookie contract is additive.

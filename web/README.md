# React Frontend

React + Vite + TypeScript frontend for the browser-native app migration.

## Local Development

```bash
cp web/.env.example web/.env
make dev-be
make dev-web
```

Backend `.env` should point OAuth redirects at React during this migration:

```bash
FRONTEND_URL=http://localhost:5173
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:8501
```

## Auth Contract

- The browser talks only to FastAPI.
- Authenticated requests use `credentials: "include"`.
- FastAPI stores the app JWT in an HTTP-only cookie.
- Supabase remains server-side only.

## Validation

```bash
make build-web
```

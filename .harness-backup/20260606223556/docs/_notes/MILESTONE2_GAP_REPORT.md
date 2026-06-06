# Milestone 2 Gap Report

**Date:** 2026-05-11
**Scope reviewed:** `docs/.plan/MASTER_PLAN.md`, `docs/.plan/MILESTONE1.md`,
`docs/.plan/MILESTONE2.md`, and current source code under `backend/`, `frontend/`,
and `supabase/`.

## Executive Summary

Milestone 1 is effectively complete. Milestone 2 is mostly complete at the code
level and has also grown beyond the original plan with full RBAC tables,
permission-code checks, role/permission management endpoints, Google OAuth
backend flow, a unified auth UI, and session CRUD.

The remaining Milestone 2 gaps are not core Python implementation gaps. They are
mostly external/live-environment and hardening gaps:

- Supabase SQL migrations/seed must be confirmed on the real Supabase project.
- Google Cloud + Supabase OAuth dashboard settings must be confirmed with real
  credentials.
- A live smoke test for Google OAuth, admin bootstrap, consent, and session start
  is still pending.
- Cookie-based persistent browser session is not implemented yet; the current UI
  uses in-memory Streamlit session state plus one-time Google auth-code exchange.

Automated backend validation currently passes: `108 passed`.

## Milestone 1 Status

Milestone 1 requested project foundation: backend/frontend structure, config,
FastAPI app, health endpoint, `.env.example`, README, DFD, Makefile, and
LlamaIndex dependencies.

Current status: **complete enough to move on**.

Evidence in codebase:

- Backend app structure exists under `backend/app/`.
- FastAPI entrypoint exists at `backend/app/main.py`.
- Config exists at `backend/app/core/config.py`.
- Health router exists at `backend/app/api/health.py`.
- Streamlit frontend exists at `frontend/main.py`.
- `.env.example` exists and includes Supabase/JWT/Google/URL/consent settings.
- README and docs exist, including `docs/DFD.md`.
- Backend dependencies include FastAPI, Supabase, JWT/passlib, LangGraph,
  LlamaIndex, OpenAI/LangChain, Qdrant.
- Makefile includes install/dev/check/format/ingest commands.

Minor difference from the original Milestone 1 plan:

- Frontend entrypoint is `frontend/main.py`, not `frontend/app.py`.
- SQL executable files have been moved out of `docs/` into `supabase/`.

These are structural decisions, not blockers.

## Milestone 2 Tracker Status

| # | Task | Current status | Notes |
|---|------|---|---|
| 2.1 | Add Supabase/passlib/python-jose dependencies | Done | Present in `backend/pyproject.toml`. |
| 2.2 | Add JWT + Supabase settings | Done | Includes JWT, Supabase, Google OAuth, URLs, consent, admin bootstrap. |
| 2.3 | Create database schema SQL | Done | Moved to `supabase/migrations/` and `supabase/seeds/`; no longer in `docs/`. |
| 2.4 | Create shared constants/enums | Done | `backend/app/core/constants.py`. |
| 2.5 | Create custom exceptions | Done | `backend/app/core/exceptions.py`. |
| 2.6 | Create Supabase client | Done | `backend/app/db/supabase_client.py`. |
| 2.7 | Create base repository | Done | `backend/app/db/repositories/base.py`. |
| 2.8 | Create schemas | Done | User, consent, audit, assignment, session, message, RBAC schemas exist. |
| 2.9 | Create user repository | Done | Includes local and provider identity lookups. |
| 2.10 | Create consent repository | Done | Supports latest/status checks. |
| 2.11 | Create audit repository | Done | Supports audit persistence. |
| 2.12 | Create assignment repository | Done | Supports active assignments and doctor/patient lookups. |
| 2.13 | Create auth service | Done | Local register/login, JWT, Google OAuth, admin bootstrap, role assignment. |
| 2.14 | Create audit service | Done | Centralized audit logging. |
| 2.15 | Create consent service | Done | Consent accept/status flow. |
| 2.16 | Create assignment service | Done | Doctor-patient assignment service. |
| 2.17 | Create JWT/security utilities | Done | JWT decode remains; permission enforcement moved to `AuthorizationService`. |
| 2.18 | Create FastAPI DI wiring | Done | `backend/app/api/dependencies.py`. |
| 2.19 | Create auth endpoints | Done | Register/login/me/google/callback/exchange. |
| 2.20 | Create consent endpoints | Done | Accept and status endpoints. |
| 2.21 | Create admin + assignment endpoints | Done | Assignment and admin user creation; RBAC management is split into `api/roles.py`. |
| 2.22 | Register routers + exception handlers | Done | `backend/app/main.py`. |
| 2.23 | Update `.env.example` | Done | Includes current Milestone 2 env vars. |
| 2.24 | Tests for auth/RBAC/consent/audit | Done | Backend test suite covers these areas. |
| 2.25 | Verify server/tests/checks | Mostly done | Automated tests pass. Live backend/frontend smoke still pending. |
| 2.26 | Frontend Google OAuth + email/password UI | Done code-wise | Unified `Log in or sign up` page exists. Persistent browser session is pending. |
| 2.27 | External Google OAuth setup | Pending verification | Must be checked in Google Cloud Console and Supabase Dashboard. |

## Work Completed Beyond Original Milestone 2

The current codebase includes several items beyond the original Milestone 2
tracker:

- Full RBAC schema: `roles`, `permissions`, `user_roles`, `role_permissions`.
- RBAC permission resolution via Postgres RPC.
- Role-name resolution via `get_user_role_names`.
- Admin endpoints for listing roles/permissions and assigning/removing
  role/permission mappings.
- Last-active-admin guardrail for removing admin role.
- Google OAuth admin bootstrap via `ADMIN_BOOTSTRAP_EMAILS`.
- Automatic `user_roles` assignment for local register and new Google OAuth users.
- Session CRUD for start/close/get/list.
- Chat message repository and schema.
- Streamlit conditional navigation that hides `Consent` and `Profile` until login.
- SQL executable files moved to `supabase/migrations/` and `supabase/seeds/`.

## Remaining Milestone 2 Gaps

### 1. Real Supabase database state is not verified

Code and SQL exist, but the live Supabase project may still be missing one or more
migrations/seeds.

Required live checks:

```sql
select name from roles order by name;
select code from permissions order by code limit 20;
select * from get_user_permission_codes((select id from users limit 1));
select * from get_user_role_names((select id from users limit 1));
```

Expected:

- `roles` includes `admin`, `doctor`, `patient`.
- `permissions` includes `consent:read_status`, `consent:accept`, `session:*`,
  `role:*`, `permission:*`.
- Existing users have matching rows in `user_roles`.

One-time repair for existing users:

```sql
insert into user_roles (user_id, role_id)
select u.id, r.id
from users u
join roles r on r.name = u.role
on conflict (user_id, role_id) do nothing;
```

### 2. Google OAuth external setup is not verified

Backend and frontend code exist, but dashboard configuration must be validated.

Supabase must allow this redirect URL:

```text
http://localhost:8000/api/v1/auth/google/callback
```

Google Cloud OAuth must use Supabase's callback URL:

```text
https://<project-ref>.supabase.co/auth/v1/callback
```

The live flow still needs a smoke test:

```text
Frontend -> Continue with Google -> Supabase/Google -> backend callback
-> frontend auth_code exchange -> logged-in session
```

### 3. Cookie-based persistent session is not implemented

Current behavior:

- Frontend stores `access_token` and `user` in `st.session_state`.
- Google callback returns a short-lived `auth_code`.
- Frontend exchanges `auth_code` for JWT through `/auth/google/exchange`.
- Reload can lose login state because `st.session_state` is not durable browser
  auth storage.

Requested next direction:

- Add cookie-based auth session.
- Backend should read auth from Bearer token or session cookie.
- Frontend should restore logged-in state from cookie via `/auth/me`.
- Logout should clear backend cookie and Streamlit state.

Implementation caveat:

- Streamlit calls backend from Python `requests`, not browser JS. Password login
  cannot reliably receive backend `Set-Cookie` in the browser unless implemented
  via browser redirect/form flow or another cookie bridge.

### 4. Live smoke test is still pending

Automated tests pass, but live integration has not been verified after all recent
changes.

Minimum live smoke test:

1. Apply Supabase migrations and RBAC seed.
2. Set backend `.env` with Supabase, JWT, Google, backend/frontend URLs, and
   `ADMIN_BOOTSTRAP_EMAILS`.
3. Start backend and frontend.
4. Register local patient and confirm Consent no longer returns 403.
5. Login Google using admin bootstrap email and confirm user is admin.
6. Open Consent and Profile after login.
7. Start a session after accepting consent.

## Technical Debt / Legacy Left After RBAC Refactor

These are not Milestone 2 blockers, but they are cleanup candidates.

### Safe cleanup candidates

- Unused role-based dependency helpers in `backend/app/api/dependencies.py`:
  `require_current_admin`, `require_current_doctor`, `require_current_patient`,
  `require_current_doctor_or_admin`.
- Role-check helpers in `backend/app/core/security.py` if the dependency helpers
  above are removed.
- Unused request schemas in `backend/app/schemas/rbac.py`:
  `UserRoleAssignRequest`, `RolePermissionAssignRequest`.
- Unused repository list helpers:
  `UserRoleRepository.list_roles_for_user`,
  `RolePermissionRepository.list_permissions_for_role`.

### Do not remove yet

- `users.role` and JWT `role` claim. They are still used for compatibility,
  frontend display, local password login responses, and assignment validation.
- Google `auth_code` exchange. It is still used by the current Streamlit OAuth
  bridge until cookie session is implemented.
- Password login/register UI. It remains useful for dev/test and local patient
  accounts.

## Recommended Next Actions

1. Apply/verify Supabase migrations and seed on the live project.
2. Run the one-time `user_roles` backfill for existing users.
3. Smoke test local register -> consent status.
4. Smoke test Google OAuth admin bootstrap.
5. Implement cookie-based persistent session.
6. Then do a cleanup PR for safe legacy removal.

## Validation Snapshot

Latest automated validation run:

```text
uv run pytest backend/tests
108 passed, 1 warning
```

Additional checks recently passed:

```text
uv run ruff format --check .
uv run ruff check .
uv run mypy .
```

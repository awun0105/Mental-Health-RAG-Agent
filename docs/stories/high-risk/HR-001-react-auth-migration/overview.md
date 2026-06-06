# Overview

## Current Behavior

The backend issues bearer JWTs for local password login and Google OAuth. The
Streamlit frontend stores the token in `st.session_state`, so browser reloads
can drop the authenticated UI state. Streamlit also makes OAuth redirects and
route guards awkward for a production browser app.

## Target Behavior

The backend supports an HTTP-only cookie session contract while preserving
Bearer token compatibility for existing tests and tooling. A new React frontend
can authenticate through the backend, call protected APIs with
`credentials: "include"`, and guard routes for consent/profile flows.

## Affected Users

- Patients logging in, accepting consent, and later using chat workflows.
- Doctors and admins logging in through the browser app.
- Developers validating auth and frontend flows locally.

## Affected Product Docs

- `docs/SRDS.md`
- `docs/DFD.md`
- `docs/ARCHITECTURE.md`
- `docs/TEST_MATRIX.md`

## Non-Goals

- Patient chat message orchestration.
- Doctor dashboard and copilot implementation.
- Full Streamlit removal in this story.
- Production deployment hardening beyond local/dev cookie settings.

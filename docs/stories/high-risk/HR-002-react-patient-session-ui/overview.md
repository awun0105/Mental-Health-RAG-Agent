# Overview

## Current Behavior

The React app can authenticate through cookie sessions and show minimal consent
and profile pages. The browser app does not yet route authenticated patients
through a stable consent gate or expose the existing session lifecycle APIs.

## Target Behavior

After login or reload, React restores the cookie session, checks consent, and
routes the patient to the correct surface. Patients with valid consent can list,
start, inspect, and close their own chat sessions from React.

## Affected Users

- Patients using the browser app after Google or password login.
- Developers validating the React replacement for Streamlit.

## Affected Product Docs

- `docs/SRDS.md`
- `docs/DFD.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- Chat message persistence.
- AI agent orchestration.
- Doctor or admin dashboards.
- Streamlit removal.

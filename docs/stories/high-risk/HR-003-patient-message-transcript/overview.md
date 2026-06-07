# Overview

## Current Behavior

React can authenticate, enforce consent, and manage session lifecycle. Session
detail does not yet show a persisted transcript, and patients cannot save chat
messages through the browser app.

## Target Behavior

Patients can create and reload persisted messages inside their own active
sessions. Message sender types are prepared for future AI and clinical workflow
messages: `patient`, `assistant`, `system`, and `doctor`. This story exposes
only patient-created messages.

## Affected Users

- Patients using the React browser app.
- Developers preparing the AI response pipeline.

## Affected Product Docs

- `docs/SRDS.md`
- `docs/DFD.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- AI replies.
- Crisis/safety routing.
- Doctor-created messages.
- Streamlit removal.

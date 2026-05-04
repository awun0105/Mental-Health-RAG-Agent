"""Thin HTTP wrapper around the FastAPI backend.

Streamlit runs synchronously, so we use ``requests`` (already in the
frontend dependencies). Token state lives in ``st.session_state`` and is
read on every authenticated call so the user can re-login without a
restart.
"""

from __future__ import annotations

import os
from typing import Any, cast

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = "/api/v1"
DEFAULT_TIMEOUT_SECONDS = 10


class BackendError(Exception):
    """Raised when the backend returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def _url(path: str) -> str:
    return f"{BACKEND_URL}{API_PREFIX}{path}"


def _auth_headers() -> dict[str, str]:
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _handle(response: requests.Response) -> dict[str, Any]:
    """Parse JSON or raise BackendError with a human-readable detail."""
    if response.status_code >= 400:
        try:
            payload = response.json()
            detail = payload.get("detail") or payload.get("message") or response.text
        except ValueError:
            detail = response.text
        raise BackendError(response.status_code, str(detail))

    body = response.json()
    if not isinstance(body, dict):
        raise BackendError(
            response.status_code,
            f"Unexpected response shape (expected JSON object, got {type(body).__name__})",
        )
    return cast(dict[str, Any], body)


def health() -> dict[str, Any]:
    """GET /api/v1/health — used for the homepage connectivity check."""
    response = requests.get(_url("/health"), timeout=DEFAULT_TIMEOUT_SECONDS)
    return _handle(response)


def register(
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
) -> dict[str, Any]:
    """POST /api/v1/auth/register — create a local email/password user."""
    response = requests.post(
        _url("/auth/register"),
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return _handle(response)


def login(*, email: str, password: str) -> dict[str, Any]:
    """POST /api/v1/auth/login — exchange credentials for a JWT + user payload."""
    response = requests.post(
        _url("/auth/login"),
        json={"email": email, "password": password},
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return _handle(response)


def get_me() -> dict[str, Any]:
    """GET /api/v1/auth/me — decode the current bearer token's claims."""
    response = requests.get(
        _url("/auth/me"),
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return _handle(response)


def accept_consent(policy_version: str) -> dict[str, Any]:
    """POST /api/v1/consent/accept — record agreement to a policy version."""
    response = requests.post(
        _url("/consent/accept"),
        json={"policy_version": policy_version},
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return _handle(response)


def consent_status() -> dict[str, Any]:
    """GET /api/v1/consent/status — current vs latest accepted policy."""
    response = requests.get(
        _url("/consent/status"),
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    return _handle(response)

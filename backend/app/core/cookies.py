from typing import Literal, cast

from fastapi import Response

from app.core.config import settings

SameSite = Literal["lax", "strict", "none"]


def _auth_cookie_samesite() -> SameSite:
    value = settings.auth_cookie_samesite.lower()
    if value in {"lax", "strict", "none"}:
        return cast(SameSite, value)
    return "lax"


def set_auth_cookie(response: Response, access_token: str) -> None:
    """Store the app JWT in an HTTP-only browser cookie."""
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        max_age=settings.jwt_expiration_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=_auth_cookie_samesite(),
        domain=settings.auth_cookie_domain or None,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear the browser auth cookie."""
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=_auth_cookie_samesite(),
        domain=settings.auth_cookie_domain or None,
        path="/",
    )

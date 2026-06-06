from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_supabase
from app.core.config import settings
from app.core.exceptions import DatabaseError, UnauthorizedError
from supabase import Client

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "0.1.0"}


@router.get("/health/supabase")
async def supabase_health_check(
    db: Annotated[Client, Depends(get_supabase)],
    x_keepalive_token: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Ping Supabase with a tiny read so free-tier projects stay active.

    Set ``KEEPALIVE_TOKEN`` in deployed environments to require callers to
    send ``X-Keepalive-Token``. Local dev can leave it blank for a public
    health check.
    """
    if settings.keepalive_token and x_keepalive_token != settings.keepalive_token:
        raise UnauthorizedError("Invalid keepalive token")

    try:
        # The RBAC seed creates `roles`; reading one id is enough to create
        # Supabase API/database activity without exposing sensitive data.
        result: Any = db.table("roles").select("id").limit(1).execute()
    except Exception as exc:
        raise DatabaseError("Supabase health check failed") from exc

    row_count = len(getattr(result, "data", []) or [])
    return {
        "status": "healthy",
        "service": "supabase",
        "checked_table": "roles",
        "row_count": str(row_count),
    }

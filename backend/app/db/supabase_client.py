from supabase import Client, create_client

from app.core.config import settings


class SupabaseClientManager:
    def __init__(self) -> None:
        self._client: Client | None = None

    def get_client(self) -> Client:
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase URL and KEY must be set in environment variables")

            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key,
            )
        return self._client


# Singleton instance
supabase_client_manager = SupabaseClientManager()


def get_supabase_client() -> Client:
    return supabase_client_manager.get_client()

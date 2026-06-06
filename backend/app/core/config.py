from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # =============================================================================
    # App
    # =============================================================================
    app_name: str = "Mental Health AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # =============================================================================
    # External Services
    # =============================================================================
    openai_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"

    # =============================================================================
    # Supabase
    # =============================================================================
    supabase_url: str = ""
    supabase_key: str = ""
    keepalive_token: str = ""

    # =============================================================================
    # JWT (Application Auth)
    # =============================================================================
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    auth_cookie_name: str = "mh_access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: str = ""
    cors_allow_origins: str = "http://localhost:5173,http://localhost:8501"

    # =============================================================================
    # OAuth (Google)
    # =============================================================================
    google_client_id: str = ""
    google_client_secret: str = ""
    admin_bootstrap_emails: str = ""

    # =============================================================================
    # App URLs
    # =============================================================================
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"

    # =============================================================================
    # Consent Policy
    # =============================================================================
    current_consent_policy_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

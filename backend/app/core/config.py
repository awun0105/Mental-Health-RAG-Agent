from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Mental Health AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False

    openai_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

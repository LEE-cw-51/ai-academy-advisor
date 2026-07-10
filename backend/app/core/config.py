from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Academy Advisor"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_academy_advisor"
    openai_api_key: str = ""
    secret_key: str = "change-me"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Managed Postgres providers (e.g. Railway) inject a plain
        # "postgresql://" URL, but SQLAlchemy needs the psycopg driver scheme.
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    cors_origins: list[str] = ["*"]

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

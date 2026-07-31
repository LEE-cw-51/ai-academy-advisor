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
    openai_embedding_base_url: str = "https://api.openai.com/v1"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    secret_key: str = "change-me"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Managed Postgres providers (e.g. Railway) inject a plain
        # "postgresql://" URL, but SQLAlchemy needs the psycopg driver scheme.
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    # 브라우저 프론트엔드(Next.js)의 오리진. env로 줄 때는 JSON 배열 형식이어야 한다
    # (pydantic-settings가 list[str]을 JSON으로 파싱하므로 콤마 나열은 기동 실패).
    cors_origins: list[str] = ["http://localhost:3000"]

    log_level: str = "INFO"

    # AI provider 선택 (app/providers/factory.py에서 이름→구현 매핑).
    # 이번 단계 기본값은 전부 stub — 실제 호출/키 없이 앱이 기동된다.
    llm_provider: str = "stub"
    embedding_provider: str = "stub"
    vector_store: str = "stub"

    # provider별 세부 설정 (실제 어댑터를 붙이는 다음 단계에서 사용).
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "BAAI/bge-m3"
    # 임베딩 차원. Review.embedding 의 Vector(dim)과 일치해야 하며,
    # 변경 시 마이그레이션이 필요하다 (docs/decision-log.md 참고).
    embedding_dim: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Settings Vercel DATABASE_URL guard."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


_POOLER_URL = (
    "postgresql+psycopg://postgres.abc:pass@"
    "aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_vercel_preview_without_database_url_raises(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(_env_file=None)


def test_vercel_production_rejects_loopback_database_url(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/ai_academy_advisor",
    )
    with pytest.raises(ValidationError, match="localhost|loopback"):
        Settings(_env_file=None)


def test_vercel_preview_accepts_pooler_database_url(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.setenv("DATABASE_URL", _POOLER_URL)
    settings = Settings(_env_file=None)
    assert "pooler.supabase.com" in settings.database_url


def test_local_without_vercel_env_keeps_default_database_url(monkeypatch):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert "localhost" in settings.database_url


def test_pasted_trailing_whitespace_is_stripped_from_keys_and_selectors(monkeypatch):
    """대시보드에 줄째 붙여 넣은 GROQ_API_KEY의 줄바꿈이 헤더 오류(LLM 전면 fallback)와
    로그의 키 노출로 이어졌다(2026-09-15). 키·provider 선택값·DATABASE_URL은 공백을 지운다."""
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", _POOLER_URL + "\n")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_value\n")
    monkeypatch.setenv("HF_API_KEY", "  hf_test_value \r\n")
    monkeypatch.setenv("LLM_PROVIDER", "groq\n")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b\n")
    monkeypatch.setenv("EMBEDDING_PROVIDER", " huggingface")
    monkeypatch.setenv("VECTOR_STORE", "pgvector\t")

    settings = Settings(_env_file=None)

    assert settings.groq_api_key == "gsk_test_value"
    assert settings.hf_api_key == "hf_test_value"
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "openai/gpt-oss-120b"
    assert settings.embedding_provider == "huggingface"
    assert settings.vector_store == "pgvector"
    assert settings.database_url == _POOLER_URL

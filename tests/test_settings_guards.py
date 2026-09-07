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

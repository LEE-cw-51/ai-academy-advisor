"""Operational DB import guard."""

import pytest

from app.core.config import get_settings
from app.core.import_guard import (
    academy_import_allowed,
    is_local_database_url,
    is_operational_database_url,
    stub_review_ingest_allowed,
)
from app.services import academy_import_service
from app.services.academy_import_service import ImportRefusedError


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://postgres:postgres@localhost:5432/ai_academy_advisor",
        "postgresql+psycopg://postgres:postgres@db:5432/ai_academy_advisor",
        "sqlite+pysqlite:///:memory:",
    ],
)
def test_local_database_urls(url: str):
    assert is_local_database_url(url)
    assert not is_operational_database_url(url)
    allowed, _ = academy_import_allowed(url)
    assert allowed


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres",
        "postgresql://postgres:pass@containers-us-west-xxx.railway.app:5432/railway",
        "postgresql+psycopg://postgres.abc:pass@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres",
        "postgresql+psycopg://postgres.abc:pass@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres",
    ],
)
def test_operational_database_urls_blocked(url: str):
    assert is_operational_database_url(url)
    allowed, reason = academy_import_allowed(url)
    assert not allowed
    assert "Studio" in reason


def test_force_allows_operational(monkeypatch):
    url = "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
    allowed, _ = academy_import_allowed(url, force=True)
    assert allowed


def test_allow_env_allows_operational(monkeypatch):
    url = "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
    monkeypatch.setenv("ALLOW_ACADEMY_IMPORT", "1")
    get_settings.cache_clear()
    try:
        allowed, _ = academy_import_allowed(url)
        assert allowed
    finally:
        monkeypatch.delenv("ALLOW_ACADEMY_IMPORT", raising=False)
        get_settings.cache_clear()


def test_allow_academy_import_via_dotenv(tmp_path, monkeypatch):
    """ALLOW_ACADEMY_IMPORT는 Settings(.env)로 읽힌다 — os.environ 직접 조회가 아니다."""
    monkeypatch.delenv("ALLOW_ACADEMY_IMPORT", raising=False)
    (tmp_path / ".env").write_text("ALLOW_ACADEMY_IMPORT=1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    try:
        assert get_settings().allow_academy_import is True
        url = "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
        allowed, _ = academy_import_allowed(url)
        assert allowed
    finally:
        get_settings.cache_clear()


def test_allow_academy_import_kwarg_overrides_settings(monkeypatch):
    monkeypatch.delenv("ALLOW_ACADEMY_IMPORT", raising=False)
    get_settings.cache_clear()
    url = "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
    allowed, _ = academy_import_allowed(url, allow_academy_import=True)
    assert allowed
    blocked, _ = academy_import_allowed(url, allow_academy_import=False)
    assert not blocked


_OPERATIONAL_URL = (
    "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
)
_POOLER_SESSION_URL = (
    "postgresql+psycopg://postgres.abc:pass@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres"
)


def test_stub_review_ingest_blocked_on_operational():
    for url in (_OPERATIONAL_URL, _POOLER_SESSION_URL):
        allowed, reason = stub_review_ingest_allowed(url, "stub")
        assert not allowed
        assert "stub" in reason
        assert "naver" in reason


def test_stub_review_ingest_allowed_on_local():
    allowed, reason = stub_review_ingest_allowed(
        "sqlite+pysqlite:///:memory:", "stub"
    )
    assert allowed
    assert reason == ""


def test_naver_review_ingest_allowed_on_operational():
    allowed, reason = stub_review_ingest_allowed(_OPERATIONAL_URL, "naver")
    assert allowed
    assert reason == ""


def test_cli_ingest_reviews_defers_db_imports_until_after_the_guard():
    """가드가 DB 를 끌어오는 임포트보다 먼저 끝나야 한다.

    `app.services.review_ingest_service` 는 `app.models.academy` → `app.db.session`
    을 타고 모듈 로드 시점에 엔진을 만든다. 그래서 서비스 임포트도 `app.db.session`
    임포트와 같이 가드 뒤에 있어야 한다. 실행 결과로는 이 순서를 볼 수 없어
    (NullPool 이라 접속이 늦게 열린다) 소스에서 확인한다.
    """
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "app"
        / "cli"
        / "ingest_reviews.py"
    ).read_text(encoding="utf-8")

    guard_at = source.index("stub_review_ingest_allowed(\n")
    assert guard_at < source.index("from app.db.session import SessionLocal")
    assert guard_at < source.index("from app.services import review_ingest_service")


def test_cli_ingest_reviews_refuses_stub_on_operational(monkeypatch, capsys):
    """가드가 SessionLocal 임포트 전에 끝나 운영 접속을 열지 않는다."""
    from app.cli import ingest_reviews

    class _Settings:
        database_url = _OPERATIONAL_URL
        review_source = "stub"
        naver_display = 10

    monkeypatch.setattr("app.core.config.get_settings", lambda: _Settings())
    exit_code = ingest_reviews.main(["--dry-run", "--limit", "1"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "거부" in captured.err
    assert "stub" in captured.err


def test_cli_refuses_operational_without_force(tmp_path, monkeypatch, capsys):
    from app.cli import import_academies

    write = tmp_path / "a.json"
    write.write_text(
        '{"name":"테스트학원","address":"경기도 하남시 미사강변대로 1"}',
        encoding="utf-8",
    )

    class _Settings:
        database_url = (
            "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
        )

    monkeypatch.setattr(import_academies, "get_settings", lambda: _Settings())
    exit_code = import_academies.main([str(tmp_path)])
    assert exit_code == 1
    assert "거부" in capsys.readouterr().err


def test_import_records_sets_skip_stamp_guc_on_postgres():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "app"
        / "services"
        / "academy_import_service.py"
    ).read_text(encoding="utf-8")
    assert "set_config('app.skip_academy_stamp', '1', true)" in source
    assert 'bind.dialect.name == "postgresql"' in source
    allow_at = source.index("academy_import_allowed")
    guc_at = source.index("set_config('app.skip_academy_stamp'")
    upsert_at = source.index("for record in records:")
    assert allow_at < guc_at < upsert_at


def test_import_records_refuses_operational_bind(monkeypatch, db_session):
    """서비스 계층도 bind URL을 본다 — CLI를 우회해도 운영 DB를 덮지 않는다."""
    monkeypatch.setattr(
        "app.services.academy_import_service.academy_import_allowed",
        lambda url, *, force=False: (False, "Studio"),
    )
    with pytest.raises(ImportRefusedError, match="Studio"):
        academy_import_service.import_records(db_session, [])


def test_import_records_preserves_null_last_verified_at(tmp_path, db_session):
    """SQLite(트리거 없음) — null last_verified_at 덮어쓰기 회귀."""
    import json

    from app.services import academy_import_service

    directory = tmp_path / "import"
    directory.mkdir()
    record = {
        "name": "확인일없음학원",
        "address": "경기도 하남시 미사강변대로 99",
        "last_verified_at": None,
    }
    (directory / "a.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    load = academy_import_service.load_records(directory)
    academy_import_service.import_records(
        db_session, [r for _, r in load.records]
    )
    from app.repositories import academy_repository

    row = academy_repository.find_by_name_and_address(
        db_session, record["name"], record["address"]
    )
    assert row is not None
    assert row.last_verified_at is None

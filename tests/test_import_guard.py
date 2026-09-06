"""Operational DB import guard."""

import pytest

from app.core.import_guard import (
    academy_import_allowed,
    is_local_database_url,
    is_operational_database_url,
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
    allowed, _ = academy_import_allowed(url)
    assert allowed
    monkeypatch.delenv("ALLOW_ACADEMY_IMPORT", raising=False)


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

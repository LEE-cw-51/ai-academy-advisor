"""Studio/Postgres CHECK 부분집합 — SQLite에서도 도는 Python 가드."""

import os
from pathlib import Path

import pytest

from app.core.academy_url_guards import (
    NON_HOMEPAGE_HOST_MARKERS,
    WEBSITE_URL_DB_REJECT_MARKERS,
    is_homepage_url,
)
from app.core.studio_guards import (
    academies_violation_select_sql,
    subjects_check_predicate_sql,
    subjects_pass_db_check,
    website_url_check_predicate_sql,
    website_url_pass_db_check,
)
from app.core.subjects import SUBJECT_TAXONOMY

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "0006_academy_studio_guards.py"
)


def test_subjects_check_allows_null_and_taxonomy():
    assert subjects_pass_db_check(None)
    assert subjects_pass_db_check(["수학", "영어"])
    assert not subjects_pass_db_check(["한문"])
    assert not subjects_pass_db_check(["수학", "코딩"])


def test_website_url_check_rejects_social_hosts():
    assert website_url_pass_db_check(None)
    assert website_url_pass_db_check("https://example-academy.com")
    for marker in NON_HOMEPAGE_HOST_MARKERS:
        assert not website_url_pass_db_check(f"https://www.{marker}/academy")


def test_website_url_check_allows_host_substring_false_positives():
    """호스트 매칭 — URL 전체 LIKE 오탐을 막는다. is_homepage_url도 같은 호스트 함수."""
    assert website_url_pass_db_check("https://notinstagram.com")
    assert website_url_pass_db_check("https://academy.example.com/?ref=instagram.com")
    assert is_homepage_url("https://notinstagram.com")
    assert is_homepage_url("https://academy.example.com/?ref=instagram.com")
    assert not website_url_pass_db_check("https://instagram.com/x")
    assert not website_url_pass_db_check("https://www.instagram.com/x")
    assert not website_url_pass_db_check("https://www.instagram.com:443/x")
    assert not is_homepage_url("https://www.instagram.com/x")


def test_website_url_check_is_subset_of_is_homepage_url():
    """CHECK는 호스트만. 스킴 없는 URL은 Python만 거부."""
    assert not is_homepage_url("example-academy.com")
    assert website_url_pass_db_check("example-academy.com")
    assert is_homepage_url("https://example-academy.com")
    assert website_url_pass_db_check("https://example-academy.com")
    assert not is_homepage_url("https://www.instagram.com/x")
    assert not website_url_pass_db_check("https://www.instagram.com/x")


def test_check_sql_uses_host_matching_not_substring_like():
    website_sql = website_url_check_predicate_sql()
    assert "NOT LIKE '%instagram.com%'" not in website_sql
    assert "split_part" in website_sql
    assert "instagram.com" in website_sql
    assert "LIKE '%.instagram.com'" in website_sql
    violation_sql = academies_violation_select_sql()
    assert "SELECT id, name FROM academies" in violation_sql
    assert "NOT LIKE '%instagram.com%'" not in violation_sql


def test_check_sql_contains_taxonomy_and_reject_markers():
    subjects_sql = subjects_check_predicate_sql()
    for name in SUBJECT_TAXONOMY:
        assert name in subjects_sql
    website_sql = website_url_check_predicate_sql()
    for marker in WEBSITE_URL_DB_REJECT_MARKERS:
        assert marker in website_sql


def test_migration_0006_imports_studio_guards():
    source = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "from app.core.studio_guards import" in source
    assert "academies_violation_select_sql" in source
    assert "SELECT id, name FROM academies" in academies_violation_select_sql()
    assert "subjects_check_predicate_sql" in source
    assert "website_url_check_predicate_sql" in source
    assert "skip_academy_stamp" in source
    assert "registration_number cannot be changed" in source
    assert "CURRENT_DATE" in source
    assert "academy_fact_revisions" in source
    assert "old_row" in source
    assert "db_role" in source
    assert "NOT LIKE '%instagram.com%'" not in source
    add_at = source.index("ADD CONSTRAINT ck_academies_subjects_taxonomy")
    assert source.index("academies_violation_select_sql") < add_at
    assert source.index("RuntimeError") < add_at


def test_revision_model_roundtrip_sqlite(db_session):
    from app.models.academy import Academy, AcademyFactRevision

    academy = Academy(name="가드학원", address="하남시 미사")
    db_session.add(academy)
    db_session.commit()
    revision = AcademyFactRevision(
        academy_id=academy.id,
        old_row={"name": "가드학원"},
        db_role="test",
    )
    db_session.add(revision)
    db_session.commit()
    db_session.refresh(revision)
    assert revision.id is not None
    assert revision.old_row["name"] == "가드학원"


def test_sqlite_import_keeps_null_last_verified_at(db_session):
    """SQLite에는 스탬프 트리거가 없고, 임포트가 null 확인일을 유지한다."""
    from app.models.academy import Academy
    from app.schemas.academy import AcademyRecord
    from app.services.academy_import_service import import_records

    record = AcademyRecord(name="스탬프테스트학원", address="하남시 미사")
    assert record.last_verified_at is None
    import_records(db_session, [record])
    row = db_session.query(Academy).filter_by(name="스탬프테스트학원").one()
    assert row.last_verified_at is None


@pytest.mark.skipif(
    not os.getenv("PGVECTOR_TEST_DATABASE_URL"),
    reason="PGVECTOR_TEST_DATABASE_URL이 설정된 실제 Postgres가 필요합니다",
)
def test_postgres_check_constraints_on_temp_table():
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["PGVECTOR_TEST_DATABASE_URL"], future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE TEMP TABLE academy_guard_probe (
                    subjects jsonb,
                    website_url text,
                    CONSTRAINT ck_probe_subjects CHECK (
                        {subjects_check_predicate_sql()}
                    ),
                    CONSTRAINT ck_probe_website CHECK (
                        {website_url_check_predicate_sql()}
                    )
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO academy_guard_probe (subjects, website_url) "
                "VALUES (NULL, NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO academy_guard_probe (subjects, website_url) "
                "VALUES ('[\"수학\"]'::jsonb, 'https://example-academy.com')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO academy_guard_probe (subjects, website_url) "
                "VALUES ('[\"수학\"]'::jsonb, 'https://notinstagram.com')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO academy_guard_probe (subjects, website_url) "
                "VALUES (NULL, 'https://academy.example.com/?ref=instagram.com')"
            )
        )
        with conn.begin_nested():
            with pytest.raises(Exception):
                conn.execute(
                    text(
                        "INSERT INTO academy_guard_probe (subjects, website_url) "
                        "VALUES ('[\"한문\"]'::jsonb, NULL)"
                    )
                )
        with conn.begin_nested():
            with pytest.raises(Exception):
                conn.execute(
                    text(
                        "INSERT INTO academy_guard_probe (subjects, website_url) "
                        "VALUES (NULL, 'https://www.instagram.com/academy')"
                    )
                )
        with conn.begin_nested():
            with pytest.raises(Exception):
                conn.execute(
                    text(
                        "INSERT INTO academy_guard_probe (subjects, website_url) "
                        "VALUES (NULL, 'https://instagram.com/x')"
                    )
                )
    engine.dispose()


@pytest.mark.skipif(
    not os.getenv("PGVECTOR_TEST_DATABASE_URL"),
    reason="PGVECTOR_TEST_DATABASE_URL이 설정된 실제 Postgres가 필요합니다",
)
def test_postgres_stamp_guc_identity_and_revision():
    from datetime import date

    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["PGVECTOR_TEST_DATABASE_URL"], future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_stamp() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_identity() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_revision() CASCADE"))
        conn.execute(
            text(
                """
                CREATE TEMP TABLE academy_stamp_probe (
                    id integer PRIMARY KEY,
                    name text NOT NULL,
                    registration_number text,
                    last_verified_at date
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TEMP TABLE academy_revision_probe (
                    academy_id integer NOT NULL,
                    old_row jsonb NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE FUNCTION trg_probe_stamp()
                RETURNS trigger AS $$
                BEGIN
                    IF current_setting('app.skip_academy_stamp', true) = '1' THEN
                        RETURN NEW;
                    END IF;
                    IF NEW.last_verified_at IS NULL THEN
                        NEW.last_verified_at := CURRENT_DATE;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE FUNCTION trg_probe_identity()
                RETURNS trigger AS $$
                BEGIN
                    IF NEW.id IS DISTINCT FROM OLD.id THEN
                        RAISE EXCEPTION 'academies.id cannot be changed';
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE FUNCTION trg_probe_revision()
                RETURNS trigger AS $$
                BEGIN
                    INSERT INTO academy_revision_probe (academy_id, old_row)
                    VALUES (OLD.id, to_jsonb(OLD));
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER academy_stamp_probe_stamp
                BEFORE UPDATE ON academy_stamp_probe
                FOR EACH ROW EXECUTE FUNCTION trg_probe_stamp()
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER academy_stamp_probe_identity
                BEFORE UPDATE ON academy_stamp_probe
                FOR EACH ROW EXECUTE FUNCTION trg_probe_identity()
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER academy_stamp_probe_revision
                AFTER UPDATE ON academy_stamp_probe
                FOR EACH ROW EXECUTE FUNCTION trg_probe_revision()
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO academy_stamp_probe "
                "(id, name, last_verified_at) VALUES (1, '가드학원', NULL)"
            )
        )
        conn.execute(text("UPDATE academy_stamp_probe SET name = '가드학원2' WHERE id = 1"))
        stamped = conn.execute(
            text("SELECT last_verified_at FROM academy_stamp_probe WHERE id = 1")
        ).scalar_one()
        assert stamped == date.today()

        conn.execute(text("SELECT set_config('app.skip_academy_stamp', '1', true)"))
        conn.execute(
            text("UPDATE academy_stamp_probe SET last_verified_at = NULL WHERE id = 1")
        )
        skipped = conn.execute(
            text("SELECT last_verified_at FROM academy_stamp_probe WHERE id = 1")
        ).scalar_one()
        assert skipped is None

        with conn.begin_nested():
            with pytest.raises(Exception, match="cannot be changed"):
                conn.execute(text("UPDATE academy_stamp_probe SET id = 99 WHERE id = 1"))

        revision_count = conn.execute(
            text("SELECT count(*) FROM academy_revision_probe")
        ).scalar_one()
        assert revision_count >= 1

        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_stamp() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_identity() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS trg_probe_revision() CASCADE"))
    engine.dispose()

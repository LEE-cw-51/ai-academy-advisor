"""academy Studio guards + revision history

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-01

Supabase Table Editor 경유 수정에 대한 Postgres 전용 가드.
SQLite 테스트(create_all)에는 적용되지 않는다.

CHECK SQL은 `app.core.studio_guards`에서 생성한다 — Python 허용 과목·거부
호스트와 목록이 갈라지지 않게. CHECK는 호스트 매칭만 담는다.
http(s) 스킴·빈 netloc·`names_match`·블로그 id 관련성은 DB에 없다.
ADD CONSTRAINT 전에 위반 행을 SELECT하고, 1건 이상이면 제약을 만들지 않는다.
스탬프 트리거는 `app.skip_academy_stamp=1`이면 건너뛴다.
"""

from alembic import op
from sqlalchemy import text

from app.core.studio_guards import (
    academies_violation_select_sql,
    subjects_check_predicate_sql,
    website_url_check_predicate_sql,
)

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.execute(
        """
        CREATE TABLE academy_fact_revisions (
            id BIGSERIAL PRIMARY KEY,
            academy_id INTEGER NOT NULL,
            old_row JSONB NOT NULL,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            db_role TEXT NOT NULL DEFAULT current_user
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_academy_fact_revisions_academy_id "
        "ON academy_fact_revisions (academy_id)"
    )

    violations = conn.execute(text(academies_violation_select_sql())).fetchall()
    if violations:
        preview = ", ".join(f"{row[0]}:{row[1]}" for row in violations[:20])
        raise RuntimeError(
            f"0006 CHECK 위반 {len(violations)}건 — 제약을 추가하지 않음. "
            f"앞 20개: {preview}"
        )

    op.execute(
        f"""
        ALTER TABLE academies
        ADD CONSTRAINT ck_academies_subjects_taxonomy
        CHECK ({subjects_check_predicate_sql()})
        """
    )

    op.execute(
        f"""
        ALTER TABLE academies
        ADD CONSTRAINT ck_academies_website_not_social
        CHECK ({website_url_check_predicate_sql()})
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_academies_guard_identity()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.id IS DISTINCT FROM OLD.id THEN
                RAISE EXCEPTION 'academies.id cannot be changed';
            END IF;
            -- NULL → 값 채움은 허용 (시드 백필). 이미 있는 값 변경·삭제는 금지.
            IF OLD.registration_number IS NOT NULL
               AND NEW.registration_number IS DISTINCT FROM OLD.registration_number THEN
                RAISE EXCEPTION 'academies.registration_number cannot be changed';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_academies_stamp_last_verified()
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

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_academies_record_revision()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO academy_fact_revisions (
                academy_id, old_row, changed_at, db_role
            )
            VALUES (
                OLD.id,
                to_jsonb(OLD),
                now(),
                current_user
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE TRIGGER academies_guard_identity
        BEFORE UPDATE ON academies
        FOR EACH ROW EXECUTE FUNCTION trg_academies_guard_identity()
        """
    )
    op.execute(
        """
        CREATE TRIGGER academies_stamp_last_verified
        BEFORE UPDATE ON academies
        FOR EACH ROW EXECUTE FUNCTION trg_academies_stamp_last_verified()
        """
    )
    op.execute(
        """
        CREATE TRIGGER academies_record_revision
        AFTER UPDATE ON academies
        FOR EACH ROW EXECUTE FUNCTION trg_academies_record_revision()
        """
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.execute("DROP TRIGGER IF EXISTS academies_record_revision ON academies")
    op.execute("DROP TRIGGER IF EXISTS academies_stamp_last_verified ON academies")
    op.execute("DROP TRIGGER IF EXISTS academies_guard_identity ON academies")
    op.execute("DROP FUNCTION IF EXISTS trg_academies_record_revision()")
    op.execute("DROP FUNCTION IF EXISTS trg_academies_stamp_last_verified()")
    op.execute("DROP FUNCTION IF EXISTS trg_academies_guard_identity()")
    op.execute(
        "ALTER TABLE academies DROP CONSTRAINT IF EXISTS ck_academies_website_not_social"
    )
    op.execute(
        "ALTER TABLE academies DROP CONSTRAINT IF EXISTS ck_academies_subjects_taxonomy"
    )
    op.execute("DROP TABLE IF EXISTS academy_fact_revisions")

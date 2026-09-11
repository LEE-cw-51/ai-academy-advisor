"""subjects taxonomy 4종 + subject_detail 컬럼

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-11

과목 taxonomy를 5종(국어·영어·수학·과학·기타)에서 4종(국어·영어·수학·기타)으로
줄이고, `기타` 버킷의 세부 이름을 담는 `subject_detail` 컬럼을 추가한다.
과학은 taxonomy에서 빠져 `기타`+`subject_detail="과학"`으로 들어간다.

CHECK SQL은 `app.core.studio_guards`에서 생성한다 — Python 허용 목록과 갈라지지
않게. ADD/재생성 전에 위반 행(과학 등 4종 밖 subjects, 기타 없는 subject_detail)을
SELECT하고 1건 이상이면 제약을 만들지 않는다 (0006 패턴).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from app.core.studio_guards import (
    subject_detail_check_predicate_sql,
    subject_detail_violation_select_sql,
    subjects_check_predicate_sql,
)

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

# downgrade용 옛 5종 목록 — 앱 코드(SUBJECT_TAXONOMY)에는 과학이 사라지므로 하드코딩한다.
_OLD_SUBJECTS_CHECK = (
    "subjects IS NULL OR ("
    "jsonb_typeof(subjects) = 'array' "
    "AND subjects <@ '[\"국어\", \"영어\", \"수학\", \"과학\", \"기타\"]'::jsonb)"
)


def upgrade() -> None:
    op.add_column(
        "academies", sa.Column("subject_detail", sa.String(length=50), nullable=True)
    )

    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    violations = conn.execute(text(subject_detail_violation_select_sql())).fetchall()
    if violations:
        preview = ", ".join(f"{row[0]}:{row[1]}" for row in violations[:20])
        raise RuntimeError(
            f"0008 CHECK 위반 {len(violations)}건 — 제약을 추가하지 않음. "
            f"과학 등 4종 밖 subjects나 기타 없는 subject_detail을 먼저 정리한다. "
            f"앞 20개: {preview}"
        )

    op.execute(
        "ALTER TABLE academies DROP CONSTRAINT IF EXISTS ck_academies_subjects_taxonomy"
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
        ADD CONSTRAINT ck_academies_subject_detail_requires_etc
        CHECK ({subject_detail_check_predicate_sql()})
        """
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE academies "
            "DROP CONSTRAINT IF EXISTS ck_academies_subject_detail_requires_etc"
        )
        op.execute(
            "ALTER TABLE academies "
            "DROP CONSTRAINT IF EXISTS ck_academies_subjects_taxonomy"
        )
        op.execute(
            f"""
            ALTER TABLE academies
            ADD CONSTRAINT ck_academies_subjects_taxonomy
            CHECK ({_OLD_SUBJECTS_CHECK})
            """
        )

    op.drop_column("academies", "subject_detail")

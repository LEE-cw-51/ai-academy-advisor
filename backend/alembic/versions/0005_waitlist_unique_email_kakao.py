"""add partial unique indexes on waitlist email/kakao

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-13

대기자 중복 등록을 막기 위해 NULL이 아닌 email/kakao에 각각 유니크 인덱스를 둔다.
동일 연락처 재신청은 서비스 계층에서 기존 행을 반환(upsert)한다.
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_waitlist_email_not_null
        ON waitlist (email)
        WHERE email IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_waitlist_kakao_not_null
        ON waitlist (kakao)
        WHERE kakao IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_waitlist_kakao_not_null")
    op.execute("DROP INDEX IF EXISTS uq_waitlist_email_not_null")

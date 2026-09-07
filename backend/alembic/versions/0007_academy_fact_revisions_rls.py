"""Lock academy_fact_revisions from Data API

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-07

감사 테이블을 Supabase Data API(anon/authenticated)에서 숨긴다.
정책 없는 RLS + REVOKE — service_role·테이블 소유자(Studio)는 계속 접근한다.
`academies` 전체 RLS는 이번 범위 밖(공개 쓰기 API 없음 + Studio 운영 유지).
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.execute("ALTER TABLE academy_fact_revisions ENABLE ROW LEVEL SECURITY")
    op.execute(
        "REVOKE ALL ON TABLE academy_fact_revisions FROM anon, authenticated"
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.execute(
        "GRANT ALL ON TABLE academy_fact_revisions TO anon, authenticated"
    )
    op.execute("ALTER TABLE academy_fact_revisions DISABLE ROW LEVEL SECURITY")

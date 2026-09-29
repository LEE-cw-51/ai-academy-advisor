"""Lock core public tables from Supabase Data API

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-29

PostgREST(anon/authenticated)로 public 테이블이 CRUD 가능한 상태를 막는다.
`0007`/`0009`와 동일: 정책 없는 RLS ENABLE + REVOKE — postgres·service_role·
Studio·FastAPI DATABASE_URL·Cursor/Claude Supabase MCP(OAuth SQL)는 그대로.

프론트는 Supabase JS를 쓰지 않으며 engagement 쓰기는 FastAPI만 한다.
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# academy_fact_revisions · academy_trait_labels는 0007/0009에서 이미 잠김.
_DATA_API_TABLES = (
    "academies",
    "reviews",
    "search_history",
    "click_logs",
    "feedback",
    "waitlist",
    "alembic_version",
)


def _lock_table(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON TABLE {table} FROM anon, authenticated")


def _unlock_table(table: str) -> None:
    op.execute(f"GRANT ALL ON TABLE {table} TO anon, authenticated")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in _DATA_API_TABLES:
        _lock_table(table)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in reversed(_DATA_API_TABLES):
        _unlock_table(table)

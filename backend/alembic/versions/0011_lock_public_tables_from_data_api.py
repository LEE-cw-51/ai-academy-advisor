"""Lock remaining public tables from the Data API

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-29

Supabase Data API(PostgREST)는 `public` 스키마를 노출한다. RLS가 꺼져 있고
`anon`/`authenticated`에 GRANT가 있으면 프로젝트 URL만으로 읽기·수정·삭제가 된다.
`0007`·`0009`와 같이 정책 없는 RLS + REVOKE로 잠근다.

`postgres`·`service_role`은 RLS를 우회하므로 Studio Table Editor와 FastAPI
(SQLAlchemy, `DATABASE_URL`)는 그대로다. 사용자 로그인용 정책이 아니다.
SQLite 테스트는 이 문을 건너뛴다.
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# Data API에 열려 있던 테이블. 이미 잠긴 academy_fact_revisions·
# academy_trait_labels는 여기 넣지 않는다.
_LOCKED_TABLES = (
    "academies",
    "reviews",
    "search_history",
    "click_logs",
    "feedback",
    "waitlist",
    "alembic_version",
)


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in _LOCKED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE {table} FROM anon, authenticated")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in reversed(_LOCKED_TABLES):
        op.execute(f"GRANT ALL ON TABLE {table} TO anon, authenticated")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

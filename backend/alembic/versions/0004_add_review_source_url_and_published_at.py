"""add reviews.source_url and reviews.published_at

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-02

네이버 검색 API 수집 경로의 중복 제거용 컬럼을 추가한다.
`(academy_id, source_url)` 복합 유니크라 같은 글이 두 학원에 각각 붙는 건 허용된다
(블로그 글 1건이 두 학원을 언급할 수 있고 그건 학원별로 유효한 근거다).

기존 행은 `source_url`이 NULL이라 제약을 즉시 만족한다 — 백필 불필요.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("source_url", sa.String(length=500), nullable=True))
    op.add_column("reviews", sa.Column("published_at", sa.Date(), nullable=True))
    op.create_unique_constraint(
        "uq_reviews_academy_id_source_url", "reviews", ["academy_id", "source_url"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_reviews_academy_id_source_url", "reviews", type_="unique")
    op.drop_column("reviews", "published_at")
    op.drop_column("reviews", "source_url")

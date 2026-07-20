"""create review and engagement tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-14

리뷰(pgvector 임베딩 포함) + 사용자 행동 로그(검색/클릭/피드백/대기자) 테이블 생성.
이 마이그레이션은 운영 PostgreSQL에서만 실행된다(테스트는 SQLite create_all 경유).
"""

import os

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# NOTE: migrations should be self-contained; avoid importing application settings here.
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # embedding 컬럼: postgres는 pgvector Vector, 그 외는 JSON(이중화 관례).
    embedding_type = (
        Vector(EMBEDDING_DIM)
        if is_postgres
        else sa.JSON()
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("academy_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("embedding", embedding_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
        sa.ForeignKeyConstraint(
            ["academy_id"], ["academies.id"], name="fk_reviews_academy_id_academies"
        ),
    )
    op.create_index("ix_reviews_academy_id", "reviews", ["academy_id"])

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_search_history"),
    )

    op.create_table(
        "click_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("academy_id", sa.Integer(), nullable=True),
        sa.Column("event", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_click_logs"),
        sa.ForeignKeyConstraint(
            ["academy_id"], ["academies.id"], name="fk_click_logs_academy_id_academies"
        ),
    )
    op.create_index("ix_click_logs_academy_id", "click_logs", ["academy_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
    )

    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("kakao", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_waitlist"),
    )


def downgrade() -> None:
    op.drop_table("waitlist")
    op.drop_table("feedback")
    op.drop_index("ix_click_logs_academy_id", table_name="click_logs")
    op.drop_table("click_logs")
    op.drop_table("search_history")
    op.drop_index("ix_reviews_academy_id", table_name="reviews")
    op.drop_table("reviews")
    # vector 확장은 다른 객체가 쓸 수 있으므로 남겨둔다.

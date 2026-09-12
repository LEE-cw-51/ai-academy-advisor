"""create academy_trait_labels + Data API lock

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-12

리뷰·공개 문구에서 뽑은 닫힌 특징 라벨 테이블. academies.curriculum_* 와
분리한다 (docs/data-strategy.md Stage 4a). Postgres 에서는 academy_fact_revisions
와 같이 정책 없는 RLS + REVOKE 로 Data API(anon/authenticated)를 잠근다.
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

_LABELS = (
    "mentions_seonhaeng",
    "mentions_naesin",
    "mentions_suneung",
    "mentions_homework",
    "mentions_clinic",
    "mentions_qna",
)
_SOURCE_TYPES = ("review", "homepage", "blog")
_STATUSES = ("candidate", "published")


def upgrade() -> None:
    label_in = ", ".join(f"'{x}'" for x in _LABELS)
    source_in = ", ".join(f"'{x}'" for x in _SOURCE_TYPES)
    status_in = ", ".join(f"'{x}'" for x in _STATUSES)

    op.create_table(
        "academy_trait_labels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("academy_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="candidate",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_academy_trait_labels"),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_academy_trait_labels_academy_id_academies",
        ),
        sa.UniqueConstraint(
            "academy_id",
            "label",
            "source_url",
            name="uq_academy_trait_labels_academy_id_label_source_url",
        ),
        # 이름은 짧게 넘긴다 — Alembic 이 `Base.metadata` 의 naming_convention
        # (`ck_%(table_name)s_%(constraint_name)s`)을 여기에 한 번 더 씌우므로,
        # 완성된 이름을 넘기면 `ck_academy_trait_labels_ck_academy_trait_labels_label`
        # 처럼 접두사가 겹쳐 모델이 만드는 이름과 갈라진다.
        sa.CheckConstraint(f"label IN ({label_in})", name="label"),
        sa.CheckConstraint(f"source_type IN ({source_in})", name="source_type"),
        sa.CheckConstraint(f"status IN ({status_in})", name="status"),
    )
    # academy_id 단독 인덱스는 두지 않는다 — 유니크 제약
    # `(academy_id, label, source_url)` 의 선두 컬럼이 같은 조회를 이미 커버한다.
    op.create_index(
        "ix_academy_trait_labels_label",
        "academy_trait_labels",
        ["label"],
    )

    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TABLE academy_trait_labels ENABLE ROW LEVEL SECURITY")
        op.execute(
            "REVOKE ALL ON TABLE academy_trait_labels FROM anon, authenticated"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(
            "GRANT ALL ON TABLE academy_trait_labels TO anon, authenticated"
        )
        op.execute("ALTER TABLE academy_trait_labels DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_academy_trait_labels_label", table_name="academy_trait_labels")
    op.drop_table("academy_trait_labels")

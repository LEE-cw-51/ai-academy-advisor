"""create academies table

Revision ID: 0001
Revises:
Create Date: 2026-07-06

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("registration_number", sa.String(length=50), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("website_url", sa.String(length=300), nullable=True),
        sa.Column("blog_url", sa.String(length=300), nullable=True),
        sa.Column("instagram_url", sa.String(length=300), nullable=True),
        sa.Column(
            "subjects",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("level_elementary", sa.Boolean(), nullable=True),
        sa.Column("level_middle", sa.Boolean(), nullable=True),
        sa.Column("level_high", sa.Boolean(), nullable=True),
        sa.Column("class_small_group", sa.Boolean(), nullable=True),
        sa.Column("class_group", sa.Boolean(), nullable=True),
        sa.Column("class_one_on_one", sa.Boolean(), nullable=True),
        sa.Column("curriculum_seonhaeng", sa.Boolean(), nullable=True),
        sa.Column("curriculum_naesin", sa.Boolean(), nullable=True),
        sa.Column("curriculum_suneung", sa.Boolean(), nullable=True),
        sa.Column("shuttle_available", sa.Boolean(), nullable=True),
        sa.Column("operating_hours", sa.Text(), nullable=True),
        sa.Column("established_year", sa.Integer(), nullable=True),
        sa.Column("teacher_count", sa.Integer(), nullable=True),
        sa.Column("classroom_count", sa.Integer(), nullable=True),
        sa.Column("tagline", sa.String(length=200), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_academies"),
        sa.UniqueConstraint(
            "registration_number", name="uq_academies_registration_number"
        ),
        sa.UniqueConstraint("name", "address", name="uq_academies_name_address"),
    )
    op.create_index("ix_academies_name", "academies", ["name"])


def downgrade() -> None:
    op.drop_index("ix_academies_name", table_name="academies")
    op.drop_table("academies")

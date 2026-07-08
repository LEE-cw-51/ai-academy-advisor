"""add tuition_monthly_fee

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08

"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "academies", sa.Column("tuition_monthly_fee", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("academies", "tuition_monthly_fee")

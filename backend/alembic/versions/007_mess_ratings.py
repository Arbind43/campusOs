"""Mess sentiment ratings table

Revision ID: 007_mess_ratings
Revises: 006_wellbeing
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_mess_ratings"
down_revision: Union[str, None] = "006_wellbeing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mess_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rating_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=20), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitter_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rating_date", "meal_type", "submitter_hash", name="uq_mess_rating"),
    )
    op.create_index("ix_mess_ratings_date", "mess_ratings", ["rating_date"])


def downgrade() -> None:
    op.drop_index("ix_mess_ratings_date", table_name="mess_ratings")
    op.drop_table("mess_ratings")

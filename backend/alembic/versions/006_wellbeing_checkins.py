"""Anonymous wellbeing check-ins table

Revision ID: 006_wellbeing
Revises: 005
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_wellbeing"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wellbeing_checkins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("year_of_study", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("stress", sa.Integer(), nullable=False),
        sa.Column("sleep", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("submitter_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_start", "submitter_hash", name="uq_wellbeing_week_submitter"),
    )
    op.create_index("ix_wellbeing_week_start", "wellbeing_checkins", ["week_start"])
    op.create_index("ix_wellbeing_department_id", "wellbeing_checkins", ["department_id"])


def downgrade() -> None:
    op.drop_index("ix_wellbeing_department_id", table_name="wellbeing_checkins")
    op.drop_index("ix_wellbeing_week_start", table_name="wellbeing_checkins")
    op.drop_table("wellbeing_checkins")

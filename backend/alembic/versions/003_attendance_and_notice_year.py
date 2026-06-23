"""Attendance records + notice year targeting

Revision ID: 003
Revises: 002
Create Date: 2026-06-15

Adds:
  - notices.target_year (nullable int) for per-year notice targeting
  - attendance_records table
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Notice year targeting
    op.add_column(
        "notices",
        sa.Column("target_year", sa.Integer(), nullable=True),
    )

    # 2) Attendance marks (per-day, per-subject). Named `attendance_marks` to
    # avoid colliding with the legacy summary table `attendance_records`.
    op.create_table(
        "attendance_marks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("year_of_study", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=False, server_default="General"),
        sa.Column("attend_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="present"),
        sa.Column("marked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["marked_by"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id", "attend_date", "subject", name="uq_attendance_student_date_subject"
        ),
    )
    op.create_index("ix_attendance_marks_student_id", "attendance_marks", ["student_id"])
    op.create_index("ix_attendance_marks_department_id", "attendance_marks", ["department_id"])
    op.create_index("ix_attendance_marks_attend_date", "attendance_marks", ["attend_date"])


def downgrade() -> None:
    op.drop_index("ix_attendance_marks_attend_date", table_name="attendance_marks")
    op.drop_index("ix_attendance_marks_department_id", table_name="attendance_marks")
    op.drop_index("ix_attendance_marks_student_id", table_name="attendance_marks")
    op.drop_table("attendance_marks")
    op.drop_column("notices", "target_year")

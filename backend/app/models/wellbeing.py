"""
Anonymous weekly wellbeing check-in.

Privacy by design: we do NOT store the submitting user's id. A one-way
`submitter_hash` (derived from user id + week + server secret) is stored only
to prevent more than one submission per student per week — it cannot be
reversed to identify the student. Department/year are coarse cohort tags used
for aggregate insights (never shown for tiny cohorts).
"""
from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.database import Base


class WellbeingCheckin(Base):
    __tablename__ = "wellbeing_checkins"
    __table_args__ = (
        UniqueConstraint("week_start", "submitter_hash", name="uq_wellbeing_week_submitter"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[date] = mapped_column(nullable=False, index=True)
    # Coarse cohort tags for aggregate insights (no direct identity).
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    year_of_study: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 3 questions, each 1–5
    mood: Mapped[int] = mapped_column(Integer, nullable=False)    # 1 = very low .. 5 = great
    stress: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = none .. 5 = overwhelmed
    sleep: Mapped[int] = mapped_column(Integer, nullable=False)   # 1 = poor .. 5 = excellent
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Anti-duplication only — NOT reversible to a user.
    submitter_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

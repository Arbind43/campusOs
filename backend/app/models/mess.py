"""
Campus-wide mess schedule.

Separate from the per-hostel `mess_menus` table: this is a single campus mess
menu with meal timings, uploaded by an admin (image OCR) like the timetable.
"""
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessSchedule(Base):
    """One row per day + meal. day_of_week may be 'Daily' for everyday meals."""
    __tablename__ = "mess_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False, default="Daily")
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # breakfast/lunch/snacks/dinner
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    items: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_special: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MessRating(Base):
    """
    One-tap rating of today's meal. Anonymous: stores no user id.
    A one-way hash enforces one rating per student per meal per day
    (re-tapping updates the existing row).
    """
    __tablename__ = "mess_ratings"
    __table_args__ = (
        UniqueConstraint("rating_date", "meal_type", "submitter_hash", name="uq_mess_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rating_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # breakfast/lunch/snacks/dinner
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 (poor) .. 5 (great)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitter_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""
Hostel domain models: Hostel, HostelRoom, MessMenu, MessNotice.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    warden_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rooms: Mapped[list["HostelRoom"]] = relationship("HostelRoom", back_populates="hostel")
    mess_menus: Mapped[list["MessMenu"]] = relationship("MessMenu", back_populates="hostel")
    mess_notices: Mapped[list["MessNotice"]] = relationship("MessNotice", back_populates="hostel")

    def __repr__(self) -> str:
        return f"<Hostel {self.name}>"


class HostelRoom(Base):
    __tablename__ = "hostel_rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hostel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="rooms")


class MessMenu(Base):
    """Weekly mess menu — one row per hostel + day + meal."""
    __tablename__ = "mess_menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)  # Monday of the week
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)  # Monday..Sunday
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # breakfast/lunch/snacks/dinner
    items: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated or freetext
    is_special: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="mess_menus")


class MessNotice(Base):
    __tablename__ = "mess_notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="mess_notices")

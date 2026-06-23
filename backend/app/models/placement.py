"""
Placement domain models: PlacementDrive, PlacementNotice.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    job_role: Mapped[str] = mapped_column(String(150), nullable=False)
    package_lpa: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)  # in LPA
    drive_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    registrations: Mapped[list["DriveRegistration"]] = relationship(
        "DriveRegistration", back_populates="drive"
    )

    def __repr__(self) -> str:
        return f"<PlacementDrive {self.company_name} - {self.job_role}>"


class DriveRegistration(Base):
    """Students registering for a placement drive."""
    __tablename__ = "drive_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("placement_drives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    drive: Mapped["PlacementDrive"] = relationship("PlacementDrive", back_populates="registrations")


class PlacementNotice(Base):
    __tablename__ = "placement_notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    drive_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("placement_drives.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

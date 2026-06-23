"""
User profile table.

Supabase Auth manages passwords and sessions. This table stores the
application-level profile keyed by the Supabase user UUID.

Roles are managed via the user_roles join table (RBAC). The legacy `role`
column is kept for backwards compatibility but is no longer the source of truth.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    # Matches auth.users.id in Supabase — set by the backend after first login
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Legacy single-role field — kept for backward compat. Source of truth is user_roles table.
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="STUDENT")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Academic context (for students and faculty)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    year_of_study: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 1–4 for students, None for staff

    # Hostel context
    hostel_room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hostel_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(  # type: ignore[name-defined]
        "UserRole",
        foreign_keys="UserRole.user_id",
        lazy="noload",  # Don't auto-load to avoid DB errors - load explicitly when needed
    )

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} email={self.email} role={self.role}>"

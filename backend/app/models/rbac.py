"""
RBAC models: Role and UserRole (join table).

Every user can have MULTIPLE roles simultaneously (e.g. a student who is also
a Placement Coordinator). An optional `scope_id` ties the role to a specific
entity — e.g. a CLUB_COORDINATOR's scope_id would be the club's UUID.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # Back-reference
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class UserRole(Base):
    """
    Assigns a Role to a UserProfile.

    scope_id is optional:
      - For CLUB_COORDINATOR: the club's UUID
      - For HOSTEL_COORDINATOR: the hostel's UUID
      - For FACULTY: department UUID (but we also use department_id on UserProfile)
      - For most roles: NULL
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "scope_id", name="uq_user_role_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role_id={self.role_id}>"


# Canonical role name constants — use these everywhere instead of magic strings
class RoleName:
    SUPER_ADMIN = "SUPER_ADMIN"
    ACADEMIC_ADMIN = "ACADEMIC_ADMIN"
    HOSTEL_ADMIN = "HOSTEL_ADMIN"
    PLACEMENT_ADMIN = "PLACEMENT_ADMIN"
    MESS_ADMIN = "MESS_ADMIN"
    CLUB_ADMIN = "CLUB_ADMIN"
    FACULTY = "FACULTY"
    PLACEMENT_COORDINATOR = "PLACEMENT_COORDINATOR"
    HOSTEL_COORDINATOR = "HOSTEL_COORDINATOR"
    CLUB_COORDINATOR = "CLUB_COORDINATOR"
    STUDENT = "STUDENT"

    ALL = [
        SUPER_ADMIN, ACADEMIC_ADMIN, HOSTEL_ADMIN, PLACEMENT_ADMIN,
        MESS_ADMIN, CLUB_ADMIN, FACULTY, PLACEMENT_COORDINATOR,
        HOSTEL_COORDINATOR, CLUB_COORDINATOR, STUDENT,
    ]

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ticket(Base):
    __tablename__ = "helpdesk_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # "Maintenance", "IT Support", "General"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open")  # "Open", "In Progress", "Resolved", "Closed"
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")  # "Low", "Medium", "High"
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator = relationship("UserProfile", foreign_keys=[created_by])
    assignee = relationship("UserProfile", foreign_keys=[assigned_to])

    def __repr__(self) -> str:
        return f"<Ticket {self.id} title='{self.title}'>"

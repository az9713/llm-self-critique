import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ChatSession(Base):
    """Persistent storage for elicitation chat sessions."""
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("domains.id"), nullable=True)
    phase: Mapped[str] = mapped_column(String(50), default="intro")
    domain_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Store elicitation data as JSON
    objects: Mapped[list] = mapped_column(JSON, default=list)
    predicates: Mapped[list] = mapped_column(JSON, default=list)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    initial_state: Mapped[list] = mapped_column(JSON, default=list)
    goal_state: Mapped[list] = mapped_column(JSON, default=list)

    # Store messages as JSON array
    messages: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

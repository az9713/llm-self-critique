import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.planning import Verdict, SessionStatus


class PlanningSession(Base):
    __tablename__ = "planning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("domains.id"))
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), default=SessionStatus.ELICITING
    )
    problem_description: Mapped[str] = mapped_column(Text)
    domain_pddl: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_pddl: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_verdict: Mapped[Verdict | None] = mapped_column(SQLEnum(Verdict), nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlanIteration(Base):
    __tablename__ = "plan_iterations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planning_sessions.id"))
    iteration_number: Mapped[int] = mapped_column(Integer)
    plan: Mapped[str] = mapped_column(Text)
    verdict: Mapped[Verdict] = mapped_column(SQLEnum(Verdict))
    confidence: Mapped[float] = mapped_column(default=0.0)
    critique_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

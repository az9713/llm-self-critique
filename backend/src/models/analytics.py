"""Analytics and usage tracking models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKey(Base):
    """API keys for public API access."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(8))  # First 8 chars for identification
    status: Mapped[APIKeyStatus] = mapped_column(default=APIKeyStatus.ACTIVE)
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # Requests per minute
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsageLog(Base):
    """Individual API request logs."""

    __tablename__ = "usage_logs"
    __table_args__ = (
        Index("ix_usage_logs_user_created", "user_id", "created_at"),
        Index("ix_usage_logs_endpoint_created", "endpoint", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(255), index=True)
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    request_size: Mapped[int | None] = mapped_column(Integer, default=None)
    response_size: Mapped[int | None] = mapped_column(Integer, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)  # IPv6 max length
    user_agent: Mapped[str | None] = mapped_column(String(500), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    extra_data: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class UsageAggregate(Base):
    """Aggregated usage statistics (hourly/daily)."""

    __tablename__ = "usage_aggregates"
    __table_args__ = (
        Index("ix_usage_agg_user_period", "user_id", "period_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_type: Mapped[str] = mapped_column(String(10))  # "hour" or "day"
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    endpoints_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    planning_sessions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

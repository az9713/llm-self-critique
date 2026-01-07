"""Analytics API endpoints for usage statistics."""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.analytics import UsageLog, UsageAggregate


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class UsageSummary(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    total_llm_tokens: int
    planning_sessions: int


class EndpointStats(BaseModel):
    endpoint: str
    request_count: int
    avg_latency_ms: float
    error_rate: float


class DailyUsage(BaseModel):
    date: str
    requests: int
    avg_latency_ms: float


class AnalyticsDashboard(BaseModel):
    summary: UsageSummary
    top_endpoints: List[EndpointStats]
    daily_usage: List[DailyUsage]
    period_start: datetime
    period_end: datetime


@router.get("/summary", response_model=UsageSummary)
async def get_usage_summary(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    """Get usage summary statistics."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Base query
    base_filter = UsageLog.created_at >= start_date
    if user_id:
        base_filter = and_(base_filter, UsageLog.user_id == user_id)

    # Total requests
    total_result = await db.execute(
        select(func.count(UsageLog.id)).where(base_filter)
    )
    total_requests = total_result.scalar() or 0

    # Successful requests (2xx status codes)
    success_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            and_(base_filter, UsageLog.status_code >= 200, UsageLog.status_code < 300)
        )
    )
    successful_requests = success_result.scalar() or 0

    # Failed requests
    failed_requests = total_requests - successful_requests

    # Average latency
    latency_result = await db.execute(
        select(func.avg(UsageLog.latency_ms)).where(base_filter)
    )
    avg_latency_ms = latency_result.scalar() or 0.0

    # LLM tokens (from extra_data)
    # Note: This is a simplified approach; in production you might want a separate token tracking table
    llm_result = await db.execute(
        select(UsageLog.extra_data).where(
            and_(base_filter, UsageLog.extra_data.isnot(None))
        )
    )
    total_llm_tokens = 0
    planning_sessions = 0

    for row in llm_result.scalars():
        if row and isinstance(row, dict):
            if row.get("type") == "llm_usage":
                total_llm_tokens += row.get("total_tokens", 0)
            elif row.get("type") == "planning_session":
                planning_sessions += 1

    return UsageSummary(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        avg_latency_ms=round(avg_latency_ms, 2),
        total_llm_tokens=total_llm_tokens,
        planning_sessions=planning_sessions,
    )


@router.get("/endpoints", response_model=List[EndpointStats])
async def get_endpoint_stats(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    limit: int = Query(10, ge=1, le=50, description="Number of endpoints to return"),
    db: AsyncSession = Depends(get_db),
) -> List[EndpointStats]:
    """Get statistics by endpoint."""
    start_date = datetime.utcnow() - timedelta(days=days)

    base_filter = UsageLog.created_at >= start_date
    if user_id:
        base_filter = and_(base_filter, UsageLog.user_id == user_id)

    result = await db.execute(
        select(
            UsageLog.endpoint,
            func.count(UsageLog.id).label("request_count"),
            func.avg(UsageLog.latency_ms).label("avg_latency"),
            func.sum(
                case((UsageLog.status_code >= 400, 1), else_=0)
            ).label("error_count"),
        )
        .where(base_filter)
        .group_by(UsageLog.endpoint)
        .order_by(func.count(UsageLog.id).desc())
        .limit(limit)
    )

    stats = []
    for row in result:
        request_count = row.request_count or 0
        error_count = row.error_count or 0
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0.0

        stats.append(EndpointStats(
            endpoint=row.endpoint,
            request_count=request_count,
            avg_latency_ms=round(row.avg_latency or 0, 2),
            error_rate=round(error_rate, 2),
        ))

    return stats


@router.get("/daily", response_model=List[DailyUsage])
async def get_daily_usage(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
) -> List[DailyUsage]:
    """Get daily usage statistics."""
    start_date = datetime.utcnow() - timedelta(days=days)

    base_filter = UsageLog.created_at >= start_date
    if user_id:
        base_filter = and_(base_filter, UsageLog.user_id == user_id)

    # Group by date
    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("date"),
            func.count(UsageLog.id).label("requests"),
            func.avg(UsageLog.latency_ms).label("avg_latency"),
        )
        .where(base_filter)
        .group_by(func.date(UsageLog.created_at))
        .order_by(func.date(UsageLog.created_at))
    )

    return [
        DailyUsage(
            date=str(row.date),
            requests=row.requests or 0,
            avg_latency_ms=round(row.avg_latency or 0, 2),
        )
        for row in result
    ]


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsDashboard:
    """Get complete analytics dashboard data."""
    summary = await get_usage_summary(user_id=user_id, days=days, db=db)
    top_endpoints = await get_endpoint_stats(user_id=user_id, days=days, limit=10, db=db)
    daily_usage = await get_daily_usage(user_id=user_id, days=days, db=db)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    return AnalyticsDashboard(
        summary=summary,
        top_endpoints=top_endpoints,
        daily_usage=daily_usage,
        period_start=period_start,
        period_end=period_end,
    )


@router.get("/recent", response_model=List[dict])
async def get_recent_logs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get recent usage logs."""
    filters = []

    if user_id:
        filters.append(UsageLog.user_id == user_id)
    if status_code:
        filters.append(UsageLog.status_code == status_code)

    query = select(UsageLog).order_by(UsageLog.created_at.desc()).limit(limit)

    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)

    return [
        {
            "id": str(log.id),
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "latency_ms": log.latency_ms,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
            "error_message": log.error_message,
        }
        for log in result.scalars()
    ]

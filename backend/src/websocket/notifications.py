"""Notification system for broadcasting events to WebSocket clients."""

from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone

from .manager import manager


class NotificationType(str, Enum):
    """Types of notifications that can be sent."""
    # Planning notifications
    PLAN_STARTED = "plan_started"
    PLAN_PROGRESS = "plan_progress"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"

    # Domain notifications
    DOMAIN_CREATED = "domain_created"
    DOMAIN_UPDATED = "domain_updated"
    DOMAIN_DELETED = "domain_deleted"
    DOMAIN_PDDL_GENERATED = "domain_pddl_generated"

    # Chat notifications
    CHAT_MESSAGE = "chat_message"
    CHAT_STATE_CHANGED = "chat_state_changed"

    # Session notifications
    SESSION_CREATED = "session_created"
    SESSION_UPDATED = "session_updated"

    # System notifications
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"


@dataclass
class Notification:
    """A notification to be sent to clients."""
    type: NotificationType
    data: dict
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class NotificationService:
    """Service for sending notifications to WebSocket clients."""

    async def notify_user(
        self,
        user_id: str,
        notification: Notification,
    ) -> int:
        """Send a notification to all connections for a user."""
        return await manager.broadcast_to_user(
            user_id,
            notification.to_dict(),
        )

    async def notify_domain(
        self,
        domain_id: str,
        notification: Notification,
        exclude_session: Optional[str] = None,
    ) -> int:
        """Send a notification to all clients subscribed to a domain."""
        return await manager.broadcast_to_topic(
            f"domain:{domain_id}",
            notification.to_dict(),
            exclude=exclude_session,
        )

    async def notify_session(
        self,
        session_id: str,
        notification: Notification,
    ) -> bool:
        """Send a notification to a specific session."""
        return await manager.send_personal(
            session_id,
            notification.to_dict(),
        )

    async def broadcast_all(
        self,
        notification: Notification,
        exclude_session: Optional[str] = None,
    ) -> int:
        """Broadcast a notification to all connected clients."""
        return await manager.broadcast_all(
            notification.to_dict(),
            exclude=exclude_session,
        )

    # Convenience methods for common notifications

    async def plan_started(
        self,
        domain_id: str,
        session_id: str,
        max_iterations: int,
    ) -> int:
        """Notify that plan generation has started."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.PLAN_STARTED,
                data={
                    "session_id": session_id,
                    "max_iterations": max_iterations,
                },
            ),
        )

    async def plan_progress(
        self,
        domain_id: str,
        session_id: str,
        iteration: int,
        status: str,
        details: Optional[dict] = None,
    ) -> int:
        """Notify about plan generation progress."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.PLAN_PROGRESS,
                data={
                    "session_id": session_id,
                    "iteration": iteration,
                    "status": status,
                    **(details or {}),
                },
            ),
        )

    async def plan_completed(
        self,
        domain_id: str,
        session_id: str,
        plan: str,
        iterations: int,
        verdict: str,
    ) -> int:
        """Notify that plan generation has completed."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.PLAN_COMPLETED,
                data={
                    "session_id": session_id,
                    "plan": plan,
                    "iterations": iterations,
                    "verdict": verdict,
                },
            ),
        )

    async def plan_failed(
        self,
        domain_id: str,
        session_id: str,
        error: str,
        iterations: int,
    ) -> int:
        """Notify that plan generation has failed."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.PLAN_FAILED,
                data={
                    "session_id": session_id,
                    "error": error,
                    "iterations": iterations,
                },
            ),
        )

    async def domain_updated(
        self,
        domain_id: str,
        changes: dict,
        exclude_session: Optional[str] = None,
    ) -> int:
        """Notify that a domain has been updated."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.DOMAIN_UPDATED,
                data={
                    "domain_id": domain_id,
                    "changes": changes,
                },
            ),
            exclude_session=exclude_session,
        )

    async def pddl_generated(
        self,
        domain_id: str,
        domain_pddl: str,
        problem_pddl: str,
    ) -> int:
        """Notify that PDDL has been generated for a domain."""
        return await self.notify_domain(
            domain_id,
            Notification(
                type=NotificationType.DOMAIN_PDDL_GENERATED,
                data={
                    "domain_id": domain_id,
                    "domain_pddl": domain_pddl,
                    "problem_pddl": problem_pddl,
                },
            ),
        )


# Global notification service instance
notifications = NotificationService()

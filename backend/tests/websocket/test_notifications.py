"""Tests for notification service."""

import pytest
from unittest.mock import AsyncMock, patch
from src.websocket.notifications import (
    NotificationService,
    NotificationType,
    Notification,
)


@pytest.fixture
def notification_service():
    return NotificationService()


def test_notification_to_dict():
    notification = Notification(
        type=NotificationType.PLAN_COMPLETED,
        data={"plan": "step1\nstep2"},
    )

    result = notification.to_dict()

    assert result["type"] == "plan_completed"
    assert result["data"]["plan"] == "step1\nstep2"
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_notify_domain(notification_service):
    with patch("src.websocket.notifications.manager") as mock_manager:
        mock_manager.broadcast_to_topic = AsyncMock(return_value=3)

        count = await notification_service.notify_domain(
            "domain-123",
            Notification(
                type=NotificationType.DOMAIN_UPDATED,
                data={"changes": {"name": "New Name"}},
            ),
        )

        assert count == 3
        mock_manager.broadcast_to_topic.assert_called_once()
        call_args = mock_manager.broadcast_to_topic.call_args
        assert call_args[0][0] == "domain:domain-123"
        assert call_args[0][1]["type"] == "domain_updated"


@pytest.mark.asyncio
async def test_notify_user(notification_service):
    with patch("src.websocket.notifications.manager") as mock_manager:
        mock_manager.broadcast_to_user = AsyncMock(return_value=2)

        count = await notification_service.notify_user(
            "user-456",
            Notification(
                type=NotificationType.SYSTEM_INFO,
                data={"message": "Welcome!"},
            ),
        )

        assert count == 2
        mock_manager.broadcast_to_user.assert_called_once()


@pytest.mark.asyncio
async def test_plan_completed(notification_service):
    with patch("src.websocket.notifications.manager") as mock_manager:
        mock_manager.broadcast_to_topic = AsyncMock(return_value=1)

        count = await notification_service.plan_completed(
            domain_id="domain-123",
            session_id="session-456",
            plan="step1\nstep2",
            iterations=3,
            verdict="correct",
        )

        assert count == 1
        call_args = mock_manager.broadcast_to_topic.call_args
        message = call_args[0][1]
        assert message["type"] == "plan_completed"
        assert message["data"]["session_id"] == "session-456"
        assert message["data"]["verdict"] == "correct"


@pytest.mark.asyncio
async def test_plan_progress(notification_service):
    with patch("src.websocket.notifications.manager") as mock_manager:
        mock_manager.broadcast_to_topic = AsyncMock(return_value=1)

        count = await notification_service.plan_progress(
            domain_id="domain-123",
            session_id="session-456",
            iteration=2,
            status="critiquing",
            details={"samples_complete": 3},
        )

        assert count == 1
        call_args = mock_manager.broadcast_to_topic.call_args
        message = call_args[0][1]
        assert message["data"]["iteration"] == 2
        assert message["data"]["status"] == "critiquing"
        assert message["data"]["samples_complete"] == 3


@pytest.mark.asyncio
async def test_notify_session(notification_service):
    with patch("src.websocket.notifications.manager") as mock_manager:
        mock_manager.send_personal = AsyncMock(return_value=True)

        result = await notification_service.notify_session(
            "session-123",
            Notification(
                type=NotificationType.CHAT_MESSAGE,
                data={"content": "Hello!"},
            ),
        )

        assert result is True
        mock_manager.send_personal.assert_called_once()

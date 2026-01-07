"""Tests for WebSocket connection manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.websocket.manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect(manager, mock_websocket):
    await manager.connect(mock_websocket, "session-1", user_id="user-1")

    assert manager.connection_count == 1
    assert manager.is_connected("session-1")
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect(manager, mock_websocket):
    await manager.connect(mock_websocket, "session-1")
    await manager.disconnect("session-1")

    assert manager.connection_count == 0
    assert not manager.is_connected("session-1")


@pytest.mark.asyncio
async def test_send_personal(manager, mock_websocket):
    await manager.connect(mock_websocket, "session-1")

    result = await manager.send_personal("session-1", {"type": "test"})

    assert result is True
    mock_websocket.send_json.assert_called_once_with({"type": "test"})


@pytest.mark.asyncio
async def test_send_personal_not_connected(manager):
    result = await manager.send_personal("nonexistent", {"type": "test"})

    assert result is False


@pytest.mark.asyncio
async def test_subscribe_and_broadcast(manager, mock_websocket):
    ws2 = AsyncMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    await manager.connect(mock_websocket, "session-1")
    await manager.connect(ws2, "session-2")

    await manager.subscribe("session-1", "domain-123")
    await manager.subscribe("session-2", "domain-123")

    count = await manager.broadcast_to_topic("domain-123", {"type": "update"})

    assert count == 2
    mock_websocket.send_json.assert_called_with({"type": "update"})
    ws2.send_json.assert_called_with({"type": "update"})


@pytest.mark.asyncio
async def test_broadcast_excludes_sender(manager, mock_websocket):
    ws2 = AsyncMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    await manager.connect(mock_websocket, "session-1")
    await manager.connect(ws2, "session-2")

    await manager.subscribe("session-1", "topic")
    await manager.subscribe("session-2", "topic")

    count = await manager.broadcast_to_topic("topic", {"type": "update"}, exclude="session-1")

    assert count == 1
    mock_websocket.send_json.assert_not_called()
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_to_user(manager):
    ws1 = AsyncMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = AsyncMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    ws3 = AsyncMock()
    ws3.accept = AsyncMock()
    ws3.send_json = AsyncMock()

    await manager.connect(ws1, "session-1", user_id="user-1")
    await manager.connect(ws2, "session-2", user_id="user-1")
    await manager.connect(ws3, "session-3", user_id="user-2")

    count = await manager.broadcast_to_user("user-1", {"type": "notification"})

    assert count == 2
    ws1.send_json.assert_called_with({"type": "notification"})
    ws2.send_json.assert_called_with({"type": "notification"})
    ws3.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_unsubscribe(manager, mock_websocket):
    await manager.connect(mock_websocket, "session-1")
    await manager.subscribe("session-1", "topic")
    await manager.unsubscribe("session-1", "topic")

    count = await manager.broadcast_to_topic("topic", {"type": "test"})

    assert count == 0

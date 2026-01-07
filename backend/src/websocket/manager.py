"""WebSocket connection manager for handling multiple clients."""

from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket
import asyncio
import json


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    user_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # session_id -> ConnectionInfo
        self._connections: Dict[str, ConnectionInfo] = {}
        # topic -> set of session_ids subscribed to that topic
        self._subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections[session_id] = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
            )

    async def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if session_id in self._connections:
                info = self._connections[session_id]
                # Remove from all subscriptions
                for topic in info.subscriptions:
                    if topic in self._subscriptions:
                        self._subscriptions[topic].discard(session_id)
                del self._connections[session_id]

    async def subscribe(self, session_id: str, topic: str) -> None:
        """Subscribe a connection to a topic for broadcasts."""
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].subscriptions.add(topic)
                if topic not in self._subscriptions:
                    self._subscriptions[topic] = set()
                self._subscriptions[topic].add(session_id)

    async def unsubscribe(self, session_id: str, topic: str) -> None:
        """Unsubscribe a connection from a topic."""
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].subscriptions.discard(topic)
            if topic in self._subscriptions:
                self._subscriptions[topic].discard(session_id)

    async def send_personal(
        self,
        session_id: str,
        message: dict,
    ) -> bool:
        """Send a message to a specific connection."""
        async with self._lock:
            if session_id not in self._connections:
                return False
            try:
                await self._connections[session_id].websocket.send_json(message)
                return True
            except Exception:
                return False

    async def broadcast_to_topic(
        self,
        topic: str,
        message: dict,
        exclude: Optional[str] = None,
    ) -> int:
        """Broadcast a message to all connections subscribed to a topic."""
        sent_count = 0
        async with self._lock:
            if topic not in self._subscriptions:
                return 0

            for session_id in list(self._subscriptions[topic]):
                if exclude and session_id == exclude:
                    continue
                if session_id in self._connections:
                    try:
                        await self._connections[session_id].websocket.send_json(message)
                        sent_count += 1
                    except Exception:
                        # Connection may be broken, will be cleaned up on next interaction
                        pass

        return sent_count

    async def broadcast_to_user(
        self,
        user_id: str,
        message: dict,
    ) -> int:
        """Broadcast a message to all connections for a specific user."""
        sent_count = 0
        async with self._lock:
            for session_id, info in self._connections.items():
                if info.user_id == user_id:
                    try:
                        await info.websocket.send_json(message)
                        sent_count += 1
                    except Exception:
                        pass
        return sent_count

    async def broadcast_all(
        self,
        message: dict,
        exclude: Optional[str] = None,
    ) -> int:
        """Broadcast a message to all connected clients."""
        sent_count = 0
        async with self._lock:
            for session_id, info in self._connections.items():
                if exclude and session_id == exclude:
                    continue
                try:
                    await info.websocket.send_json(message)
                    sent_count += 1
                except Exception:
                    pass
        return sent_count

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    def is_connected(self, session_id: str) -> bool:
        """Check if a session is connected."""
        return session_id in self._connections


# Global connection manager instance
manager = ConnectionManager()

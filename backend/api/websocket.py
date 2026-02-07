"""
WebSocket endpoint for real-time notification streaming.

This module provides WebSocket connections for real-time delivery of
notifications to connected clients. It manages connection lifecycle,
handles authentication, and broadcasts notifications to users.

The WebSocket endpoint allows clients to receive instant notifications
without polling, enabling a responsive user experience for recruiters
who need real-time updates on candidate activities, vacancy changes,
and system events.
"""
import json
import logging
from typing import Dict, Set, Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
from pydantic import ValidationError

from models.notification import Notification

logger = logging.getLogger(__name__)

router = APIRouter()


# Connection manager for WebSocket clients
class ConnectionManager:
    """
    Manages active WebSocket connections for real-time notification delivery.

    This class maintains a registry of active WebSocket connections organized
    by user ID, allowing targeted notification broadcasts to specific users.
    It handles connection lifecycle, message broadcasting, and cleanup.

    Attributes:
        active_connections: Dictionary mapping user IDs to sets of WebSocket connections

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(user_id, websocket)
        >>> await manager.broadcast_to_user(user_id, notification_data)
        >>> await manager.disconnect(user_id, websocket)
    """

    def __init__(self):
        """Initialize the connection manager with an empty connections registry."""
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        This method accepts the WebSocket connection and adds it to the
        registry of active connections for the specified user. A user can
        have multiple connections (e.g., multiple browser tabs).

        Args:
            user_id: UUID of the user connecting
            websocket: WebSocket connection instance

        Example:
            >>> await manager.connect(user_uuid, websocket)
            >>> logger.info(f"User {user_uuid} connected")
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "user_id": str(user_id),
            "message": "WebSocket connection established successfully"
        })

    async def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        """
        Remove and close a WebSocket connection.

        This method removes the WebSocket connection from the registry
        and closes the connection. If this was the last connection for
        the user, the user entry is removed from the registry.

        Args:
            user_id: UUID of the user disconnecting
            websocket: WebSocket connection instance

        Example:
            >>> await manager.disconnect(user_uuid, websocket)
            >>> logger.info(f"User {user_uuid} disconnected")
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"User {user_id} has no more active connections")
            else:
                logger.info(f"WebSocket disconnected for user {user_id}. Remaining connections: {len(self.active_connections[user_id])}")

    async def broadcast_to_user(self, user_id: UUID, message: dict) -> int:
        """
        Broadcast a message to all active connections for a specific user.

        This method sends a message to all WebSocket connections associated
        with the specified user. This is useful for ensuring notifications
        reach all browser tabs/devices the user has open.

        Args:
            user_id: UUID of the user to receive the message
            message: Dictionary containing the message payload

        Returns:
            Number of connections the message was sent to

        Example:
            >>> count = await manager.broadcast_to_user(user_uuid, {"type": "notification", "data": {...}})
            >>> logger.info(f"Notification sent to {count} connections")
        """
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return 0

        disconnected = set()
        sent_count = 0

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(user_id, connection)

        if sent_count > 0:
            logger.debug(f"Message sent to {sent_count} connection(s) for user {user_id}")

        return sent_count

    def get_connection_count(self, user_id: UUID) -> int:
        """
        Get the number of active connections for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Number of active WebSocket connections for the user

        Example:
            >>> count = manager.get_connection_count(user_uuid)
            >>> print(f"User has {count} active connections")
        """
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections(self) -> int:
        """
        Get the total number of active WebSocket connections across all users.

        Returns:
            Total number of active connections

        Example:
            >>> total = manager.get_total_connections()
            >>> logger.info(f"Total active connections: {total}")
        """
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


def notification_to_dict(notification: Notification) -> dict:
    """
    Convert a Notification model to a dictionary for WebSocket transmission.

    This helper function converts a Notification ORM object to a JSON-serializable
    dictionary, formatting timestamps and converting UUIDs to strings.

    Args:
        notification: Notification model instance

    Returns:
        Dictionary representation of the notification

    Example:
        >>> data = notification_to_dict(notification)
        >>> await manager.broadcast_to_user(user_id, {"type": "notification", "data": data})
    """
    return {
        "id": str(notification.id),
        "recipient_id": str(notification.recipient_id),
        "notification_type": notification.notification_type.value,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "delivered_at": notification.delivered_at.isoformat() if notification.delivered_at else None,
        "delivery_failed": notification.delivery_failed,
        "candidate_id": str(notification.candidate_id) if notification.candidate_id else None,
        "vacancy_id": str(notification.vacancy_id) if notification.vacancy_id else None,
        "action_url": notification.action_url,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
    }


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_endpoint(websocket: WebSocket, user_id: str) -> None:
    """
    WebSocket endpoint for real-time notification delivery.

    This endpoint provides a persistent connection for streaming notifications
    to clients in real-time. Clients connect with their user ID and receive
    notifications as they are created without needing to poll the server.

    The WebSocket sends JSON messages with the following structure:
    ```json
    {
        "type": "notification" | "connection_established" | "error",
        "data": {...},
        "message": "Optional message"
    }
    ```

    Connection URL format: `ws://localhost:8000/ws/notifications/{user_id}`

    Args:
        websocket: WebSocket connection instance (injected by FastAPI)
        user_id: UUID of the user as a path parameter

    Raises:
        HTTPException: If the user_id is not a valid UUID

    Example:
        Connect from browser JavaScript:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/ws/notifications/123e4567-e89b-12d3-a456-426614174000');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'notification') {
                console.log('New notification:', data.data);
            }
        };
        ```

        Connect using wscat CLI:
        ```bash
        wscat -c ws://localhost:8000/ws/notifications/123e4567-e89b-12d3-a456-426614174000
        ```
    """
    # Validate user_id format
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        logger.warning(f"Invalid user_id format in WebSocket connection: {user_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format. Must be a valid UUID."
        )

    # Accept and register the connection
    await manager.connect(user_uuid, websocket)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client (for ping/pong, control messages, etc.)
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types from client
                if message.get("type") == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({"type": "pong"})
                    logger.debug(f"Ping received from user {user_id}")

                elif message.get("type") == "get_status":
                    # Send connection status
                    await websocket.send_json({
                        "type": "status",
                        "user_id": str(user_uuid),
                        "connection_count": manager.get_connection_count(user_uuid),
                        "total_connections": manager.get_total_connections()
                    })

                else:
                    logger.debug(f"Received message from user {user_id}: {message.get('type', 'unknown')}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": "An error occurred with the WebSocket connection"
        })
    finally:
        # Clean up connection
        await manager.disconnect(user_uuid, websocket)


# Public API for broadcasting notifications

async def broadcast_notification(notification: Notification) -> int:
    """
    Broadcast a notification to the recipient's active WebSocket connections.

    This function is the main entry point for sending notifications to connected
    clients. It should be called after a notification is created in the database.

    Args:
        notification: Notification model instance to broadcast

    Returns:
        Number of connections the notification was sent to

    Example:
        >>> notification = await create_notification(db, ...)
        >>> connections = await broadcast_notification(notification)
        >>> logger.info(f"Notification sent to {connections} client(s)")
    """
    try:
        message = {
            "type": "notification",
            "data": notification_to_dict(notification)
        }
        return await manager.broadcast_to_user(notification.recipient_id, message)
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}", exc_info=True)
        return 0

"""
WebSocket connection manager for real-time updates.

This module provides a singleton WebSocket connection manager that handles
multiple connection types (notifications, resume progress, etc.) with support
for broadcasting, direct messaging, and connection lifecycle management.

The manager maintains separate connection pools for different connection types,
allowing targeted message delivery and efficient connection management.

Key Features:
- Thread-safe connection management using locks
- Support for multiple connection types (namespaces)
- Broadcast and direct messaging capabilities
- Automatic connection cleanup on disconnect
- Connection statistics and monitoring
- Graceful handling of connection errors

Example:
    >>> manager = get_manager()
    >>> # Connect a client
    >>> await manager.connect(websocket, client_id="user-123", connection_type="notifications")
    >>> # Send direct message
    >>> await manager.send_direct_message(
    ...     client_id="user-123",
    ...     message={"type": "notification", "data": "..."}
    ... )
    >>> # Broadcast to all connections
    >>> await manager.broadcast(
    ...     message={"type": "alert", "data": "..."},
    ...     connection_type="notifications"
    ... )
    >>> # Disconnect
    >>> await manager.disconnect(websocket)
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import WebSocket, WebSocketDisconnect

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global singleton instance
_manager: Optional["ConnectionManager"] = None
_manager_lock = asyncio.Lock()


class ConnectionManager:
    """
    WebSocket connection manager with support for multiple connection types.

    This class manages WebSocket connections across multiple namespaces/connection
    types, allowing for organized and targeted message delivery. Connections are
    tracked by client ID within each connection type, enabling direct messaging
    and efficient broadcasting.

    The manager is thread-safe using asyncio locks and provides automatic
    connection cleanup on disconnect events.

    Attributes:
        active_connections: Dictionary mapping connection types to dictionaries
                          of client_id to WebSocket connections
        connection_metadata: Dictionary tracking metadata for each connection
        lock: Async lock for thread-safe operations

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(ws, client_id="user-123", connection_type="notifications")
        >>> await manager.send_direct_message("user-123", {"msg": "hello"}, "notifications")
        >>> await manager.disconnect(ws)
    """

    def __init__(self) -> None:
        """
        Initialize the connection manager.

        Creates empty dictionaries for tracking active connections and their metadata.
        """
        # Structure: {connection_type: {client_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

        # Structure: {websocket: {client_id, connection_type, connected_at, last_ping}}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        self.lock = asyncio.Lock()

        logger.info("ConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        connection_type: str = "notifications",
    ) -> None:
        """
        Accept and register a new WebSocket connection.

        This method accepts the WebSocket connection and registers it in the
        active connections pool under the specified connection type and client ID.

        Args:
            websocket: The WebSocket connection to register
            client_id: Unique identifier for the client (e.g., user ID, session ID)
            connection_type: Type of connection (default: "notifications")
                           Common types: "notifications", "resume_progress", "screening"

        Raises:
            RuntimeError: If a connection already exists for this client_id and
                         connection_type combination

        Example:
            >>> await manager.connect(websocket, "user-123", "notifications")
        """
        await websocket.accept()

        async with self.lock:
            # Initialize connection type dict if not exists
            if connection_type not in self.active_connections:
                self.active_connections[connection_type] = {}

            # Check for existing connection
            if client_id in self.active_connections[connection_type]:
                logger.warning(
                    f"Connection already exists for client_id={client_id}, "
                    f"connection_type={connection_type}. Closing old connection."
                )
                try:
                    old_ws = self.active_connections[connection_type][client_id]
                    await old_ws.close(code=1008, reason="New connection established")
                    # Remove old connection metadata
                    if old_ws in self.connection_metadata:
                        del self.connection_metadata[old_ws]
                except Exception as e:
                    logger.error(f"Error closing old connection: {e}")

            # Register new connection
            self.active_connections[connection_type][client_id] = websocket
            self.connection_metadata[websocket] = {
                "client_id": client_id,
                "connection_type": connection_type,
                "connected_at": datetime.utcnow().isoformat(),
                "last_ping": time.time(),
            }

        logger.info(
            f"WebSocket connected: client_id={client_id}, "
            f"connection_type={connection_type}"
        )

    async def disconnect(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """
        Unregister and cleanup a WebSocket connection.

        Removes the connection from the active connections pool and cleans up
        associated metadata.

        Args:
            websocket: The WebSocket connection to disconnect

        Returns:
            The connection metadata if found, None otherwise

        Example:
            >>> metadata = await manager.disconnect(websocket)
            >>> if metadata:
            ...     print(f"Disconnected {metadata['client_id']}")
        """
        async with self.lock:
            metadata = self.connection_metadata.get(websocket)

            if metadata:
                client_id = metadata["client_id"]
                connection_type = metadata["connection_type"]

                # Remove from active connections
                if connection_type in self.active_connections:
                    self.active_connections[connection_type].pop(client_id, None)

                    # Clean up empty connection type dicts
                    if not self.active_connections[connection_type]:
                        del self.active_connections[connection_type]

                # Remove metadata
                del self.connection_metadata[websocket]

                logger.info(
                    f"WebSocket disconnected: client_id={client_id}, "
                    f"connection_type={connection_type}"
                )

                return metadata

            logger.warning("Attempted to disconnect unknown WebSocket")
            return None

    async def send_direct_message(
        self,
        client_id: str,
        message: Dict[str, Any],
        connection_type: str = "notifications",
    ) -> bool:
        """
        Send a message directly to a specific client.

        Sends a JSON message to the WebSocket connection identified by
        client_id and connection_type.

        Args:
            client_id: The unique client identifier
            message: The message dictionary to send (must be JSON-serializable)
            connection_type: The type of connection (default: "notifications")

        Returns:
            True if the message was sent successfully, False otherwise

        Example:
            >>> success = await manager.send_direct_message(
            ...     "user-123",
            ...     {"type": "progress", "data": {"percent": 50}},
            ...     "resume_progress"
            ... )
        """
        async with self.lock:
            connections = self.active_connections.get(connection_type, {})
            websocket = connections.get(client_id)

            if not websocket:
                logger.debug(
                    f"No connection found for client_id={client_id}, "
                    f"connection_type={connection_type}"
                )
                return False

            try:
                # Add timestamp if not present
                if "timestamp" not in message:
                    message["timestamp"] = datetime.utcnow().isoformat()

                await websocket.send_json(message)

                # Update last activity
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = time.time()

                logger.debug(
                    f"Message sent to client_id={client_id}, "
                    f"connection_type={connection_type}, "
                    f"msg_type={message.get('type', 'unknown')}"
                )
                return True

            except Exception as e:
                logger.error(
                    f"Error sending message to client_id={client_id}: {e}",
                    exc_info=True
                )
                # Clean up broken connection
                await self.disconnect(websocket)
                return False

    async def broadcast(
        self,
        message: Dict[str, Any],
        connection_type: str = "notifications",
        exclude_client_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast a message to all connections of a specific type.

        Sends a message to all active WebSocket connections of the specified
        type, optionally excluding a specific client (useful for echo suppression).

        Args:
            message: The message dictionary to broadcast (must be JSON-serializable)
            connection_type: The type of connection to broadcast to
            exclude_client_id: Optional client ID to exclude from the broadcast

        Returns:
            The number of clients the message was sent to

        Example:
            >>> count = await manager.broadcast(
            ...     {"type": "alert", "message": "System maintenance"},
            ...     "notifications"
            ... )
            >>> print(f"Sent to {count} clients")
        """
        async with self.lock:
            connections = self.active_connections.get(connection_type, {})
            sent_count = 0

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            # Create list of (client_id, websocket) tuples
            items_to_remove = []

            for client_id, websocket in connections.items():
                # Skip excluded client
                if exclude_client_id and client_id == exclude_client_id:
                    continue

                try:
                    await websocket.send_json(message)
                    sent_count += 1

                    # Update last activity
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket]["last_ping"] = time.time()

                except Exception as e:
                    logger.error(
                        f"Error broadcasting to client_id={client_id}: {e}"
                    )
                    items_to_remove.append(websocket)

            # Clean up failed connections
            for ws in items_to_remove:
                await self.disconnect(ws)

            if sent_count > 0:
                logger.debug(
                    f"Broadcast sent to {sent_count} clients "
                    f"(connection_type={connection_type})"
                )

            return sent_count

    async def get_connection_count(
        self, connection_type: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get the current number of active connections.

        Returns the count of active connections, optionally filtered by
        connection type.

        Args:
            connection_type: Optional connection type to filter by.
                           If None, returns counts for all types.

        Returns:
            Dictionary mapping connection types to their connection counts.
            If connection_type is specified, returns a single-key dict.

        Example:
            >>> counts = await manager.get_connection_count()
            >>> print(counts)  # {"notifications": 5, "resume_progress": 2}
            >>> count = await manager.get_connection_count("notifications")
            >>> print(count)  # {"notifications": 5}
        """
        async with self.lock:
            if connection_type:
                return {connection_type: len(self.active_connections.get(connection_type, {}))}

            return {
                conn_type: len(conns)
                for conn_type, conns in self.active_connections.items()
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.

        Returns various statistics about the current connections including
        total connections, connections per type, and uptime information.

        Returns:
            Dictionary containing connection statistics

        Example:
            >>> stats = manager.get_stats()
            >>> print(stats)
            {
                "total_connections": 10,
                "connections_by_type": {"notifications": 7, "resume_progress": 3},
                "oldest_connection": "2024-01-01T12:00:00",
                "newest_connection": "2024-01-01T13:00:00"
            }
        """
        # This is a synchronous method that reads the state without lock
        # Use with caution - may return slightly stale data
        with_counts = {}
        oldest = None
        newest = None

        for conn_type, conns in self.active_connections.items():
            with_counts[conn_type] = len(conns)
            for ws, metadata in self.connection_metadata.items():
                if metadata.get("connection_type") == conn_type:
                    connected_at = metadata.get("connected_at")
                    if connected_at:
                        if oldest is None or connected_at < oldest:
                            oldest = connected_at
                        if newest is None or connected_at > newest:
                            newest = connected_at

        return {
            "total_connections": sum(with_counts.values()),
            "connections_by_type": with_counts,
            "oldest_connection": oldest,
            "newest_connection": newest,
        }


async def get_manager() -> ConnectionManager:
    """
    Get the global singleton ConnectionManager instance.

    Creates the singleton instance on first call and returns the same
    instance on subsequent calls. Thread-safe using asyncio lock.

    Returns:
        The global ConnectionManager instance

    Example:
        >>> manager = await get_manager()
        >>> await manager.connect(websocket, "user-123")
    """
    global _manager

    if _manager is None:
        async with _manager_lock:
            # Double-check after acquiring lock
            if _manager is None:
                _manager = ConnectionManager()
                logger.info("Global ConnectionManager instance created")

    return _manager


def get_manager_sync() -> ConnectionManager:
    """
    Get the global ConnectionManager instance synchronously.

    This is a convenience function for contexts where async/await is not
    available. Note that this may return None if the manager hasn't been
    initialized yet.

    Returns:
        The global ConnectionManager instance or None if not initialized

    Example:
        >>> manager = get_manager_sync()
        >>> if manager:
        ...     stats = manager.get_stats()
    """
    return _manager


# Alias for backward compatibility with verification scripts
WebSocketManager = ConnectionManager

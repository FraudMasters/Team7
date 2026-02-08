"""
WebSocket support for real-time updates.

This package provides WebSocket functionality for the resume analysis system,
including connection management and real-time progress updates.
"""

from websocket.manager import get_manager, ConnectionManager, WebSocketManager
from websocket.resume_progress import (
    broadcast_resume_progress,
    send_resume_progress,
    ResumeProgressStage,
    ProgressMessage,
)

__all__ = [
    "get_manager",
    "ConnectionManager",
    "WebSocketManager",
    "broadcast_resume_progress",
    "send_resume_progress",
    "ResumeProgressStage",
    "ProgressMessage",
]

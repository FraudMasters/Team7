"""
Common enums and types shared across services
"""
import enum


class StatusType(str, enum.Enum):
    """Common status types for entities across services"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PriorityLevel(str, enum.Enum):
    """Priority levels for tasks and jobs"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

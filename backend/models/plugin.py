"""
Plugin models for plugin marketplace and installation tracking
"""
import enum
from uuid import UUID
from typing import Optional, List

from sqlalchemy import ForeignKey, JSON, String, Boolean, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class PluginCategory(str, enum.Enum):
    """Categories of plugins available in the marketplace"""

    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    NOTIFICATION = "notification"
    EXPORT = "export"
    IMPORT = "import"
    WORKFLOW = "workflow"
    CUSTOM_UI = "custom_ui"
    DATA_SOURCE = "data_source"
    AI_ENHANCEMENT = "ai_enhancement"
    OTHER = "other"


class PluginStatus(str, enum.Enum):
    """Status of a plugin in the marketplace"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Plugin(Base, UUIDMixin, TimestampMixin):
    """
    Plugin model for marketplace plugins

    This model enables the plugin marketplace by storing plugin metadata,
    allowing users to discover, install, and manage plugins.

    Attributes:
        id: UUID primary key
        name: Plugin name (unique)
        slug: URL-friendly slug for the plugin (unique)
        version: Current version of the plugin
        author: Plugin author/developer name
        author_email: Contact email for the plugin author
        description: Short description of the plugin
        long_description: Detailed description of the plugin
        category: Plugin category for filtering
        tags: JSON array of tags for searchability
        logo_url: Optional URL to plugin logo/image
        manifest_url: URL to the plugin manifest JSON
        download_url: URL to download the plugin package
        homepage_url: Optional URL to plugin homepage
        repository_url: Optional URL to plugin source repository
        documentation_url: Optional URL to plugin documentation
        is_official: Whether this is an official plugin
        status: Approval status of the plugin
        is_active: Whether the plugin is currently active/available
        install_count: Number of times the plugin has been installed
        rating_count: Number of ratings received
        average_rating: Average rating (0-5)
        latest_version: Latest available version
        min_agenthr_version: Minimum AgentHR version required
        max_agenthr_version: Maximum AgentHR version supported (optional)
        permissions: JSON array of required permissions
        dependencies: JSON object with plugin dependencies
        created_at: Timestamp when plugin was created (inherited)
        updated_at: Timestamp when plugin was last updated (inherited)
    """

    __tablename__ = "plugins"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[PluginCategory] = mapped_column(String(50), nullable=False, index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    manifest_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    download_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    documentation_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    status: Mapped[PluginStatus] = mapped_column(
        String(50), nullable=False, default=PluginStatus.PENDING_REVIEW, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    install_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latest_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    min_agenthr_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_agenthr_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    dependencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Plugin(id={self.id}, name={self.name}, version={self.version}, category={self.category})>"

    def is_compatible_with(self, agenthr_version: str) -> bool:
        """
        Check if plugin is compatible with given AgentHR version

        Args:
            agenthr_version: Version string to check compatibility against

        Returns:
            True if compatible, False otherwise
        """
        from packaging import version as pkg_version

        if self.min_agenthr_version and pkg_version.parse(
            agenthr_version
        ) < pkg_version.parse(self.min_agenthr_version):
            return False
        if self.max_agenthr_version and pkg_version.parse(
            agenthr_version
        ) > pkg_version.parse(self.max_agenthr_version):
            return False
        return True


class PluginInstallation(Base, UUIDMixin, TimestampMixin):
    """
    PluginInstallation model for tracking plugin installations

    This model enables tracking which plugins are installed by which recruiters,
    along with configuration and usage information.

    Attributes:
        id: UUID primary key
        plugin_id: Foreign key to Plugin
        recruiter_id: Foreign key to Recruiter who installed the plugin
        version: Version of the installed plugin
        config: JSON object with plugin-specific configuration
        is_enabled: Whether the plugin is currently enabled
        install_notes: Optional notes about the installation
        installed_at: Timestamp when the plugin was installed
        last_used_at: Timestamp when the plugin was last used
        created_at: Timestamp when installation record was created (inherited)
        updated_at: Timestamp when installation record was last updated (inherited)
    """

    __tablename__ = "plugin_installations"

    plugin_id: Mapped[UUID] = mapped_column(
        ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    install_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    installed_at: Mapped[str] = mapped_column(
        String(50), nullable=False, default="now()"
    )
    last_used_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<PluginInstallation(id={self.id}, plugin_id={self.plugin_id}, version={self.version}, enabled={self.is_enabled})>"

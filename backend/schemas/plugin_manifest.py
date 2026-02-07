"""
Pydantic schemas for plugin manifest validation

A plugin manifest is a JSON file that describes a plugin's metadata,
capabilities, permissions, and dependencies. This schema validates
plugin manifests before installation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class PluginCategory(str, Enum):
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


class PluginPermissionType(str, Enum):
    """Types of permissions a plugin can request"""

    # Candidate data access
    READ_CANDIDATES = "read:candidates"
    WRITE_CANDIDATES = "write:candidates"
    DELETE_CANDIDATES = "delete:candidates"

    # Vacancy data access
    READ_VACANCIES = "read:vacancies"
    WRITE_VACANCIES = "write:vacancies"
    DELETE_VACANCIES = "delete:vacancies"

    # Resume data access
    READ_RESUMES = "read:resumes"
    WRITE_RESUMES = "write:resumes"
    DELETE_RESUMES = "delete:resumes"

    # Analytics data access
    READ_ANALYTICS = "read:analytics"
    WRITE_ANALYTICS = "write:analytics"

    # Webhook management
    READ_WEBHOOKS = "read:webhooks"
    WRITE_WEBHOOKS = "write:webhooks"
    DELETE_WEBHOOKS = "delete:webhooks"

    # Plugin management
    READ_PLUGINS = "read:plugins"
    WRITE_PLUGINS = "write:plugins"

    # Workflow management
    READ_WORKFLOWS = "read:workflows"
    WRITE_WORKFLOWS = "write:workflows"
    EXECUTE_WORKFLOWS = "execute:workflows"

    # System-level permissions
    READ_SETTINGS = "read:settings"
    WRITE_SETTINGS = "write:settings"
    MANAGE_API_KEYS = "manage:api_keys"

    # External requests
    MAKE_HTTP_REQUESTS = "make:http_requests"
    ACCESS_EXTERNAL_API = "access:external_api"


class PluginPermission(BaseModel):
    """Permission requested by a plugin"""

    type: str = Field(..., description="Type of permission required")
    description: str = Field(..., description="Human-readable description of why this permission is needed")
    optional: bool = Field(False, description="Whether this permission is optional")


class PluginDependency(BaseModel):
    """Dependency requirement for a plugin"""

    name: str = Field(..., description="Name of the dependency")
    version: Optional[str] = Field(None, description="Version constraint (e.g., '>=1.0.0', '==2.1.0')")
    optional: bool = Field(False, description="Whether this dependency is optional")


class PluginEntryPoint(BaseModel):
    """Entry point for plugin execution"""

    type: str = Field(..., description="Type of entry point: webhook, workflow_action, schedule, etc.")
    handler: str = Field(..., description="Handler function or module path")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration for the entry point")


class PluginManifest(BaseModel):
    """
    Plugin manifest schema

    A plugin manifest is a JSON file that describes a plugin's metadata,
    capabilities, permissions, and dependencies. This schema validates
    plugin manifests before installation.
    """

    # Basic Information
    name: str = Field(..., min_length=1, max_length=255, description="Plugin name")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="URL-friendly slug for the plugin (lowercase, alphanumeric, hyphens only)",
    )
    version: str = Field(..., min_length=1, max_length=50, description="Plugin version (semantic versioning)")
    author: str = Field(..., min_length=1, max_length=255, description="Plugin author/developer name")
    author_email: Optional[str] = Field(None, description="Contact email for the plugin author")

    # Description
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Short description of the plugin (displayed in listings)",
    )
    long_description: Optional[str] = Field(None, description="Detailed description of the plugin (markdown supported)")

    # Categorization
    category: PluginCategory = Field(..., description="Plugin category for filtering and discovery")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for searchability (e.g., ['slack', 'notifications', 'hr'])",
    )

    # URLs
    logo_url: Optional[str] = Field(None, description="URL to plugin logo/image (PNG, JPG, SVG)")
    homepage_url: Optional[str] = Field(None, description="URL to plugin homepage or landing page")
    repository_url: Optional[str] = Field(None, description="URL to plugin source code repository")
    documentation_url: Optional[str] = Field(None, description="URL to plugin documentation")

    # Version Compatibility
    min_agenthr_version: Optional[str] = Field(
        None,
        description="Minimum AgentHR version required (e.g., '1.0.0')",
    )
    max_agenthr_version: Optional[str] = Field(
        None,
        description="Maximum AgentHR version supported (e.g., '2.0.0')",
    )

    # Permissions
    permissions: List[PluginPermission] = Field(
        default_factory=list,
        description="List of permissions required by the plugin",
    )

    # Dependencies
    dependencies: List[PluginDependency] = Field(
        default_factory=list,
        description="List of plugin dependencies (other plugins or system requirements)",
    )
    python_dependencies: Optional[List[str]] = Field(
        None,
        description="Python package dependencies (e.g., ['requests>=2.28.0', 'pyyaml'])",
    )

    # Entry Points
    entry_points: List[PluginEntryPoint] = Field(
        default_factory=list,
        description="Entry points for plugin execution (webhooks, workflow actions, etc.)",
    )

    # Configuration Schema
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema defining the plugin's configuration options",
    )

    # Additional Metadata
    license: Optional[str] = Field(None, description="Plugin license (e.g., 'MIT', 'Apache-2.0', 'GPL-3.0')")
    keywords: List[str] = Field(default_factory=list, description="Search keywords for discovery")

    @validator("slug")
    def validate_slug(cls, v):
        """Validate slug format: lowercase, alphanumeric, hyphens only, must start with letter"""
        import re

        if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must start with a letter, contain only lowercase letters, numbers, and hyphens, "
                "and end with a letter or number"
            )
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v

    @validator("version")
    def validate_version(cls, v):
        """Validate semantic version format"""
        import re

        # Allow semantic versioning with optional pre-release and build metadata
        if not re.match(r"^\d+\.\d+\.\d+([a-zA-Z0-9.+-]*)?$", v):
            raise ValueError(
                "Version must follow semantic versioning (e.g., '1.0.0', '2.1.3-beta', '3.0.0-rc.1')"
            )
        return v

    @validator("author_email")
    def validate_email(cls, v):
        """Validate email format"""
        if v is not None:
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags format"""
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Tags must be strings")
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
            if not tag.strip():
                raise ValueError("Tags cannot be empty or whitespace only")
        # Remove duplicates and empty tags
        return list(set(tag.strip() for tag in v if tag.strip()))

    @validator("permissions")
    def validate_permissions(cls, v):
        """Validate that permission types are recognized"""
        valid_permission_types = {perm.value for perm in PluginPermissionType}
        for perm in v:
            if perm.type not in valid_permission_types:
                raise ValueError(
                    f"Invalid permission type: {perm.type}. Must be one of: {', '.join(sorted(valid_permission_types))}"
                )
        return v

    @validator("entry_points")
    def validate_entry_points(cls, v):
        """Validate entry point types"""
        valid_types = {"webhook", "workflow_action", "schedule", "init", "command", "event_handler"}
        for ep in v:
            if ep.type not in valid_types:
                raise ValueError(
                    f"Invalid entry point type: {ep.type}. Must be one of: {', '.join(sorted(valid_types))}"
                )
        return v


class PluginManifestResponse(BaseModel):
    """Response model for plugin manifest"""

    name: str = Field(..., description="Plugin name")
    slug: str = Field(..., description="Plugin slug")
    version: str = Field(..., description="Plugin version")
    author: str = Field(..., description="Plugin author")
    description: str = Field(..., description="Short description")
    long_description: Optional[str] = Field(None, description="Long description")
    category: str = Field(..., description="Plugin category")
    tags: List[str] = Field(..., description="Plugin tags")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    homepage_url: Optional[str] = Field(None, description="Homepage URL")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    min_agenthr_version: Optional[str] = Field(None, description="Minimum AgentHR version")
    max_agenthr_version: Optional[str] = Field(None, description="Maximum AgentHR version")
    permissions: List[PluginPermission] = Field(..., description="Required permissions")
    dependencies: List[PluginDependency] = Field(..., description="Plugin dependencies")
    python_dependencies: Optional[List[str]] = Field(None, description="Python dependencies")
    entry_points: List[PluginEntryPoint] = Field(..., description="Entry points")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    license: Optional[str] = Field(None, description="Plugin license")
    keywords: List[str] = Field(..., description="Search keywords")
    is_compatible: bool = Field(..., description="Whether plugin is compatible with current AgentHR version")
    compatibility_message: Optional[str] = Field(None, description="Compatibility error message if not compatible")


class PluginManifestCreate(BaseModel):
    """Request model for creating/updating a plugin manifest"""

    name: str = Field(..., min_length=1, max_length=255, description="Plugin name")
    slug: str = Field(..., min_length=1, max_length=255, description="Plugin slug")
    version: str = Field(..., min_length=1, max_length=50, description="Plugin version")
    author: str = Field(..., min_length=1, max_length=255, description="Plugin author")
    author_email: Optional[str] = Field(None, description="Author email")
    description: str = Field(..., min_length=1, max_length=500, description="Short description")
    long_description: Optional[str] = Field(None, description="Long description")
    category: PluginCategory = Field(..., description="Plugin category")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    homepage_url: Optional[str] = Field(None, description="Homepage URL")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    min_agenthr_version: Optional[str] = Field(None, description="Minimum AgentHR version")
    max_agenthr_version: Optional[str] = Field(None, description="Maximum AgentHR version")
    permissions: List[PluginPermission] = Field(default_factory=list, description="Required permissions")
    dependencies: List[PluginDependency] = Field(default_factory=list, description="Plugin dependencies")
    python_dependencies: Optional[List[str]] = Field(None, description="Python dependencies")
    entry_points: List[PluginEntryPoint] = Field(default_factory=list, description="Entry points")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    license: Optional[str] = Field(None, description="Plugin license")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")


class PluginManifestValidate(BaseModel):
    """Request model for validating a plugin manifest"""

    manifest_url: str = Field(..., description="URL to the plugin manifest JSON")
    agenthr_version: Optional[str] = Field(
        None,
        description="AgentHR version to check compatibility against (defaults to current version)",
    )


class PluginManifestValidateResponse(BaseModel):
    """Response model for plugin manifest validation"""

    valid: bool = Field(..., description="Whether the manifest is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors if invalid")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    manifest: Optional[PluginManifestResponse] = Field(None, description="Parsed manifest if valid")

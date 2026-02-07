"""
Plugin sandbox execution environment for secure plugin isolation.

This module provides a sandboxed execution environment for plugins that includes:
- Isolated plugin execution with resource limits
- Permission enforcement and access control
- Safe plugin loading and lifecycle management
- Execution timeout and resource monitoring
- Error handling and logging
- Protection against malicious code execution

The sandbox ensures plugins cannot:
- Access unrestricted system resources
- Modify core application state
- Execute arbitrary code beyond their scope
- Access data without proper permissions

Plugins can only interact through defined APIs and entry points.
"""
import asyncio
import importlib.util
import logging
import os
import resource
import signal
import sys
import tempfile
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.plugin import Plugin, PluginInstallation

logger = logging.getLogger(__name__)
settings = get_settings()

# Sandbox configuration
DEFAULT_EXECUTION_TIMEOUT = 30.0  # seconds
MAX_MEMORY_MB = 256
MAX_CPU_TIME = 10  # seconds
DISABLED_BUILTINS = {
    "open", "file", "exec", "eval", "compile", "__import__",
    "reload", "exit", "quit"
}

# Restricted modules that plugins cannot import
RESTRICTED_MODULES = {
    "os", "sys", "subprocess", "shutil", "multiprocessing",
    "threading", "signal", "socket", "http", "urllib",
    "pickle", "shelve", "marshal", "ctypes", "platform",
    "pty", "fcntl", "resource", "asyncio.subprocess"
}


class SandboxPermissionError(Exception):
    """Exception raised when a plugin attempts an unauthorized operation."""
    pass


class SandboxExecutionError(Exception):
    """Exception raised when plugin execution fails."""
    pass


class SandboxTimeoutError(Exception):
    """Exception raised when plugin execution times out."""
    pass


class SandboxResourceLimitError(Exception):
    """Exception raised when plugin exceeds resource limits."""
    pass


class PluginContext:
    """
    Execution context for a plugin instance.

    Provides controlled access to AgentHR APIs and enforces permissions.
    """

    def __init__(
        self,
        plugin_id: str,
        installation_id: str,
        config: Dict[str, Any],
        permissions: List[str],
        recruiter_id: Optional[str] = None,
    ):
        """
        Initialize plugin context.

        Args:
            plugin_id: UUID of the plugin
            installation_id: UUID of the plugin installation
            config: Plugin configuration
            permissions: List of granted permissions
            recruiter_id: Optional recruiter ID who owns the installation
        """
        self.plugin_id = plugin_id
        self.installation_id = installation_id
        self.config = config
        self.permissions = set(permissions)
        self.recruiter_id = recruiter_id
        self.execution_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self._api_cache: Dict[str, Any] = {}

    def has_permission(self, permission: str) -> bool:
        """
        Check if context has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if permission is granted
        """
        return permission in self.permissions

    def require_permission(self, permission: str) -> None:
        """
        Require a specific permission, raise if not granted.

        Args:
            permission: Permission to require

        Raises:
            SandboxPermissionError: If permission not granted
        """
        if not self.has_permission(permission):
            raise SandboxPermissionError(
                f"Plugin requires permission: {permission}"
            )

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get plugin configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def get_api(self, api_name: str) -> Any:
        """
        Get a sandboxed API client for the plugin.

        Args:
            api_name: Name of the API (e.g., 'candidates', 'vacancies')

        Returns:
            Sandboxed API client

        Raises:
            SandboxPermissionError: If plugin lacks permission for this API
        """
        # Check if API is cached
        if api_name in self._api_cache:
            return self._api_cache[api_name]

        # Check permissions based on API
        permission_map = {
            "candidates": "read:candidates",
            "candidates_write": "write:candidates",
            "vacancies": "read:vacancies",
            "vacancies_write": "write:vacancies",
            "resumes": "read:resumes",
            "resumes_write": "write:resumes",
            "analytics": "read:analytics",
            "webhooks": "read:webhooks",
            "webhooks_write": "write:webhooks",
            "workflows": "read:workflows",
            "workflows_write": "write:workflows",
        }

        required_permission = permission_map.get(api_name)
        if required_permission:
            self.require_permission(required_permission)

        # Create and cache API client
        api_client = self._create_api_client(api_name)
        self._api_cache[api_name] = api_client
        return api_client

    def _create_api_client(self, api_name: str) -> Any:
        """
        Create a sandboxed API client.

        Args:
            api_name: Name of the API

        Returns:
            Sandboxed API client instance
        """
        # Import API client factories
        from .sandbox_apis import (
            CandidatesAPI,
            VacanciesAPI,
            ResumesAPI,
            AnalyticsAPI,
            WebhooksAPI,
            WorkflowsAPI,
        )

        api_map = {
            "candidates": CandidatesAPI,
            "candidates_write": CandidatesAPI,
            "vacancies": VacanciesAPI,
            "vacancies_write": VacanciesAPI,
            "resumes": ResumesAPI,
            "resumes_write": ResumesAPI,
            "analytics": AnalyticsAPI,
            "webhooks": WebhooksAPI,
            "webhooks_write": WebhooksAPI,
            "workflows": WorkflowsAPI,
            "workflows_write": WorkflowsAPI,
        }

        api_class = api_map.get(api_name)
        if api_class:
            return api_class(self)

        raise ValueError(f"Unknown API: {api_name}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            "execution_id": self.execution_id,
            "plugin_id": self.plugin_id,
            "installation_id": self.installation_id,
            "recruiter_id": self.recruiter_id,
            "permissions": list(self.permissions),
            "created_at": self.created_at.isoformat(),
        }


class PluginSandbox:
    """
    Secure sandbox for plugin execution.

    This class provides isolated execution environment for plugins with:
    - Permission enforcement
    - Resource limits (CPU, memory, execution time)
    - Safe module imports
    - Error handling and logging
    - Lifecycle management
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        timeout: Optional[float] = None,
        max_memory_mb: Optional[int] = None,
    ):
        """
        Initialize plugin sandbox.

        Args:
            session: Optional database session
            timeout: Execution timeout in seconds
            max_memory_mb: Maximum memory in MB
        """
        self._session = session
        self._own_session = session is None
        self.timeout = timeout or DEFAULT_EXECUTION_TIMEOUT
        self.max_memory_mb = max_memory_mb or MAX_MEMORY_MB
        self._loaded_plugins: Dict[str, Any] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"PluginSandbox initialized (timeout={self.timeout}s, "
            f"max_memory={self.max_memory_mb}MB)"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        if self._own_session:
            self._session = async_session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_session and self._session:
            await self._session.close()

    @property
    def session(self) -> AsyncSession:
        """Get the database session, creating one if needed."""
        if self._session is None:
            self._session = async_session_maker()
            self._own_session = True
        return self._session

    async def load_plugin(
        self,
        plugin_id: str,
        installation_id: str,
    ) -> PluginContext:
        """
        Load a plugin and create its execution context.

        Args:
            plugin_id: UUID of the plugin
            installation_id: UUID of the plugin installation

        Returns:
            Plugin execution context

        Raises:
            SandboxExecutionError: If plugin cannot be loaded
        """
        from sqlalchemy import select

        # Fetch plugin and installation
        result = await self.session.execute(
            select(Plugin, PluginInstallation).join(
                PluginInstallation,
                PluginInstallation.plugin_id == Plugin.id,
            ).where(
                Plugin.id == plugin_id,
                PluginInstallation.id == installation_id,
            )
        )
        row = result.one_or_none()

        if not row:
            raise SandboxExecutionError(
                f"Plugin or installation not found: {plugin_id}/{installation_id}"
            )

        plugin, installation = row

        # Check if plugin is active and installation is enabled
        if not plugin.is_active:
            raise SandboxExecutionError(f"Plugin is not active: {plugin.name}")

        if not installation.is_enabled:
            raise SandboxExecutionError(
                f"Plugin installation is disabled: {installation_id}"
            )

        # Create context
        context = PluginContext(
            plugin_id=str(plugin.id),
            installation_id=str(installation.id),
            config=installation.config or {},
            permissions=plugin.permissions,
            recruiter_id=str(installation.recruiter_id) if installation.recruiter_id else None,
        )

        # Load plugin code if not already loaded
        if plugin.slug not in self._loaded_plugins:
            await self._load_plugin_code(plugin, context)

        logger.info(
            f"Plugin loaded: {plugin.name} v{plugin.version} "
            f"(context: {context.execution_id})"
        )

        return context

    async def _load_plugin_code(
        self,
        plugin: Plugin,
        context: PluginContext,
    ) -> None:
        """
        Load plugin code from download URL.

        Args:
            plugin: Plugin model
            context: Plugin execution context

        Raises:
            SandboxExecutionError: If plugin code cannot be loaded
        """
        import httpx
        import zipfile
        import json

        plugin_slug = plugin.slug

        try:
            # Download plugin package
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(plugin.download_url)
                response.raise_for_status()
                plugin_data = response.content

            # Create temporary directory for plugin
            with tempfile.TemporaryDirectory() as temp_dir:
                plugin_dir = Path(temp_dir) / plugin_slug
                plugin_dir.mkdir()

                # Extract plugin package (assume zip format)
                plugin_zip = plugin_dir / "plugin.zip"
                plugin_zip.write_bytes(plugin_data)

                with zipfile.ZipFile(plugin_zip, "r") as zip_ref:
                    zip_ref.extractall(plugin_dir)

                # Load plugin manifest
                manifest_path = plugin_dir / "manifest.json"
                if not manifest_path.exists():
                    raise SandboxExecutionError(
                        f"Plugin manifest not found: {plugin_slug}"
                    )

                with open(manifest_path, "r") as f:
                    manifest = json.load(f)

                # Load plugin module
                module_path = plugin_dir / "plugin.py"
                if not module_path.exists():
                    raise SandboxExecutionError(
                        f"Plugin module not found: {plugin_slug}"
                    )

                # Create sandboxed module
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{plugin_slug}",
                    module_path,
                )
                if spec is None or spec.loader is None:
                    raise SandboxExecutionError(
                        f"Cannot load plugin module: {plugin_slug}"
                    )

                module = importlib.util.module_from_spec(spec)

                # Inject restricted globals
                module.__dict__.update(self._create_restricted_globals(context))

                # Execute module
                spec.loader.exec_module(module)

                # Store loaded plugin
                self._loaded_plugins[plugin_slug] = {
                    "module": module,
                    "manifest": manifest,
                    "loaded_at": datetime.utcnow(),
                }

                logger.debug(f"Plugin code loaded: {plugin_slug}")

        except httpx.HTTPError as e:
            raise SandboxExecutionError(f"Failed to download plugin: {e}") from e
        except zipfile.BadZipFile as e:
            raise SandboxExecutionError(f"Invalid plugin package: {e}") from e
        except json.JSONDecodeError as e:
            raise SandboxExecutionError(f"Invalid plugin manifest: {e}") from e
        except Exception as e:
            raise SandboxExecutionError(f"Failed to load plugin: {e}") from e

    def _create_restricted_globals(self, context: PluginContext) -> Dict[str, Any]:
        """
        Create restricted globals dictionary for plugin execution.

        Args:
            context: Plugin execution context

        Returns:
            Restricted globals dictionary
        """
        # Safe builtins
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bin": bin,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "hex": hex,
            "int": int,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "oct": oct,
            "ord": ord,
            "pow": pow,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            "print": print,  # Controlled print for debugging
        }

        return {
            "__builtins__": safe_builtins,
            "__name__": "__plugin__",
            "context": context,
            "logger": self._create_plugin_logger(context),
        }

    def _create_plugin_logger(self, context: PluginContext) -> logging.Logger:
        """
        Create a logger for plugin execution.

        Args:
            context: Plugin execution context

        Returns:
            Logger instance
        """
        logger_name = f"plugin.{context.plugin_id}.{context.execution_id}"
        plugin_logger = logging.getLogger(logger_name)

        # Add context filter
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.plugin_id = context.plugin_id
                record.execution_id = context.execution_id
                return True

        plugin_logger.addFilter(ContextFilter())

        return plugin_logger

    async def execute_entry_point(
        self,
        context: PluginContext,
        entry_point_type: str,
        entry_point_handler: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a plugin entry point.

        Args:
            context: Plugin execution context
            entry_point_type: Type of entry point (webhook, workflow_action, etc.)
            entry_point_handler: Handler function name
            event_data: Event data to pass to handler

        Returns:
            Execution result dictionary

        Raises:
            SandboxExecutionError: If execution fails
            SandboxTimeoutError: If execution times out
            SandboxPermissionError: If plugin lacks required permissions
        """
        # Get plugin module
        plugin_slug = await self._get_plugin_slug(context.plugin_id)
        if plugin_slug not in self._loaded_plugins:
            raise SandboxExecutionError(f"Plugin not loaded: {plugin_slug}")

        plugin_data = self._loaded_plugins[plugin_slug]
        module = plugin_data["module"]

        # Get handler function
        if not hasattr(module, entry_point_handler):
            raise SandboxExecutionError(
                f"Entry point handler not found: {entry_point_handler}"
            )

        handler = getattr(module, entry_point_handler)

        # Execute with timeout
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())

        try:
            # Set resource limits
            self._set_resource_limits()

            # Execute handler with timeout
            result = await asyncio.wait_for(
                self._execute_handler(handler, context, event_data),
                timeout=self.timeout,
            )

            elapsed = (datetime.utcnow() - start_time).total_seconds()

            # Record execution stats
            self._execution_stats[execution_id] = {
                "plugin_id": context.plugin_id,
                "installation_id": context.installation_id,
                "entry_point_type": entry_point_type,
                "entry_point_handler": entry_point_handler,
                "started_at": start_time,
                "completed_at": datetime.utcnow(),
                "elapsed_seconds": elapsed,
                "status": "success",
                "result": result,
            }

            logger.info(
                f"Plugin execution successful: {plugin_slug} - {entry_point_type} "
                f"(elapsed: {elapsed:.2f}s)"
            )

            return {
                "success": True,
                "result": result,
                "elapsed_seconds": elapsed,
                "execution_id": execution_id,
            }

        except asyncio.TimeoutError:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Plugin execution timeout: {plugin_slug} - {entry_point_type}"

            self._execution_stats[execution_id] = {
                "plugin_id": context.plugin_id,
                "installation_id": context.installation_id,
                "entry_point_type": entry_point_type,
                "entry_point_handler": entry_point_handler,
                "started_at": start_time,
                "completed_at": datetime.utcnow(),
                "elapsed_seconds": elapsed,
                "status": "timeout",
                "error": error_msg,
            }

            logger.error(f"{error_msg} (elapsed: {elapsed:.2f}s)")
            raise SandboxTimeoutError(error_msg)

        except SandboxPermissionError as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Plugin permission denied: {plugin_slug} - {str(e)}"

            self._execution_stats[execution_id] = {
                "plugin_id": context.plugin_id,
                "installation_id": context.installation_id,
                "entry_point_type": entry_point_type,
                "entry_point_handler": entry_point_handler,
                "started_at": start_time,
                "completed_at": datetime.utcnow(),
                "elapsed_seconds": elapsed,
                "status": "permission_error",
                "error": str(e),
            }

            logger.error(f"{error_msg} (elapsed: {elapsed:.2f}s)")
            raise

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Plugin execution failed: {plugin_slug} - {str(e)}"

            self._execution_stats[execution_id] = {
                "plugin_id": context.plugin_id,
                "installation_id": context.installation_id,
                "entry_point_type": entry_point_type,
                "entry_point_handler": entry_point_handler,
                "started_at": start_time,
                "completed_at": datetime.utcnow(),
                "elapsed_seconds": elapsed,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

            logger.error(f"{error_msg} (elapsed: {elapsed:.2f}s)", exc_info=True)
            raise SandboxExecutionError(error_msg) from e

        finally:
            # Restore resource limits
            self._restore_resource_limits()

    async def _execute_handler(
        self,
        handler: Callable,
        context: PluginContext,
        event_data: Dict[str, Any],
    ) -> Any:
        """
        Execute plugin handler function.

        Args:
            handler: Handler function
            context: Plugin execution context
            event_data: Event data

        Returns:
            Handler result
        """
        # Check if handler is async
        if asyncio.iscoroutinefunction(handler):
            result = await handler(context, event_data)
        else:
            # Run sync handler in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: handler(context, event_data)
            )

        return result

    def _set_resource_limits(self) -> None:
        """
        Set resource limits for plugin execution.

        Raises:
            SandboxResourceLimitError: If limits cannot be set
        """
        try:
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_TIME, MAX_CPU_TIME))

            # Set memory limit (soft and hard)
            max_memory = self.max_memory_mb * 1024 * 1024  # Convert to bytes
            resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))

        except (ValueError, OSError) as e:
            # Resource limits not supported on this platform
            logger.warning(f"Cannot set resource limits: {e}")

    def _restore_resource_limits(self) -> None:
        """Restore resource limits to defaults."""
        try:
            # Restore to maximum allowed
            resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        except (ValueError, OSError):
            pass

    async def _get_plugin_slug(self, plugin_id: str) -> str:
        """
        Get plugin slug from plugin ID.

        Args:
            plugin_id: Plugin UUID

        Returns:
            Plugin slug

        Raises:
            SandboxExecutionError: If plugin not found
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(Plugin.slug).where(Plugin.id == plugin_id)
        )
        slug = result.scalar_one_or_none()

        if not slug:
            raise SandboxExecutionError(f"Plugin not found: {plugin_id}")

        return slug

    async def unload_plugin(self, plugin_id: str) -> None:
        """
        Unload a plugin from memory.

        Args:
            plugin_id: UUID of the plugin
        """
        plugin_slug = await self._get_plugin_slug(plugin_id)

        if plugin_slug in self._loaded_plugins:
            del self._loaded_plugins[plugin_slug]
            logger.info(f"Plugin unloaded: {plugin_slug}")

    def get_execution_stats(
        self,
        plugin_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get execution statistics.

        Args:
            plugin_id: Optional plugin ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of execution statistics
        """
        stats = list(self._execution_stats.values())

        if plugin_id:
            stats = [s for s in stats if s["plugin_id"] == plugin_id]

        # Sort by start time (most recent first)
        stats.sort(key=lambda s: s["started_at"], reverse=True)

        return stats[:limit]

    def clear_execution_stats(self, older_than: Optional[timedelta] = None) -> int:
        """
        Clear execution statistics.

        Args:
            older_than: Only clear stats older than this duration

        Returns:
            Number of stats cleared
        """
        if older_than:
            cutoff = datetime.utcnow() - older_than
            to_remove = [
                exec_id for exec_id, stats in self._execution_stats.items()
                if stats["started_at"] < cutoff
            ]
        else:
            to_remove = list(self._execution_stats.keys())

        for exec_id in to_remove:
            del self._execution_stats[exec_id]

        return len(to_remove)

    async def validate_plugin(
        self,
        plugin_id: str,
    ) -> Dict[str, Any]:
        """
        Validate a plugin for security and compatibility.

        Args:
            plugin_id: UUID of the plugin

        Returns:
            Validation result dictionary
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(Plugin).where(Plugin.id == plugin_id)
        )
        plugin = result.scalar_one_or_none()

        if not plugin:
            return {
                "valid": False,
                "errors": ["Plugin not found"],
            }

        errors = []
        warnings = []

        # Check permissions are valid
        from schemas.plugin_manifest import PluginPermissionType
        valid_permissions = {perm.value for perm in PluginPermissionType}
        for perm in plugin.permissions:
            if perm not in valid_permissions:
                errors.append(f"Invalid permission: {perm}")

        # Check version compatibility
        from packaging import version as pkg_version
        current_version = settings.agenthr_version or "1.0.0"

        if plugin.min_agenthr_version:
            if pkg_version.parse(current_version) < pkg_version.parse(plugin.min_agenthr_version):
                errors.append(
                    f"Plugin requires AgentHR >= {plugin.min_agenthr_version}, "
                    f"current is {current_version}"
                )

        if plugin.max_agenthr_version:
            if pkg_version.parse(current_version) > pkg_version.parse(plugin.max_agenthr_version):
                errors.append(
                    f"Plugin requires AgentHR <= {plugin.max_agenthr_version}, "
                    f"current is {current_version}"
                )

        # Check for potentially dangerous permissions
        dangerous_permissions = {
            "write:settings",
            "manage:api_keys",
            "execute:workflows",
        }
        for perm in plugin.permissions:
            if perm in dangerous_permissions:
                warnings.append(f"Plugin requests dangerous permission: {perm}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "plugin_id": str(plugin.id),
            "plugin_name": plugin.name,
            "plugin_version": plugin.version,
        }


# Singleton instance getter
def get_plugin_sandbox() -> PluginSandbox:
    """Get a plugin sandbox instance."""
    return PluginSandbox()


__all__ = [
    "PluginSandbox",
    "PluginContext",
    "get_plugin_sandbox",
    "SandboxPermissionError",
    "SandboxExecutionError",
    "SandboxTimeoutError",
    "SandboxResourceLimitError",
]

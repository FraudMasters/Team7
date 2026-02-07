"""
AgentHR Python SDK

Official Python SDK for AgentHR - AI-powered resume analysis and candidate ranking system.

Example usage:
    >>> from agenthr import Client
    >>> client = Client(api_key="your-api-key")
    >>> vacancies = client.vacancies.list()
    >>> client.close()
"""

from typing import Optional

import httpx

__version__ = "0.1.0"
__author__ = "AgentHR Team"
__email__ = "team@agenthr.dev"


class Client:
    """
    AgentHR API client.

    This is the main entry point for interacting with the AgentHR API.
    It provides access to all API resources through nested resource objects.

    Example:
        >>> from agenthr import Client
        >>> client = Client(api_key="your-api-key")
        >>> vacancies = client.vacancies.list()
        >>> client.close()

    Or use as a context manager:
        >>> with Client(api_key="your-api-key") as client:
        ...     vacancies = client.vacancies.list()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the AgentHR client.

        Args:
            api_key: AgentHR API key. If not provided, reads from AGENTHR_API_KEY env var.
            base_url: Base URL of the AgentHR API.
            timeout: Request timeout in seconds.
        """
        import os

        self.api_key = api_key or os.getenv("AGENTHR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set AGENTHR_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create HTTP client with default headers
        self._http_client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )

        # Lazy import resources to avoid circular imports
        self._resources = {}

    @property
    def resumes(self):
        """Access resume operations."""
        if "resumes" not in self._resources:
            from agenthr.resources import Resumes
            self._resources["resumes"] = Resumes(self._http_client)
        return self._resources["resumes"]

    @property
    def vacancies(self):
        """Access vacancy operations."""
        if "vacancies" not in self._resources:
            from agenthr.resources import Vacancies
            self._resources["vacancies"] = Vacancies(self._http_client)
        return self._resources["vacancies"]

    @property
    def candidates(self):
        """Access candidate operations."""
        if "candidates" not in self._resources:
            from agenthr.resources import Candidates
            self._resources["candidates"] = Candidates(self._http_client)
        return self._resources["candidates"]

    @property
    def ranking(self):
        """Access ranking operations."""
        if "ranking" not in self._resources:
            from agenthr.resources import Ranking
            self._resources["ranking"] = Ranking(self._http_client)
        return self._resources["ranking"]

    @property
    def analytics(self):
        """Access analytics operations."""
        if "analytics" not in self._resources:
            from agenthr.resources import Analytics
            self._resources["analytics"] = Analytics(self._http_client)
        return self._resources["analytics"]

    @property
    def webhooks(self):
        """Access webhook operations."""
        if "webhooks" not in self._resources:
            from agenthr.resources import Webhooks
            self._resources["webhooks"] = Webhooks(self._http_client)
        return self._resources["webhooks"]

    @property
    def api_keys(self):
        """Access API key operations."""
        if "api_keys" not in self._resources:
            from agenthr.resources import APIKeys
            self._resources["api_keys"] = APIKeys(self._http_client)
        return self._resources["api_keys"]

    @property
    def workflows(self):
        """Access workflow operations."""
        if "workflows" not in self._resources:
            from agenthr.resources import Workflows
            self._resources["workflows"] = Workflows(self._http_client)
        return self._resources["workflows"]

    @property
    def plugins(self):
        """Access plugin operations."""
        if "plugins" not in self._resources:
            from agenthr.resources import Plugins
            self._resources["plugins"] = Plugins(self._http_client)
        return self._resources["plugins"]

    def close(self):
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncClient:
    """
    Async AgentHR API client.

    This is the async version of the AgentHR client, using httpx.AsyncClient.
    All methods return awaitable coroutines.

    Example:
        >>> import asyncio
        >>> from agenthr import AsyncClient
        >>>
        >>> async def main():
        ...     async with AsyncClient(api_key="your-api-key") as client:
        ...         vacancies = await client.vacancies.list()
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the async AgentHR client.

        Args:
            api_key: AgentHR API key. If not provided, reads from AGENTHR_API_KEY env var.
            base_url: Base URL of the AgentHR API.
            timeout: Request timeout in seconds.
        """
        import os

        self.api_key = api_key or os.getenv("AGENTHR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set AGENTHR_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create async HTTP client with default headers
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )

        # Lazy import resources to avoid circular imports
        self._resources = {}

    @property
    def resumes(self):
        """Access resume operations."""
        if "resumes" not in self._resources:
            from agenthr.resources import AsyncResumes
            self._resources["resumes"] = AsyncResumes(self._http_client)
        return self._resources["resumes"]

    @property
    def vacancies(self):
        """Access vacancy operations."""
        if "vacancies" not in self._resources:
            from agenthr.resources import AsyncVacancies
            self._resources["vacancies"] = AsyncVacancies(self._http_client)
        return self._resources["vacancies"]

    @property
    def candidates(self):
        """Access candidate operations."""
        if "candidates" not in self._resources:
            from agenthr.resources import AsyncCandidates
            self._resources["candidates"] = AsyncCandidates(self._http_client)
        return self._resources["candidates"]

    @property
    def ranking(self):
        """Access ranking operations."""
        if "ranking" not in self._resources:
            from agenthr.resources import AsyncRanking
            self._resources["ranking"] = AsyncRanking(self._http_client)
        return self._resources["ranking"]

    @property
    def analytics(self):
        """Access analytics operations."""
        if "analytics" not in self._resources:
            from agenthr.resources import AsyncAnalytics
            self._resources["analytics"] = AsyncAnalytics(self._http_client)
        return self._resources["analytics"]

    @property
    def webhooks(self):
        """Access webhook operations."""
        if "webhooks" not in self._resources:
            from agenthr.resources import AsyncWebhooks
            self._resources["webhooks"] = AsyncWebhooks(self._http_client)
        return self._resources["webhooks"]

    @property
    def api_keys(self):
        """Access API key operations."""
        if "api_keys" not in self._resources:
            from agenthr.resources import AsyncAPIKeys
            self._resources["api_keys"] = AsyncAPIKeys(self._http_client)
        return self._resources["api_keys"]

    @property
    def workflows(self):
        """Access workflow operations."""
        if "workflows" not in self._resources:
            from agenthr.resources import AsyncWorkflows
            self._resources["workflows"] = AsyncWorkflows(self._http_client)
        return self._resources["workflows"]

    @property
    def plugins(self):
        """Access plugin operations."""
        if "plugins" not in self._resources:
            from agenthr.resources import AsyncPlugins
            self._resources["plugins"] = AsyncPlugins(self._http_client)
        return self._resources["plugins"]

    async def close(self):
        """Close the async HTTP client."""
        await self._http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


__all__ = [
    "Client",
    "AsyncClient",
    "__version__",
]

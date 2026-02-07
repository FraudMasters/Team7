"""
Resource classes for the AgentHR SDK.

This module provides resource classes for interacting with different
parts of the AgentHR API. These are stubs - full implementation will
be provided in the complete SDK.
"""

from typing import Any
import httpx


class BaseResource:
    """Base class for all API resources."""

    def __init__(self, client: httpx.Client):
        """
        Initialize resource with HTTP client.

        Args:
            client: httpx client instance
        """
        self._client = client


class Resumes(BaseResource):
    """Resume resource stub."""

    def upload(self, file_path: str, vacancy_id: str | None = None) -> Any:
        """Upload a resume file."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list(self, limit: int = 50, offset: int = 0, status: str | None = None) -> Any:
        """List all resumes."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get(self, resume_id: str) -> Any:
        """Get resume details."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Vacancies(BaseResource):
    """Vacancy resource stub."""

    def create(self, title: str, description: str, required_skills: list[str], **kwargs) -> Any:
        """Create a vacancy."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list(self, limit: int = 50, offset: int = 0) -> Any:
        """List all vacancies."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get(self, vacancy_id: str) -> Any:
        """Get vacancy details."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def find_matches(self, vacancy_id: str, limit: int = 10) -> Any:
        """Find matching candidates."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Candidates(BaseResource):
    """Candidate resource stub."""

    def list(self, vacancy_id: str | None = None, stage: str | None = None, **kwargs) -> Any:
        """List candidates."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get(self, candidate_id: str) -> Any:
        """Get candidate details."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def move(self, candidate_id: str, stage_id: str, vacancy_id: str, notes: str | None = None) -> Any:
        """Move candidate to a stage."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Ranking(BaseResource):
    """Ranking resource stub."""

    def rank(self, vacancy_id: str, resume_id: str) -> Any:
        """Rank a candidate for a vacancy."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Analytics(BaseResource):
    """Analytics resource stub."""

    def get_key_metrics(self, start_date: str | None = None, end_date: str | None = None) -> Any:
        """Get key metrics."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get_funnel(self, vacancy_id: str | None = None) -> Any:
        """Get funnel metrics."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Webhooks(BaseResource):
    """Webhook resource stub."""

    def create(self, url: str, events: list[str]) -> Any:
        """Create webhook subscription."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list(self) -> Any:
        """List webhooks."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def delete(self, webhook_id: str) -> Any:
        """Delete webhook."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get_delivery_logs(self, webhook_id: str) -> Any:
        """Get webhook delivery logs."""
        raise NotImplementedError("Full SDK implementation coming soon")


class APIKeys(BaseResource):
    """API Keys resource stub."""

    def generate(self, name: str, scopes: list[str], **kwargs) -> Any:
        """Generate API key."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list(self) -> Any:
        """List API keys."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def revoke(self, key_id: str) -> Any:
        """Revoke API key."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Workflows(BaseResource):
    """Workflow resource stub."""

    def create(self, name: str, trigger: dict, actions: list[dict]) -> Any:
        """Create workflow."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list(self) -> Any:
        """List workflows."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def execute(self, workflow_id: str) -> Any:
        """Execute workflow."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def get_executions(self, workflow_id: str) -> Any:
        """Get workflow executions."""
        raise NotImplementedError("Full SDK implementation coming soon")


class Plugins(BaseResource):
    """Plugin resource stub."""

    def list(self, category: str | None = None) -> Any:
        """List plugins."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def install(self, plugin_id: str) -> Any:
        """Install plugin."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def uninstall(self, installation_id: str) -> Any:
        """Uninstall plugin."""
        raise NotImplementedError("Full SDK implementation coming soon")

    def list_installed(self) -> Any:
        """List installed plugins."""
        raise NotImplementedError("Full SDK implementation coming soon")


# Async versions of resources

class AsyncBaseResource:
    """Base class for all async API resources."""

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize resource with async HTTP client.

        Args:
            client: httpx.AsyncClient instance
        """
        self._client = client


class AsyncResumes(Resumes, AsyncBaseResource):
    """Async resume resource stub."""
    pass


class AsyncVacancies(Vacancies, AsyncBaseResource):
    """Async vacancy resource stub."""
    pass


class AsyncCandidates(Candidates, AsyncBaseResource):
    """Async candidate resource stub."""
    pass


class AsyncRanking(Ranking, AsyncBaseResource):
    """Async ranking resource stub."""
    pass


class AsyncAnalytics(Analytics, AsyncBaseResource):
    """Async analytics resource stub."""
    pass


class AsyncWebhooks(Webhooks, AsyncBaseResource):
    """Async webhook resource stub."""
    pass


class AsyncAPIKeys(APIKeys, AsyncBaseResource):
    """Async API keys resource stub."""
    pass


class AsyncWorkflows(Workflows, AsyncBaseResource):
    """Async workflow resource stub."""
    pass


class AsyncPlugins(Plugins, AsyncBaseResource):
    """Async plugin resource stub."""
    pass


__all__ = [
    "Resumes",
    "Vacancies",
    "Candidates",
    "Ranking",
    "Analytics",
    "Webhooks",
    "APIKeys",
    "Workflows",
    "Plugins",
    "AsyncResumes",
    "AsyncVacancies",
    "AsyncCandidates",
    "AsyncRanking",
    "AsyncAnalytics",
    "AsyncWebhooks",
    "AsyncAPIKeys",
    "AsyncWorkflows",
    "AsyncPlugins",
]

"""
Service Dependency Graph Utility Module

This module provides a dependency graph for tracking relationships between
system services and detecting cascading failures.

It supports:
- Service dependency modeling and visualization
- Cascading failure detection and propagation analysis
- Impact analysis for service outages
- Dependency depth calculation
- Critical path identification

The dependency graph is used by the health check system to understand
how failures in one service can affect dependent services.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from services.health_check import HealthCheckResult, HealthCheckService

logger = logging.getLogger(__name__)


@dataclass
class ServiceNode:
    """
    Represents a service in the dependency graph.

    Attributes:
        name: Unique service identifier (e.g., 'database', 'redis', 'celery_worker')
        display_name: Human-readable service name
        description: Brief description of the service
        dependencies: List of service names this service depends on
        dependents: List of service names that depend on this service (computed)
        essential: Whether this service is essential for system operation
        category: Service category (infrastructure, worker, external, model)

    Example:
        >>> node = ServiceNode(
        ...     name="database",
        ...     display_name="PostgreSQL Database",
        ...     dependencies=[],
        ...     essential=True,
        ...     category="infrastructure"
        ... )
    """

    name: str
    display_name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    essential: bool = True
    category: str = "infrastructure"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert service node to dictionary.

        Returns:
            Dictionary representation of the service node
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "essential": self.essential,
            "category": self.category,
        }


@dataclass
class DependencyImpact:
    """
    Represents the impact of a service failure on the system.

    Attributes:
        failed_service: Name of the service that failed
        affected_services: List of services affected by the failure
        total_impact_count: Total number of services affected
        critical_services_affected: List of essential services affected
        cascade_depth: Maximum depth of the failure cascade
        impact_paths: List of dependency paths showing how the failure propagates

    Example:
        >>> impact = DependencyImpact(
        ...     failed_service="redis",
        ...     affected_services=["backend_api", "celery_worker"],
        ...     total_impact_count=2,
        ...     critical_services_affected=["backend_api"],
        ...     cascade_depth=1
        ... )
    """

    failed_service: str
    affected_services: List[str] = field(default_factory=list)
    total_impact_count: int = 0
    critical_services_affected: List[str] = field(default_factory=list)
    cascade_depth: int = 0
    impact_paths: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert impact analysis to dictionary.

        Returns:
            Dictionary representation of the impact analysis
        """
        return {
            "failed_service": self.failed_service,
            "affected_services": self.affected_services,
            "total_impact_count": self.total_impact_count,
            "critical_services_affected": self.critical_services_affected,
            "cascade_depth": self.cascade_depth,
            "impact_paths": self.impact_paths,
        }


class DependencyGraph:
    """
    Service dependency graph for tracking service relationships and failures.

    This class maintains a directed graph of service dependencies and provides
    methods for analyzing the impact of service failures, detecting cascading
    failures, and identifying critical services.

    Attributes:
        services: Dictionary mapping service names to ServiceNode objects
        health_check_service: Health check service for querying service status

    Example:
        >>> graph = DependencyGraph()
        >>> # Get all services
        >>> services = graph.get_all_services()
        >>> # Analyze impact of Redis failure
        >>> impact = graph.analyze_failure_impact("redis")
        >>> # Detect cascading failures
        >>> failures = graph.detect_cascading_failures({"redis": "unhealthy"})
    """

    # Default service definitions for the AgentHR system
    DEFAULT_SERVICES = {
        "database": ServiceNode(
            name="database",
            display_name="PostgreSQL Database",
            description="Primary database for storing resumes, vacancies, and matches",
            dependencies=[],
            essential=True,
            category="infrastructure",
        ),
        "redis": ServiceNode(
            name="redis",
            display_name="Redis Cache",
            description="In-memory cache for session data and query results",
            dependencies=[],
            essential=True,
            category="infrastructure",
        ),
        "celery_broker": ServiceNode(
            name="celery_broker",
            display_name="Celery Message Broker",
            description="Message broker (Redis) for background task queue",
            dependencies=["redis"],
            essential=True,
            category="infrastructure",
        ),
        "celery_worker": ServiceNode(
            name="celery_worker",
            display_name="Celery Worker",
            description="Background task processor for async operations",
            dependencies=["celery_broker", "database", "redis"],
            essential=True,
            category="worker",
        ),
        "backend_api": ServiceNode(
            name="backend_api",
            display_name="Backend API",
            description="FastAPI REST API server",
            dependencies=["database", "redis"],
            essential=True,
            category="infrastructure",
        ),
        "ml_ner_model": ServiceNode(
            name="ml_ner_model",
            display_name="NER Model",
            description="Named Entity Recognition model for resume parsing",
            dependencies=[],
            essential=False,
            category="model",
        ),
        "ml_zero_shot_model": ServiceNode(
            name="ml_zero_shot_model",
            display_name="Zero-Shot Classifier",
            description="Zero-shot classification model for skill matching",
            dependencies=[],
            essential=False,
            category="model",
        ),
        "ml_language_tools": ServiceNode(
            name="ml_language_tools",
            display_name="Language Tools",
            description="LanguageTool integration for grammar checking",
            dependencies=[],
            essential=False,
            category="external",
        ),
        "external_api": ServiceNode(
            name="external_api",
            display_name="External APIs",
            description="External API integrations (e.g., LanguageTool server)",
            dependencies=[],
            essential=False,
            category="external",
        ),
    }

    def __init__(
        self,
        services: Optional[Dict[str, ServiceNode]] = None,
        health_check_service: Optional[HealthCheckService] = None,
    ) -> None:
        """
        Initialize the dependency graph.

        Args:
            services: Optional custom service definitions. If None, uses DEFAULT_SERVICES.
            health_check_service: Optional health check service for querying status.
        """
        self.services: Dict[str, ServiceNode] = services or self.DEFAULT_SERVICES.copy()
        self.health_check_service = health_check_service
        self._build_dependent_lists()
        logger.info(f"DependencyGraph initialized with {len(self.services)} services")

    def _build_dependent_lists(self) -> None:
        """
        Build the list of dependents for each service.

        For each service, populates the 'dependents' list with all services
        that directly depend on it.
        """
        # Clear existing dependents
        for service in self.services.values():
            service.dependents = []

        # Build dependents lists
        for service_name, service in self.services.items():
            for dep in service.dependencies:
                if dep in self.services:
                    self.services[dep].dependents.append(service_name)

        logger.debug("Built dependent lists for all services")

    def get_service(self, name: str) -> Optional[ServiceNode]:
        """
        Get a service node by name.

        Args:
            name: Service name

        Returns:
            ServiceNode if found, None otherwise
        """
        return self.services.get(name)

    def get_all_services(self) -> Dict[str, ServiceNode]:
        """
        Get all services in the graph.

        Returns:
            Dictionary mapping service names to ServiceNode objects
        """
        return self.services.copy()

    def get_dependencies(self, service_name: str, recursive: bool = False) -> List[str]:
        """
        Get dependencies for a service.

        Args:
            service_name: Name of the service
            recursive: If True, include all transitive dependencies

        Returns:
            List of dependency service names

        Raises:
            ValueError: If service_name is not found
        """
        if service_name not in self.services:
            raise ValueError(f"Service not found: {service_name}")

        service = self.services[service_name]

        if not recursive:
            return service.dependencies.copy()

        # Get all transitive dependencies
        deps: Set[str] = set()
        to_visit = service.dependencies.copy()

        while to_visit:
            dep = to_visit.pop()
            if dep not in deps and dep in self.services:
                deps.add(dep)
                to_visit.extend(self.services[dep].dependencies)

        return list(deps)

    def get_dependents(self, service_name: str, recursive: bool = False) -> List[str]:
        """
        Get services that depend on a given service.

        Args:
            service_name: Name of the service
            recursive: If True, include all transitive dependents

        Returns:
            List of dependent service names

        Raises:
            ValueError: If service_name is not found
        """
        if service_name not in self.services:
            raise ValueError(f"Service not found: {service_name}")

        service = self.services[service_name]

        if not recursive:
            return service.dependents.copy()

        # Get all transitive dependents
        dependents: Set[str] = set()
        to_visit = service.dependents.copy()

        while to_visit:
            dependent = to_visit.pop()
            if dependent not in dependents and dependent in self.services:
                dependents.add(dependent)
                to_visit.extend(self.services[dependent].dependents)

        return list(dependents)

    def analyze_failure_impact(
        self, failed_service: str, health_status: Optional[Dict[str, str]] = None
    ) -> DependencyImpact:
        """
        Analyze the impact of a service failure on the system.

        Determines which services will be affected if the given service fails,
        including cascading failures through the dependency chain.

        Args:
            failed_service: Name of the service that failed
            health_status: Optional current health status of all services.
                          If None, queries the health check service.

        Returns:
            DependencyImpact object with analysis results

        Raises:
            ValueError: If failed_service is not found
        """
        if failed_service not in self.services:
            raise ValueError(f"Service not found: {failed_service}")

        # Get current health status if not provided
        if health_status is None and self.health_check_service:
            # In a real implementation, this would query the health check service
            # For now, we'll assume all services are healthy unless specified
            health_status = {name: "healthy" for name in self.services.keys()}
        elif health_status is None:
            health_status = {name: "healthy" for name in self.services.keys()}

        # Find all affected services using BFS
        affected: Set[str] = set()
        queue: List[Tuple[str, int]] = [(failed_service, 0)]  # (service, depth)
        max_depth = 0
        paths: List[List[str]] = []

        visited = {failed_service}

        while queue:
            current, depth = queue.pop(0)
            max_depth = max(max_depth, depth)

            if current != failed_service:
                affected.add(current)

            # Add dependents to queue
            for dependent in self.services[current].dependents:
                if dependent not in visited:
                    visited.add(dependent)
                    queue.append((dependent, depth + 1))

        # Determine which affected services are critical
        critical_affected = [
            s for s in affected if self.services[s].essential
        ]

        # Build impact paths
        paths = self._build_impact_paths(failed_service, affected)

        impact = DependencyImpact(
            failed_service=failed_service,
            affected_services=list(affected),
            total_impact_count=len(affected),
            critical_services_affected=critical_affected,
            cascade_depth=max_depth,
            impact_paths=paths,
        )

        logger.info(
            f"Failure impact analysis for {failed_service}: "
            f"{len(affected)} services affected, depth {max_depth}"
        )

        return impact

    def _build_impact_paths(
        self, failed_service: str, affected_services: Set[str]
    ) -> List[List[str]]:
        """
        Build dependency paths showing how failures propagate.

        Args:
            failed_service: The service that failed
            affected_services: Set of affected service names

        Returns:
            List of paths from failed service to affected services
        """
        paths = []

        for service in affected_services:
            path = self._find_shortest_path(failed_service, service)
            if path:
                paths.append(path)

        return paths

    def _find_shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """
        Find the shortest dependency path from start to end.

        Uses BFS to find the shortest path in the dependency graph.

        Args:
            start: Starting service name
            end: Target service name

        Returns:
            List of service names representing the path, or None if no path exists
        """
        if start not in self.services or end not in self.services:
            return None

        if start == end:
            return [start]

        from collections import deque

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            # Check dependents (not dependencies)
            for dependent in self.services[current].dependents:
                if dependent == end:
                    return path + [end]

                if dependent not in visited:
                    visited.add(dependent)
                    queue.append((dependent, path + [dependent]))

        return None

    def detect_cascading_failures(
        self, health_status: Dict[str, str]
    ) -> List[DependencyImpact]:
        """
        Detect cascading failures based on current health status.

        Analyzes the health status of all services and determines which
        failures are causing cascading effects on dependent services.

        Args:
            health_status: Dictionary mapping service names to health status
                          ('healthy', 'degraded', 'unhealthy')

        Returns:
            List of DependencyImpact objects for each cascading failure detected
        """
        cascading_failures = []

        # Find all unhealthy services
        unhealthy_services = [
            name for name, status in health_status.items()
            if status == "unhealthy"
        ]

        # Analyze impact of each unhealthy service
        for failed_service in unhealthy_services:
            impact = self.analyze_failure_impact(failed_service, health_status)

            # Only include if there are actual affected services
            if impact.affected_services:
                cascading_failures.append(impact)

        logger.info(
            f"Detected {len(cascading_failures)} cascading failures "
            f"from {len(unhealthy_services)} unhealthy services"
        )

        return cascading_failures

    def get_critical_path(self) -> List[str]:
        """
        Get the critical path of essential services.

        The critical path is the longest chain of dependencies through
        essential services. This represents the most vulnerable path
        in the system.

        Returns:
            Ordered list of service names representing the critical path
        """
        # Find services with no dependencies (roots)
        roots = [
            name for name, service in self.services.items()
            if not service.dependencies and service.essential
        ]

        if not roots:
            return []

        # For each root, find the longest path through essential services
        longest_path = []

        for root in roots:
            path = self._find_longest_essential_path(root)
            if len(path) > len(longest_path):
                longest_path = path

        return longest_path

    def _find_longest_essential_path(self, start: str) -> List[str]:
        """
        Find the longest path from start through essential services.

        Args:
            start: Starting service name

        Returns:
            List of service names representing the longest essential path
        """
        def dfs(current: str, visited: Set[str]) -> List[str]:
            if current in visited or current not in self.services:
                return []

            visited.add(current)
            service = self.services[current]

            # If not essential, stop here
            if not service.essential:
                return [current]

            # Recursively find longest path through dependents
            best_path = [current]

            for dependent in service.dependents:
                if dependent not in visited and self.services[dependent].essential:
                    path = dfs(dependent, visited.copy())
                    if len(path) + 1 > len(best_path):
                        best_path = [current] + path

            return best_path

        return dfs(start, set())

    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the dependency graph.

        Returns:
            Dictionary with graph statistics and structure
        """
        essential_count = sum(
            1 for s in self.services.values() if s.essential
        )
        categories = {}
        for service in self.services.values():
            categories[service.category] = categories.get(service.category, 0) + 1

        # Find services with most dependents
        most_dependent = sorted(
            self.services.items(),
            key=lambda x: len(x[1].dependents),
            reverse=True
        )[:5]

        # Find services with most dependencies
        most_dependencies = sorted(
            self.services.items(),
            key=lambda x: len(x[1].dependencies),
            reverse=True
        )[:5]

        return {
            "total_services": len(self.services),
            "essential_services": essential_count,
            "categories": categories,
            "services_with_most_dependents": [
                {"name": name, "dependent_count": len(s.dependents)}
                for name, s in most_dependent
            ],
            "services_with_most_dependencies": [
                {"name": name, "dependency_count": len(s.dependencies)}
                for name, s in most_dependencies
            ],
            "critical_path": self.get_critical_path(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entire dependency graph to a dictionary.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "services": {
                name: service.to_dict()
                for name, service in self.services.items()
            },
            "summary": self.get_graph_summary(),
        }


# Singleton instance for global access
_graph_instance: Optional[DependencyGraph] = None


def get_dependency_graph() -> DependencyGraph:
    """
    Get the singleton DependencyGraph instance.

    Creates the instance on first call and returns the same instance
    on subsequent calls.

    Returns:
        DependencyGraph singleton instance

    Example:
        >>> graph = get_dependency_graph()
        >>> impact = graph.analyze_failure_impact("redis")
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = DependencyGraph()
        logger.info("Created DependencyGraph singleton instance")
    return _graph_instance

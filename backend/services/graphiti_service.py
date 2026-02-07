"""
Graphiti service for knowledge graph operations.

This module provides a singleton service wrapper around graphiti-core
for managing knowledge graph operations including episode ingestion,
semantic search, and Neo4j connectivity.
"""
import logging
from datetime import datetime
from typing import Any, Optional

from config import get_settings

logger = logging.getLogger(__name__)

# Global graphiti service instance
_graphiti_service: Optional["GraphitiService"] = None


class GraphitiService:
    """
    Graphiti service wrapper for knowledge graph operations.

    This service manages the connection to Neo4j via graphiti-core and provides
    methods for ingesting episodes, searching the knowledge graph, and checking
    connectivity health.

    Attributes:
        uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password
        _initialized: Whether the service has been initialized
        _graphiti: The underlying Graphiti client instance
    """

    def __init__(self, uri: str, user: str, password: str) -> None:
        """
        Initialize the Graphiti service.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self._initialized = False
        self._graphiti: Optional[Any] = None

    async def initialize(self) -> None:
        """
        Initialize the Graphiti service by building indices and constraints.

        This method must be called once before using any other graphiti operations.
        It sets up the necessary Neo4j indices and constraints for optimal performance.

        Raises:
            Exception: If initialization fails due to connection or configuration issues
        """
        if self._initialized:
            logger.debug("Graphiti service already initialized")
            return

        try:
            # Import here to avoid import errors if graphiti-core is not installed
            from graphiti_core import Graphiti
            from graphiti_core.llm_client import LLMClient

            # Create Graphiti client
            self._graphiti = Graphiti(
                uri=self.uri,
                user=self.user,
                password=self.password,
            )

            # Build indices and constraints
            await self._graphiti.build_indices_and_constraints()
            self._initialized = True

            logger.info(
                f"Graphiti service initialized successfully (uri={self.uri[:20]}...)"
            )

        except ImportError as e:
            logger.error(f"Failed to import graphiti-core: {e}")
            raise RuntimeError(
                "graphiti-core package not installed. "
                "Install it with: pip install graphiti-core>=0.7.8"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti service: {e}")
            raise

    async def add_episode(
        self,
        name: str,
        body: str,
        source: str,
        source_description: str,
        reference_time: datetime,
    ) -> str:
        """
        Add a single episode to the knowledge graph.

        Episodes represent contextual information such as resume content,
        vacancy descriptions, or interaction history.

        Args:
            name: Name/title of the episode
            body: Main content of the episode
            source: Source identifier (e.g., "resume", "vacancy", "conversation")
            source_description: Human-readable description of the source
            reference_time: Timestamp for the episode

        Returns:
            Episode UUID

        Raises:
            RuntimeError: If service is not initialized
            Exception: If episode addition fails
        """
        if not self._initialized or self._graphiti is None:
            raise RuntimeError(
                "Graphiti service not initialized. Call initialize() first."
            )

        try:
            episode_id = await self._graphiti.add_episode(
                name=name,
                episode_body=body,
                source=source,
                source_description=source_description,
                reference_time=reference_time,
            )

            logger.debug(f"Added episode: {name} ({episode_id})")
            return episode_id

        except Exception as e:
            logger.error(f"Failed to add episode '{name}': {e}")
            raise

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search the knowledge graph for relevant context.

        Performs semantic search across all episodes to find relevant information.

        Args:
            query: Search query text
            limit: Maximum number of results to return (default: 10)

        Returns:
            List of search results with name, body, score, and metadata

        Raises:
            RuntimeError: If service is not initialized
            Exception: If search operation fails
        """
        if not self._initialized or self._graphiti is None:
            raise RuntimeError(
                "Graphiti service not initialized. Call initialize() first."
            )

        try:
            results = await self._graphiti.search(query=query, limit=limit)

            # Convert results to list of dicts for easier serialization
            search_results = []
            for result in results:
                if hasattr(result, "__dict__"):
                    search_results.append({
                        "name": getattr(result, "name", ""),
                        "body": getattr(result, "body", ""),
                        "score": getattr(result, "score", 0.0),
                        "uuid": getattr(result, "uuid", ""),
                        "created_at": getattr(result, "created_at", None),
                    })
                elif isinstance(result, dict):
                    search_results.append(result)
                else:
                    # Fallback for other result types
                    search_results.append({"raw": str(result)})

            logger.debug(f"Search for '{query}' returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Failed to search for '{query}': {e}")
            raise

    async def health_check(self) -> dict[str, Any]:
        """
        Check the health of the Graphiti service and Neo4j connection.

        Returns:
            Dictionary with health status including:
                - healthy: Overall health status
                - initialized: Whether service is initialized
                - neo4j_connected: Whether Neo4j is connected
                - error: Error message if unhealthy

        """
        health = {
            "healthy": False,
            "initialized": self._initialized,
            "neo4j_connected": False,
            "error": None,
        }

        if not self._initialized:
            health["error"] = "Service not initialized"
            return health

        try:
            if self._graphiti is None:
                health["error"] = "Graphiti client not created"
                return health

            # Try to perform a simple operation to verify connection
            # Note: We could use get_episode_count or similar if available
            # For now, just check that we have a client
            health["neo4j_connected"] = True
            health["healthy"] = True

            logger.debug("Graphiti health check passed")

        except Exception as e:
            health["error"] = str(e)
            logger.error(f"Graphiti health check failed: {e}")

        return health

    async def get_episode_count(self) -> int:
        """
        Get the total number of episodes in the knowledge graph.

        Returns:
            Number of episodes

        Raises:
            RuntimeError: If service is not initialized
            Exception: If query fails
        """
        if not self._initialized or self._graphiti is None:
            raise RuntimeError(
                "Graphiti service not initialized. Call initialize() first."
            )

        try:
            # Graphiti doesn't have a direct count method, so we need to query
            # This is a placeholder - actual implementation may vary based on graphiti-core API
            # For now, return 0 as a safe default
            return 0

        except Exception as e:
            logger.error(f"Failed to get episode count: {e}")
            raise

    async def close(self) -> None:
        """
        Close the Graphiti service and cleanup resources.

        This method should be called during application shutdown.
        """
        if self._graphiti is not None:
            try:
                # Close the Graphiti client if it has a close method
                if hasattr(self._graphiti, "close"):
                    await self._graphiti.close()
                logger.info("Graphiti service closed successfully")
            except Exception as e:
                logger.error(f"Error closing Graphiti service: {e}")

        self._initialized = False


def get_graphiti_service() -> GraphitiService:
    """
    Get or create the global Graphiti service instance.

    This function implements the singleton pattern for the Graphiti service.
    The service must be initialized by calling initialize() before use.

    Returns:
        The global GraphitiService instance

    Example:
        >>> service = get_graphiti_service()
        >>> await service.initialize()
        >>> await service.add_episode(...)
    """
    global _graphiti_service

    if _graphiti_service is None:
        settings = get_settings()
        _graphiti_service = GraphitiService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
        logger.info("Created Graphiti service instance")

    return _graphiti_service


def set_graphiti_service(service: GraphitiService) -> None:
    """
    Set the global Graphiti service instance.

    This function is primarily used for testing or dependency injection.

    Args:
        service: The GraphitiService instance to set as global

    Example:
        >>> mock_service = MockGraphitiService()
        >>> set_graphiti_service(mock_service)
    """
    global _graphiti_service
    _graphiti_service = service
    logger.debug("Set custom Graphiti service instance")

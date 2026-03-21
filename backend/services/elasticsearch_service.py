"""
Elasticsearch Service for Candidate Search

This module provides an async Elasticsearch wrapper for indexing and searching
candidate resumes with full-text search capabilities.

Features:
- Async Elasticsearch client for non-blocking operations
- Resume indexing with structured mapping
- Full-text search with relevance scoring
- Bulk indexing for efficient batch operations
- Index management (create, delete, refresh)
- Query DSL generation for complex searches
- Boolean query parsing with AND/OR/NOT operators
- Error handling with graceful fallbacks

The service integrates with the existing resume_analyses table and provides
scalable full-text search capabilities using Elasticsearch 8.x.

Example:
    >>> from services.elasticsearch_service import ElasticsearchService
    >>> es_service = ElasticsearchService()
    >>> await es_service.initialize()
    >>> await es_service.index_resume(resume_id, resume_data)
    >>> results = await es_service.search("Python developer", filters={})
"""
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import async_bulk

from services.query_parser import QueryParser

logger = logging.getLogger(__name__)

# Default Elasticsearch configuration
DEFAULT_ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
DEFAULT_INDEX_NAME = "candidates"


@dataclass
class SearchQuery:
    """
    Elasticsearch search query configuration.

    Attributes:
        query_string: The search query text (optional)
        filters: Dictionary of field filters (optional)
        skills: List of required skills (optional)
        min_experience_years: Minimum years of experience (optional)
        max_experience_years: Maximum years of experience (optional)
        location: Location filter (optional)
        education_level: Education level filter (optional)
        languages: List of languages (optional)
        from_: Offset for pagination (default 0)
        size: Number of results to return (default 100)
        sort_by: Sort field (relevance, experience_years, etc.)
    """

    query_string: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    location: Optional[str] = None
    education_level: Optional[str] = None
    languages: Optional[List[str]] = None
    from_: int = 0
    size: int = 100
    sort_by: str = "relevance"


@dataclass
class SearchResponse:
    """
    Elasticsearch search response.

    Attributes:
        total: Total number of matching documents
        hits: List of search results with scores
        took_ms: Time taken to execute search (milliseconds)
        max_score: Maximum relevance score
        aggregations: Aggregation results (optional)
    """

    total: int
    hits: List[Dict[str, Any]]
    took_ms: int
    max_score: Optional[float]
    aggregations: Optional[Dict[str, Any]] = None


class ElasticsearchService:
    """
    Service for Elasticsearch operations on candidate resumes.

    This service provides async methods for indexing and searching candidate
    resumes using Elasticsearch. It handles connection management, index
    creation, document indexing, and search query execution.

    Features:
    - Async Elasticsearch client with connection pooling
    - Automatic index creation with optimized mappings
    - Full-text search with relevance scoring
    - Structured filtering on resume fields
    - Bulk indexing for batch operations
    - Error handling with logging

    Example:
        >>> es_service = ElasticsearchService()
        >>> await es_service.initialize()
        >>> await es_service.ensure_index()
        >>>
        >>> # Index a resume
        >>> resume_data = {
        ...     "resume_id": "uuid-here",
        ...     "raw_text": "Python developer with 5 years experience...",
        ...     "skills": ["Python", "Django", "PostgreSQL"],
        ...     "experience_years": 5,
        ...     "location": "Remote"
        ... }
        >>> await es_service.index_resume("uuid-here", resume_data)
        >>>
        >>> # Search for candidates
        >>> query = SearchQuery(query_string="Python developer", skills=["Django"])
        >>> results = await es_service.search(query)
        >>> print(f"Found {results.total} candidates")
    """

    def __init__(
        self,
        elasticsearch_url: Optional[str] = None,
        index_name: str = DEFAULT_INDEX_NAME,
    ):
        """
        Initialize the Elasticsearch service.

        Args:
            elasticsearch_url: Elasticsearch connection URL (defaults to env var)
            index_name: Name of the index for candidate documents
        """
        self.elasticsearch_url = elasticsearch_url or DEFAULT_ELASTICSEARCH_URL
        self.index_name = index_name
        self.client: Optional[AsyncElasticsearch] = None
        self._initialized = False

        logger.info(
            f"ElasticsearchService initialized with URL: {self.elasticsearch_url}, "
            f"index: {self.index_name}"
        )

    async def initialize(self) -> None:
        """
        Initialize the Elasticsearch async client.

        Creates the async Elasticsearch client connection. This must be called
        before using any other methods.

        Raises:
            Exception: If connection to Elasticsearch fails
        """
        if self._initialized:
            logger.debug("Elasticsearch client already initialized")
            return

        try:
            self.client = AsyncElasticsearch(
                [self.elasticsearch_url],
                # Disable SSL verification for development
                verify_certs=False,
                # Connection timeout settings
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )

            # Verify connection
            info = await self.client.info()
            logger.info(
                f"Connected to Elasticsearch {info['version']['number']} "
                f"cluster: {info['cluster_name']}"
            )

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
            raise

    async def close(self) -> None:
        """
        Close the Elasticsearch client connection.

        Should be called when shutting down the service to properly clean up
        resources.
        """
        if self.client:
            await self.client.close()
            self._initialized = False
            logger.info("Elasticsearch client closed")

    async def ensure_index(self, mapping: Optional[Dict[str, Any]] = None) -> bool:
        """
        Ensure the index exists, create it if it doesn't.

        Args:
            mapping: Custom index mapping (uses default if not provided)

        Returns:
            True if index was created, False if it already existed

        Raises:
            Exception: If index creation fails
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            exists = await self.client.indices.exists(index=self.index_name)

            if exists:
                logger.debug(f"Index '{self.index_name}' already exists")
                return False

            # Use provided mapping or get default
            index_mapping = mapping or get_candidate_mapping()

            # Create index with mapping
            await self.client.indices.create(
                index=self.index_name,
                body=index_mapping,
            )

            logger.info(f"Created index '{self.index_name}' with mapping")
            return True

        except Exception as e:
            logger.error(f"Failed to create index '{self.index_name}': {e}")
            raise

    async def delete_index(self) -> bool:
        """
        Delete the index.

        Returns:
            True if index was deleted, False if it didn't exist

        Raises:
            Exception: If index deletion fails
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            exists = await self.client.indices.exists(index=self.index_name)

            if not exists:
                logger.debug(f"Index '{self.index_name}' does not exist")
                return False

            await self.client.indices.delete(index=self.index_name)
            logger.info(f"Deleted index '{self.index_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete index '{self.index_name}': {e}")
            raise

    async def index_resume(
        self, resume_id: str, resume_data: Dict[str, Any]
    ) -> bool:
        """
        Index a single resume document.

        Args:
            resume_id: Unique identifier for the resume
            resume_data: Dictionary containing resume fields to index

        Returns:
            True if indexing succeeded

        Raises:
            Exception: If indexing fails

        Example:
            >>> resume_data = {
            ...     "resume_id": "uuid",
            ...     "raw_text": "Experienced Python developer...",
            ...     "skills": ["Python", "Django"],
            ...     "experience_years": 5,
            ...     "education": "Bachelor's in Computer Science",
            ...     "location": "San Francisco, CA",
            ...     "languages": ["English", "Spanish"]
            ... }
            >>> await service.index_resume("uuid", resume_data)
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            # Ensure index exists
            await self.ensure_index()

            # Index the document
            response = await self.client.index(
                index=self.index_name,
                id=resume_id,
                document=resume_data,
                refresh=False,  # Don't force refresh for better performance
            )

            logger.debug(
                f"Indexed resume {resume_id}, result: {response['result']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to index resume {resume_id}: {e}")
            raise

    async def bulk_index(
        self, resumes: List[Dict[str, Any]], refresh: bool = False
    ) -> Dict[str, int]:
        """
        Bulk index multiple resume documents.

        Args:
            resumes: List of resume dictionaries with 'id' and data fields
            refresh: Whether to refresh index after bulk operation

        Returns:
            Dictionary with success and failed counts

        Raises:
            Exception: If bulk indexing fails

        Example:
            >>> resumes = [
            ...     {"id": "uuid1", "raw_text": "...", "skills": [...]},
            ...     {"id": "uuid2", "raw_text": "...", "skills": [...]}
            ... ]
            >>> stats = await service.bulk_index(resumes)
            >>> print(f"Indexed {stats['success']} resumes")
        """
        if not self._initialized or not self.client:
            await self.initialize()

        if not resumes:
            logger.warning("No resumes provided for bulk indexing")
            return {"success": 0, "failed": 0}

        try:
            # Ensure index exists
            await self.ensure_index()

            # Prepare bulk actions
            actions = []
            for resume in resumes:
                resume_id = resume.pop("id", None)
                if not resume_id:
                    logger.warning("Resume missing 'id' field, skipping")
                    continue

                actions.append(
                    {
                        "_index": self.index_name,
                        "_id": resume_id,
                        "_source": resume,
                    }
                )

            # Execute bulk operation
            success, failed = await async_bulk(
                self.client,
                actions,
                raise_on_error=False,
                raise_on_exception=False,
            )

            if refresh:
                await self.client.indices.refresh(index=self.index_name)

            logger.info(
                f"Bulk indexed {success} resumes, {len(failed)} failed"
            )

            return {"success": success, "failed": len(failed)}

        except Exception as e:
            logger.error(f"Failed to bulk index resumes: {e}")
            raise

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        Search for candidate resumes.

        Args:
            query: SearchQuery object with search parameters

        Returns:
            SearchResponse with results and metadata

        Raises:
            Exception: If search fails

        Example:
            >>> query = SearchQuery(
            ...     query_string="Python Django",
            ...     skills=["PostgreSQL"],
            ...     min_experience_years=3
            ... )
            >>> results = await service.search(query)
            >>> for hit in results.hits:
            ...     print(f"{hit['_source']['raw_text'][:100]}...")
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            # Build Elasticsearch query
            es_query = self._build_query(query)

            # Execute search
            response = await self.client.search(
                index=self.index_name,
                body=es_query,
                from_=query.from_,
                size=query.size,
            )

            # Parse response
            total = (
                response["hits"]["total"]["value"]
                if isinstance(response["hits"]["total"], dict)
                else response["hits"]["total"]
            )

            return SearchResponse(
                total=total,
                hits=response["hits"]["hits"],
                took_ms=response["took"],
                max_score=response["hits"].get("max_score"),
                aggregations=response.get("aggregations"),
            )

        except NotFoundError:
            logger.warning(f"Index '{self.index_name}' not found")
            return SearchResponse(total=0, hits=[], took_ms=0, max_score=None)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _build_query(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Build Elasticsearch query DSL from SearchQuery.

        Uses the QueryParser for boolean query syntax support (AND/OR/NOT).

        Args:
            query: SearchQuery object

        Returns:
            Elasticsearch query DSL dictionary
        """
        must_clauses = []
        filter_clauses = []

        # Full-text search with boolean query parser
        if query.query_string:
            # Parse boolean query syntax
            parser = QueryParser()
            parsed_query = parser.parse(query.query_string)

            if parsed_query and "query" in parsed_query:
                # Extract the query portion from the parsed result
                must_clauses.append(parsed_query["query"])
                logger.debug(f"Parsed boolean query: {query.query_string}")
            else:
                # Empty query or None - use simple multi_match
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query.query_string,
                            "fields": [
                                "raw_text^2",  # Boost raw text
                                "skills^3",  # Boost skills more
                                "education",
                                "location",
                            ],
                            "type": "best_fields",
                            "operator": "or",
                        }
                    }
                )

        # Skills filter (OR logic)
        if query.skills:
            filter_clauses.append(
                {"terms": {"skills.keyword": query.skills}}
            )

        # Experience range filter
        if query.min_experience_years is not None:
            filter_clauses.append(
                {"range": {"experience_years": {"gte": query.min_experience_years}}}
            )

        if query.max_experience_years is not None:
            filter_clauses.append(
                {"range": {"experience_years": {"lte": query.max_experience_years}}}
            )

        # Location filter
        if query.location:
            filter_clauses.append(
                {"match": {"location": query.location}}
            )

        # Education level filter
        if query.education_level:
            filter_clauses.append(
                {"match": {"education": query.education_level}}
            )

        # Languages filter
        if query.languages:
            filter_clauses.append(
                {"terms": {"languages.keyword": query.languages}}
            )

        # Additional filters from dict
        if query.filters:
            for field, value in query.filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {f"{field}.keyword": value}})
                elif isinstance(value, dict):
                    # Range query
                    filter_clauses.append({"range": {field: value}})
                else:
                    filter_clauses.append({"term": {f"{field}.keyword": value}})

        # Build bool query
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        # If no clauses, match all
        if not bool_query:
            es_query = {"query": {"match_all": {}}}
        else:
            es_query = {"query": {"bool": bool_query}}

        # Add sorting
        if query.sort_by and query.sort_by != "relevance":
            es_query["sort"] = [{query.sort_by: {"order": "desc"}}]

        return es_query

    async def refresh_index(self) -> None:
        """
        Refresh the index to make recent changes visible.

        Useful after bulk indexing or when immediate visibility is needed.
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            await self.client.indices.refresh(index=self.index_name)
            logger.debug(f"Refreshed index '{self.index_name}'")

        except Exception as e:
            logger.error(f"Failed to refresh index: {e}")
            raise

    async def get_document(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single document by ID.

        Args:
            resume_id: Resume document ID

        Returns:
            Document source dictionary or None if not found
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            response = await self.client.get(
                index=self.index_name,
                id=resume_id,
            )
            return response["_source"]

        except NotFoundError:
            logger.debug(f"Document {resume_id} not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get document {resume_id}: {e}")
            raise

    async def delete_document(self, resume_id: str) -> bool:
        """
        Delete a single document by ID.

        Args:
            resume_id: Resume document ID

        Returns:
            True if document was deleted, False if not found
        """
        if not self._initialized or not self.client:
            await self.initialize()

        try:
            await self.client.delete(
                index=self.index_name,
                id=resume_id,
                refresh=False,
            )
            logger.debug(f"Deleted document {resume_id}")
            return True

        except NotFoundError:
            logger.debug(f"Document {resume_id} not found")
            return False

        except Exception as e:
            logger.error(f"Failed to delete document {resume_id}: {e}")
            raise


def get_candidate_mapping() -> Dict[str, Any]:
    """
    Get the default Elasticsearch mapping for candidate resumes.

    This mapping defines the schema for indexed resume documents with
    optimized field types and analyzers for full-text search.

    Returns:
        Dictionary containing Elasticsearch index mapping

    Field types:
    - raw_text: text with standard analyzer for full-text search
    - skills: text + keyword for both search and exact filtering
    - experience_years: integer for range queries
    - education: text for full-text matching
    - location: text + keyword for flexible location search
    - languages: text + keyword for language filtering
    - resume_id: keyword for exact matching
    - indexed_at: date for temporal filtering
    """
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,  # Single node development
            "analysis": {
                "analyzer": {
                    "skill_analyzer": {
                        "type": "standard",
                        "stopwords": "_none_",  # Don't remove tech terms
                    }
                }
            },
        },
        "mappings": {
            "properties": {
                "resume_id": {
                    "type": "keyword",
                },
                "raw_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "skills": {
                    "type": "text",
                    "analyzer": "skill_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                        }
                    },
                },
                "experience_years": {
                    "type": "integer",
                },
                "education": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                        }
                    },
                },
                "location": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                        }
                    },
                },
                "languages": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                        }
                    },
                },
                "indexed_at": {
                    "type": "date",
                },
            }
        },
    }

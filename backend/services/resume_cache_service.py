"""
Resume parsing cache service with hash-based keys.

This module provides a specialized caching layer for resume parsing results
using content-based hashing to avoid re-parsing identical resumes.

The resume cache service supports:
- Content-based hash keys (SHA-256 of resume content)
- Parsed resume data caching with TTL
- Metadata caching (file type, upload date, etc.)
- Invalidation on resume updates
- Batch operations for multiple resumes
- Graceful fallback when Redis is unavailable

Cache key format: {prefix}:{namespace}:{content_hash}
Example: agenthr:resume_parsing:a1b2c3d4e5f6...
"""
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from redis.exceptions import RedisError

from services.cache_service import CacheService, get_cache_service
from config import get_settings

logger = logging.getLogger(__name__)

# Global resume cache service instance
_resume_cache_service: Optional["ResumeParsingCache"] = None


class ResumeParsingCache:
    """
    Resume parsing cache service with content-based hashing.

    This class provides a specialized cache for resume parsing results
    using SHA-256 hashes of resume content as cache keys. This allows
    identical resumes to be parsed once and reused.

    Attributes:
        cache: underlying CacheService instance
        enabled: Whether resume caching is enabled
        default_ttl: Default TTL for resume parse results

    Example:
        >>> cache = ResumeParsingCache()
        >>> content_hash = cache.hash_content(b"resume content")
        >>> cache.set_parsed_result(content_hash, {"skills": ["Python"]})
        >>> result = cache.get_parsed_result(content_hash)
    """

    # Cache namespace for resume parsing
    NAMESPACE_RESUME_PARSING = "resume_parsing"
    NAMESPACE_RESUME_METADATA = "resume_metadata"
    NAMESPACE_RESUME_ANALYSIS = "resume_analysis"

    # Default TTL values (in seconds)
    DEFAULT_TTL_PARSED = 86400  # 24 hours
    DEFAULT_TTL_METADATA = 604800  # 7 days
    DEFAULT_TTL_ANALYSIS = 3600  # 1 hour

    def __init__(
        self,
        cache_service: Optional[CacheService] = None,
        enabled: Optional[bool] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """
        Initialize the resume parsing cache service.

        Args:
            cache_service: CacheService instance (defaults to global instance)
            enabled: Whether resume caching is enabled (defaults to settings)
            default_ttl: Default TTL for cache entries in seconds
        """
        settings = get_settings()

        self.cache = cache_service or get_cache_service()
        self.enabled = enabled if enabled is not None else getattr(
            settings, 'redis_cache_enabled', True
        )
        self.default_ttl = default_ttl or self.DEFAULT_TTL_PARSED

        logger.info(
            f"ResumeParsingCache initialized (enabled={self.enabled}, "
            f"ttl={self.default_ttl}s)"
        )

    def hash_content(self, content: bytes) -> str:
        """
        Generate SHA-256 hash of resume content.

        Args:
            content: Raw resume file content as bytes

        Returns:
            Hexadecimal SHA-256 hash string

        Example:
            >>> cache = ResumeParsingCache()
            >>> content_hash = cache.hash_content(b"resume content")
            >>> print(len(content_hash))
            64
        """
        return hashlib.sha256(content).hexdigest()

    def hash_content_string(self, content: str) -> str:
        """
        Generate SHA-256 hash of string content.

        Args:
            content: Resume content as string

        Returns:
            Hexadecimal SHA-256 hash string

        Example:
            >>> cache = ResumeParsingCache()
            >>> content_hash = cache.hash_content_string("resume text")
            >>> print(len(content_hash))
            64
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_parsed_result(
        self, content_hash: str, default: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached parsed resume data by content hash.

        Args:
            content_hash: SHA-256 hash of resume content
            default: Default value if not found

        Returns:
            Cached parsing result or default if not found

        Example:
            >>> cache = ResumeParsingCache()
            >>> result = cache.get_parsed_result('abc123...')
            >>> if result:
            ...     print(f"Found cached parse: {result['email']}")
        """
        if not self.enabled:
            return default

        try:
            result = self.cache.get(
                self.NAMESPACE_RESUME_PARSING, content_hash, default=default
            )
            if result:
                logger.debug(f"Cache hit for resume parse: {content_hash[:16]}...")
            else:
                logger.debug(f"Cache miss for resume parse: {content_hash[:16]}...")
            return result
        except Exception as e:
            logger.error(f"Error getting cached parse result: {e}")
            return default

    def set_parsed_result(
        self,
        content_hash: str,
        parsed_data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store parsed resume data in cache.

        Args:
            content_hash: SHA-256 hash of resume content
            parsed_data: Parsed resume data to cache
            ttl: Time-to-live in seconds (defaults to instance default_ttl)

        Returns:
            True if successful, False otherwise

        Example:
            >>> cache = ResumeParsingCache()
            >>> parsed = {"email": "test@example.com", "skills": ["Python"]}
            >>> cache.set_parsed_result('abc123...', parsed, ttl=86400)
        """
        if not self.enabled:
            logger.debug("Resume caching disabled, skipping cache set")
            return False

        ttl = ttl if ttl is not None else self.default_ttl

        # Add cache timestamp
        parsed_data["_cached_at"] = datetime.utcnow().isoformat()

        try:
            success = self.cache.set(
                self.NAMESPACE_RESUME_PARSING, content_hash, parsed_data, ttl=ttl
            )
            if success:
                logger.debug(
                    f"Cached parsed resume: {content_hash[:16]}... (ttl={ttl}s)"
                )
            return success
        except Exception as e:
            logger.error(f"Error caching parsed resume: {e}")
            return False

    def get_analysis_result(
        self, content_hash: str, default: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result by content hash.

        Args:
            content_hash: SHA-256 hash of resume content
            default: Default value if not found

        Returns:
            Cached analysis result or default if not found

        Example:
            >>> cache = ResumeParsingCache()
            >>> analysis = cache.get_analysis_result('abc123...')
            >>> if analysis:
            ...     print(f"Score: {analysis['ats_score']}")
        """
        if not self.enabled:
            return default

        try:
            return self.cache.get(
                self.NAMESPACE_RESUME_ANALYSIS, content_hash, default=default
            )
        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return default

    def set_analysis_result(
        self,
        content_hash: str,
        analysis_data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store analysis result in cache.

        Args:
            content_hash: SHA-256 hash of resume content
            analysis_data: Analysis result to cache
            ttl: Time-to-live in seconds (defaults to DEFAULT_TTL_ANALYSIS)

        Returns:
            True if successful, False otherwise

        Example:
            >>> cache = ResumeParsingCache()
            >>> analysis = {"ats_score": 0.85, "rank": 1}
            >>> cache.set_analysis_result('abc123...', analysis)
        """
        if not self.enabled:
            return False

        ttl = ttl if ttl is not None else self.DEFAULT_TTL_ANALYSIS

        # Add cache timestamp
        analysis_data["_cached_at"] = datetime.utcnow().isoformat()

        try:
            return self.cache.set(
                self.NAMESPACE_RESUME_ANALYSIS, content_hash, analysis_data, ttl=ttl
            )
        except Exception as e:
            logger.error(f"Error caching analysis result: {e}")
            return False

    def get_metadata(
        self, content_hash: str, default: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached resume metadata by content hash.

        Args:
            content_hash: SHA-256 hash of resume content
            default: Default value if not found

        Returns:
            Cached metadata or default if not found

        Example:
            >>> cache = ResumeParsingCache()
            >>> metadata = cache.get_metadata('abc123...')
            >>> if metadata:
            ...     print(f"File type: {metadata['file_type']}")
        """
        if not self.enabled:
            return default

        try:
            return self.cache.get(
                self.NAMESPACE_RESUME_METADATA, content_hash, default=default
            )
        except Exception as e:
            logger.error(f"Error getting cached metadata: {e}")
            return default

    def set_metadata(
        self,
        content_hash: str,
        metadata: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store resume metadata in cache.

        Args:
            content_hash: SHA-256 hash of resume content
            metadata: Metadata to cache (file_type, upload_date, etc.)
            ttl: Time-to-live in seconds (defaults to DEFAULT_TTL_METADATA)

        Returns:
            True if successful, False otherwise

        Example:
            >>> cache = ResumeParsingCache()
            >>> metadata = {"file_type": "pdf", "size": 1024}
            >>> cache.set_metadata('abc123...', metadata)
        """
        if not self.enabled:
            return False

        ttl = ttl if ttl is not None else self.DEFAULT_TTL_METADATA

        try:
            return self.cache.set(
                self.NAMESPACE_RESUME_METADATA, content_hash, metadata, ttl=ttl
            )
        except Exception as e:
            logger.error(f"Error caching metadata: {e}")
            return False

    def get_all(self, content_hash: str) -> Dict[str, Any]:
        """
        Retrieve all cached data for a resume (parse, analysis, metadata).

        Args:
            content_hash: SHA-256 hash of resume content

        Returns:
            Dictionary with 'parsed', 'analysis', and 'metadata' keys

        Example:
            >>> cache = ResumeParsingCache()
            >>> all_data = cache.get_all('abc123...')
            >>> print(f"Parse: {all_data['parsed']}")
            >>> print(f"Analysis: {all_data['analysis']}")
        """
        return {
            "parsed": self.get_parsed_result(content_hash),
            "analysis": self.get_analysis_result(content_hash),
            "metadata": self.get_metadata(content_hash),
        }

    def invalidate(self, content_hash: str) -> bool:
        """
        Invalidate all cached data for a resume.

        Args:
            content_hash: SHA-256 hash of resume content

        Returns:
            True if any data was invalidated, False otherwise

        Example:
            >>> cache = ResumeParsingCache()
            >>> cache.invalidate('abc123...')
        """
        if not self.enabled:
            return False

        try:
            deleted = 0
            deleted += 1 if self.cache.delete(self.NAMESPACE_RESUME_PARSING, content_hash) else 0
            deleted += 1 if self.cache.delete(self.NAMESPACE_RESUME_ANALYSIS, content_hash) else 0
            deleted += 1 if self.cache.delete(self.NAMESPACE_RESUME_METADATA, content_hash) else 0

            if deleted > 0:
                logger.info(f"Invalidated {deleted} cache entries for {content_hash[:16]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidating cache for {content_hash[:16]}...: {e}")
            return False

    def get_many_parsed(self, content_hashes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve multiple cached parsed resumes.

        Args:
            content_hashes: List of content hashes

        Returns:
            Dictionary mapping hashes to their cached parsed data

        Example:
            >>> cache = ResumeParsingCache()
            >>> hashes = ['hash1', 'hash2', 'hash3']
            >>> results = cache.get_many_parsed(hashes)
            >>> print(f"Found {len(results)} cached parses")
        """
        if not self.enabled or not content_hashes:
            return {}

        try:
            return self.cache.get_many(self.NAMESPACE_RESUME_PARSING, content_hashes)
        except Exception as e:
            logger.error(f"Error getting multiple cached parses: {e}")
            return {}

    def set_many_parsed(
        self, parsed_data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None
    ) -> int:
        """
        Store multiple parsed resumes in cache.

        Args:
            parsed_data: Dictionary mapping content hashes to parsed data
            ttl: Time-to-live in seconds (defaults to instance default_ttl)

        Returns:
            Number of entries successfully cached

        Example:
            >>> cache = ResumeParsingCache()
            >>> data = {'hash1': {...}, 'hash2': {...}}
            >>> count = cache.set_many_parsed(data)
        """
        if not self.enabled or not parsed_data:
            return 0

        ttl = ttl if ttl is not None else self.default_ttl

        # Add timestamps
        for data in parsed_data.values():
            data["_cached_at"] = datetime.utcnow().isoformat()

        try:
            return self.cache.set_many(
                self.NAMESPACE_RESUME_PARSING, parsed_data, ttl=ttl
            )
        except Exception as e:
            logger.error(f"Error caching multiple parses: {e}")
            return 0

    def exists(self, content_hash: str) -> bool:
        """
        Check if any cached data exists for a resume.

        Args:
            content_hash: SHA-256 hash of resume content

        Returns:
            True if any cached data exists, False otherwise

        Example:
            >>> cache = ResumeParsingCache()
            >>> if cache.exists('abc123...'):
            ...     print("Resume is cached")
        """
        if not self.enabled:
            return False

        # Check if any namespace has this hash
        return (
            self.cache.exists(self.NAMESPACE_RESUME_PARSING, content_hash) or
            self.cache.exists(self.NAMESPACE_RESUME_ANALYSIS, content_hash) or
            self.cache.exists(self.NAMESPACE_RESUME_METADATA, content_hash)
        )

    def clear_all(self) -> int:
        """
        Clear all resume parsing cache entries.

        Useful for invalidating all resume caches after model updates
        or when fresh parsing is required for all resumes.

        Returns:
            Number of cache keys deleted

        Example:
            >>> cache = ResumeParsingCache()
            >>> count = cache.clear_all()
            >>> print(f"Cleared {count} resume cache entries")
        """
        if not self.enabled:
            return 0

        deleted = 0
        deleted += self.cache.clear_namespace(self.NAMESPACE_RESUME_PARSING)
        deleted += self.cache.clear_namespace(self.NAMESPACE_RESUME_ANALYSIS)
        deleted += self.cache.clear_namespace(self.NAMESPACE_RESUME_METADATA)

        logger.info(f"Cleared {deleted} resume cache entries")
        return deleted

    def health_check(self) -> Dict[str, Any]:
        """
        Check resume cache health and get statistics.

        Returns:
            Dictionary with health status and statistics

        Example:
            >>> cache = ResumeParsingCache()
            >>> health = cache.health_check()
            >>> print(health)
        """
        base_health = self.cache.health_check()

        # Add resume-specific stats
        result = {
            "status": base_health.get("status", "unknown"),
            "enabled": self.enabled,
            "cache_enabled": base_health.get("enabled", False),
            "cache_connected": base_health.get("connected", False),
        }

        return result


def get_resume_cache() -> ResumeParsingCache:
    """
    Get or create global resume cache service instance.

    Returns:
        Global ResumeParsingCache instance

    Example:
        >>> cache = get_resume_cache()
        >>> result = cache.get_parsed_result('abc123...')
    """
    global _resume_cache_service
    if _resume_cache_service is None:
        _resume_cache_service = ResumeParsingCache()
    return _resume_cache_service


def invalidate_resume_cache(content_hash: str) -> bool:
    """
    Invalidate all cached data for a resume by content hash.

    Convenience function for cache invalidation.

    Args:
        content_hash: SHA-256 hash of resume content

    Returns:
        True if any data was invalidated, False otherwise

    Example:
        >>> invalidate_resume_cache('abc123...')
        True
    """
    cache = get_resume_cache()
    return cache.invalidate(content_hash)


def clear_all_resume_cache() -> int:
    """
    Clear all resume parsing cache entries.

    Useful for invalidating all resume caches after model updates.

    Returns:
        Number of cache keys deleted

    Example:
        >>> clear_all_resume_cache()
        1250
    """
    cache = get_resume_cache()
    return cache.clear_all()

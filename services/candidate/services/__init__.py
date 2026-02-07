"""Services package for candidate microservice."""
from .search_service import SearchService, SearchFilters, SearchResult, get_search_service

__all__ = [
    "SearchService",
    "SearchFilters",
    "SearchResult",
    "get_search_service",
]

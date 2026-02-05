"""API package for Taxonomy Service.

API пакет для Taxonomy Service.
"""
from .skill_taxonomies import router as skill_taxonomies_router
from .taxonomy_import_export import router as taxonomy_import_export_router

__all__ = ["skill_taxonomies_router", "taxonomy_import_export_router"]

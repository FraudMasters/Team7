"""
API router module for resume endpoints.

This module serves as the central entry point for all resume-related API endpoints.
It aggregates specialized sub-routers into a unified FastAPI router, following the
Single Responsibility Principle by separating concerns into focused modules.

## Modular Architecture

The original monolithic `api/resumes.py` file (800+ lines) has been split into
specialized modules to improve maintainability, testability, and code organization:

* **upload** - Resume file upload endpoint with validation
  - File type validation (PDF, DOCX)
  - File size validation
  - File storage and database record creation
  - Supports internationalized error messages

* **listing** - Resume listing and retrieval endpoints
  - Paginated list of all resumes
  - Resume metadata display
  - Pre-analyzed skills extraction

* **analysis** - Resume analysis retrieval endpoint
  - Fetch analysis results for specific resumes
  - Returns keywords, entities, grammar errors, and experience data
  - Placeholder for future database integration

* **management** - Resume lifecycle management endpoints
  - Status updates for Kanban board workflow
  - Resume deletion with file cleanup
  - Audit logging for all changes

## Usage

Include this router in the main FastAPI application:

```python
from api.resumes import router as resumes_router

app.include_router(resumes_router, prefix="/api/resumes", tags=["Resumes"])
```

## Benefits of Modular Structure

1. **Separation of Concerns**: Each module handles one specific aspect
2. **Easier Testing**: Smaller modules are easier to unit test
3. **Better Navigation**: Developers can quickly find relevant code
4. **Reduced Merge Conflicts**: Changes to different features affect different files
5. **Clearer Dependencies**: Each module's imports and dependencies are explicit
"""
from fastapi import APIRouter
from . import (
    analysis,
    listing,
    management,
    upload,
)

# Create main router that includes all sub-routers
# This router aggregates all resume-related endpoints under a single prefix
router = APIRouter()

# Include sub-routers in logical order:
# 1. upload - Entry point for new resumes
# 2. listing - Browse existing resumes
# 3. analysis - View detailed analysis
# 4. management - Update status and delete resumes
router.include_router(upload.router)
router.include_router(listing.router)
router.include_router(analysis.router)
router.include_router(management.router)

# Export public API
# Modules are exported for potential direct access in tests or other modules
__all__ = [
    "analysis",
    "listing",
    "management",
    "upload",
    "router",
]

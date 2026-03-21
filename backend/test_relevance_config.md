# Search Relevance Config API Testing

## Overview
This document describes the search relevance configuration API endpoints for managing search result boost values.

## Implementation Summary

### Files Created
- `backend/models/search_relevance_config.py` - SQLAlchemy model for storing relevance configs
- `backend/alembic/versions/20260321_add_search_relevance_config.py` - Database migration

### Files Modified
- `backend/models/__init__.py` - Added SearchRelevanceConfig export
- `backend/api/search_analytics.py` - Added GET and PUT endpoints for relevance-config
- `backend/services/elasticsearch_service.py` - Updated SearchQuery dataclass and _build_query method

## API Endpoints

### GET /api/search/analytics/relevance-config
Get the currently active search relevance configuration.

**Response:**
```json
{
  "id": "uuid-string",
  "name": "Default",
  "skills_boost": 1.0,
  "experience_boost": 1.0,
  "education_boost": 1.0,
  "location_boost": 1.0,
  "is_active": true,
  "created_at": "2026-03-21T...",
  "updated_at": "2026-03-21T..."
}
```

### PUT /api/search/analytics/relevance-config
Update the active search relevance configuration.

**Request Body:**
```json
{
  "name": "Skills-focused",
  "skills_boost": 2.0,
  "experience_boost": 1.5,
  "education_boost": 1.0,
  "location_boost": 1.0
}
```

**Response:** Same as GET endpoint

## Testing

### Manual Testing with curl

1. **Get current config:**
```bash
curl -X GET http://localhost:8000/api/search/analytics/relevance-config \
  -H "Content-Type: application/json"
```

2. **Update config (as per verification test):**
```bash
curl -X PUT http://localhost:8000/api/search/analytics/relevance-config \
  -H "Content-Type: application/json" \
  -d '{"skills_boost": 2, "experience_boost": 1.5, "education_boost": 1}'
```

Expected: HTTP 200 status code with updated config in response

3. **Verify update:**
```bash
curl -X GET http://localhost:8000/api/search/analytics/relevance-config \
  -H "Content-Type: application/json"
```

Expected: skills_boost=2.0, experience_boost=1.5, education_boost=1.0

## Database Migration

To apply the migration:
```bash
cd backend
alembic upgrade head
```

This creates the `search_relevance_configs` table with the following schema:
- `id` (UUID, primary key)
- `name` (String, indexed)
- `skills_boost` (Float, default 1.0)
- `experience_boost` (Float, default 1.0)
- `education_boost` (Float, default 1.0)
- `location_boost` (Float, default 1.0)
- `is_active` (Boolean, indexed, default true)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Integration with Elasticsearch

The boost values are applied to Elasticsearch multi_match queries:

**Before (hardcoded):**
```python
"fields": [
    "raw_text^2",
    "skills^3",
    "education",
    "location",
]
```

**After (dynamic):**
```python
fields = ["raw_text^2"]
if query.skills_boost > 0:
    fields.append(f"skills^{query.skills_boost}")
if query.education_boost > 0:
    fields.append(f"education^{query.education_boost}")
if query.location_boost > 0:
    fields.append(f"location^{query.location_boost}")
```

## Usage in Search Flow

1. Admin updates boost values via PUT endpoint
2. Config is stored in `search_relevance_configs` table
3. Search API fetches active config and passes boost values to ElasticsearchService
4. SearchQuery dataclass includes boost fields with defaults of 1.0
5. _build_query method uses boost values to weight field importance
6. Search results reflect the adjusted relevance scoring

## Validation

All boost values are validated:
- Must be between 0.1 and 10.0 (enforced by Pydantic model)
- Default value is 1.0 (no boost)
- Values > 1.0 increase field importance
- Values < 1.0 decrease field importance

## Default Behavior

If no configuration exists:
- GET endpoint creates a default config with all boosts = 1.0
- This ensures backward compatibility
- Existing searches work unchanged until admin modifies config

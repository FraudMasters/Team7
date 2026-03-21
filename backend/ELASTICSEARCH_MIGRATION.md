# Elasticsearch Bulk Indexing Migration Guide

## Overview

This guide explains how to migrate existing resumes from PostgreSQL to Elasticsearch for full-text search capabilities.

## Prerequisites

1. **Elasticsearch must be running**
   ```bash
   # Check Elasticsearch health
   curl http://localhost:9200/_cluster/health

   # Expected output: {"status":"yellow"} or {"status":"green"}
   ```

2. **Database must be accessible**
   ```bash
   # The backend service should be able to connect to PostgreSQL
   ```

3. **Python environment**
   ```bash
   # Make sure you're in the backend directory with dependencies installed
   cd backend
   pip install -r requirements.txt
   ```

## Method 1: Direct Script Execution (Recommended for Migration)

Use the provided script for synchronous execution with detailed progress:

```bash
cd backend
python run_bulk_index.py
```

This will:
- Index all resumes from PostgreSQL into Elasticsearch
- Process resumes in batches of 100 (configurable)
- Show detailed progress and statistics
- Report any errors encountered

### Expected Output

```
================================================================================
Starting bulk indexing of resumes into Elasticsearch
================================================================================
2026-03-21 10:00:00 - tasks.elasticsearch_indexing - INFO - Starting bulk indexing of resumes (organization_id=None, batch_size=100, status=None)
2026-03-21 10:00:01 - tasks.elasticsearch_indexing - INFO - Found 1500 resumes to index
2026-03-21 10:00:05 - tasks.elasticsearch_indexing - INFO - Batch 1: indexed 100, failed 0
2026-03-21 10:00:10 - tasks.elasticsearch_indexing - INFO - Batch 2: indexed 100, failed 0
...
2026-03-21 10:01:00 - tasks.elasticsearch_indexing - INFO - Bulk indexing completed: 1500 indexed, 0 failed in 60000ms
================================================================================
Bulk indexing completed!
================================================================================
Status: completed
Total resumes: 1500
Batches processed: 15
Successfully indexed: 1500
Failed: 0
Processing time: 60000ms
✓ All resumes indexed successfully
```

## Method 2: Using Celery Task Queue

If Celery workers are running, you can queue the task:

```bash
cd backend
python -c "from tasks.elasticsearch_indexing import bulk_index_resumes; result = bulk_index_resumes.delay(); print(f'Task queued: {result.id}')"
```

Check task status:
```bash
# Using Celery Flower (if running)
open http://localhost:5555

# Or check Celery logs
docker-compose logs -f celery_worker
```

## Method 3: Filtered Migration

Index only specific resumes:

```python
cd backend
python -c "
from tasks.elasticsearch_indexing import bulk_index_resumes

# Index only resumes for a specific organization
result = bulk_index_resumes(
    organization_id='org-uuid-here',
    batch_size=50
)
print(result)
"
```

Or index only completed resumes:

```python
cd backend
python -c "
from tasks.elasticsearch_indexing import bulk_index_resumes

# Index only completed resumes
result = bulk_index_resumes(
    resume_status='COMPLETED',
    batch_size=100
)
print(result)
"
```

## Verification

After running the migration, verify that resumes are indexed:

```bash
# Check index statistics
curl http://localhost:9200/resumes/_count

# Search for a test query
curl -X POST http://localhost:9200/resumes/_search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "skills": "Python"
      }
    },
    "size": 10
  }'
```

## Troubleshooting

### Elasticsearch not responding

```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Start Elasticsearch via docker-compose
docker-compose -f docker-compose.search.yml up -d elasticsearch

# Wait for Elasticsearch to be ready (30-60 seconds)
sleep 30
curl http://localhost:9200/_cluster/health
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check backend environment variables
cat .env | grep DATABASE_URL
cat .env | grep ELASTICSEARCH_URL
```

### Import errors

```bash
# Make sure you're in the backend directory
cd backend

# Verify Python path
python -c "import sys; print(sys.path)"

# Test imports
python -c "from tasks.elasticsearch_indexing import bulk_index_resumes; print('OK')"
```

### Partial failures

If some resumes fail to index:
- Check the error details in the output
- Verify resume data integrity in PostgreSQL
- Check Elasticsearch logs for errors
- Re-run the migration (it will reindex all resumes)

## Re-running the Migration

The bulk indexing is idempotent - you can safely re-run it multiple times:
- Existing documents will be updated
- New resumes will be added
- The index will be refreshed at the end

```bash
cd backend
python run_bulk_index.py
```

## Performance Tuning

For large datasets (10,000+ resumes), you can adjust batch size:

```python
cd backend
python -c "
from tasks.elasticsearch_indexing import bulk_index_resumes

# Use larger batches for better performance
result = bulk_index_resumes(batch_size=500)
print(result)
"
```

## Monitoring

Monitor indexing progress in real-time:

```bash
# Watch Elasticsearch index size
watch -n 1 'curl -s http://localhost:9200/resumes/_count'

# Watch task logs
tail -f backend/logs/celery.log
```

## Next Steps

After successful migration:
1. Verify search functionality in the UI
2. Test advanced search features (boolean queries, filters)
3. Check search analytics dashboard
4. Set up real-time indexing for new resumes (already implemented via hooks)

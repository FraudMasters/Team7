#!/usr/bin/env python
"""
Script to run bulk indexing of resumes into Elasticsearch.

This script executes the bulk_index_resumes task directly (not via Celery queue)
to migrate all existing resumes from PostgreSQL to Elasticsearch.
"""
import logging
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the bulk indexing task."""
    try:
        # Import the task
        from tasks.elasticsearch_indexing import bulk_index_resumes

        logger.info("=" * 80)
        logger.info("Starting bulk indexing of resumes into Elasticsearch")
        logger.info("=" * 80)

        # Run the task directly (synchronous execution)
        # This calls the task function directly without going through Celery queue
        result = bulk_index_resumes()

        # Print results
        logger.info("=" * 80)
        logger.info("Bulk indexing completed!")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Total resumes: {result.get('total_resumes', 0)}")
        logger.info(f"Batches processed: {result.get('batches_processed', 0)}")
        logger.info(f"Successfully indexed: {result.get('total_indexed', 0)}")
        logger.info(f"Failed: {result.get('total_failed', 0)}")
        logger.info(f"Processing time: {result.get('processing_time_ms', 0)}ms")

        if result.get('errors'):
            logger.warning(f"Errors encountered: {len(result['errors'])}")
            for i, error in enumerate(result['errors'][:5], 1):
                logger.warning(f"  Error {i}: {error}")

        # Exit with appropriate code
        if result.get('status') == 'completed':
            logger.info("✓ All resumes indexed successfully")
            sys.exit(0)
        elif result.get('status') == 'partial':
            logger.warning("⚠ Partial success - some resumes failed to index")
            sys.exit(0)  # Still exit 0 as partial success is acceptable
        else:
            logger.error("✗ Bulk indexing failed")
            sys.exit(1)

    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure you're running from the backend directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during bulk indexing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

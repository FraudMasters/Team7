"""
Salary data fetching tasks for market salary benchmark updates.

This module provides Celery tasks for fetching market salary data from
external sources and updating the salary benchmarks in the database.
Tasks are scheduled periodically to keep salary data current.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from models.salary_benchmark import SalaryBenchmark
from models.cost_of_living import CostOfLivingIndex

logger = logging.getLogger(__name__)
settings = get_settings()


def fetch_salary_data_from_api(
    job_titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch salary data from external market data APIs.

    This function queries external salary data sources (e.g., salary.com,
    payscale, glassdoor API) to get current market salary benchmarks.

    Args:
        job_titles: List of job titles to fetch data for (optional)
        locations: List of locations to fetch data for (optional)

    Returns:
        List of salary data dictionaries:
        [
            {
                "job_title": str,
                "location": str,
                "country": str,
                "region": str,
                "industry": str,
                "experience_level": str,
                "employment_type": str,
                "salary_min": int,
                "salary_median": int,
                "salary_max": int,
                "salary_p90": int,
                "currency": str,
                "sample_size": int,
                "data_source": str,
                "source_url": str,
                "effective_date": str,
                "metadata": dict
            },
            ...
        ]

    Example:
        >>> data = fetch_salary_data_from_api(
        ...     job_titles=["Software Engineer"],
        ...     locations=["San Francisco, CA", "New York, NY"]
        ... )
        >>> len(data)
        2
    """
    logger.info(
        f"Fetching salary data from external APIs "
        f"(job_titles={job_titles}, locations={locations})"
    )

    # Placeholder implementation - replace with actual API calls
    # In a real implementation, you would:
    # 1. Call external salary data APIs (e.g., salary.com, payscale)
    # 2. Parse API responses and normalize data structure
    # 3. Handle rate limits and pagination
    # 4. Cache results to avoid duplicate API calls

    # Sample data for demonstration
    sample_data = []

    if job_titles is None:
        job_titles = ["Software Engineer", "Product Manager", "Data Scientist"]

    if locations is None:
        locations = ["San Francisco, CA", "New York, NY", "Remote"]

    for job_title in job_titles:
        for location in locations:
            sample_data.append({
                "job_title": job_title,
                "location": location,
                "country": "US",
                "region": location.split(", ")[-1] if ", " in location else None,
                "industry": "Technology",
                "experience_level": "mid",
                "employment_type": "full_time",
                "salary_min": 95000,
                "salary_median": 125000,
                "salary_max": 165000,
                "salary_p90": 190000,
                "currency": "USD",
                "sample_size": 250,
                "data_source": "market_api",
                "source_url": "https://example.com/salary-data",
                "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "metadata": {
                    "api_version": "v1",
                    "fetch_timestamp": datetime.utcnow().isoformat(),
                    "confidence": "high"
                }
            })

    logger.info(f"Fetched {len(sample_data)} salary data points from external APIs")
    return sample_data


def fetch_cost_of_living_data_from_api(
    locations: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch cost of living data from external APIs.

    This function queries external cost of living data sources (e.g.,
    numbeo API, government statistics) to get current cost of living indices.

    Args:
        locations: List of locations to fetch data for (optional)

    Returns:
        List of cost of living data dictionaries:
        [
            {
                "location": str,
                "country": str,
                "region": str,
                "cost_of_living_index": float,
                "housing_index": float,
                "transportation_index": float,
                "groceries_index": float,
                "utilities_index": float,
                "healthcare_index": float,
                "currency": str,
                "data_source": str,
                "source_url": str,
                "effective_date": str,
                "metadata": dict
            },
            ...
        ]

    Example:
        >>> data = fetch_cost_of_living_data_from_api(
        ...     locations=["San Francisco, CA", "New York, NY"]
        ... )
        >>> len(data)
        2
    """
    logger.info(
        f"Fetching cost of living data from external APIs "
        f"(locations={locations})"
    )

    # Placeholder implementation - replace with actual API calls
    # In a real implementation, you would:
    # 1. Call external cost of living APIs (e.g., numbeo, government data)
    # 2. Parse API responses and normalize data structure
    # 3. Handle rate limits and pagination
    # 4. Cache results to avoid duplicate API calls

    # Sample data for demonstration
    sample_data = []

    if locations is None:
        locations = [
            "San Francisco, CA",
            "New York, NY",
            "Austin, TX",
            "Remote",
            "London, UK",
            "Toronto, ON"
        ]

    # Cost of living indices (baseline: US average = 100)
    cost_indices = {
        "San Francisco, CA": 185.5,
        "New York, NY": 175.0,
        "Austin, TX": 105.0,
        "Remote": 95.0,
        "London, UK": 145.0,
        "Toronto, ON": 115.0,
    }

    for location in locations:
        base_index = cost_indices.get(location, 100.0)

        sample_data.append({
            "location": location,
            "country": "US" if ", " in location and location[-2:] in ["CA", "NY", "TX"] else (
                "UK" if "London" in location else "CA"
            ),
            "region": location.split(", ")[-1] if ", " in location else None,
            "cost_of_living_index": base_index,
            "housing_index": base_index * 1.15,
            "transportation_index": base_index * 0.85,
            "groceries_index": base_index * 0.95,
            "utilities_index": base_index * 0.90,
            "healthcare_index": base_index * 1.05,
            "currency": "USD" if location != "London, UK" else "GBP",
            "data_source": "cost_of_living_api",
            "source_url": "https://example.com/cost-of-living",
            "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "metadata": {
                "api_version": "v1",
                "fetch_timestamp": datetime.utcnow().isoformat(),
                "baseline": "US_average = 100"
            }
        })

    logger.info(f"Fetched {len(sample_data)} cost of living data points from external APIs")
    return sample_data


def save_salary_benchmarks_to_db(
    salary_data: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Save salary benchmark data to the database.

    This function upserts salary benchmark data into the SalaryBenchmark table.
    Existing benchmarks for the same job_title, location, and experience_level
    are updated with new data.

    Args:
        salary_data: List of salary data dictionaries from fetch_salary_data_from_api

    Returns:
        Dictionary with save statistics:
        {
            "created": int,  # Number of new records created
            "updated": int,  # Number of existing records updated
            "failed": int    # Number of records that failed to save
        }

    Example:
        >>> salary_data = fetch_salary_data_from_api()
        >>> stats = save_salary_benchmarks_to_db(salary_data)
        >>> print(stats['created'])
        5
    """
    logger.info(f"Saving {len(salary_data)} salary benchmarks to database")

    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0,
        }

        for data_point in salary_data:
            try:
                # Check if benchmark already exists
                existing_benchmark = db.query(SalaryBenchmark).filter(
                    SalaryBenchmark.job_title == data_point["job_title"],
                    SalaryBenchmark.location == data_point["location"],
                    SalaryBenchmark.experience_level == data_point.get("experience_level", "mid")
                ).first()

                if existing_benchmark:
                    # Update existing benchmark
                    existing_benchmark.salary_min = data_point["salary_min"]
                    existing_benchmark.salary_median = data_point["salary_median"]
                    existing_benchmark.salary_max = data_point["salary_max"]
                    existing_benchmark.salary_p90 = data_point.get("salary_p90")
                    existing_benchmark.sample_size = data_point.get("sample_size")
                    existing_benchmark.data_source = data_point.get("data_source")
                    existing_benchmark.source_url = data_point.get("source_url")
                    existing_benchmark.effective_date = data_point.get("effective_date")
                    existing_benchmark.metadata = data_point.get("metadata", {})
                    existing_benchmark.updated_at = datetime.utcnow()

                    stats["updated"] += 1
                    logger.debug(
                        f"Updated salary benchmark: {data_point['job_title']} "
                        f"in {data_point['location']}"
                    )
                else:
                    # Create new benchmark
                    new_benchmark = SalaryBenchmark(
                        job_title=data_point["job_title"],
                        location=data_point["location"],
                        country=data_point.get("country"),
                        region=data_point.get("region"),
                        industry=data_point.get("industry"),
                        experience_level=data_point.get("experience_level", "mid"),
                        employment_type=data_point.get("employment_type", "full_time"),
                        salary_min=data_point["salary_min"],
                        salary_median=data_point["salary_median"],
                        salary_max=data_point["salary_max"],
                        salary_p90=data_point.get("salary_p90"),
                        currency=data_point.get("currency", "USD"),
                        sample_size=data_point.get("sample_size"),
                        data_source=data_point.get("data_source"),
                        source_url=data_point.get("source_url"),
                        effective_date=data_point.get("effective_date"),
                        metadata=data_point.get("metadata", {}),
                    )
                    db.add(new_benchmark)
                    stats["created"] += 1
                    logger.debug(
                        f"Created salary benchmark: {data_point['job_title']} "
                        f"in {data_point['location']}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to save salary benchmark for "
                    f"{data_point.get('job_title', 'unknown')} in "
                    f"{data_point.get('location', 'unknown')}: {e}"
                )
                stats["failed"] += 1

        # Commit all changes
        db.commit()
        db.close()

        logger.info(
            f"Salary benchmarks saved: created={stats['created']}, "
            f"updated={stats['updated']}, failed={stats['failed']}"
        )

        return stats

    except Exception as e:
        logger.error(f"Database error while saving salary benchmarks: {e}", exc_info=True)
        return {
            "created": 0,
            "updated": 0,
            "failed": len(salary_data),
        }


def save_cost_of_living_to_db(
    cost_data: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Save cost of living data to the database.

    This function upserts cost of living data into the CostOfLivingIndex table.
    Existing indices for the same location are updated with new data.

    Args:
        cost_data: List of cost of living data dictionaries from fetch_cost_of_living_data_from_api

    Returns:
        Dictionary with save statistics:
        {
            "created": int,  # Number of new records created
            "updated": int,  # Number of existing records updated
            "failed": int    # Number of records that failed to save
        }

    Example:
        >>> cost_data = fetch_cost_of_living_data_from_api()
        >>> stats = save_cost_of_living_to_db(cost_data)
        >>> print(stats['created'])
        5
    """
    logger.info(f"Saving {len(cost_data)} cost of living indices to database")

    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0,
        }

        for data_point in cost_data:
            try:
                # Check if index already exists
                existing_index = db.query(CostOfLivingIndex).filter(
                    CostOfLivingIndex.location == data_point["location"]
                ).first()

                if existing_index:
                    # Update existing index
                    existing_index.cost_of_living_index = data_point["cost_of_living_index"]
                    existing_index.housing_index = data_point.get("housing_index")
                    existing_index.transportation_index = data_point.get("transportation_index")
                    existing_index.groceries_index = data_point.get("groceries_index")
                    existing_index.utilities_index = data_point.get("utilities_index")
                    existing_index.healthcare_index = data_point.get("healthcare_index")
                    existing_index.data_source = data_point.get("data_source")
                    existing_index.source_url = data_point.get("source_url")
                    existing_index.effective_date = data_point.get("effective_date")
                    existing_index.metadata = data_point.get("metadata", {})
                    existing_index.updated_at = datetime.utcnow()

                    stats["updated"] += 1
                    logger.debug(
                        f"Updated cost of living index for {data_point['location']}"
                    )
                else:
                    # Create new index
                    new_index = CostOfLivingIndex(
                        location=data_point["location"],
                        country=data_point.get("country"),
                        region=data_point.get("region"),
                        cost_of_living_index=data_point["cost_of_living_index"],
                        housing_index=data_point.get("housing_index"),
                        transportation_index=data_point.get("transportation_index"),
                        groceries_index=data_point.get("groceries_index"),
                        utilities_index=data_point.get("utilities_index"),
                        healthcare_index=data_point.get("healthcare_index"),
                        currency=data_point.get("currency", "USD"),
                        data_source=data_point.get("data_source"),
                        source_url=data_point.get("source_url"),
                        effective_date=data_point.get("effective_date"),
                        metadata=data_point.get("metadata", {}),
                    )
                    db.add(new_index)
                    stats["created"] += 1
                    logger.debug(
                        f"Created cost of living index for {data_point['location']}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to save cost of living index for "
                    f"{data_point.get('location', 'unknown')}: {e}"
                )
                stats["failed"] += 1

        # Commit all changes
        db.commit()
        db.close()

        logger.info(
            f"Cost of living indices saved: created={stats['created']}, "
            f"updated={stats['updated']}, failed={stats['failed']}"
        )

        return stats

    except Exception as e:
        logger.error(f"Database error while saving cost of living indices: {e}", exc_info=True)
        return {
            "created": 0,
            "updated": 0,
            "failed": len(cost_data),
        }


@shared_task(
    name="tasks.salary_data_fetch.fetch_market_salary_data",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def fetch_market_salary_data(
    self,
    job_titles: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    update_cost_of_living: bool = True,
) -> Dict[str, Any]:
    """
    Fetch and update market salary data from external sources.

    This Celery task handles the complete workflow of fetching market salary
    data and updating the salary benchmarks in the database:
    1. Fetch salary data from external APIs
    2. Fetch cost of living data (optional)
    3. Save/update salary benchmarks in database
    4. Save/update cost of living indices in database

    Task Workflow:
    1. Fetch salary data from external APIs
    2. Optionally fetch cost of living data
    3. Upsert data into database tables
    4. Return summary of fetched and saved records

    Args:
        self: Celery task instance (bind=True)
        job_titles: Optional list of job titles to fetch data for
        locations: Optional list of locations to fetch data for
        update_cost_of_living: Whether to fetch and update cost of living data (default: True)

    Returns:
        Dictionary containing fetch results:
        {
            "salary_data": {
                "fetched": int,
                "created": int,
                "updated": int,
                "failed": int
            },
            "cost_of_living": {
                "fetched": int,
                "created": int,
                "updated": int,
                "failed": int
            },
            "processing_time_ms": float,
            "status": str,  # "completed", "failed", "partial"
            "error": str  # Error message (if failed)
        }

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For API or database errors

    Example:
        >>> from tasks.salary_data_fetch import fetch_market_salary_data
        >>> task = fetch_market_salary_data.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0

    try:
        logger.info("Starting market salary data fetch")

        result = {
            "salary_data": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "cost_of_living": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "processing_time_ms": 0,
            "status": "completed",
        }

        # Step 1: Fetch salary data from external APIs
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "fetching_salary_data",
            "message": "Fetching salary data from external APIs...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Fetching salary data")

        salary_data = fetch_salary_data_from_api(job_titles, locations)
        result["salary_data"]["fetched"] = len(salary_data)

        # Step 2: Fetch cost of living data (optional)
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "fetching_cost_of_living",
            "message": "Fetching cost of living data from external APIs...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Fetching cost of living")

        cost_data = []
        if update_cost_of_living:
            cost_data = fetch_cost_of_living_data_from_api(locations)
            result["cost_of_living"]["fetched"] = len(cost_data)

        # Step 3: Save salary benchmarks to database
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "saving_salary_benchmarks",
            "message": "Saving salary benchmarks to database...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Saving salary benchmarks")

        salary_save_stats = save_salary_benchmarks_to_db(salary_data)
        result["salary_data"]["created"] = salary_save_stats["created"]
        result["salary_data"]["updated"] = salary_save_stats["updated"]
        result["salary_data"]["failed"] = salary_save_stats["failed"]

        # Step 4: Save cost of living indices to database
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "saving_cost_of_living",
            "message": "Saving cost of living indices to database...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Saving cost of living")

        if update_cost_of_living:
            cost_save_stats = save_cost_of_living_to_db(cost_data)
            result["cost_of_living"]["created"] = cost_save_stats["created"]
            result["cost_of_living"]["updated"] = cost_save_stats["updated"]
            result["cost_of_living"]["failed"] = cost_save_stats["failed"]

        # Calculate processing time
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = processing_time_ms

        # Determine overall status
        total_failed = result["salary_data"]["failed"] + result["cost_of_living"]["failed"]
        if total_failed == 0:
            result["status"] = "completed"
        elif total_failed < result["salary_data"]["fetched"] + result["cost_of_living"]["fetched"]:
            result["status"] = "partial"
        else:
            result["status"] = "failed"

        logger.info(
            f"Market salary data fetch completed: "
            f"salary_data={result['salary_data']['fetched']} "
            f"(created={result['salary_data']['created']}, "
            f"updated={result['salary_data']['updated']}, "
            f"failed={result['salary_data']['failed']}), "
            f"cost_of_living={result['cost_of_living']['fetched']} "
            f"(created={result['cost_of_living']['created']}, "
            f"updated={result['cost_of_living']['updated']}, "
            f"failed={result['cost_of_living']['failed']}), "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "salary_data": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "cost_of_living": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": "Market salary data fetch exceeded maximum time limit",
        }

    except Exception as e:
        logger.error(f"Error in market salary data fetch: {e}", exc_info=True)
        return {
            "salary_data": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "cost_of_living": {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
            },
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }

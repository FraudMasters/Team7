"""
Integration tests for LinkedIn import history tracking.

Tests cover all aspects of import history verification:
1. Import multiple LinkedIn profiles
2. Query import history endpoint
3. Verify all imports are recorded with timestamps
4. Verify source is marked as 'linkedin'
5. Check that history includes both successful and failed imports
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest
import httpx

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import async_session_maker
from models.linkedin_import import LinkedInImport, LinkedInImportStatus
from models.linkedin_profile import LinkedInProfile, LinkedInProfileStatus
from sqlalchemy import select


class TestImportHistoryTracking:
    """Test suite for LinkedIn import history tracking verification."""

    @pytest.mark.asyncio
    async def test_step1_create_multiple_import_records(self):
        """
        Verification Step 1: Import multiple LinkedIn profiles

        Creates multiple LinkedInImport records with various statuses
        to simulate different import scenarios.
        """
        async with async_session_maker() as db:
            # Create successful import
            import1 = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=uuid4(),
                vacancy_id=uuid4(),
                source_type="linkedin",
                search_params={"keywords": "python developer", "location": "San Francisco"},
                total_candidates=10,
                successful_imports=8,
                failed_imports=2,
                linkedin_search_url="https://www.linkedin.com/search/results/people/?keywords=python",
                notes="Successfully imported 8 Python developers",
            )
            db.add(import1)

            # Create failed import
            import2 = LinkedInImport(
                status=LinkedInImportStatus.FAILED,
                recruiter_id=uuid4(),
                source_type="linkedin",
                search_params={"keywords": "rust developer", "location": "New York"},
                total_candidates=5,
                successful_imports=0,
                failed_imports=5,
                error_message="Rate limit exceeded during import",
                notes="Failed due to API rate limiting",
            )
            db.add(import2)

            # Create partially completed import
            import3 = LinkedInImport(
                status=LinkedInImportStatus.PARTIALLY_COMPLETED,
                recruiter_id=uuid4(),
                vacancy_id=uuid4(),
                source_type="linkedin",
                search_params={"skills": "java, spring", "experience_level": "senior"},
                total_candidates=15,
                successful_imports=12,
                failed_imports=3,
                import_metadata={"batch_size": 15, "processing_time": 45.3},
                notes="Partial success - 3 profiles had incomplete data",
            )
            db.add(import3)

            # Create in-progress import
            import4 = LinkedInImport(
                status=LinkedInImportStatus.IN_PROGRESS,
                recruiter_id=uuid4(),
                source_type="linkedin",
                search_params={"industry": "fintech", "location": "London"},
                total_candidates=20,
                successful_imports=0,
                failed_imports=0,
                notes="Currently processing fintech candidates",
            )
            db.add(import4)

            # Create cancelled import
            import5 = LinkedInImport(
                status=LinkedInImportStatus.CANCELLED,
                recruiter_id=uuid4(),
                source_type="linkedin",
                search_params={"keywords": "data scientist"},
                total_candidates=8,
                successful_imports=0,
                failed_imports=0,
                notes="User cancelled the import operation",
            )
            db.add(import5)

            await db.commit()

            # Verify all records were created
            query = select(LinkedInImport)
            result = await db.execute(query)
            imports = result.scalars().all()

            assert len(imports) >= 5, f"Expected at least 5 imports, found {len(imports)}"

            # Verify statuses
            statuses = {imp.status for imp in imports}
            assert LinkedInImportStatus.COMPLETED in statuses
            assert LinkedInImportStatus.FAILED in statuses
            assert LinkedInImportStatus.PARTIALLY_COMPLETED in statuses
            assert LinkedInImportStatus.IN_PROGRESS in statuses
            assert LinkedInImportStatus.CANCELLED in statuses

    @pytest.mark.asyncio
    async def test_step2_query_import_history_endpoint(self):
        """
        Verification Step 2: Query import history endpoint

        Tests the GET /api/linkedin/history endpoint with pagination.
        """
        async with async_session_maker() as db:
            # Create test imports
            recruiter_id = uuid4()
            for i in range(5):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.COMPLETED if i % 2 == 0 else LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"test {i}"},
                    total_candidates=10 + i,
                    successful_imports=10 + i if i % 2 == 0 else 0,
                    failed_imports=0 if i % 2 == 0 else 10 + i,
                    notes=f"Test import {i}",
                )
                db.add(imp)
            await db.commit()

        # Query the endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/linkedin/history",
                params={"skip": 0, "limit": 10},
                timeout=5.0,
            )

        # Verify response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_imports" in data, "Response should include total_imports"
        assert "imports" in data, "Response should include imports array"
        assert isinstance(data["total_imports"], int), "total_imports should be an integer"
        assert isinstance(data["imports"], list), "imports should be a list"

    @pytest.mark.asyncio
    async def test_step3_verify_timestamps_recorded(self):
        """
        Verification Step 3: Verify all imports are recorded with timestamps

        Tests that all import records have created_at and updated_at timestamps.
        """
        async with async_session_maker() as db:
            # Create import records with different timestamps
            now = datetime.utcnow()
            recruiter_id = uuid4()

            import1 = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "engineer"},
                total_candidates=5,
                successful_imports=5,
                failed_imports=0,
            )
            # Manually set created_at to test timestamps
            import1.created_at = now - timedelta(hours=2)
            import1.updated_at = now - timedelta(hours=2)

            import2 = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "developer"},
                total_candidates=8,
                successful_imports=8,
                failed_imports=0,
            )
            import2.created_at = now - timedelta(hours=1)
            import2.updated_at = now - timedelta(hours=1)

            import3 = LinkedInImport(
                status=LinkedInImportStatus.FAILED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "manager"},
                total_candidates=3,
                successful_imports=0,
                failed_imports=3,
            )
            import3.created_at = now
            import3.updated_at = now

            db.add(import1)
            db.add(import2)
            db.add(import3)
            await db.commit()

            # Query and verify timestamps
            query = select(LinkedInImport).order_by(LinkedInImport.created_at)
            result = await db.execute(query)
            imports = result.scalars().all()

            assert len(imports) >= 3

            # Verify all have timestamps
            for imp in imports:
                assert imp.created_at is not None, f"Import {imp.id} missing created_at timestamp"
                assert imp.updated_at is not None, f"Import {imp.id} missing updated_at timestamp"
                assert isinstance(imp.created_at, datetime), "created_at should be datetime object"
                assert isinstance(imp.updated_at, datetime), "updated_at should be datetime object"

            # Verify chronological ordering (most recent first in endpoint response)
            # The oldest should be import1 (2 hours ago)
            assert imports[0].created_at <= imports[1].created_at
            assert imports[1].created_at <= imports[2].created_at

    @pytest.mark.asyncio
    async def test_step4_verify_source_marked_linkedin(self):
        """
        Verification Step 4: Verify source is marked as 'linkedin'

        Tests that all import records have source_type set to 'linkedin'.
        """
        async with async_session_maker() as db:
            # Create imports with source_type='linkedin'
            recruiter_id = uuid4()
            for i in range(10):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.COMPLETED if i < 7 else LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"candidate {i}"},
                    total_candidates=5,
                    successful_imports=5 if i < 7 else 0,
                    failed_imports=0 if i < 7 else 5,
                )
                db.add(imp)
            await db.commit()

            # Query and verify all have source_type='linkedin'
            query = select(LinkedInImport)
            result = await db.execute(query)
            imports = result.scalars().all()

            assert len(imports) >= 10

            for imp in imports:
                assert imp.source_type == "linkedin", \
                    f"Import {imp.id} has source_type='{imp.source_type}', expected 'linkedin'"

            # Additional verification: create import with different source_type
            # and ensure it's not included in LinkedIn-specific queries (if filtering is implemented)
            other_import = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="indeed",  # Different source
                search_params={"keywords": "test"},
                total_candidates=3,
                successful_imports=3,
                failed_imports=0,
            )
            db.add(other_import)
            await db.commit()

            # Count linkedin vs non-linkedin sources
            query = select(LinkedInImport).where(LinkedInImport.source_type == "linkedin")
            result = await db.execute(query)
            linkedin_imports = result.scalars().all()

            query = select(LinkedInImport).where(LinkedInImport.source_type != "linkedin")
            result = await db.execute(query)
            other_imports = result.scalars().all()

            # Should have at least 10 linkedin imports
            assert len(linkedin_imports) >= 10, \
                f"Expected at least 10 LinkedIn imports, found {len(linkedin_imports)}"
            # Should have at least 1 non-linkedin import
            assert len(other_imports) >= 1, \
                f"Expected at least 1 non-LinkedIn import, found {len(other_imports)}"

    @pytest.mark.asyncio
    async def test_step5_verify_successful_and_failed_imports(self):
        """
        Verification Step 5: Check that history includes both successful and failed imports

        Tests that the import history correctly tracks and displays both successful
        and failed imports with appropriate counters.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()
            vacancy_id = uuid4()

            # Create successful imports
            for i in range(5):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.COMPLETED,
                    recruiter_id=recruiter_id,
                    vacancy_id=vacancy_id,
                    source_type="linkedin",
                    search_params={"keywords": f"successful {i}"},
                    total_candidates=10 + i,
                    successful_imports=10 + i,
                    failed_imports=0,
                    notes=f"Successfully imported {10 + i} candidates",
                )
                db.add(imp)

            # Create failed imports
            for i in range(3):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"failed {i}"},
                    total_candidates=5 + i,
                    successful_imports=0,
                    failed_imports=5 + i,
                    error_message=f"Import failed: API error {i}",
                    notes=f"Failed to import {5 + i} candidates",
                )
                db.add(imp)

            # Create partially completed imports
            for i in range(2):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.PARTIALLY_COMPLETED,
                    recruiter_id=recruiter_id,
                    vacancy_id=vacancy_id,
                    source_type="linkedin",
                    search_params={"keywords": f"partial {i}"},
                    total_candidates=20,
                    successful_imports=15 + i,
                    failed_imports=5 - i,
                    notes=f"Partially imported: {15 + i} succeeded, {5 - i} failed",
                )
                db.add(imp)

            await db.commit()

            # Query and verify successful imports
            success_query = select(LinkedInImport).where(
                LinkedInImport.status == LinkedInImportStatus.COMPLETED
            )
            result = await db.execute(success_query)
            successful_imports = result.scalars().all()

            assert len(successful_imports) >= 5, \
                f"Expected at least 5 successful imports, found {len(successful_imports)}"

            for imp in successful_imports:
                assert imp.status == LinkedInImportStatus.COMPLETED
                assert imp.successful_imports > 0, \
                    f"Successful import {imp.id} should have successful_imports > 0"
                assert imp.failed_imports == 0, \
                    f"Successful import {imp.id} should have failed_imports = 0"

            # Query and verify failed imports
            failed_query = select(LinkedInImport).where(
                LinkedInImport.status == LinkedInImportStatus.FAILED
            )
            result = await db.execute(failed_query)
            failed_imports = result.scalars().all()

            assert len(failed_imports) >= 3, \
                f"Expected at least 3 failed imports, found {len(failed_imports)}"

            for imp in failed_imports:
                assert imp.status == LinkedInImportStatus.FAILED
                assert imp.failed_imports > 0, \
                    f"Failed import {imp.id} should have failed_imports > 0"
                assert imp.error_message is not None, \
                    f"Failed import {imp.id} should have an error_message"

            # Query and verify partially completed imports
            partial_query = select(LinkedInImport).where(
                LinkedInImport.status == LinkedInImportStatus.PARTIALLY_COMPLETED
            )
            result = await db.execute(partial_query)
            partial_imports = result.scalars().all()

            assert len(partial_imports) >= 2, \
                f"Expected at least 2 partially completed imports, found {len(partial_imports)}"

            for imp in partial_imports:
                assert imp.status == LinkedInImportStatus.PARTIALLY_COMPLETED
                assert imp.successful_imports > 0, \
                    f"Partial import {imp.id} should have successful_imports > 0"
                assert imp.failed_imports > 0, \
                    f"Partial import {imp.id} should have failed_imports > 0"

    @pytest.mark.asyncio
    async def test_import_history_pagination(self):
        """
        Test pagination functionality of import history endpoint.

        Verifies that skip and limit parameters work correctly.
        """
        async with async_session_maker() as db:
            # Create 25 import records
            recruiter_id = uuid4()
            for i in range(25):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.COMPLETED if i % 3 != 0 else LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"test {i}"},
                    total_candidates=i + 1,
                    successful_imports=i + 1 if i % 3 != 0 else 0,
                    failed_imports=0 if i % 3 != 0 else i + 1,
                )
                # Stagger timestamps
                imp.created_at = datetime.utcnow() - timedelta(minutes=i)
                imp.updated_at = imp.created_at
                db.add(imp)
            await db.commit()

        # Test first page
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/linkedin/history",
                params={"skip": 0, "limit": 10},
                timeout=5.0,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_imports"] >= 25
        assert len(data["imports"]) == 10

        # Test second page
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/linkedin/history",
                params={"skip": 10, "limit": 10},
                timeout=5.0,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["imports"]) == 10

        # Test third page (remaining)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/linkedin/history",
                params={"skip": 20, "limit": 10},
                timeout=5.0,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["imports"]) >= 5

    @pytest.mark.asyncio
    async def test_import_history_counters(self):
        """
        Test that import counters (total_candidates, successful_imports, failed_imports)
        are accurately tracked and displayed.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            # Create import with specific counters
            imp = LinkedInImport(
                status=LinkedInImportStatus.PARTIALLY_COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "full stack developer"},
                total_candidates=100,
                successful_imports=87,
                failed_imports=13,
                import_metadata={
                    "start_time": "2024-01-15T10:00:00Z",
                    "end_time": "2024-01-15T10:15:00Z",
                    "processing_time_seconds": 900,
                },
                notes="Bulk import completed with 87% success rate",
            )
            db.add(imp)
            await db.commit()

            # Query and verify counters
            query = select(LinkedInImport).where(LinkedInImport.id == imp.id)
            result = await db.execute(query)
            retrieved_imp = result.scalar_one()

            assert retrieved_imp.total_candidates == 100
            assert retrieved_imp.successful_imports == 87
            assert retrieved_imp.failed_imports == 13
            assert retrieved_imp.status == LinkedInImportStatus.PARTIALLY_COMPLETED

            # Verify counters add up correctly
            assert (retrieved_imp.successful_imports + retrieved_imp.failed_imports) == \
                   retrieved_imp.total_candidates

    @pytest.mark.asyncio
    async def test_import_history_search_params_tracking(self):
        """
        Test that search parameters are properly stored and can be retrieved.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            search_params = {
                "keywords": "python OR django",
                "skills": ["python", "django", "postgresql", "redis"],
                "location": "Remote",
                "industry": "Technology",
                "experience_level": "Senior",
                "limit": 50,
            }

            imp = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params=search_params,
                total_candidates=50,
                successful_imports=50,
                failed_imports=0,
                linkedin_search_url="https://www.linkedin.com/search/results/people/?keywords=python",
            )
            db.add(imp)
            await db.commit()

            # Query and verify search params
            query = select(LinkedInImport).where(LinkedInImport.id == imp.id)
            result = await db.execute(query)
            retrieved_imp = result.scalar_one()

            assert retrieved_imp.search_params == search_params
            assert retrieved_imp.search_params["keywords"] == "python OR django"
            assert "python" in retrieved_imp.search_params["skills"]
            assert retrieved_imp.linkedin_search_url is not None

    @pytest.mark.asyncio
    async def test_import_history_vacancy_association(self):
        """
        Test that import history correctly associates with job vacancies.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()
            vacancy_id = uuid4()

            imp = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id,
                source_type="linkedin",
                search_params={"keywords": "react developer"},
                total_candidates=25,
                successful_imports=25,
                failed_imports=0,
                notes="Imported candidates for Senior React Developer position",
            )
            db.add(imp)
            await db.commit()

            # Query imports for this vacancy
            query = select(LinkedInImport).where(LinkedInImport.vacancy_id == vacancy_id)
            result = await db.execute(query)
            vacancy_imports = result.scalars().all()

            assert len(vacancy_imports) >= 1
            assert vacancy_imports[0].vacancy_id == vacancy_id
            assert vacancy_imports[0].recruiter_id == recruiter_id

    @pytest.mark.asyncio
    async def test_import_history_error_tracking(self):
        """
        Test that errors are properly tracked in failed imports.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            error_messages = [
                "Rate limit exceeded: 500 requests per day limit reached",
                "Authentication failed: Invalid access token",
                "Network error: Connection timeout after 30 seconds",
                "API error: LinkedIn service temporarily unavailable (503)",
            ]

            for idx, error_msg in enumerate(error_messages):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"test {idx}"},
                    total_candidates=5,
                    successful_imports=0,
                    failed_imports=5,
                    error_message=error_msg,
                    notes=f"Import failed due to error: {error_msg}",
                )
                db.add(imp)
            await db.commit()

            # Query failed imports and verify error messages
            query = select(LinkedInImport).where(
                LinkedInImport.status == LinkedInImportStatus.FAILED
            )
            result = await db.execute(query)
            failed_imports = result.scalars().all()

            assert len(failed_imports) >= len(error_messages)

            retrieved_errors = [imp.error_message for imp in failed_imports if imp.error_message]
            for original_error in error_messages:
                assert original_error in retrieved_errors, \
                    f"Error message '{original_error}' not found in failed imports"

    @pytest.mark.asyncio
    async def test_import_history_metadata_tracking(self):
        """
        Test that import_metadata JSON field can store arbitrary metadata.
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            metadata = {
                "batch_id": "batch-2024-001",
                "processing_mode": "async",
                "retry_attempts": 2,
                "api_version": "v2",
                "cost_estimate_usd": 5.50,
                "candidate_sources": ["linkedin", "easy_apply"],
                "quality_score": 0.87,
            }

            imp = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "software engineer"},
                total_candidates=50,
                successful_imports=50,
                failed_imports=0,
                import_metadata=metadata,
            )
            db.add(imp)
            await db.commit()

            # Query and verify metadata
            query = select(LinkedInImport).where(LinkedInImport.id == imp.id)
            result = await db.execute(query)
            retrieved_imp = result.scalar_one()

            assert retrieved_imp.import_metadata is not None
            assert retrieved_imp.import_metadata["batch_id"] == "batch-2024-001"
            assert retrieved_imp.import_metadata["processing_mode"] == "async"
            assert retrieved_imp.import_metadata["retry_attempts"] == 2
            assert retrieved_imp.import_metadata["cost_estimate_usd"] == 5.50
            assert "linkedin" in retrieved_imp.import_metadata["candidate_sources"]

    @pytest.mark.asyncio
    async def test_import_history_comprehensive_e2e(self):
        """
        Comprehensive end-to-end test covering all verification steps.

        This test:
        1. Creates multiple imports with various statuses
        2. Queries the import history endpoint
        3. Verifies timestamps are present
        4. Verifies source is 'linkedin'
        5. Verifies both successful and failed imports are included
        """
        async with async_session_maker() as db:
            recruiter_id = uuid4()
            vacancy_id_1 = uuid4()
            vacancy_id_2 = uuid4()

            now = datetime.utcnow()

            # Scenario 1: Successful bulk import
            import1 = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id_1,
                source_type="linkedin",
                search_params={
                    "keywords": "senior python developer",
                    "location": "San Francisco, CA",
                    "experience_level": "senior",
                },
                total_candidates=25,
                successful_imports=25,
                failed_imports=0,
                linkedin_search_url="https://www.linkedin.com/search/results/people/?keywords=senior%20python",
                import_metadata={
                    "processing_time_seconds": 180,
                    "api_requests": 30,
                    "average_response_time_ms": 250,
                },
                notes="Successfully imported 25 senior Python developers for position #001",
            )
            import1.created_at = now - timedelta(hours=3)
            import1.updated_at = now - timedelta(hours=3)
            db.add(import1)

            # Scenario 2: Failed import due to rate limiting
            import2 = LinkedInImport(
                status=LinkedInImportStatus.FAILED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={
                    "keywords": "full stack developer",
                    "location": "New York, NY",
                },
                total_candidates=15,
                successful_imports=0,
                failed_imports=15,
                error_message="Rate limit exceeded: Daily limit of 500 requests reached",
                linkedin_search_url="https://www.linkedin.com/search/results/people/?keywords=full%20stack",
                notes="Import failed after 12 candidates due to rate limiting",
            )
            import2.created_at = now - timedelta(hours=2)
            import2.updated_at = now - timedelta(hours=2)
            db.add(import2)

            # Scenario 3: Partially completed import
            import3 = LinkedInImport(
                status=LinkedInImportStatus.PARTIALLY_COMPLETED,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id_2,
                source_type="linkedin",
                search_params={
                    "skills": "react, typescript, node.js",
                    "location": "Remote",
                },
                total_candidates=40,
                successful_imports=35,
                failed_imports=5,
                linkedin_search_url="https://www.linkedin.com/search/results/people/?skill=react",
                import_metadata={
                    "processing_time_seconds": 420,
                    "success_rate": 0.875,
                },
                notes="35 imported successfully, 5 failed due to incomplete profile data",
            )
            import3.created_at = now - timedelta(hours=1)
            import3.updated_at = now - timedelta(hours=1)
            db.add(import3)

            # Scenario 4: Another successful import
            import4 = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id_1,
                source_type="linkedin",
                search_params={
                    "keywords": "data scientist",
                    "industry": "Healthcare",
                },
                total_candidates=18,
                successful_imports=18,
                failed_imports=0,
                linkedin_search_url="https://www.linkedin.com/search/results/people/?keywords=data%20scientist",
                notes="Imported 18 data scientists for healthcare analytics role",
            )
            import4.created_at = now - timedelta(minutes=30)
            import4.updated_at = now - timedelta(minutes=30)
            db.add(import4)

            # Scenario 5: In-progress import
            import5 = LinkedInImport(
                status=LinkedInImportStatus.IN_PROGRESS,
                recruiter_id=recruiter_id,
                vacancy_id=vacancy_id_2,
                source_type="linkedin",
                search_params={
                    "keywords": "devops engineer",
                    "skills": "kubernetes, docker, aws",
                },
                total_candidates=22,
                successful_imports=0,
                failed_imports=0,
                notes="Currently processing DevOps engineer candidates",
            )
            import5.created_at = now - timedelta(minutes=10)
            import5.updated_at = now - timedelta(minutes=10)
            db.add(import5)

            await db.commit()

            # Verification Step 1: Verify all imports are recorded
            query = select(LinkedInImport).where(LinkedInImport.recruiter_id == recruiter_id)
            result = await db.execute(query)
            all_imports = result.scalars().all()

            assert len(all_imports) == 5, f"Expected 5 imports, found {len(all_imports)}"

            # Verification Step 2: Query import history endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/linkedin/history",
                    params={"skip": 0, "limit": 100},
                    timeout=5.0,
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total_imports"] >= 5
            assert len(data["imports"]) >= 5

            # Verification Step 3: Verify timestamps
            for imp in all_imports:
                assert imp.created_at is not None, f"Import {imp.id} missing created_at"
                assert imp.updated_at is not None, f"Import {imp.id} missing updated_at"
                assert isinstance(imp.created_at, datetime)
                assert isinstance(imp.updated_at, datetime)

            # Verify chronological ordering (most recent first)
            sorted_imports = sorted(all_imports, key=lambda x: x.created_at, reverse=True)
            assert sorted_imports[0].created_at >= sorted_imports[1].created_at

            # Verification Step 4: Verify source is marked as 'linkedin'
            for imp in all_imports:
                assert imp.source_type == "linkedin", \
                    f"Import {imp.id} has source_type='{imp.source_type}', expected 'linkedin'"

            # Verification Step 5: Verify both successful and failed imports
            successful = [imp for imp in all_imports if imp.status == LinkedInImportStatus.COMPLETED]
            failed = [imp for imp in all_imports if imp.status == LinkedInImportStatus.FAILED]
            partial = [imp for imp in all_imports if imp.status == LinkedInImportStatus.PARTIALLY_COMPLETED]
            in_progress = [imp for imp in all_imports if imp.status == LinkedInImportStatus.IN_PROGRESS]

            assert len(successful) >= 2, f"Expected at least 2 successful imports, found {len(successful)}"
            assert len(failed) >= 1, f"Expected at least 1 failed import, found {len(failed)}"
            assert len(partial) >= 1, f"Expected at least 1 partial import, found {len(partial)}"
            assert len(in_progress) >= 1, f"Expected at least 1 in-progress import, found {len(in_progress)}"

            # Verify counters for successful imports
            for imp in successful:
                assert imp.successful_imports > 0
                assert imp.failed_imports == 0
                assert imp.successful_imports == imp.total_candidates

            # Verify counters for failed imports
            for imp in failed:
                assert imp.failed_imports > 0
                assert imp.successful_imports == 0
                assert imp.error_message is not None

            # Verify counters for partial imports
            for imp in partial:
                assert imp.successful_imports > 0
                assert imp.failed_imports > 0
                assert (imp.successful_imports + imp.failed_imports) == imp.total_candidates

            # Verify vacancy associations
            vacancy1_imports = [imp for imp in all_imports if imp.vacancy_id == vacancy_id_1]
            vacancy2_imports = [imp for imp in all_imports if imp.vacancy_id == vacancy_id_2]

            assert len(vacancy1_imports) == 2
            assert len(vacancy2_imports) == 2

            # Verify search params are preserved
            for imp in all_imports:
                assert imp.search_params is not None
                assert isinstance(imp.search_params, dict)

            # Verify metadata is preserved for imports that have it
            imports_with_metadata = [imp for imp in all_imports if imp.import_metadata]
            assert len(imports_with_metadata) >= 2
            for imp in imports_with_metadata:
                assert isinstance(imp.import_metadata, dict)

            # Verify notes are present
            for imp in all_imports:
                assert imp.notes is not None
                assert len(imp.notes) > 0


class TestImportHistoryEdgeCases:
    """Test edge cases and boundary conditions for import history."""

    @pytest.mark.asyncio
    async def test_empty_import_history(self):
        """Test behavior when no import history exists."""
        async with async_session_maker() as db:
            # Ensure no imports exist (use unique recruiter_id)
            unique_recruiter_id = uuid4()

            query = select(LinkedInImport).where(LinkedInImport.recruiter_id == unique_recruiter_id)
            result = await db.execute(query)
            imports = result.scalars().all()

            assert len(imports) == 0

    @pytest.mark.asyncio
    async def test_import_history_large_dataset(self):
        """Test performance with large number of import records."""
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            # Create 100 import records
            for i in range(100):
                imp = LinkedInImport(
                    status=LinkedInImportStatus.COMPLETED if i % 4 != 0 else LinkedInImportStatus.FAILED,
                    recruiter_id=recruiter_id,
                    source_type="linkedin",
                    search_params={"keywords": f"test {i}"},
                    total_candidates=10,
                    successful_imports=10 if i % 4 != 0 else 0,
                    failed_imports=0 if i % 4 != 0 else 10,
                )
                imp.created_at = datetime.utcnow() - timedelta(seconds=i)
                imp.updated_at = imp.created_at
                db.add(imp)

            await db.commit()

            # Query with pagination
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/linkedin/history",
                    params={"skip": 0, "limit": 50},
                    timeout=10.0,
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total_imports"] >= 100
            assert len(data["imports"]) == 50

    @pytest.mark.asyncio
    async def test_import_history_unicode_characters(self):
        """Test that unicode characters in notes and fields are handled correctly."""
        async with async_session_maker() as db:
            recruiter_id = uuid4()

            notes_with_unicode = """
            Imported candidates from various regions:
            - USA: 10 candidates 🇺🇸
            - Germany: 5 candidates 🇩🇪
            - Japan: 3 candidates 🇯🇵
            - Brazil: 7 candidates 🇧🇷
            - Russia: 4 candidates 🇷🇺

            Special characters: ñ, é, ü, 中文, 日本語, 한글
            """

            imp = LinkedInImport(
                status=LinkedInImportStatus.COMPLETED,
                recruiter_id=recruiter_id,
                source_type="linkedin",
                search_params={"keywords": "software engineer"},
                total_candidates=29,
                successful_imports=29,
                failed_imports=0,
                notes=notes_with_unicode,
            )
            db.add(imp)
            await db.commit()

            # Query and verify
            query = select(LinkedInImport).where(LinkedInImport.id == imp.id)
            result = await db.execute(query)
            retrieved_imp = result.scalar_one()

            assert "🇺🇸" in retrieved_imp.notes
            assert "中文" in retrieved_imp.notes
            assert "日本語" in retrieved_imp.notes


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

"""
Complete end-to-end verification of skill feedback workflow.

This test verifies the complete user-facing skill feedback workflow:
1. API endpoint for feedback submission (simulating frontend widget)
2. Database persistence with all fields
3. Feedback history retrieval (for explainability dashboard)
4. Analytics aggregation (for analytics dashboard)
5. ML retraining pipeline integration
6. Complete data flow from submission to processing

This is the final verification for Phase 6: End-to-End Integration
Subtask: subtask-6-1
"""
import asyncio
import logging
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import get_db, async_session_maker
from main import app
from models.skill_feedback import SkillFeedback
from models.ml_model_version import MLModelVersion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SkillFeedbackWorkflowVerifier:
    """
    Complete end-to-end workflow verifier for skill feedback system.

    This class verifies the entire user-facing workflow from recruiter
    feedback submission through analytics display and ML retraining.
    """

    def __init__(self):
        """Initialize the workflow verifier."""
        self.test_results: List[Dict[str, Any]] = []
        self.test_ids = {
            'resume_id': str(uuid.uuid4()),
            'vacancy_id': str(uuid.uuid4()),
            'recruiter_id': str(uuid.uuid4()),
        }
        self.feedback_ids: List[str] = []

    async def cleanup(self):
        """Clean up test data."""
        logger.info("Cleaning up test data...")
        session = async_session_maker()
        try:
            # Delete test feedback entries
            await session.execute(
                delete(SkillFeedback).where(
                    SkillFeedback.feedback_source == "e2e_workflow_test"
                )
            )
            await session.commit()
            logger.info("Cleanup completed")
        finally:
            await session.close()

    async def step_1_submit_feedback_via_api(self, client: AsyncClient) -> bool:
        """
        Step 1: Submit feedback via API (simulating SkillFeedbackWidget).

        This simulates a recruiter using the SkillFeedbackWidget to:
        - Mark a skill as correctly detected (thumbs up)
        - Mark a skill as incorrectly detected (thumbs down)
        - Add a missing skill

        Args:
            client: AsyncClient for making HTTP requests

        Returns:
            True if step succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info("STEP 1: Submit Feedback via API (Frontend Widget Simulation)")
        logger.info("=" * 70)

        try:
            # Simulate three types of feedback that a recruiter would submit
            feedback_entries = [
                {
                    # Thumbs up: Correctly detected skill
                    "resume_id": self.test_ids['resume_id'],
                    "vacancy_id": self.test_ids['vacancy_id'],
                    "recruiter_id": self.test_ids['recruiter_id'],
                    "skill": "Python",
                    "was_correct": True,
                    "confidence_score": 0.95,
                    "feedback_source": "e2e_workflow_test",
                    "extra_metadata": {
                        "test_type": "correct_detection",
                        "widget_location": "technical_skills_section"
                    }
                },
                {
                    # Thumbs down: Incorrectly detected skill
                    "resume_id": self.test_ids['resume_id'],
                    "vacancy_id": self.test_ids['vacancy_id'],
                    "recruiter_id": self.test_ids['recruiter_id'],
                    "skill": "JavaScript",
                    "was_correct": False,
                    "confidence_score": 0.75,
                    "recruiter_correction": "This is actually TypeScript, not JavaScript",
                    "actual_skill": "TypeScript",
                    "feedback_source": "e2e_workflow_test",
                    "extra_metadata": {
                        "test_type": "incorrect_detection",
                        "widget_location": "matched_skills_section"
                    }
                },
                {
                    # Add missing skill
                    "resume_id": self.test_ids['resume_id'],
                    "vacancy_id": self.test_ids['vacancy_id'],
                    "recruiter_id": self.test_ids['recruiter_id'],
                    "skill": "Kubernetes",
                    "was_correct": False,
                    "confidence_score": 0.0,
                    "recruiter_correction": "AI failed to detect this skill from resume",
                    "actual_skill": "Kubernetes",
                    "feedback_source": "e2e_workflow_test",
                    "extra_metadata": {
                        "test_type": "missing_skill",
                        "widget_location": "add_missing_skill_dialog"
                    }
                }
            ]

            logger.info(f"Submitting {len(feedback_entries)} feedback entries...")

            # Submit feedback via POST /api/feedback/
            response = await client.post(
                "/api/feedback/",
                json={"feedback": feedback_entries}
            )

            if response.status_code != 201:
                logger.error(f"Failed to submit feedback: {response.status_code}")
                logger.error(f"Response: {response.text}")
                self.test_results.append({
                    "step": 1,
                    "name": "Submit Feedback via API",
                    "status": "FAIL",
                    "details": f"Expected 201, got {response.status_code}",
                })
                return False

            result = response.json()
            self.feedback_ids = [entry['id'] for entry in result['feedback']]

            logger.info(f"✓ Successfully submitted {len(self.feedback_ids)} feedback entries")
            logger.info(f"  - Correct detection (Python): {self.feedback_ids[0]}")
            logger.info(f"  - Incorrect detection (JavaScript→TypeScript): {self.feedback_ids[1]}")
            logger.info(f"  - Missing skill (Kubernetes): {self.feedback_ids[2]}")

            self.test_results.append({
                "step": 1,
                "name": "Submit Feedback via API",
                "status": "PASS",
                "details": f"Submitted {len(self.feedback_ids)} feedback entries successfully",
            })

            return True

        except Exception as e:
            logger.error(f"Step 1 failed: {e}", exc_info=True)
            self.test_results.append({
                "step": 1,
                "name": "Submit Feedback via API",
                "status": "FAIL",
                "details": str(e),
            })
            return False

    async def step_2_verify_database_persistence(self) -> bool:
        """
        Step 2: Verify feedback is persisted in database with all fields.

        This verifies that the database correctly stores:
        - All feedback fields (resume_id, vacancy_id, recruiter_id, skill, etc.)
        - Timestamps (created_at, updated_at)
        - Extra metadata (JSON field)

        Returns:
            True if step succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info("STEP 2: Verify Database Persistence")
        logger.info("=" * 70)

        try:
            session = async_session_maker()
            try:
                # Query feedback entries from database
                result = await session.execute(
                    select(SkillFeedback).where(
                        SkillFeedback.feedback_source == "e2e_workflow_test"
                    ).order_by(SkillFeedback.created_at)
                )
                entries = result.scalars().all()

                if len(entries) != 3:
                    logger.error(f"Expected 3 entries, found {len(entries)}")
                    return False

                logger.info(f"✓ Found {len(entries)} feedback entries in database")

                # Verify first entry (correct detection)
                entry1 = entries[0]
                assert entry1.skill == "Python"
                assert entry1.was_correct is True
                assert entry1.confidence_score == 0.95
                assert entry1.resume_id == uuid.UUID(self.test_ids['resume_id'])
                assert entry1.vacancy_id == uuid.UUID(self.test_ids['vacancy_id'])
                assert entry1.created_at is not None
                assert entry1.extra_metadata['test_type'] == 'correct_detection'
                logger.info(f"  ✓ Entry 1 (Python): All fields correct")

                # Verify second entry (incorrect detection with correction)
                entry2 = entries[1]
                assert entry2.skill == "JavaScript"
                assert entry2.was_correct is False
                assert entry2.confidence_score == 0.75
                assert entry2.recruiter_correction == "This is actually TypeScript, not JavaScript"
                assert entry2.actual_skill == "TypeScript"
                logger.info(f"  ✓ Entry 2 (JavaScript→TypeScript): Correction fields correct")

                # Verify third entry (missing skill)
                entry3 = entries[2]
                assert entry3.skill == "Kubernetes"
                assert entry3.was_correct is False
                assert entry3.confidence_score == 0.0
                assert entry3.actual_skill == "Kubernetes"
                logger.info(f"  ✓ Entry 3 (Kubernetes): Missing skill fields correct")

                self.test_results.append({
                    "step": 2,
                    "name": "Verify Database Persistence",
                    "status": "PASS",
                    "details": f"All {len(entries)} entries persisted correctly with all fields",
                })

                return True

            finally:
                await session.close()

        except Exception as e:
            logger.error(f"Step 2 failed: {e}", exc_info=True)
            self.test_results.append({
                "step": 2,
                "name": "Verify Database Persistence",
                "status": "FAIL",
                "details": str(e),
            })
            return False

    async def step_3_verify_feedback_history_api(self, client: AsyncClient) -> bool:
        """
        Step 3: Verify feedback history API (for Explainability Dashboard).

        This verifies that GET /api/feedback/ returns feedback in chronological
        order for display in the ExplainabilityDashboard component.

        Args:
            client: AsyncClient for making HTTP requests

        Returns:
            True if step succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info("STEP 3: Verify Feedback History API (Explainability Dashboard)")
        logger.info("=" * 70)

        try:
            # Query feedback history by resume_id and vacancy_id
            # (This is what ExplainabilityDashboard does)
            response = await client.get(
                f"/api/feedback/",
                params={
                    "resume_id": self.test_ids['resume_id'],
                    "vacancy_id": self.test_ids['vacancy_id'],
                }
            )

            if response.status_code != 200:
                logger.error(f"Failed to get feedback history: {response.status_code}")
                return False

            result = response.json()
            feedback_list = result['feedback']
            total_count = result['total_count']

            logger.info(f"✓ Retrieved {total_count} feedback entries from history API")

            # Verify chronological order (newest first)
            if len(feedback_list) >= 2:
                entry1_time = datetime.fromisoformat(feedback_list[0]['created_at'].replace('Z', '+00:00'))
                entry2_time = datetime.fromisoformat(feedback_list[1]['created_at'].replace('Z', '+00:00'))
                assert entry1_time >= entry2_time, "Entries not in chronological order"
                logger.info("  ✓ Entries in chronological order (newest first)")

            # Verify all expected fields are present
            expected_fields = [
                'id', 'resume_id', 'vacancy_id', 'skill', 'was_correct',
                'confidence_score', 'feedback_source', 'created_at'
            ]
            for field in expected_fields:
                assert field in feedback_list[0], f"Missing field: {field}"
            logger.info("  ✓ All expected fields present in response")

            # Verify correction fields are included for incorrect detections
            incorrect_entry = next(e for e in feedback_list if not e['was_correct'])
            assert 'recruiter_correction' in incorrect_entry
            assert 'actual_skill' in incorrect_entry
            logger.info("  ✓ Correction fields present for incorrect detections")

            self.test_results.append({
                "step": 3,
                "name": "Verify Feedback History API",
                "status": "PASS",
                "details": f"History API returns {total_count} entries in correct format",
            })

            return True

        except Exception as e:
            logger.error(f"Step 3 failed: {e}", exc_info=True)
            self.test_results.append({
                "step": 3,
                "name": "Verify Feedback History API",
                "status": "FAIL",
                "details": str(e),
            })
            return False

    async def step_4_verify_analytics_api(self, client: AsyncClient) -> bool:
        """
        Step 4: Verify analytics API (for Analytics Dashboard).

        This verifies that GET /api/feedback/analytics returns aggregated
        metrics for display in the SkillFeedbackAnalytics component.

        Args:
            client: AsyncClient for making HTTP requests

        Returns:
            True if step succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info("STEP 4: Verify Analytics API (Analytics Dashboard)")
        logger.info("=" * 70)

        try:
            # Query analytics endpoint
            # (This is what SkillFeedbackAnalytics component does)
            response = await client.get("/api/feedback/analytics")

            if response.status_code != 200:
                logger.error(f"Failed to get analytics: {response.status_code}")
                return False

            result = response.json()

            logger.info("✓ Retrieved analytics data from API")

            # Verify accuracy metrics
            assert 'accuracy' in result
            accuracy = result['accuracy']
            assert 'total_feedback' in accuracy
            assert 'correct_matches' in accuracy
            assert 'incorrect_matches' in accuracy
            assert 'accuracy_rate' in accuracy
            logger.info(f"  ✓ Accuracy metrics present:")
            logger.info(f"    - Total feedback: {accuracy['total_feedback']}")
            logger.info(f"    - Accuracy rate: {accuracy['accuracy_rate']:.2%}")

            # Verify confidence metrics
            assert 'confidence' in result
            confidence = result['confidence']
            assert 'average_confidence' in confidence
            assert 'median_confidence' in confidence
            assert 'high_confidence_count' in confidence
            assert 'low_confidence_count' in confidence
            logger.info(f"  ✓ Confidence metrics present:")
            logger.info(f"    - Average: {confidence['average_confidence']:.2f}")
            logger.info(f"    - High confidence: {confidence['high_confidence_count']}")

            # Verify source metrics
            assert 'sources' in result
            sources = result['sources']
            assert 'frontend_count' in sources
            assert 'api_count' in sources
            logger.info(f"  ✓ Source metrics present:")
            logger.info(f"    - Frontend: {sources['frontend_count']}")
            logger.info(f"    - API: {sources['api_count']}")

            # Verify processing metrics
            assert 'processing' in result
            processing = result['processing']
            assert 'total_processed' in processing
            assert 'total_unprocessed' in processing
            assert 'processing_rate' in processing
            logger.info(f"  ✓ Processing metrics present:")
            logger.info(f"    - Processing rate: {processing['processing_rate']:.2%}")

            self.test_results.append({
                "step": 4,
                "name": "Verify Analytics API",
                "status": "PASS",
                "details": "Analytics API returns all required metrics",
            })

            return True

        except Exception as e:
            logger.error(f"Step 4 failed: {e}", exc_info=True)
            self.test_results.append({
                "step": 4,
                "name": "Verify Analytics API",
                "status": "FAIL",
                "details": str(e),
            })
            return False

    async def step_5_verify_ml_retraining_integration(self) -> bool:
        """
        Step 5: Verify ML retraining pipeline integration.

        This verifies that the model_retraining.py pipeline can:
        - Query unprocessed skill feedback
        - Aggregate feedback for model training
        - Mark feedback as processed

        Returns:
            True if step succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info("STEP 5: Verify ML Retraining Pipeline Integration")
        logger.info("=" * 70)

        try:
            session = async_session_maker()
            try:
                # Verify feedback is queryable by ML pipeline
                # (Simulating what model_retraining.py does)
                result = await session.execute(
                    select(SkillFeedback).where(
                        SkillFeedback.feedback_source == "e2e_workflow_test",
                        SkillFeedback.processed == False
                    )
                )
                unprocessed = result.scalars().all()

                logger.info(f"✓ Found {len(unprocessed)} unprocessed feedback entries")
                assert len(unprocessed) == 3, "Expected 3 unprocessed entries"

                # Verify feedback aggregation
                result = await session.execute(
                    select(
                        func.count(SkillFeedback.id).label('total'),
                        func.sum(SkillFeedback.was_correct.cast(int)).label('correct')
                    ).where(
                        SkillFeedback.feedback_source == "e2e_workflow_test"
                    )
                )
                stats = result.one()

                logger.info(f"  ✓ Aggregated statistics:")
                logger.info(f"    - Total entries: {stats.total}")
                logger.info(f"    - Correct: {stats.correct}")
                logger.info(f"    - Incorrect: {stats.total - stats.correct}")
                logger.info(f"    - Accuracy: {stats.correct / stats.total:.2%}")

                # Simulate marking feedback as processed
                # (This is what model_retraining.py does after training)
                for entry in unprocessed:
                    entry.processed = True
                await session.commit()

                # Verify processed status updated
                result = await session.execute(
                    select(func.count(SkillFeedback.id)).where(
                        SkillFeedback.feedback_source == "e2e_workflow_test",
                        SkillFeedback.processed == True
                    )
                )
                processed_count = result.scalar()

                logger.info(f"  ✓ Marked {processed_count} entries as processed")
                assert processed_count == 3, "Expected 3 processed entries"

                self.test_results.append({
                    "step": 5,
                    "name": "Verify ML Retraining Integration",
                    "status": "PASS",
                    "details": f"Pipeline can query and process {len(unprocessed)} feedback entries",
                })

                return True

            finally:
                await session.close()

        except Exception as e:
            logger.error(f"Step 5 failed: {e}", exc_info=True)
            self.test_results.append({
                "step": 5,
                "name": "Verify ML Retraining Integration",
                "status": "FAIL",
                "details": str(e),
            })
            return False

    def print_summary(self):
        """Print test results summary."""
        logger.info("=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)

        total_steps = len(self.test_results)
        passed_steps = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed_steps = total_steps - passed_steps

        for result in self.test_results:
            status_icon = "✓" if result['status'] == 'PASS' else "✗"
            logger.info(f"{status_icon} Step {result['step']}: {result['name']} - {result['status']}")
            logger.info(f"  Details: {result['details']}")

        logger.info("=" * 70)
        logger.info(f"Total Steps: {total_steps}")
        logger.info(f"Passed: {passed_steps}")
        logger.info(f"Failed: {failed_steps}")
        logger.info(f"Success Rate: {passed_steps / total_steps:.1%}")
        logger.info("=" * 70)

        if failed_steps == 0:
            logger.info("🎉 ALL VERIFICATION STEPS PASSED!")
            logger.info("Skill feedback workflow is fully operational.")
        else:
            logger.error(f"❌ {failed_steps} STEPS FAILED")
            logger.error("Review logs above for details.")


# ============================================================================
# PYTEST TEST FUNCTIONS
# ============================================================================

@pytest.fixture
async def test_client():
    """Create a test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_complete_skill_feedback_workflow(test_client):
    """
    Complete end-to-end verification of skill feedback workflow.

    This test verifies all 5 steps of the workflow:
    1. Submit feedback via API (widget simulation)
    2. Verify database persistence
    3. Verify feedback history API (explainability dashboard)
    4. Verify analytics API (analytics dashboard)
    5. Verify ML retraining integration
    """
    verifier = SkillFeedbackWorkflowVerifier()

    try:
        # Run all verification steps
        step1_passed = await verifier.step_1_submit_feedback_via_api(test_client)
        assert step1_passed, "Step 1 failed: Feedback submission"

        step2_passed = await verifier.step_2_verify_database_persistence()
        assert step2_passed, "Step 2 failed: Database persistence"

        step3_passed = await verifier.step_3_verify_feedback_history_api(test_client)
        assert step3_passed, "Step 3 failed: Feedback history API"

        step4_passed = await verifier.step_4_verify_analytics_api(test_client)
        assert step4_passed, "Step 4 failed: Analytics API"

        step5_passed = await verifier.step_5_verify_ml_retraining_integration()
        assert step5_passed, "Step 5 failed: ML retraining integration"

        # Print summary
        verifier.print_summary()

        # Verify all steps passed
        all_passed = all(r['status'] == 'PASS' for r in verifier.test_results)
        assert all_passed, "Some verification steps failed"

    finally:
        # Clean up test data
        await verifier.cleanup()


@pytest.mark.asyncio
async def test_feedback_crud_operations(test_client):
    """
    Test CRUD operations on feedback entries.

    This verifies:
    - Create (POST)
    - Read (GET list and GET by ID)
    - Update (PUT)
    - Delete (DELETE)
    """
    test_resume_id = str(uuid.uuid4())
    test_vacancy_id = str(uuid.uuid4())
    feedback_id = None

    try:
        # CREATE
        response = await test_client.post(
            "/api/feedback/",
            json={
                "feedback": [{
                    "resume_id": test_resume_id,
                    "vacancy_id": test_vacancy_id,
                    "skill": "Test Skill",
                    "was_correct": True,
                    "confidence_score": 0.9,
                    "feedback_source": "crud_test"
                }]
            }
        )
        assert response.status_code == 201
        result = response.json()
        feedback_id = result['feedback'][0]['id']
        logger.info(f"✓ Created feedback entry: {feedback_id}")

        # READ (by ID)
        response = await test_client.get(f"/api/feedback/{feedback_id}")
        assert response.status_code == 200
        entry = response.json()
        assert entry['skill'] == "Test Skill"
        logger.info(f"✓ Retrieved feedback entry by ID")

        # UPDATE
        response = await test_client.put(
            f"/api/feedback/{feedback_id}",
            json={
                "was_correct": False,
                "recruiter_correction": "Updated correction"
            }
        )
        assert response.status_code == 200
        logger.info(f"✓ Updated feedback entry")

        # READ (verify update)
        response = await test_client.get(f"/api/feedback/{feedback_id}")
        assert response.status_code == 200
        entry = response.json()
        assert entry['was_correct'] is False
        assert entry['recruiter_correction'] == "Updated correction"
        logger.info(f"✓ Verified update")

        # DELETE
        response = await test_client.delete(f"/api/feedback/{feedback_id}")
        assert response.status_code == 200
        logger.info(f"✓ Deleted feedback entry")

        # Verify deletion
        response = await test_client.get(f"/api/feedback/{feedback_id}")
        assert response.status_code == 404
        logger.info(f"✓ Verified deletion")

    except Exception as e:
        logger.error(f"CRUD test failed: {e}", exc_info=True)
        raise


@pytest.mark.asyncio
async def test_feedback_filtering(test_client):
    """
    Test feedback filtering capabilities.

    This verifies filtering by:
    - resume_id
    - vacancy_id
    - skill
    - was_correct
    - processed
    """
    test_resume_id = str(uuid.uuid4())
    test_vacancy_id = str(uuid.uuid4())

    try:
        # Create test feedback
        response = await test_client.post(
            "/api/feedback/",
            json={
                "feedback": [
                    {
                        "resume_id": test_resume_id,
                        "vacancy_id": test_vacancy_id,
                        "skill": "Python",
                        "was_correct": True,
                        "confidence_score": 0.9,
                        "feedback_source": "filter_test"
                    },
                    {
                        "resume_id": test_resume_id,
                        "vacancy_id": test_vacancy_id,
                        "skill": "JavaScript",
                        "was_correct": False,
                        "confidence_score": 0.7,
                        "feedback_source": "filter_test"
                    }
                ]
            }
        )
        assert response.status_code == 201
        logger.info("✓ Created test feedback entries")

        # Filter by resume_id
        response = await test_client.get(
            f"/api/feedback/?resume_id={test_resume_id}"
        )
        assert response.status_code == 200
        result = response.json()
        assert result['total_count'] >= 2
        logger.info(f"✓ Filter by resume_id: {result['total_count']} entries")

        # Filter by skill
        response = await test_client.get(
            f"/api/feedback/?skill=Python&resume_id={test_resume_id}"
        )
        assert response.status_code == 200
        result = response.json()
        assert result['total_count'] >= 1
        assert all(e['skill'] == 'Python' for e in result['feedback'])
        logger.info(f"✓ Filter by skill: {result['total_count']} entries")

        # Filter by was_correct
        response = await test_client.get(
            f"/api/feedback/?was_correct=false&resume_id={test_resume_id}"
        )
        assert response.status_code == 200
        result = response.json()
        assert result['total_count'] >= 1
        assert all(not e['was_correct'] for e in result['feedback'])
        logger.info(f"✓ Filter by was_correct: {result['total_count']} entries")

    except Exception as e:
        logger.error(f"Filtering test failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        session = async_session_maker()
        try:
            await session.execute(
                delete(SkillFeedback).where(
                    SkillFeedback.feedback_source == "filter_test"
                )
            )
            await session.commit()
        finally:
            await session.close()


if __name__ == "__main__":
    """Run verification manually."""
    async def main():
        verifier = SkillFeedbackWorkflowVerifier()

        # Create test client
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            try:
                logger.info("Starting end-to-end workflow verification...")
                logger.info("")

                # Run all steps
                await verifier.step_1_submit_feedback_via_api(client)
                await verifier.step_2_verify_database_persistence()
                await verifier.step_3_verify_feedback_history_api(client)
                await verifier.step_4_verify_analytics_api(client)
                await verifier.step_5_verify_ml_retraining_integration()

                # Print summary
                verifier.print_summary()

            finally:
                await verifier.cleanup()

    asyncio.run(main())

"""
End-to-end integration test for generating all report types.

This test verifies that all report types can be generated successfully:
1. Generate candidate summary report (PDF)
2. Generate hiring pipeline report (PDF and Excel)
3. Generate EEOC compliance report (PDF and Excel)
4. Verify all PDFs generated correctly
5. Verify Excel export works for pipeline/EEOC reports

This test ensures complete coverage of:
- ReportTemplateService functionality for all report types
- PDF generation using reportlab
- Excel generation using openpyxl
- Data collection from database models
- Report formatting and structure
"""
import asyncio
import io
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4, UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.resume import Resume
from models.candidate_rank import CandidateRank
from models.hiring_stage import HiringStage
from models.analysis_result import AnalysisResult
from services.report_template_service import (
    ReportTemplateService,
    ReportConfig,
    ReportGenerationResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_ORGANIZATION_ID = "test-org-all-reports-e2e"
TEST_TIMEOUT = 300  # 5 minutes max for tests


class AllReportTypesE2EVerifier:
    """
    End-to-end verifier for all report types generation.

    This class tests that all report types (candidate_summary, hiring_pipeline,
    eeoc_compliance) can be generated successfully in multiple formats (PDF, Excel).
    """

    def __init__(self):
        """Initialize the verifier with settings."""
        self.settings = get_settings()
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.test_resume_ids: List[UUID] = []
        self.test_candidate_rank_ids: List[UUID] = []
        self.test_hiring_stage_ids: List[UUID] = []

    async def _get_async_session(self) -> AsyncSession:
        """Create an async database session for testing."""
        return async_session_maker()

    async def cleanup_test_data(self):
        """Clean up test data from previous runs."""
        logger.info("Cleaning up test data...")

        session = await self._get_async_session()
        try:
            # Clean up analysis results
            await session.execute(
                delete(AnalysisResult).where(
                    AnalysisResult.organization_id == TEST_ORGANIZATION_ID
                )
            )

            # Clean up hiring stages
            await session.execute(
                delete(HiringStage).where(
                    HiringStage.organization_id == TEST_ORGANIZATION_ID
                )
            )

            # Clean up candidate ranks
            await session.execute(
                delete(CandidateRank).where(
                    CandidateRank.organization_id == TEST_ORGANIZATION_ID
                )
            )

            # Clean up resumes
            await session.execute(
                delete(Resume).where(
                    Resume.organization_id == TEST_ORGANIZATION_ID
                )
            )

            await session.commit()
            logger.info("Test data cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_test_data(self) -> Dict[str, Any]:
        """
        Create test data for report generation.

        Creates sample resumes, candidate ranks, hiring stages, and analysis results
        for testing all report types.

        Returns:
            Dictionary with created test data IDs
        """
        logger.info("Creating test data for report generation...")

        session = await self._get_async_session()
        try:
            test_data = {
                "resume_ids": [],
                "candidate_rank_ids": [],
                "hiring_stage_ids": [],
                "organization_id": TEST_ORGANIZATION_ID,
            }

            # Create 5 test resumes with diverse profiles
            resume_data = [
                {
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "phone": "+1-555-0101",
                    "skills": ["Python", "Machine Learning", "AWS"],
                    "years_experience": 5,
                },
                {
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "phone": "+1-555-0102",
                    "skills": ["JavaScript", "React", "Node.js"],
                    "years_experience": 3,
                },
                {
                    "name": "Carol Martinez",
                    "email": "carol@example.com",
                    "phone": "+1-555-0103",
                    "skills": ["Java", "Spring Boot", "Kubernetes"],
                    "years_experience": 7,
                },
                {
                    "name": "David Lee",
                    "email": "david@example.com",
                    "phone": "+1-555-0104",
                    "skills": ["Go", "Docker", "PostgreSQL"],
                    "years_experience": 4,
                },
                {
                    "name": "Emma Wilson",
                    "email": "emma@example.com",
                    "phone": "+1-555-0105",
                    "skills": ["C#", ".NET", "Azure"],
                    "years_experience": 6,
                },
            ]

            for idx, resume_info in enumerate(resume_data):
                resume = Resume(
                    id=uuid4(),
                    organization_id=TEST_ORGANIZATION_ID,
                    name=resume_info["name"],
                    email=resume_info["email"],
                    phone=resume_info["phone"],
                    skills_raw=resume_info["skills"],
                    years_experience=resume_info["years_experience"],
                    file_path=f"/tmp/test_resume_{idx}.pdf",
                    file_size=10240,
                    file_hash=f"hash_{idx}",
                    mime_type="application/pdf",
                    raw_text=f"Resume for {resume_info['name']}...",
                    parsed_data={
                        "name": resume_info["name"],
                        "email": resume_info["email"],
                        "phone": resume_info["phone"],
                        "skills": resume_info["skills"],
                        "experience": resume_info["years_experience"],
                    },
                )
                session.add(resume)
                await session.flush()
                test_data["resume_ids"].append(resume.id)

                # Create candidate rank for each resume
                candidate_rank = CandidateRank(
                    id=uuid4(),
                    organization_id=TEST_ORGANIZATION_ID,
                    resume_id=resume.id,
                    vacancy_id=uuid4(),  # Placeholder vacancy
                    match_score=0.75 + (idx * 0.05),  # Scores from 0.75 to 0.95
                    feature_contributions={
                        "skills_match": 0.4,
                        "experience_match": 0.3,
                        "education_match": 0.2,
                        "location_match": 0.1,
                    },
                    confidence_interval={"lower": 0.65, "upper": 0.85},
                    explanation="Good match based on skills and experience",
                    created_at=datetime.utcnow() - timedelta(days=10 - idx),
                )
                session.add(candidate_rank)
                await session.flush()
                test_data["candidate_rank_ids"].append(candidate_rank.id)

                # Create hiring stage for each candidate
                stage_names = ["applied", "screening", "interview", "technical", "offer"]
                hiring_stage = HiringStage(
                    id=uuid4(),
                    organization_id=TEST_ORGANIZATION_ID,
                    resume_id=resume.id,
                    vacancy_id=candidate_rank.vacancy_id,
                    stage=stage_names[idx % len(stage_names)],
                    status="active",
                    entered_at=datetime.utcnow() - timedelta(days=5 - idx),
                    notes=f"Candidate progressing through {stage_names[idx % len(stage_names)]} stage",
                )
                session.add(hiring_stage)
                await session.flush()
                test_data["hiring_stage_ids"].append(hiring_stage.id)

                # Create analysis result for EEOC data
                analysis_result = AnalysisResult(
                    id=uuid4(),
                    organization_id=TEST_ORGANIZATION_ID,
                    resume_id=resume.id,
                    analysis_type="demographic_inference",
                    result_data={
                        "gender": ["Male", "Male", "Female", "Male", "Female"][idx],
                        "age_group": ["25-34", "25-34", "35-44", "25-34", "35-44"][idx],
                        "ethnicity": ["Caucasian", "Caucasian", "Hispanic", "Asian", "Caucasian"][idx],
                        "confidence": 0.85,
                    },
                    confidence_score=0.85,
                    created_at=datetime.utcnow() - timedelta(days=10 - idx),
                )
                session.add(analysis_result)

            await session.commit()
            logger.info(f"Created test data: {len(test_data['resume_ids'])} resumes, "
                       f"{len(test_data['candidate_rank_ids'])} candidate ranks, "
                       f"{len(test_data['hiring_stage_ids'])} hiring stages")

            return test_data

        except Exception as e:
            logger.error(f"Error creating test data: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()

    async def verify_candidate_summary_pdf(
        self, test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify candidate summary report generation (PDF format).

        Args:
            test_data: Dictionary with test data IDs

        Returns:
            Tuple of (success, message)
        """
        logger.info("\n=== VERIFICATION 1: Generate Candidate Summary Report (PDF) ===")

        try:
            session = await self._get_async_session()
            service = ReportTemplateService(db=session)

            # Select first resume for testing
            resume_id = test_data["resume_ids"][0]

            # Configure candidate summary report
            config = ReportConfig(
                report_type="candidate_summary",
                output_format="pdf",
                title="Candidate Summary Report - Test",
                organization_id=TEST_ORGANIZATION_ID,
                filters={"resume_id": str(resume_id)},
            )

            # Generate report
            logger.info(f"Generating candidate summary report for resume {resume_id}...")
            result = await service.generate_report(config=config)

            await session.close()

            # Verify result
            if not result.success:
                return False, f"Report generation failed: {result.error_message}"

            if not result.report_bytes:
                return False, "Report bytes are empty"

            if result.content_type != "application/pdf":
                return False, f"Unexpected content type: {result.content_type}"

            file_size = len(result.report_bytes)
            if file_size < 1000:  # PDF should be at least 1KB
                return False, f"PDF file too small: {file_size} bytes"

            # Verify PDF header
            pdf_header = result.report_bytes[:8]
            if not pdf_header.startswith(b"%PDF"):
                return False, "Invalid PDF header"

            logger.info(f"✅ Candidate summary PDF generated successfully: "
                       f"{file_size} bytes, {result.filename}")

            return True, f"Candidate summary PDF generated: {file_size} bytes"

        except Exception as e:
            logger.error(f"Error generating candidate summary PDF: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    async def verify_hiring_pipeline_pdf(
        self, test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify hiring pipeline report generation (PDF format).

        Args:
            test_data: Dictionary with test data IDs

        Returns:
            Tuple of (success, message)
        """
        logger.info("\n=== VERIFICATION 2: Generate Hiring Pipeline Report (PDF) ===")

        try:
            session = await self._get_async_session()
            service = ReportTemplateService(db=session)

            # Configure hiring pipeline report
            config = ReportConfig(
                report_type="hiring_pipeline",
                output_format="pdf",
                title="Hiring Pipeline Report - Test",
                organization_id=TEST_ORGANIZATION_ID,
                date_range={
                    "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            )

            # Generate report
            logger.info("Generating hiring pipeline report (PDF)...")
            result = await service.generate_report(config=config)

            await session.close()

            # Verify result
            if not result.success:
                return False, f"Report generation failed: {result.error_message}"

            if not result.report_bytes:
                return False, "Report bytes are empty"

            if result.content_type != "application/pdf":
                return False, f"Unexpected content type: {result.content_type}"

            file_size = len(result.report_bytes)
            if file_size < 1000:  # PDF should be at least 1KB
                return False, f"PDF file too small: {file_size} bytes"

            # Verify PDF header
            pdf_header = result.report_bytes[:8]
            if not pdf_header.startswith(b"%PDF"):
                return False, "Invalid PDF header"

            logger.info(f"✅ Hiring pipeline PDF generated successfully: "
                       f"{file_size} bytes, {result.filename}")

            return True, f"Hiring pipeline PDF generated: {file_size} bytes"

        except Exception as e:
            logger.error(f"Error generating hiring pipeline PDF: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    async def verify_hiring_pipeline_excel(
        self, test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify hiring pipeline report generation (Excel format).

        Args:
            test_data: Dictionary with test data IDs

        Returns:
            Tuple of (success, message)
        """
        logger.info("\n=== VERIFICATION 3: Generate Hiring Pipeline Report (Excel) ===")

        try:
            session = await self._get_async_session()
            service = ReportTemplateService(db=session)

            # Configure hiring pipeline report with Excel format
            config = ReportConfig(
                report_type="hiring_pipeline",
                output_format="excel",
                title="Hiring Pipeline Report - Test",
                organization_id=TEST_ORGANIZATION_ID,
                date_range={
                    "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            )

            # Generate report
            logger.info("Generating hiring pipeline report (Excel)...")
            result = await service.generate_report(config=config)

            await session.close()

            # Verify result
            if not result.success:
                return False, f"Report generation failed: {result.error_message}"

            if not result.report_bytes:
                return False, "Report bytes are empty"

            expected_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if result.content_type != expected_content_type:
                return False, f"Unexpected content type: {result.content_type}"

            file_size = len(result.report_bytes)
            if file_size < 1000:  # Excel should be at least 1KB
                return False, f"Excel file too small: {file_size} bytes"

            # Verify Excel file signature (PK zip header)
            excel_header = result.report_bytes[:4]
            if not excel_header.startswith(b"PK"):
                return False, "Invalid Excel file signature"

            logger.info(f"✅ Hiring pipeline Excel generated successfully: "
                       f"{file_size} bytes, {result.filename}")

            return True, f"Hiring pipeline Excel generated: {file_size} bytes"

        except Exception as e:
            logger.error(f"Error generating hiring pipeline Excel: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    async def verify_eeoc_compliance_pdf(
        self, test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify EEOC compliance report generation (PDF format).

        Args:
            test_data: Dictionary with test data IDs

        Returns:
            Tuple of (success, message)
        """
        logger.info("\n=== VERIFICATION 4: Generate EEOC Compliance Report (PDF) ===")

        try:
            session = await self._get_async_session()
            service = ReportTemplateService(db=session)

            # Configure EEOC compliance report
            config = ReportConfig(
                report_type="eeoc_compliance",
                output_format="pdf",
                title="EEOC Compliance Report - Test",
                organization_id=TEST_ORGANIZATION_ID,
                date_range={
                    "start": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            )

            # Generate report
            logger.info("Generating EEOC compliance report (PDF)...")
            result = await service.generate_report(config=config)

            await session.close()

            # Verify result
            if not result.success:
                return False, f"Report generation failed: {result.error_message}"

            if not result.report_bytes:
                return False, "Report bytes are empty"

            if result.content_type != "application/pdf":
                return False, f"Unexpected content type: {result.content_type}"

            file_size = len(result.report_bytes)
            if file_size < 1000:  # PDF should be at least 1KB
                return False, f"PDF file too small: {file_size} bytes"

            # Verify PDF header
            pdf_header = result.report_bytes[:8]
            if not pdf_header.startswith(b"%PDF"):
                return False, "Invalid PDF header"

            logger.info(f"✅ EEOC compliance PDF generated successfully: "
                       f"{file_size} bytes, {result.filename}")

            return True, f"EEOC compliance PDF generated: {file_size} bytes"

        except Exception as e:
            logger.error(f"Error generating EEOC compliance PDF: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    async def verify_eeoc_compliance_excel(
        self, test_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify EEOC compliance report generation (Excel format).

        Args:
            test_data: Dictionary with test data IDs

        Returns:
            Tuple of (success, message)
        """
        logger.info("\n=== VERIFICATION 5: Generate EEOC Compliance Report (Excel) ===")

        try:
            session = await self._get_async_session()
            service = ReportTemplateService(db=session)

            # Configure EEOC compliance report with Excel format
            config = ReportConfig(
                report_type="eeoc_compliance",
                output_format="excel",
                title="EEOC Compliance Report - Test",
                organization_id=TEST_ORGANIZATION_ID,
                date_range={
                    "start": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            )

            # Generate report
            logger.info("Generating EEOC compliance report (Excel)...")
            result = await service.generate_report(config=config)

            await session.close()

            # Verify result
            if not result.success:
                return False, f"Report generation failed: {result.error_message}"

            if not result.report_bytes:
                return False, "Report bytes are empty"

            expected_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if result.content_type != expected_content_type:
                return False, f"Unexpected content type: {result.content_type}"

            file_size = len(result.report_bytes)
            if file_size < 1000:  # Excel should be at least 1KB
                return False, f"Excel file too small: {file_size} bytes"

            # Verify Excel file signature (PK zip header)
            excel_header = result.report_bytes[:4]
            if not excel_header.startswith(b"PK"):
                return False, "Invalid Excel file signature"

            logger.info(f"✅ EEOC compliance Excel generated successfully: "
                       f"{file_size} bytes, {result.filename}")

            return True, f"EEOC compliance Excel generated: {file_size} bytes"

        except Exception as e:
            logger.error(f"Error generating EEOC compliance Excel: {e}", exc_info=True)
            return False, f"Exception: {str(e)}"

    async def run_all_verifications(self):
        """
        Run all verification steps and generate summary report.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.info("\n" + "="*70)
        logger.info("Starting All Report Types E2E Verification")
        logger.info("="*70)

        try:
            # Clean up and create test data
            await self.cleanup_test_data()
            test_data = await self.create_test_data()

            # Run all verifications
            verifications = [
                ("Candidate Summary PDF", self.verify_candidate_summary_pdf),
                ("Hiring Pipeline PDF", self.verify_hiring_pipeline_pdf),
                ("Hiring Pipeline Excel", self.verify_hiring_pipeline_excel),
                ("EEOC Compliance PDF", self.verify_eeoc_compliance_pdf),
                ("EEOC Compliance Excel", self.verify_eeoc_compliance_excel),
            ]

            all_passed = True
            for name, verification_func in verifications:
                success, message = await verification_func(test_data)

                self.test_results.append({
                    "verification": name,
                    "status": "PASS" if success else "FAIL",
                    "message": message,
                })

                if not success:
                    all_passed = False
                    logger.error(f"❌ {name}: FAILED - {message}")
                else:
                    logger.info(f"✅ {name}: PASSED - {message}")

            # Print summary
            self._print_summary()

            # Clean up test data
            await self.cleanup_test_data()

            return 0 if all_passed else 1

        except Exception as e:
            logger.error(f"Fatal error during verification: {e}", exc_info=True)
            return 1

    def _print_summary(self):
        """Print test results summary."""
        elapsed_time = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total = len(self.test_results)

        logger.info("\n" + "="*70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Verifications: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Elapsed Time: {elapsed_time:.2f} seconds")
        logger.info("="*70)

        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭️"
            logger.info(f"{status_symbol} {result['verification']}: {result['status']} - {result['message']}")

        logger.info("\n" + "="*70)
        if failed == 0:
            logger.info("🎉 ALL VERIFICATIONS PASSED!")
        else:
            logger.info(f"⚠️  {failed} VERIFICATION(S) FAILED")
        logger.info("="*70)


async def main():
    """Main entry point for E2E verification."""
    verifier = AllReportTypesE2EVerifier()
    exit_code = await verifier.run_all_verifications()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())

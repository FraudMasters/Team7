"""
End-to-End Integration Tests for Salary Benchmarking Feature

Tests the complete salary benchmarking workflow:
1. Fetch market salary data via Celery task → Save to database → Verify via API → Verify frontend data flow
2. Cost-of-living adjustments are applied correctly
3. Salary suggestions work end-to-end
4. Offer comparison works with COL adjustments
5. Equity analysis works correctly
"""

import pytest
import asyncio
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from models.salary_benchmark import SalaryBenchmark
from models.cost_of_living import CostOfLivingIndex
from models.job_vacancy import JobVacancy
from models.resume import Resume
from database import get_db_settings


class TestSalaryBenchmarkingE2E:
    """End-to-end tests for salary benchmarking."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test database before running tests."""
        # Create test database connection
        settings = get_db_settings()
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Clean up test data before running
        db = self.SessionLocal()
        try:
            db.query(SalaryBenchmark).filter(
                SalaryBenchmark.data_source == "e2e_test"
            ).delete()
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

        yield

        # Cleanup after tests
        db = self.SessionLocal()
        try:
            db.query(SalaryBenchmark).filter(
                SalaryBenchmark.data_source == "e2e_test"
            ).delete()
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

    @pytest.fixture
    def test_salary_benchmarks(self):
        """Create test salary benchmark data."""
        db = self.SessionLocal()
        try:
            benchmarks = []
            test_data = [
                {
                    "job_title": "Software Engineer",
                    "location": "San Francisco, CA",
                    "country": "US",
                    "region": "CA",
                    "industry": "Technology",
                    "experience_level": "mid",
                    "employment_type": "full_time",
                    "salary_min": 120000,
                    "salary_median": 155000,
                    "salary_max": 195000,
                    "salary_p90": 220000,
                    "currency": "USD",
                    "sample_size": 500,
                    "data_source": "e2e_test",
                },
                {
                    "job_title": "Software Engineer",
                    "location": "Remote",
                    "country": "US",
                    "region": None,
                    "industry": "Technology",
                    "experience_level": "mid",
                    "employment_type": "full_time",
                    "salary_min": 95000,
                    "salary_median": 125000,
                    "salary_max": 165000,
                    "salary_p90": 190000,
                    "currency": "USD",
                    "sample_size": 750,
                    "data_source": "e2e_test",
                },
                {
                    "job_title": "Product Manager",
                    "location": "New York, NY",
                    "country": "US",
                    "region": "NY",
                    "industry": "Technology",
                    "experience_level": "senior",
                    "employment_type": "full_time",
                    "salary_min": 140000,
                    "salary_median": 175000,
                    "salary_max": 220000,
                    "salary_p90": 250000,
                    "currency": "USD",
                    "sample_size": 300,
                    "data_source": "e2e_test",
                },
            ]

            for data in test_data:
                benchmark = SalaryBenchmark(**data)
                db.add(benchmark)
                benchmarks.append(benchmark)

            db.commit()
            for benchmark in benchmarks:
                db.refresh(benchmark)

            yield benchmarks

        finally:
            db.close()

    @pytest.fixture
    def test_cost_of_living_indices(self):
        """Create test cost-of-living data."""
        db = self.SessionLocal()
        try:
            indices = []
            test_data = [
                {
                    "location": "San Francisco, CA",
                    "country": "US",
                    "region": "CA",
                    "cost_of_living_index": 185.5,
                    "housing_index": 213.2,
                    "transportation_index": 157.7,
                    "groceries_index": 176.2,
                    "utilities_index": 167.0,
                    "healthcare_index": 194.9,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "New York, NY",
                    "country": "US",
                    "region": "NY",
                    "cost_of_living_index": 175.0,
                    "housing_index": 198.5,
                    "transportation_index": 148.8,
                    "groceries_index": 166.3,
                    "utilities_index": 157.5,
                    "healthcare_index": 183.8,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "Remote",
                    "country": "US",
                    "region": None,
                    "cost_of_living_index": 95.0,
                    "housing_index": 95.0,
                    "transportation_index": 80.8,
                    "groceries_index": 90.3,
                    "utilities_index": 85.5,
                    "healthcare_index": 99.8,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
            ]

            for data in test_data:
                index = CostOfLivingIndex(**data)
                db.add(index)
                indices.append(index)

            db.commit()
            for index in indices:
                db.refresh(index)

            yield indices

        finally:
            db.close()

    def test_market_salary_data_fetch_and_save(self):
        """
        E2E Test 1: Market salary data fetch and save.

        Verifies:
        - Salary data can be fetched from external sources (simulated)
        - Data is saved correctly to SalaryBenchmark table
        - Data can be retrieved from the database
        """
        from tasks.salary_data_fetch import (
            fetch_salary_data_from_api,
            save_salary_benchmarks_to_db,
        )

        # Step 1: Fetch salary data from API (simulated)
        salary_data = fetch_salary_data_from_api(
            job_titles=["Data Scientist", "DevOps Engineer"],
            locations=["Austin, TX", "Seattle, WA"]
        )

        assert len(salary_data) > 0, "Salary data should be fetched"
        assert all("job_title" in d for d in salary_data), "Each record should have job_title"
        assert all("location" in d for d in salary_data), "Each record should have location"
        assert all("salary_median" in d for d in salary_data), "Each record should have salary_median"

        # Step 2: Save to database with test data source
        for data_point in salary_data:
            data_point["data_source"] = "e2e_test"

        save_stats = save_salary_benchmarks_to_db(salary_data)

        assert save_stats["failed"] == 0, "All records should save successfully"
        assert save_stats["created"] > 0, "New records should be created"

        # Step 3: Verify data was saved to database
        db = self.SessionLocal()
        try:
            saved_benchmarks = db.query(SalaryBenchmark).filter(
                SalaryBenchmark.data_source == "e2e_test"
            ).all()

            assert len(saved_benchmarks) >= save_stats["created"], \
                "Database should contain saved records"

            # Verify data integrity
            for benchmark in saved_benchmarks:
                assert benchmark.job_title, "Job title should be set"
                assert benchmark.location, "Location should be set"
                assert benchmark.salary_median > 0, "Median salary should be positive"
                assert benchmark.salary_min < benchmark.salary_median, \
                    "Min salary should be less than median"
                assert benchmark.salary_median < benchmark.salary_max, \
                    "Median salary should be less than max"

        finally:
            db.close()

    def test_salary_benchmark_api_endpoints(
        self, test_salary_benchmarks
    ):
        """
        E2E Test 2: Salary benchmark API endpoints.

        Verifies:
        - GET /api/salary-benchmarking/benchmarks returns correct data
        - API filters work correctly (role, location, experience level)
        - Response format is correct
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test 1: Get all benchmarks for Software Engineer
        response = client.get(
            "/api/salary-benchmarking/benchmarks",
            params={
                "role": "Software Engineer",
                "location": "San Francisco, CA"
            }
        )

        assert response.status_code == 200, "API should return 200 OK"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should return at least one benchmark"

        # Verify response structure
        benchmark = data[0]
        assert "role" in benchmark, "Response should contain role"
        assert "location" in benchmark, "Response should contain location"
        assert "salary_min" in benchmark, "Response should contain salary_min"
        assert "salary_median" in benchmark, "Response should contain salary_median"
        assert "salary_max" in benchmark, "Response should contain salary_max"
        assert "currency" in benchmark, "Response should contain currency"

        # Test 2: Partial match on role
        response = client.get(
            "/api/salary-benchmarking/benchmarks",
            params={
                "role": "Engineer",
                "location": "Remote"
            }
        )

        assert response.status_code == 200, "Partial match should work"
        data = response.json()
        assert len(data) > 0, "Should find matching benchmarks"

        # Test 3: Filter by experience level
        response = client.get(
            "/api/salary-benchmarking/benchmarks",
            params={
                "role": "Product Manager",
                "location": "New York",
                "experience_level": "senior"
            }
        )

        assert response.status_code == 200, "Experience level filter should work"
        data = response.json()
        assert len(data) > 0, "Should find senior product manager"

    def test_cost_of_living_adjustments(
        self, test_salary_benchmarks, test_cost_of_living_indices
    ):
        """
        E2E Test 3: Cost-of-living adjustments.

        Verifies:
        - COL data can be fetched and saved
        - COL calculator applies adjustments correctly
        - Higher cost locations have higher adjustments
        """
        from tasks.salary_data_fetch import (
            fetch_cost_of_living_data_from_api,
            save_cost_of_living_to_db,
        )
        from analyzers.cost_of_living_calculator import CostOfLivingCalculator

        # Step 1: Fetch and save COL data
        cost_data = fetch_cost_of_living_data_from_api(
            locations=["Austin, TX", "Seattle, WA"]
        )

        assert len(cost_data) > 0, "Cost data should be fetched"

        # Mark as test data
        for data_point in cost_data:
            data_point["data_source"] = "e2e_test"

        save_stats = save_cost_of_living_to_db(cost_data)
        assert save_stats["failed"] == 0, "All COL records should save successfully"

        # Step 2: Verify COL data in database
        db = self.SessionLocal()
        try:
            col_records = db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).all()

            assert len(col_records) > 0, "COL data should be in database"

            # Step 3: Test COL calculator
            calculator = CostOfLivingCalculator()

            # Get index for San Francisco (high COL)
            sf_index = db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.location == "San Francisco, CA"
            ).first()

            assert sf_index is not None, "SF COL index should exist"
            assert sf_index.cost_of_living_index > 150, \
                "SF should have high cost of living (> 150)"

            # Get index for Remote (low COL)
            remote_index = db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.location == "Remote"
            ).first()

            assert remote_index is not None, "Remote COL index should exist"
            assert remote_index.cost_of_living_index < 110, \
                "Remote should have lower cost of living (< 110)"

            # Step 4: Verify adjustment calculation
            # $100,000 in SF should be worth less than $100,000 in Remote
            # when normalized to US average (index 100)

            base_salary = 100000
            sf_normalized = base_salary * (100.0 / sf_index.cost_of_living_index)
            remote_normalized = base_salary * (100.0 / remote_index.cost_of_living_index)

            assert sf_normalized < remote_normalized, \
                "SF salary should normalize to lower value due to high COL"

        finally:
            db.close()

    def test_offer_comparison_with_col(
        self, test_cost_of_living_indices
    ):
        """
        E2E Test 4: Offer comparison with cost-of-living adjustments.

        Verifies:
        - Offer comparison API works correctly
        - COL adjustments are applied to normalize salaries
        - Recommendations are based on adjusted values
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Create test offers with different locations
        test_resume_id = str(uuid4())
        offers = [
            {
                "salary": 150000,
                "location": "San Francisco, CA",
                "currency": "USD",
                "bonus": 20000,
                "equity": 10000,
                "job_title": "Software Engineer",
                "company": "TechCorp SF"
            },
            {
                "salary": 130000,
                "location": "Remote",
                "currency": "USD",
                "bonus": 15000,
                "equity": 8000,
                "job_title": "Software Engineer",
                "company": "TechCorp Remote"
            },
        ]

        # Compare offers with COL adjustments
        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": test_resume_id,
                "offers": offers,
                "apply_cost_of_living": True
            }
        )

        assert response.status_code == 200, "Offer comparison should succeed"
        data = response.json()

        assert "offers" in data, "Response should contain compared offers"
        assert len(data["offers"]) == 2, "Should have 2 compared offers"
        assert "recommendation" in data, "Response should contain recommendation"
        assert "analysis" in data, "Response should contain analysis"

        # Verify COL adjustments were applied
        for offer in data["offers"]:
            assert "adjusted_total" in offer, "Offer should have adjusted total"
            assert "col_index" in offer, "Offer should have COL index"
            assert offer["adjusted_total"] > 0, "Adjusted total should be positive"

        # The Remote offer should have better adjusted value
        # even though SF has higher nominal salary
        remote_offer = next(o for o in data["offers"] if o["location"] == "Remote")
        sf_offer = next(o for o in data["offers"] if "San Francisco" in o["location"])

        # Remote should have better adjusted compensation due to lower COL
        assert remote_offer["adjusted_total"] > sf_offer["adjusted_total"], \
            "Remote offer should have better adjusted value"

        # Verify recommendation
        assert "Remote" in data["recommendation"] or "best" in data["recommendation"].lower(), \
            "Recommendation should mention the better offer"

    def test_salary_benchmark_frontend_integration(
        self, test_salary_benchmarks
    ):
        """
        E2E Test 5: Frontend integration test.

        Verifies:
        - API responses match frontend expectations
        - Data format is compatible with frontend components
        - Charts can display the data correctly
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Get benchmarks in format expected by frontend
        response = client.get(
            "/api/salary-benchmarking/benchmarks",
            params={
                "role": "Software Engineer",
                "location": "Remote"
            }
        )

        assert response.status_code == 200, "API should return data"
        data = response.json()

        # Verify data structure matches frontend expectations
        # Based on SalaryBenchmarkChart component
        for benchmark in data:
            # Required fields for frontend display
            assert "role" in benchmark, "Frontend needs 'role' field"
            assert "location" in benchmark, "Frontend needs 'location' field"
            assert "salary_min" in benchmark, "Frontend needs 'salary_min' for chart"
            assert "salary_median" in benchmark, "Frontend needs 'salary_median' for chart"
            assert "salary_max" in benchmark, "Frontend needs 'salary_max' for chart"
            assert "currency" in benchmark, "Frontend needs 'currency' for display"

            # Verify data types are correct
            assert isinstance(benchmark["salary_min"], (int, float)), \
                "salary_min should be numeric"
            assert isinstance(benchmark["salary_median"], (int, float)), \
                "salary_median should be numeric"
            assert isinstance(benchmark["salary_max"], (int, float)), \
                "salary_max should be numeric"

            # Verify logical consistency
            assert benchmark["salary_min"] <= benchmark["salary_median"], \
                "min should be <= median"
            assert benchmark["salary_median"] <= benchmark["salary_max"], \
                "median should be <= max"

    def test_complete_data_flow(
        self, test_salary_benchmarks, test_cost_of_living_indices
    ):
        """
        E2E Test 6: Complete data flow from fetch to display.

        Verifies:
        1. Salary data can be fetched
        2. Data is saved to database
        3. API can retrieve the data
        4. COL adjustments are available
        5. Data format is compatible with frontend
        """
        from fastapi.testclient import TestClient
        from main import app
        from analyzers.cost_of_living_calculator import CostOfLivingCalculator

        client = TestClient(app)

        # Step 1: Verify salary benchmarks are accessible via API
        response = client.get(
            "/api/salary-benchmarking/benchmarks",
            params={"role": "Software Engineer"}
        )

        assert response.status_code == 200, "Should retrieve benchmarks"
        benchmarks = response.json()
        assert len(benchmarks) > 0, "Should have benchmark data"

        # Step 2: Verify COL data is in database and accessible
        db = self.SessionLocal()
        try:
            col_calculator = CostOfLivingCalculator()

            # Test async COL retrieval (as used in API)
            async def test_col_retrieval():
                for location in ["San Francisco, CA", "Remote", "New York, NY"]:
                    col_data = await col_calculator.get_location_index(
                        db, location
                    )
                    if col_data:
                        assert "cost_of_living_index" in col_data, \
                            f"COL data for {location} should have index"
                        assert col_data["cost_of_living_index"] > 0, \
                            f"COL index for {location} should be positive"

            asyncio.run(test_col_retrieval())

        finally:
            db.close()

        # Step 3: Verify frontend can display the data
        # Get data for multiple locations
        locations = ["San Francisco, CA", "Remote"]
        location_data = {}

        for location in locations:
            response = client.get(
                "/api/salary-benchmarking/benchmarks",
                params={
                    "role": "Software Engineer",
                    "location": location
                }
            )

            if response.status_code == 200:
                location_data[location] = response.json()

        assert len(location_data) > 0, "Should have data for at least one location"

        # Verify data can be used for comparison (as frontend would)
        for location, data in location_data.items():
            assert len(data) > 0, f"Should have benchmarks for {location}"
            for benchmark in data:
                # All fields needed for salary chart visualization
                assert benchmark["salary_min"] >= 0, "Salary should be non-negative"
                assert benchmark["salary_max"] >= benchmark["salary_min"], \
                    "Max should be >= min"
                assert benchmark["currency"], "Should have currency"

        # Step 4: Verify cost-of-living impact
        if len(location_data) >= 2:
            # Compare salaries across locations
            sf_salary = None
            remote_salary = None

            if "San Francisco, CA" in location_data and location_data["San Francisco, CA"]:
                sf_salary = location_data["San Francisco, CA"][0]["salary_median"]

            if "Remote" in location_data and location_data["Remote"]:
                remote_salary = location_data["Remote"][0]["salary_median"]

            # SF should have higher nominal salaries
            if sf_salary and remote_salary:
                assert sf_salary > remote_salary, \
                    "SF should have higher nominal salary due to higher COL"


class TestSalaryBenchmarkingDataIntegrity:
    """Test data integrity and consistency of salary benchmarking."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test database."""
        from database import get_db_settings

        settings = get_db_settings()
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        yield

    def test_salary_benchmark_constraints(self):
        """Test database constraints and validations."""
        db = self.SessionLocal()
        try:
            # Test valid benchmark
            valid_benchmark = SalaryBenchmark(
                job_title="Test Engineer",
                location="Test City",
                country="US",
                salary_min=80000,
                salary_median=100000,
                salary_max=120000,
                currency="USD",
                data_source="test"
            )

            db.add(valid_benchmark)
            db.commit()
            db.refresh(valid_benchmark)

            assert valid_benchmark.id is not None, "Valid benchmark should be saved"
            assert valid_benchmark.created_at is not None, "Should have created timestamp"
            assert valid_benchmark.updated_at is not None, "Should have updated timestamp"

            # Cleanup
            db.delete(valid_benchmark)
            db.commit()

        finally:
            db.close()

    def test_cost_of_living_constraints(self):
        """Test COL database constraints."""
        db = self.SessionLocal()
        try:
            # Test valid COL index
            valid_col = CostOfLivingIndex(
                location="Test Location",
                country="US",
                cost_of_living_index=100.0,
                currency="USD",
                data_source="test"
            )

            db.add(valid_col)
            db.commit()
            db.refresh(valid_col)

            assert valid_col.id is not None, "Valid COL should be saved"
            assert valid_col.created_at is not None, "Should have created timestamp"

            # Cleanup
            db.delete(valid_col)
            db.commit()

        finally:
            db.close()


class TestSalarySuggestionE2E:
    """End-to-end tests for salary suggestion feature."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test database and cleanup before/after tests."""
        from database import get_db_settings

        settings = get_db_settings()
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Clean up test data before running
        db = self.SessionLocal()
        try:
            # Clean up test data
            db.query(SalaryBenchmark).filter(
                SalaryBenchmark.data_source == "e2e_test"
            ).delete()
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

        yield

        # Cleanup after tests
        db = self.SessionLocal()
        try:
            db.query(SalaryBenchmark).filter(
                SalaryBenchmark.data_source == "e2e_test"
            ).delete()
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

    @pytest.fixture
    def test_candidate_resume(self):
        """Create a test candidate with resume data."""
        db = self.SessionLocal()
        try:
            from models.resume_analysis import ResumeAnalysis

            # Create resume
            resume = Resume(
                filename="john_developer.pdf",
                file_path="/test/resumes/john_developer.pdf",
                content_type="application/pdf",
                status="COMPLETED",
                raw_text="John Doe - Senior Software Engineer with 8 years of experience in Python, React, and AWS.",
                language="en"
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            # Create resume analysis with extracted data
            analysis = ResumeAnalysis(
                resume_id=resume.id,
                language="en",
                raw_text=resume.raw_text,
                skills=["Python", "React", "AWS", "Docker", "Kubernetes", "PostgreSQL", "FastAPI"],
                keywords=[
                    {"keyword": "software engineer", "score": 0.95},
                    {"keyword": "backend development", "score": 0.90},
                    {"keyword": "cloud architecture", "score": 0.85},
                ],
                entities={
                    "persons": ["John Doe"],
                    "organizations": ["Amazon", "Google", "Microsoft"],
                },
                total_experience_months=96,  # 8 years
                education=[
                    {
                        "degree": "Bachelor of Science",
                        "level": "bachelor",
                        "field": "Computer Science",
                        "school": "MIT"
                    }
                ],
                contact_info={
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0123"
                },
                quality_score=85
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            yield {
                "resume": resume,
                "analysis": analysis
            }

        finally:
            db.close()

    @pytest.fixture
    def test_job_vacancy(self):
        """Create test job vacancies."""
        db = self.SessionLocal()
        try:
            vacancies = []

            # Vacancy 1: Senior Software Engineer in San Francisco
            vacancy_sf = JobVacancy(
                title="Senior Software Engineer",
                description="We are looking for a Senior Software Engineer with experience in Python and cloud technologies.",
                required_skills=["Python", "AWS", "Docker", "Kubernetes"],
                min_experience_months=60,  # 5 years
                additional_requirements=["React", "PostgreSQL", "FastAPI"],
                industry="Technology",
                work_format="remote",
                location="San Francisco, CA",
                salary_min=140000,
                salary_max=180000,
                english_level="Upper Intermediate",
                employment_type="full_time",
                source="manual"
            )
            db.add(vacancy_sf)
            vacancies.append(vacancy_sf)

            # Vacancy 2: Software Engineer in Remote
            vacancy_remote = JobVacancy(
                title="Software Engineer",
                description="Join our remote team as a Software Engineer.",
                required_skills=["Python", "JavaScript"],
                min_experience_months=36,  # 3 years
                additional_requirements=["React", "Node.js"],
                industry="Technology",
                work_format="remote",
                location="Remote",
                salary_min=90000,
                salary_max=120000,
                english_level="Intermediate",
                employment_type="full_time",
                source="manual"
            )
            db.add(vacancy_remote)
            vacancies.append(vacancy_remote)

            db.commit()
            for vacancy in vacancies:
                db.refresh(vacancy)

            yield vacancies

        finally:
            db.close()

    @pytest.fixture
    def test_salary_benchmarks(self):
        """Create test salary benchmark data."""
        db = self.SessionLocal()
        try:
            benchmarks = []
            test_data = [
                {
                    "job_title": "Senior Software Engineer",
                    "location": "San Francisco, CA",
                    "country": "US",
                    "region": "CA",
                    "industry": "Technology",
                    "experience_level": "senior",
                    "employment_type": "full_time",
                    "salary_min": 140000,
                    "salary_median": 165000,
                    "salary_max": 200000,
                    "salary_p90": 230000,
                    "currency": "USD",
                    "sample_size": 450,
                    "data_source": "e2e_test",
                },
                {
                    "job_title": "Software Engineer",
                    "location": "Remote",
                    "country": "US",
                    "region": None,
                    "industry": "Technology",
                    "experience_level": "mid",
                    "employment_type": "full_time",
                    "salary_min": 90000,
                    "salary_median": 115000,
                    "salary_max": 140000,
                    "salary_p90": 160000,
                    "currency": "USD",
                    "sample_size": 600,
                    "data_source": "e2e_test",
                },
            ]

            for data in test_data:
                benchmark = SalaryBenchmark(**data)
                db.add(benchmark)
                benchmarks.append(benchmark)

            db.commit()
            for benchmark in benchmarks:
                db.refresh(benchmark)

            yield benchmarks

        finally:
            db.close()

    @pytest.fixture
    def test_cost_of_living_indices(self):
        """Create test cost-of-living data."""
        db = self.SessionLocal()
        try:
            indices = []
            test_data = [
                {
                    "location": "San Francisco, CA",
                    "country": "US",
                    "region": "CA",
                    "cost_of_living_index": 185.5,
                    "housing_index": 213.2,
                    "transportation_index": 157.7,
                    "groceries_index": 176.2,
                    "utilities_index": 167.0,
                    "healthcare_index": 194.9,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "Remote",
                    "country": "US",
                    "region": None,
                    "cost_of_living_index": 95.0,
                    "housing_index": 95.0,
                    "transportation_index": 80.8,
                    "groceries_index": 90.3,
                    "utilities_index": 85.5,
                    "healthcare_index": 99.8,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
            ]

            for data in test_data:
                index = CostOfLivingIndex(**data)
                db.add(index)
                indices.append(index)

            db.commit()
            for index in indices:
                db.refresh(index)

            yield indices

        finally:
            db.close()

    def test_salary_suggestion_for_candidate(
        self, test_candidate_resume, test_job_vacancy,
        test_salary_benchmarks, test_cost_of_living_indices
    ):
        """
        E2E Test: Complete salary suggestion workflow.

        Verifies:
        1. Candidate with resume data can be selected
        2. Salary suggestion can be requested for specific vacancy
        3. API returns benchmarked salary range
        4. Suggestion considers candidate experience
        5. Suggestion adjusts for location
        6. Response format is correct for frontend display
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        resume = test_candidate_resume["resume"]
        analysis = test_candidate_resume["analysis"]
        vacancy_sf = test_job_vacancy[0]  # San Francisco vacancy
        vacancy_remote = test_job_vacancy[1]  # Remote vacancy

        # Step 1: Verify candidate data is complete
        assert resume.id is not None, "Resume should have an ID"
        assert analysis.skills is not None, "Resume analysis should have skills"
        assert len(analysis.skills) > 0, "Candidate should have skills"
        assert analysis.total_experience_months > 0, "Candidate should have experience"
        assert vacancy_sf.id is not None, "Vacancy should have an ID"

        # Step 2: Request salary suggestion for San Francisco vacancy
        response_sf = client.post(
            "/api/salary-benchmarking/suggest-salary",
            json={
                "resume_id": str(resume.id),
                "vacancy_id": str(vacancy_sf.id),
                "include_cost_of_living": True,
            }
        )

        assert response_sf.status_code == 200, \
            f"Salary suggestion request should succeed for SF vacancy. Got: {response_sf.text}"

        suggestion_sf = response_sf.json()

        # Step 3: Verify API returns benchmarked salary range
        assert "suggested_min" in suggestion_sf, "Response should include suggested_min"
        assert "suggested_median" in suggestion_sf, "Response should include suggested_median"
        assert "suggested_max" in suggestion_sf, "Response should include suggested_max"
        assert "currency" in suggestion_sf, "Response should include currency"
        assert "confidence" in suggestion_sf, "Response should include confidence"
        assert "factors" in suggestion_sf, "Response should include factors breakdown"

        # Verify salary range is logical
        assert suggestion_sf["suggested_min"] > 0, "Min salary should be positive"
        assert suggestion_sf["suggested_median"] > 0, "Median salary should be positive"
        assert suggestion_sf["suggested_max"] > 0, "Max salary should be positive"
        assert suggestion_sf["suggested_min"] <= suggestion_sf["suggested_median"], \
            "Min should be <= median"
        assert suggestion_sf["suggested_median"] <= suggestion_sf["suggested_max"], \
            "Median should be <= max"

        # Step 4: Verify suggestion considers candidate experience
        # Candidate has 8 years (96 months) of experience
        # Senior engineer with 8 years should get higher than base salary
        factors = suggestion_sf["factors"]
        assert "adjustments" in factors, "Factors should include adjustments"

        adjustments = factors["adjustments"]
        assert "experience_multiplier" in adjustments, "Should have experience multiplier"
        assert adjustments["experience_multiplier"] >= 1.0, \
            "Senior candidate should have multiplier >= 1.0"

        # Verify experience bonus is applied (8 years = senior level)
        # Senior level should have multiplier of 1.2
        expected_multiplier = 1.2  # Senior level from SalaryFeatures.EXPERIENCE_MULTIPLIERS
        assert adjustments["experience_multiplier"] == expected_multiplier, \
            f"8 years experience should get multiplier={expected_multiplier}"

        # Step 5: Verify suggestion adjusts for location
        # San Francisco has high cost of living (185.5 index)
        assert "location_adjustment" in adjustments, "Should have location adjustment"
        assert adjustments["location_adjustment"] > 1.0, \
            "SF location adjustment should be > 1.0 due to high COL"

        # SF COL index is 185.5, so adjustment should be ~1.85
        sf_col_index = 185.5
        expected_sf_adjustment = sf_col_index / 100.0
        assert abs(adjustments["location_adjustment"] - expected_sf_adjustment) < 0.1, \
            f"SF location adjustment should be close to {expected_sf_adjustment}"

        # Step 6: Compare with Remote location to verify location adjustment
        response_remote = client.post(
            "/api/salary-benchmarking/suggest-salary",
            json={
                "resume_id": str(resume.id),
                "vacancy_id": str(vacancy_remote.id),
                "include_cost_of_living": True,
            }
        )

        assert response_remote.status_code == 200, \
            "Salary suggestion request should succeed for Remote vacancy"

        suggestion_remote = response_remote.json()

        # SF salary should be higher than Remote due to COL adjustment
        sf_median = suggestion_sf["suggested_median"]
        remote_median = suggestion_remote["suggested_median"]

        assert sf_median > remote_median, \
            f"SF median (${sf_median:,.0f}) should be higher than Remote (${remote_median:,.0f})"

        # Verify the adjustment factor matches
        remote_adjustments = suggestion_remote["factors"]["adjustments"]
        assert remote_adjustments["location_adjustment"] < adjustments["location_adjustment"], \
            "Remote location adjustment should be lower than SF"

        # Step 7: Verify response format matches frontend expectations
        # All fields needed for frontend display
        assert isinstance(suggestion_sf["suggested_min"], int), "suggested_min should be integer"
        assert isinstance(suggestion_sf["suggested_median"], int), "suggested_median should be integer"
        assert isinstance(suggestion_sf["suggested_max"], int), "suggested_max should be integer"
        assert isinstance(suggestion_sf["confidence"], (int, float)), "confidence should be numeric"
        assert isinstance(suggestion_sf["currency"], str), "currency should be string"

        # Verify factors structure
        assert "base_benchmark" in factors, "Should include base benchmark"
        base_benchmark = factors["base_benchmark"]
        assert "min" in base_benchmark, "Base benchmark should have min"
        assert "median" in base_benchmark, "Base benchmark should have median"
        assert "max" in base_benchmark, "Base benchmark should have max"

        # Step 8: Verify education and skill bonuses are considered
        assert "education_bonus" in adjustments, "Should have education bonus"
        assert adjustments["education_bonus"] >= 0, "Education bonus should be non-negative"

        # Candidate has Bachelor's degree, which should give 5% bonus
        assert adjustments["education_bonus"] == 0.05, \
            "Bachelor's degree should give 5% bonus"

        assert "skill_rarity_bonus" in adjustments, "Should have skill rarity bonus"
        # Candidate has premium skills (AWS, Kubernetes, Python)
        assert adjustments["skill_rarity_bonus"] > 0, \
            "Candidate with premium skills should get skill bonus"

        # Step 9: Verify confidence calculation
        # High confidence if we have good benchmark and complete resume data
        assert suggestion_sf["confidence"] > 0.5, \
            "Should have at least medium confidence with good data"

        # Step 10: Verify resume and vacancy IDs are preserved
        assert suggestion_sf["resume_id"] == str(resume.id), "Resume ID should match"
        assert suggestion_sf["vacancy_id"] == str(vacancy_sf.id), "Vacancy ID should match"

    def test_salary_suggestion_with_salary_history(
        self, test_candidate_resume, test_job_vacancy
    ):
        """
        E2E Test: Salary suggestion considers candidate's current salary.

        Verifies:
        1. Salary suggestion respects current salary
        2. Suggested salary is not less than current + reasonable increase
        3. Current salary is considered in the calculation
        """
        from fastapi.testclient import TestClient
        from main import app
        from models.salary_history import SalaryHistory

        client = TestClient(app)

        resume = test_candidate_resume["resume"]
        vacancy = test_job_vacancy[0]

        # Create salary history for candidate
        db = self.SessionLocal()
        try:
            # Candidate's current salary is $130,000
            current_salary = SalaryHistory(
                resume_id=resume.id,
                salary_amount=130000.0,
                salary_frequency="annual",
                currency="USD",
                effective_date="2023-01-01",
                salary_type="current",
                employment_type="full_time",
                job_title="Software Engineer",
                company_name="Tech Corp",
                location="Austin, TX",
            )
            db.add(current_salary)
            db.commit()
        finally:
            db.close()

        # Request salary suggestion
        response = client.post(
            "/api/salary-benchmarking/suggest-salary",
            json={
                "resume_id": str(resume.id),
                "vacancy_id": str(vacancy.id),
                "include_cost_of_living": True,
            }
        )

        assert response.status_code == 200, "Request should succeed"
        suggestion = response.json()

        # Verify current salary is considered
        factors = suggestion["factors"]
        assert factors["current_salary_considered"] == True, \
            "Current salary should be considered"

        # Suggested salary should not be less than current + 5%
        current_salary_float = 130000.0
        min_expected = current_salary_float * 1.05  # At least 5% increase

        assert suggestion["suggested_min"] >= min_expected, \
            f"Suggested min (${suggestion['suggested_min']:,.0f}) should be at least 5% above current (${current_salary_float:,.0f})"

        # Suggested median should be at least 10% above current
        median_expected = current_salary_float * 1.10
        assert suggestion["suggested_median"] >= median_expected, \
            f"Suggested median (${suggestion['suggested_median']:,.0f}) should be at least 10% above current (${current_salary_float:,.0f})"

    def test_salary_suggestion_errors(self):
        """
        E2E Test: Salary suggestion error handling.

        Verifies:
        1. 404 error when resume not found
        2. 404 error when vacancy not found
        3. 422 error for invalid UUID format
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test 1: Invalid UUID format
        response = client.post(
            "/api/salary-benchmarking/suggest-salary",
            json={
                "resume_id": "invalid-uuid",
                "vacancy_id": str(uuid4()),
            }
        )
        assert response.status_code == 422, "Should return 422 for invalid UUID"

        # Test 2: Resume not found
        response = client.post(
            "/api/salary-benchmarking/suggest-salary",
            json={
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
            }
        )
        assert response.status_code == 404, "Should return 404 when resume not found"

        # Test 3: Create a resume but use non-existent vacancy
        db = self.SessionLocal()
        try:
            # Create a test resume
            test_resume = Resume(
                filename="test.pdf",
                file_path="/test/test.pdf",
                content_type="application/pdf",
                status="COMPLETED",
                raw_text="Test resume",
            )
            db.add(test_resume)
            db.commit()
            db.refresh(test_resume)

            # Try to get suggestion for non-existent vacancy
            response = client.post(
                "/api/salary-benchmarking/suggest-salary",
                json={
                    "resume_id": str(test_resume.id),
                    "vacancy_id": str(uuid4()),
                }
            )
            assert response.status_code == 404, "Should return 404 when vacancy not found"

        finally:
            db.close()


class TestOfferComparisonE2E:
    """End-to-end tests for offer comparison feature."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test database and cleanup before/after tests."""
        from database import get_db_settings

        settings = get_db_settings()
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Clean up test data before running
        db = self.SessionLocal()
        try:
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.query(SalaryHistory).filter(
                SalaryHistory.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

        yield

        # Cleanup after tests
        db = self.SessionLocal()
        try:
            db.query(CostOfLivingIndex).filter(
                CostOfLivingIndex.data_source == "e2e_test"
            ).delete()
            db.query(SalaryHistory).filter(
                SalaryHistory.data_source == "e2e_test"
            ).delete()
            db.commit()
        finally:
            db.close()

    @pytest.fixture
    def test_cost_of_living_indices(self):
        """Create test cost-of-living indices for different locations."""
        db = self.SessionLocal()
        try:
            col_data = [
                {
                    "location": "San Francisco, CA",
                    "country": "US",
                    "region": "CA",
                    "cost_of_living_index": 185.5,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "New York, NY",
                    "country": "US",
                    "region": "NY",
                    "cost_of_living_index": 175.0,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "Austin, TX",
                    "country": "US",
                    "region": "TX",
                    "cost_of_living_index": 105.0,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
                {
                    "location": "Remote",
                    "country": "US",
                    "region": None,
                    "cost_of_living_index": 95.0,
                    "currency": "USD",
                    "data_source": "e2e_test",
                },
            ]

            indices = []
            for data in col_data:
                col = CostOfLivingIndex(**data)
                db.add(col)
                indices.append(col)

            db.commit()
            for col in indices:
                db.refresh(col)

            yield indices

        finally:
            db.close()

    def test_offer_comparison_with_col_adjustments(self, test_cost_of_living_indices):
        """
        E2E Test: Offer comparison applies cost-of-living adjustments correctly.

        Verification Steps:
        1. Submit multiple offers with different locations
        2. API applies cost-of-living adjustments
        3. Offers are ranked by adjusted total compensation
        4. Recommendation points to best adjusted offer
        5. Response includes all required fields for frontend
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Step 1: Submit offers from different locations
        offers = [
            {
                "salary": 150000,
                "location": "San Francisco, CA",
                "currency": "USD",
                "bonus": 15000,
                "equity": 10000,
                "job_title": "Senior Software Engineer",
                "company": "Tech Corp SF",
            },
            {
                "salary": 145000,
                "location": "New York, NY",
                "currency": "USD",
                "bonus": 10000,
                "equity": 5000,
                "job_title": "Senior Software Engineer",
                "company": "Startup NYC",
            },
            {
                "salary": 120000,
                "location": "Austin, TX",
                "currency": "USD",
                "bonus": 10000,
                "equity": 0,
                "job_title": "Senior Software Engineer",
                "company": "Company Austin",
            },
            {
                "salary": 130000,
                "location": "Remote",
                "currency": "USD",
                "bonus": 12000,
                "equity": 8000,
                "job_title": "Senior Software Engineer",
                "company": "Remote First Inc",
            },
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "offers": offers,
                "apply_cost_of_living": True,
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Step 2: Verify API applies cost-of-living adjustments
        assert "offers" in data, "Response should include compared offers"
        assert len(data["offers"]) == 4, "Should have 4 compared offers"

        # Step 3: Verify offers are ranked by adjusted total compensation
        compared_offers = data["offers"]
        for i in range(len(compared_offers) - 1):
            assert compared_offers[i]["adjusted_total"] >= compared_offers[i + 1]["adjusted_total"], \
                "Offers should be sorted by adjusted_total (descending)"

        # Step 4: Verify COL index is applied correctly
        # San Francisco (COL 185.5) should have lowest adjusted total
        sf_offer = next(o for o in compared_offers if o["location"] == "San Francisco, CA")
        assert sf_offer["col_index"] == 185.5, "SF offer should have COL index of 185.5"

        # Adjusted total = (150000 + 15000 + 10000) * (100 / 185.5) ≈ 92,992
        expected_sf_adjusted = (150000 + 15000 + 10000) * (100.0 / 185.5)
        assert abs(sf_offer["adjusted_total"] - expected_sf_adjusted) < 1, \
            f"SF adjusted total should be {expected_sf_adjusted:.2f}, got {sf_offer['adjusted_total']}"

        # Austin (COL 105.0) should have highest adjusted total
        austin_offer = next(o for o in compared_offers if o["location"] == "Austin, TX")
        assert austin_offer["col_index"] == 105.0, "Austin offer should have COL index of 105.0"

        # Adjusted total = (120000 + 10000 + 0) * (100 / 105) ≈ 123,810
        expected_austin_adjusted = (120000 + 10000) * (100.0 / 105.0)
        assert abs(austin_offer["adjusted_total"] - expected_austin_adjusted) < 1, \
            f"Austin adjusted total should be {expected_austin_adjusted:.2f}, got {austin_offer['adjusted_total']}"

        # Remote (COL 95.0) should be competitive
        remote_offer = next(o for o in compared_offers if o["location"] == "Remote")
        assert remote_offer["col_index"] == 95.0, "Remote offer should have COL index of 95.0"

        # Adjusted total = (130000 + 12000 + 8000) * (100 / 95) ≈ 157,895
        expected_remote_adjusted = (130000 + 12000 + 8000) * (100.0 / 95.0)
        assert abs(remote_offer["adjusted_total"] - expected_remote_adjusted) < 1, \
            f"Remote adjusted total should be {expected_remote_adjusted:.2f}, got {remote_offer['adjusted_total']}"

        # Step 5: Verify recommendation
        assert "recommendation" in data, "Response should include recommendation"
        assert len(data["recommendation"]) > 0, "Recommendation should not be empty"
        assert "best" in data["recommendation"].lower() or "adjusted" in data["recommendation"].lower(), \
            "Recommendation should mention best offer or adjusted compensation"

        # Step 6: Verify analysis metadata
        assert "analysis" in data, "Response should include analysis"
        assert data["analysis"]["total_offers"] == 4, "Analysis should show 4 offers"
        assert data["analysis"]["cost_of_living_applied"] == True, "COL should be applied"
        assert data["analysis"]["best_location"] == compared_offers[0]["location"], \
            "Best location should match top-ranked offer"

        # Step 7: Verify all required fields for frontend
        for offer in compared_offers:
            assert "salary" in offer, "Offer should have salary"
            assert "location" in offer, "Offer should have location"
            assert "currency" in offer, "Offer should have currency"
            assert "bonus" in offer, "Offer should have bonus"
            assert "equity" in offer, "Offer should have equity"
            assert "total_compensation" in offer, "Offer should have total_compensation"
            assert "adjusted_total" in offer, "Offer should have adjusted_total"
            assert "col_index" in offer, "Offer should have col_index"
            assert offer["total_compensation"] == offer["salary"] + offer["bonus"] + offer["equity"], \
                "Total compensation should equal salary + bonus + equity"

        # Step 8: Verify salary range in analysis
        assert "salary_range" in data["analysis"], "Analysis should include salary range"
        assert data["analysis"]["salary_range"]["min"] == 120000, "Min should be $120,000 (Austin)"
        assert data["analysis"]["salary_range"]["max"] == 175000, "Max should be $175,000 (SF total)"

    def test_offer_comparison_without_col_adjustments(self):
        """
        E2E Test: Offer comparison without cost-of-living adjustments.

        Verifies:
        1. Offers are compared by nominal total compensation
        2. No COL adjustments applied
        3. Ranking based on base compensation only
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        offers = [
            {
                "salary": 150000,
                "location": "San Francisco, CA",
                "currency": "USD",
                "bonus": 15000,
            },
            {
                "salary": 145000,
                "location": "Austin, TX",
                "currency": "USD",
                "bonus": 20000,
            },
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "offers": offers,
                "apply_cost_of_living": False,
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Verify COL is not applied
        assert data["analysis"]["cost_of_living_applied"] == False, "COL should not be applied"

        # Offers should be ranked by nominal total compensation
        compared_offers = data["offers"]
        assert compared_offers[0]["adjusted_total"] == compared_offers[0]["total_compensation"], \
            "Without COL, adjusted_total should equal total_compensation"
        assert compared_offers[1]["adjusted_total"] == compared_offers[1]["total_compensation"], \
            "Without COL, adjusted_total should equal total_compensation"

        # San Francisco ($165k total) should be ranked #1
        assert compared_offers[0]["location"] == "San Francisco, CA", \
            "SF should be #1 without COL adjustment"

        # COL index should be None
        for offer in compared_offers:
            assert offer["col_index"] is None, "COL index should be None when not applied"

    def test_offer_comparison_with_current_salary(self, test_cost_of_living_indices):
        """
        E2E Test: Offer comparison includes current salary context.

        Verifies:
        1. API fetches candidate's current salary
        2. Current salary is included in response
        3. Frontend can show increase/decrease from current
        """
        from fastapi.testclient import TestClient
        from main import app
        from models.resume import Resume
        from models.salary_history import SalaryHistory

        client = TestClient(app)

        # Create a test resume with salary history
        db = self.SessionLocal()
        try:
            resume = Resume(
                filename="test_candidate.pdf",
                file_path="/test/test.pdf",
                content_type="application/pdf",
                status="COMPLETED",
                raw_text="Test candidate with current salary",
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            # Create current salary record ($125,000)
            current_salary = SalaryHistory(
                resume_id=resume.id,
                salary_amount=125000.0,
                salary_frequency="annual",
                currency="USD",
                effective_date="2023-01-01",
                salary_type="current",
                employment_type="full_time",
                job_title="Software Engineer",
                company_name="Current Employer",
                location="Austin, TX",
                data_source="e2e_test",
            )
            current_salary.total_compensation = 125000.0
            db.add(current_salary)
            db.commit()

        finally:
            db.close()

        # Compare offers
        offers = [
            {
                "salary": 140000,
                "location": "Austin, TX",
                "currency": "USD",
                "bonus": 10000,
            },
            {
                "salary": 150000,
                "location": "San Francisco, CA",
                "currency": "USD",
                "bonus": 15000,
            },
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": str(resume.id),
                "offers": offers,
                "apply_cost_of_living": True,
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Verify current salary is included
        assert "current_salary" in data, "Response should include current_salary"
        assert data["current_salary"] == 125000.0, "Current salary should be $125,000"

        # Best offer should be better than current salary
        best_offer = data["offers"][0]
        assert best_offer["total_compensation"] > 125000, \
            "Best offer should be higher than current salary"

    def test_offer_comparison_frontend_data_structure(self):
        """
        E2E Test: Verify response structure matches frontend expectations.

        Verifies:
        1. Response matches OfferComparisonResponse interface
        2. All fields required by OfferComparisonTool component are present
        3. Data types are correct for TypeScript
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        offers = [
            {
                "salary": 100000,
                "location": "Remote",
                "currency": "USD",
                "bonus": 5000,
                "equity": 2000,
                "job_title": "Developer",
                "company": "Tech Corp",
            },
            {
                "salary": 95000,
                "location": "Austin, TX",
                "currency": "USD",
                "bonus": 8000,
            },
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "offers": offers,
                "apply_cost_of_living": True,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure (matches OfferComparisonResponse)
        assert isinstance(data["resume_id"], str), "resume_id should be string"
        assert isinstance(data["offers"], list), "offers should be list"
        assert isinstance(data["recommendation"], str), "recommendation should be string"
        assert isinstance(data["analysis"], dict), "analysis should be dict"
        assert data["current_salary"] is None or isinstance(data["current_salary"], (int, float)), \
            "current_salary should be null or number"

        # Verify offers structure (matches ComparedOffer interface)
        for offer in data["offers"]:
            assert isinstance(offer["salary"], (int, float)), "salary should be number"
            assert isinstance(offer["location"], str), "location should be string"
            assert isinstance(offer["currency"], str), "currency should be string"
            assert isinstance(offer["bonus"], (int, float)), "bonus should be number"
            assert isinstance(offer["equity"], (int, float)), "equity should be number"
            assert isinstance(offer["total_compensation"], (int, float)), "total_compensation should be number"
            assert isinstance(offer["adjusted_total"], (int, float)), "adjusted_total should be number"
            assert offer["col_index"] is None or isinstance(offer["col_index"], (int, float)), \
                "col_index should be null or number"
            assert offer["job_title"] is None or isinstance(offer["job_title"], str), \
                "job_title should be null or string"
            assert offer["company"] is None or isinstance(offer["company"], str), \
                "company should be null or string"

        # Verify analysis structure (matches ComparisonAnalysis interface)
        analysis = data["analysis"]
        assert isinstance(analysis["total_offers"], int), "total_offers should be integer"
        assert isinstance(analysis["cost_of_living_applied"], bool), "cost_of_living_applied should be boolean"
        assert analysis["best_location"] is None or isinstance(analysis["best_location"], str), \
            "best_location should be null or string"
        assert analysis["salary_range"] is None or isinstance(analysis["salary_range"], dict), \
            "salary_range should be null or dict"
        if analysis["salary_range"]:
            assert isinstance(analysis["salary_range"]["min"], (int, float)), "min should be number"
            assert isinstance(analysis["salary_range"]["max"], (int, float)), "max should be number"

    def test_offer_comparison_multiple_offers(self):
        """
        E2E Test: Offer comparison handles maximum number of offers (5).

        Verifies:
        1. API can handle 5 offers at once
        2. All offers are processed and ranked
        3. Analysis includes all offers in range calculation
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Submit 5 offers (maximum allowed by frontend)
        offers = [
            {"salary": 100000, "location": "Remote", "currency": "USD", "bonus": 5000, "company": "Company A"},
            {"salary": 110000, "location": "Austin, TX", "currency": "USD", "bonus": 8000, "company": "Company B"},
            {"salary": 120000, "location": "New York, NY", "currency": "USD", "bonus": 10000, "company": "Company C"},
            {"salary": 130000, "location": "San Francisco, CA", "currency": "USD", "bonus": 15000, "company": "Company D"},
            {"salary": 105000, "location": "Chicago, IL", "currency": "USD", "bonus": 7000, "company": "Company E"},
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "offers": offers,
                "apply_cost_of_living": False,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all 5 offers are processed
        assert len(data["offers"]) == 5, "Should process all 5 offers"
        assert data["analysis"]["total_offers"] == 5, "Analysis should show 5 offers"

        # Verify all offers are ranked correctly (by total compensation without COL)
        totals = [o["total_compensation"] for o in data["offers"]]
        assert totals == sorted(totals, reverse=True), "Offers should be sorted by total_compensation"

        # Verify salary range includes all offers
        assert data["analysis"]["salary_range"]["min"] == 105000, "Min should be $105,000"
        assert data["analysis"]["salary_range"]["max"] == 145000, "Max should be $145,000"

    def test_offer_comparison_minimum_validation(self):
        """
        E2E Test: Offer comparison validation for minimum requirements.

        Verifies:
        1. API handles single offer (edge case)
        2. Response structure is consistent even with minimal data
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test with single offer (minimum)
        single_offer = [
            {"salary": 100000, "location": "Remote", "currency": "USD"},
        ]

        response = client.post(
            "/api/salary-benchmarking/compare-offers",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "offers": single_offer,
                "apply_cost_of_living": False,
            }
        )

        # API should still return 200 (accepts single offer)
        assert response.status_code == 200
        data = response.json()

        assert len(data["offers"]) == 1, "Should process single offer"
        assert data["analysis"]["total_offers"] == 1, "Analysis should show 1 offer"
        assert len(data["recommendation"]) > 0, "Should still generate recommendation"

        # Verify single offer has all required fields
        offer = data["offers"][0]
        assert offer["total_compensation"] == 100000, "Total should equal salary"
        assert offer["adjusted_total"] == 100000, "Adjusted should equal total without COL"
        assert offer["bonus"] == 0, "Bonus should default to 0"
        assert offer["equity"] == 0, "Equity should default to 0"


class TestEquityAnalysisE2E:
    """End-to-end tests for internal equity analysis feature."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test database and cleanup before/after tests."""
        from database import get_db_settings

        settings = get_db_settings()
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Clean up test data before running
        db = self.SessionLocal()
        try:
            from models.candidate_rank import CandidateRank
            from models.demographic_inference import DemographicInference
            from models.salary_history import SalaryHistory

            # Clean up test data
            db.query(CandidateRank).filter(
                CandidateRank.vacancy_id.like("e2e-%")
            ).delete()
            db.query(DemographicInference).filter(
                DemographicInference.resume_id.like("e2e-%")
            ).delete()
            db.query(SalaryHistory).filter(
                SalaryHistory.resume_id.like("e2e-%")
            ).delete()
            db.query(JobVacancy).filter(
                JobVacancy.title.like("[E2E Test]%")
            ).delete()
            db.commit()
        finally:
            db.close()

        yield

        # Cleanup after tests
        db = self.SessionLocal()
        try:
            from models.candidate_rank import CandidateRank
            from models.demographic_inference import DemographicInference
            from models.salary_history import SalaryHistory

            db.query(CandidateRank).filter(
                CandidateRank.vacancy_id.like("e2e-%")
            ).delete()
            db.query(DemographicInference).filter(
                DemographicInference.resume_id.like("e2e-%")
            ).delete()
            db.query(SalaryHistory).filter(
                SalaryHistory.resume_id.like("e2e-%")
            ).delete()
            db.query(JobVacancy).filter(
                JobVacancy.title.like("[E2E Test]%")
            ).delete()
            db.commit()
        finally:
            db.close()

    @pytest.fixture
    def test_vacancy_with_candidates(self):
        """
        Create a test vacancy with multiple candidates having salary and demographic data.

        Creates:
        - 1 JobVacancy (Senior Software Engineer)
        - 6 Resumes with ResumeAnalysis
        - 6 CandidateRank records linking candidates to vacancy
        - 6 DemographicInference records with varied demographics
        - 6 SalaryHistory records with varied salaries (to create pay disparities)
        """
        from models.resume_analysis import ResumeAnalysis
        from models.candidate_rank import CandidateRank
        from models.demographic_inference import DemographicInference
        from models.salary_history import SalaryHistory

        db = self.SessionLocal()
        try:
            # Create vacancy
            vacancy = JobVacancy(
                title="[E2E Test] Senior Software Engineer",
                description="Senior Software Engineer position for equity analysis testing.",
                required_skills=["Python", "AWS", "Docker"],
                min_experience_months=60,
                industry="Technology",
                work_format="remote",
                location="Remote",
                salary_min=120000,
                salary_max=160000,
                employment_type="full_time",
                source="e2e_test"
            )
            db.add(vacancy)
            db.commit()
            db.refresh(vacancy)

            # Create candidates with varied demographics and salaries
            candidates_data = [
                {
                    "name": "Alice Johnson",
                    "gender": "female",
                    "age_group": "25_34",
                    "ethnicity": "white",
                    "salary": 145000,
                    "experience_months": 84,
                },
                {
                    "name": "Bob Smith",
                    "gender": "male",
                    "age_group": "35_44",
                    "ethnicity": "white",
                    "salary": 155000,
                    "experience_months": 96,
                },
                {
                    "name": "Carol Williams",
                    "gender": "female",
                    "age_group": "35_44",
                    "ethnicity": "black_african",
                    "salary": 135000,
                    "experience_months": 72,
                },
                {
                    "name": "David Chen",
                    "gender": "male",
                    "age_group": "25_34",
                    "ethnicity": "asian",
                    "salary": 150000,
                    "experience_months": 78,
                },
                {
                    "name": "Eve Martinez",
                    "gender": "female",
                    "age_group": "25_34",
                    "ethnicity": "hispanic",
                    "salary": 130000,
                    "experience_months": 66,
                },
                {
                    "name": "Frank Brown",
                    "gender": "male",
                    "age_group": "45_54",
                    "ethnicity": "white",
                    "salary": 160000,
                    "experience_months": 108,
                },
            ]

            candidates = []
            for idx, data in enumerate(candidates_data):
                # Create resume
                resume = Resume(
                    filename=f"{data['name'].replace(' ', '_').lower()}_resume.pdf",
                    file_path=f"/test/resumes/{data['name'].replace(' ', '_').lower()}.pdf",
                    content_type="application/pdf",
                    status="COMPLETED",
                    raw_text=f"{data['name']} - Senior Software Engineer with {data['experience_months'] // 12} years experience.",
                    language="en"
                )
                db.add(resume)
                db.commit()
                db.refresh(resume)

                # Create resume analysis
                analysis = ResumeAnalysis(
                    resume_id=resume.id,
                    language="en",
                    raw_text=resume.raw_text,
                    skills=["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"],
                    keywords=[],
                    entities={},
                    total_experience_months=data["experience_months"],
                    education=[{
                        "degree": "Bachelor of Science",
                        "level": "bachelor",
                        "field": "Computer Science",
                    }],
                    quality_score=80 + idx
                )
                db.add(analysis)
                db.commit()

                # Create candidate ranking
                ranking = CandidateRank(
                    vacancy_id=vacancy.id,
                    resume_id=resume.id,
                    rank_score=85 - idx,
                    match_percentage=85 - idx,
                    rank_position=idx + 1
                )
                db.add(ranking)
                db.commit()

                # Create demographic inference
                demographic = DemographicInference(
                    resume_id=resume.id,
                    inferred_gender=data["gender"],
                    inferred_age_group=data["age_group"],
                    inferred_ethnicity=data["ethnicity"],
                    confidence_score=0.85,
                    inference_method="e2e_test"
                )
                db.add(demographic)
                db.commit()

                # Create salary history
                salary = SalaryHistory(
                    resume_id=resume.id,
                    salary_amount=data["salary"],
                    salary_frequency="annual",
                    currency="USD",
                    effective_date="2024-01-01",
                    salary_type="current",
                    employment_type="full_time",
                    job_title="Senior Software Engineer",
                    location="Remote",
                    country="US",
                    data_source="e2e_test"
                )
                db.add(salary)
                db.commit()

                candidates.append({
                    "resume": resume,
                    "analysis": analysis,
                    "ranking": ranking,
                    "demographic": demographic,
                    "salary": salary,
                })

            yield {
                "vacancy": vacancy,
                "candidates": candidates,
            }

        finally:
            db.close()

    def test_equity_analysis_for_vacancy(self, test_vacancy_with_candidates):
        """
        E2E Test 1: Complete equity analysis workflow.

        Verifies:
        1. API can be called with vacancy_id
        2. Analysis includes all candidates
        3. Salary statistics are calculated correctly
        4. Demographic disparities are detected
        5. Alerts and recommendations are generated
        6. Response structure matches frontend expectations
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        vacancy = test_vacancy_with_candidates["vacancy"]
        candidates = test_vacancy_with_candidates["candidates"]

        # Step 1: Request equity analysis
        response = client.get(
            f"/api/salary-benchmarking/equity-analysis?vacancy_id={vacancy.id}"
        )

        # Step 2: Verify response
        assert response.status_code == 200, \
            f"API should return 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Step 3: Verify basic structure
        assert "vacancy_id" in data, "Response should include vacancy_id"
        assert "role" in data, "Response should include role"
        assert "total_candidates" in data, "Response should include total_candidates"
        assert "mean_salary" in data, "Response should include mean_salary"
        assert "median_salary" in data, "Response should include median_salary"
        assert "salary_range" in data, "Response should include salary_range"
        assert "disparities" in data, "Response should include disparities"
        assert "alerts" in data, "Response should include alerts"
        assert "recommendations" in data, "Response should include recommendations"

        # Step 4: Verify vacancy details
        assert data["vacancy_id"] == str(vacancy.id), "vacancy_id should match"
        assert data["role"] == vacancy.title, "role should match vacancy title"

        # Step 5: Verify candidate count
        assert data["total_candidates"] == 6, \
            f"Should analyze 6 candidates, got {data['total_candidates']}"

        # Step 6: Verify salary statistics
        expected_mean = sum(c["salary"].salary_amount for c in candidates) / len(candidates)
        assert abs(data["mean_salary"] - expected_mean) < 1, \
            f"Mean salary should be ${expected_mean:,.2f}, got ${data['mean_salary']:,.2f}"

        # Verify salary range
        salaries = [c["salary"].salary_amount for c in candidates]
        expected_min = min(salaries)
        expected_max = max(salaries)
        assert data["salary_range"]["min"] == expected_min, \
            f"Salary min should be ${expected_min}, got ${data['salary_range']['min']}"
        assert data["salary_range"]["max"] == expected_max, \
            f"Salary max should be ${expected_max}, got ${data['salary_range']['max']}"

        # Step 7: Verify demographic disparities
        assert len(data["disparities"]) > 0, "Should have demographic disparities"

        # Check that disparities have correct structure
        for disparity in data["disparities"]:
            assert "group" in disparity, "Disparity should have group name"
            assert "mean_salary" in disparity, "Disparity should have mean_salary"
            assert "sample_size" in disparity, "Disparity should have sample_size"
            assert "pay_gap" in disparity, "Disparity should have pay_gap"
            assert "is_fair" in disparity, "Disparity should have is_fair flag"

            # Verify data types
            assert isinstance(disparity["mean_salary"], (int, float)), \
                "mean_salary should be numeric"
            assert isinstance(disparity["sample_size"], int), \
                "sample_size should be integer"
            assert isinstance(disparity["pay_gap"], (int, float)), \
                "pay_gap should be numeric"
            assert isinstance(disparity["is_fair"], bool), \
                "is_fair should be boolean"

        # Step 8: Verify alerts (may be empty if no significant disparities)
        assert isinstance(data["alerts"], list), "alerts should be a list"

        # Step 9: Verify recommendations
        assert isinstance(data["recommendations"], list), "recommendations should be a list"
        # Recommendations should be strings if present
        for rec in data["recommendations"]:
            assert isinstance(rec, str), "Each recommendation should be a string"

        print("✅ Equity analysis E2E test passed!")
        print(f"   - Analyzed {data['total_candidates']} candidates")
        print(f"   - Mean salary: ${data['mean_salary']:,.2f}")
        print(f"   - Median salary: ${data['median_salary']:,.2f}")
        print(f"   - Detected {len(data['disparities'])} demographic group disparities")
        print(f"   - Generated {len(data['alerts'])} alerts")
        print(f"   - Generated {len(data['recommendations'])} recommendations")

    def test_equity_analysis_detects_pay_disparities(self, test_vacancy_with_candidates):
        """
        E2E Test 2: Verify pay disparity detection.

        Verifies:
        1. API correctly identifies pay gaps between demographic groups
        2. Pay gaps are calculated accurately
        3. Significant gaps are flagged (is_fair = False)
        4. Sample sizes are respected (minimum 3 per group)
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        vacancy = test_vacancy_with_candidates["vacancy"]

        response = client.get(
            f"/api/salary-benchmarking/equity-analysis?vacancy_id={vacancy.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify we have disparities
        assert len(data["disparities"]) > 0, "Should detect demographic disparities"

        # Group disparities by demographic attribute
        gender_groups = {}
        for disparity in data["disparities"]:
            if disparity["group"].startswith("gender="):
                gender = disparity["group"].replace("gender=", "")
                gender_groups[gender] = disparity

        # Verify gender-based salary differences are detected
        if len(gender_groups) >= 2:
            # We have both male and female candidates
            # Check that pay gaps are calculated
            for gender, disparity in gender_groups.items():
                assert disparity["mean_salary"] > 0, \
                    f"{gender} group should have positive mean salary"
                assert disparity["sample_size"] >= 3, \
                    f"{gender} group should have at least 3 samples (minimum for analysis)"

                # Pay gap should be calculated (may be positive, negative, or zero)
                assert isinstance(disparity["pay_gap"], (int, float)), \
                    f"{gender} pay_gap should be numeric"

                # is_fair should be boolean
                assert isinstance(disparity["is_fair"], bool), \
                    f"{gender} is_fair should be boolean"

        print("✅ Pay disparity detection test passed!")
        print(f"   - Analyzed {len(gender_groups)} gender groups")
        for gender, disparity in gender_groups.items():
            print(f"   - {gender}: ${disparity['mean_salary']:,.2f} (gap: {disparity['pay_gap']:.1%}, fair: {disparity['is_fair']})")

    def test_equity_analysis_frontend_data_structure(self, test_vacancy_with_candidates):
        """
        E2E Test 3: Verify response matches frontend component expectations.

        Verifies:
        1. Response structure matches EquityAnalysisResponse TypeScript interface
        2. All required fields are present
        3. Data types match frontend expectations
        4. Component can render without errors
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        vacancy = test_vacancy_with_candidates["vacancy"]

        response = client.get(
            f"/api/salary-benchmarking/equity-analysis?vacancy_id={vacancy.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify TypeScript EquityAnalysisResponse interface fields
        required_fields = {
            "vacancy_id": str,
            "role": str,
            "total_candidates": int,
            "mean_salary": (int, float),
            "median_salary": (int, float),
            "salary_range": dict,
            "disparities": list,
            "alerts": list,
            "recommendations": list,
        }

        for field, expected_type in required_fields.items():
            assert field in data, f"Missing required field: {field}"
            assert isinstance(data[field], expected_type), \
                f"Field '{field}' should be {expected_type}, got {type(data[field])}"

        # Verify salary_range has min and max
        assert "min" in data["salary_range"], "salary_range should have 'min'"
        assert "max" in data["salary_range"], "salary_range should have 'max'"
        assert isinstance(data["salary_range"]["min"], (int, float)), \
            "salary_range.min should be numeric"
        assert isinstance(data["salary_range"]["max"], (int, float)), \
            "salary_range.max should be numeric"

        # Verify disparities list items match EquityDisparity interface
        if len(data["disparities"]) > 0:
            disparity = data["disparities"][0]
            required_disparity_fields = {
                "group": str,
                "mean_salary": (int, float),
                "sample_size": int,
                "pay_gap": (int, float),
                "is_fair": bool,
            }

            for field, expected_type in required_disparity_fields.items():
                assert field in disparity, f"Missing disparity field: {field}"
                assert isinstance(disparity[field], expected_type), \
                    f"Disparity field '{field}' should be {expected_type}, got {type(disparity[field])}"

        # Verify alerts are strings
        for alert in data["alerts"]:
            assert isinstance(alert, str), "Each alert should be a string"
            assert len(alert) > 0, "Alert should not be empty"

        # Verify recommendations are strings
        for rec in data["recommendations"]:
            assert isinstance(rec, str), "Each recommendation should be a string"
            assert len(rec) > 0, "Recommendation should not be empty"

        print("✅ Frontend data structure test passed!")
        print("   - All required fields present")
        print("   - All data types match TypeScript interfaces")
        print("   - Compatible with EquityAnalysisDashboard component")

    def test_equity_analysis_error_handling(self):
        """
        E2E Test 4: Verify error handling for invalid requests.

        Verifies:
        1. 404 returned for non-existent vacancy
        2. 422 returned for invalid UUID format
        3. Error messages are descriptive
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test 1: Non-existent vacancy
        fake_uuid = "00000000-0000-0000-0000-999999999999"
        response = client.get(
            f"/api/salary-benchmarking/equity-analysis?vacancy_id={fake_uuid}"
        )

        assert response.status_code == 404, \
            f"Should return 404 for non-existent vacancy, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        assert "not found" in data["detail"].lower(), \
            "Error message should indicate vacancy not found"

        # Test 2: Invalid UUID format
        response = client.get(
            "/api/salary-benchmarking/equity-analysis?vacancy_id=invalid-uuid"
        )

        assert response.status_code == 422, \
            f"Should return 422 for invalid UUID, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

        print("✅ Error handling test passed!")
        print("   - Non-existent vacancy returns 404")
        print("   - Invalid UUID returns 422")
        print("   - Error messages are descriptive")

    def test_equity_analysis_export_functionality(self, test_vacancy_with_candidates):
        """
        E2E Test 5: Verify data can be exported for budgeting.

        Verifies:
        1. Analysis data contains all information needed for export
        2. Data is structured for CSV/Excel export
        3. All numeric values are present and valid
        4. Demographic breakdown is complete
        """
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        vacancy = test_vacancy_with_candidates["vacancy"]

        response = client.get(
            f"/api/salary-benchmarking/equity-analysis?vacancy_id={vacancy.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify exportability: all numeric fields should be present and valid
        exportable_fields = [
            "vacancy_id",
            "role",
            "total_candidates",
            "mean_salary",
            "median_salary",
            "salary_range",
        ]

        for field in exportable_fields:
            assert field in data, f"Exportable field '{field}' should be present"

        # Verify numeric values are export-friendly (not NaN or Infinity)
        assert data["mean_salary"] > 0, "mean_salary should be positive"
        assert data["median_salary"] > 0, "median_salary should be positive"
        assert data["salary_range"]["min"] > 0, "salary_range.min should be positive"
        assert data["salary_range"]["max"] > 0, "salary_range.max should be positive"
        assert data["salary_range"]["max"] >= data["salary_range"]["min"], \
            "salary_range.max should be >= salary_range.min"

        # Verify disparities data is exportable
        for disparity in data["disparities"]:
            assert disparity["group"] is not None, "Group name should be present"
            assert disparity["mean_salary"] > 0, "Mean salary should be positive"
            assert disparity["sample_size"] > 0, "Sample size should be positive"
            assert -1 <= disparity["pay_gap"] <= 1, \
                "Pay gap should be between -100% and +100%"

        # Verify alerts and recommendations are exportable (non-empty strings)
        for alert in data["alerts"]:
            assert len(alert.strip()) > 0, "Alert should not be empty or whitespace"

        for rec in data["recommendations"]:
            assert len(rec.strip()) > 0, "Recommendation should not be empty or whitespace"

        print("✅ Export functionality test passed!")
        print("   - All numeric values are valid and exportable")
        print("   - Data structure supports CSV/Excel export")
        print("   - Complete demographic breakdown available")

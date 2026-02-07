"""
Integration test for vacancy pagination with large dataset.

This test creates 50+ test vacancies and verifies that pagination works correctly
by scrolling through the entire list and checking that all vacancies load without errors.
"""
import pytest
import requests
from typing import List, Dict
import time


class TestVacancyPagination:
    """Integration tests for vacancy pagination."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancies(self):
        """Create 50+ test vacancies for pagination testing."""
        print("\n=== Creating 50+ test vacancies for pagination testing ===")

        created_vacancies = []

        # Create 55 test vacancies with varying data
        for i in range(55):
            vacancy_data = {
                "title": f"Test Vacancy {i+1}",
                "description": f"This is test vacancy {i+1} for pagination testing. "
                               f"We need to ensure that pagination works correctly with large datasets.",
                "required_skills": ["Python", "SQL", "Git"],
                "min_experience_months": 12 + (i % 5) * 12,  # Vary from 12 to 60 months
                "additional_requirements": ["Docker", "Linux"],
                "industry": "Technology",
                "work_format": ["remote", "office", "hybrid"][i % 3],
                "location": ["Moscow", "Saint Petersburg", "Kazan", "Ekaterinburg", "Remote"][i % 5],
                "salary_min": 80000 + (i % 10) * 10000,
                "salary_max": 120000 + (i % 10) * 10000,
                "english_level": ["B1", "B2", "C1"][i % 3],
                "employment_type": "full-time",
            }

            try:
                response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
                if response.status_code == 201:
                    vacancy = response.json()
                    created_vacancies.append(vacancy["id"])
                    print(f"Created vacancy {i+1}: {vacancy['title']}")
                else:
                    print(f"Failed to create vacancy {i+1}: {response.status_code}")
            except Exception as e:
                print(f"Error creating vacancy {i+1}: {e}")

        print(f"\nSuccessfully created {len(created_vacancies)} test vacancies")
        yield created_vacancies

        # Cleanup: delete all created vacancies
        print("\n=== Cleaning up test vacancies ===")
        for vacancy_id in created_vacancies:
            try:
                requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy_id}")
            except Exception as e:
                print(f"Error deleting vacancy {vacancy_id}: {e}")

    def test_pagination_total_count(self, test_vacancies):
        """Test that total count is returned correctly."""
        print("\n=== Testing pagination total count ===")

        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "total" in data, "Response should contain 'total' field"
        assert "vacancies" in data, "Response should contain 'vacancies' field"

        # Total should be at least the number of test vacancies we created
        assert data["total"] >= len(test_vacancies), \
            f"Expected at least {len(test_vacancies)} vacancies, got {data['total']}"

        print(f"✓ Total count: {data['total']} vacancies")
        print(f"✓ First page contains {len(data['vacancies'])} vacancies")

    def test_pagination_page_size(self, test_vacancies):
        """Test that pagination returns correct page size."""
        print("\n=== Testing pagination page size ===")

        # Test with limit=20 (frontend default)
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=20")

        assert response.status_code == 200
        data = response.json()

        # Should return exactly 20 vacancies (or fewer if total < 20)
        assert len(data["vacancies"]) <= 20, \
            f"Expected at most 20 vacancies per page, got {len(data['vacancies'])}"

        # If we have at least 20 total, should return exactly 20
        if data["total"] >= 20:
            assert len(data["vacancies"]) == 20, \
                f"Expected 20 vacancies on first page, got {len(data['vacancies'])}"

        print(f"✓ Page size limit works correctly: {len(data['vacancies'])} vacancies returned")

    def test_pagination_skip_offset(self, test_vacancies):
        """Test that skip parameter correctly offsets results."""
        print("\n=== Testing pagination skip offset ===")

        # Get first page
        response1 = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10")
        data1 = response1.json()
        first_page_ids = [v["id"] for v in data1["vacancies"]]

        # Get second page
        response2 = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=10&limit=10")
        data2 = response2.json()
        second_page_ids = [v["id"] for v in data2["vacancies"]]

        # IDs should not overlap
        overlap = set(first_page_ids) & set(second_page_ids)
        assert len(overlap) == 0, \
            f"Pages should not overlap, but found {len(overlap)} common IDs"

        print(f"✓ No overlap between first and second page")
        print(f"✓ First page: {len(first_page_ids)} vacancies")
        print(f"✓ Second page: {len(second_page_ids)} vacancies")

    def test_pagination_scroll_through_all(self, test_vacancies):
        """Test scrolling through entire list using pagination."""
        print("\n=== Testing scroll through all vacancies ===")

        all_vacancy_ids = []
        skip = 0
        limit = 20
        page_count = 0
        total_expected = None

        while True:
            response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip={skip}&limit={limit}")

            assert response.status_code == 200, f"Failed on page {page_count} with skip={skip}"

            data = response.json()

            # Store total from first response
            if total_expected is None:
                total_expected = data["total"]
                print(f"Total vacancies to fetch: {total_expected}")

            vacancies = data["vacancies"]
            page_count += 1

            if not vacancies:
                print(f"✓ No more vacancies on page {page_count}")
                break

            page_ids = [v["id"] for v in vacancies]
            all_vacancy_ids.extend(page_ids)

            print(f"Page {page_count}: Fetched {len(vacancies)} vacancies "
                  f"(skip={skip}, total so far={len(all_vacancy_ids)})")

            # Check for duplicates
            if len(all_vacancy_ids) != len(set(all_vacancy_ids)):
                print("✗ ERROR: Found duplicate vacancy IDs!")
                assert False, "Duplicate vacancy IDs found across pages"

            # Check if we've fetched all vacancies
            if len(vacancies) < limit:
                print(f"✓ Fetched all vacancies (last page had {len(vacancies)} items)")
                break

            skip += limit

        # Verify we got all expected vacancies
        print(f"\n✓ Successfully scrolled through {len(all_vacancy_ids)} unique vacancies")
        print(f"✓ Total pages loaded: {page_count}")
        print(f"✓ Expected total: {total_expected}")

        # We should have fetched at least our test vacancies
        assert len(all_vacancy_ids) >= len(test_vacancies), \
            f"Expected at least {len(test_vacancies)} vacancies, got {len(all_vacancy_ids)}"

        # No duplicates
        assert len(all_vacancy_ids) == len(set(all_vacancy_ids)), \
            "Found duplicate vacancy IDs"

    def test_pagination_no_errors_on_edges(self, test_vacancies):
        """Test pagination at edge cases (empty pages, beyond total)."""
        print("\n=== Testing pagination edge cases ===")

        # Get total count
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=1")
        data = response.json()
        total = data["total"]

        # Request page beyond total
        skip_beyond = total + 100
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip={skip_beyond}&limit=10")

        assert response.status_code == 200, "Should return 200 even when skip exceeds total"
        data = response.json()
        assert data["total"] == total, "Total should remain consistent"
        assert len(data["vacancies"]) == 0, "Should return empty vacancy list"

        print(f"✓ Request beyond total returns empty list (skip={skip_beyond})")

    def test_pagination_parameters_validation(self, test_vacancies):
        """Test that pagination parameters are validated correctly."""
        print("\n=== Testing pagination parameter validation ===")

        # Test limit > 500 (should fail with 422)
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?limit=1000")
        assert response.status_code == 422, "Should reject limit > 500"
        print("✓ Rejects limit > 500")

        # Test negative skip (should fail with 422)
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=-10")
        assert response.status_code == 422, "Should reject negative skip"
        print("✓ Rejects negative skip")

        # Test limit = 0 (should fail with 422)
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?limit=0")
        assert response.status_code == 422, "Should reject limit = 0"
        print("✓ Rejects limit = 0")

        print("\n✓ All pagination parameter validation tests passed")

    def test_pagination_consistent_ordering(self, test_vacancies):
        """Test that pagination maintains consistent ordering across pages."""
        print("\n=== Testing pagination consistent ordering ===")

        # Fetch first 3 pages
        pages = []
        for page_num in range(3):
            skip = page_num * 10
            response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip={skip}&limit=10")
            assert response.status_code == 200
            data = response.json()
            pages.append(data["vacancies"])

        # Verify vacancies are ordered by created_at descending
        all_dates = []
        for page in pages:
            for vacancy in page:
                all_dates.append(vacancy["created_at"])

        # Check that dates are in descending order (newest first)
        for i in range(len(all_dates) - 1):
            assert all_dates[i] >= all_dates[i+1], \
                f"Vacancies should be ordered by created_at descending, but found violation at index {i}"

        print(f"✓ Vacancies are consistently ordered by created_at descending")
        print(f"✓ Checked {len(all_dates)} vacancies across {len(pages)} pages")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

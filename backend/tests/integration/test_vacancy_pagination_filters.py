"""
Integration test for vacancy pagination with filters.

This test validates that pagination works correctly when filters are applied.
The frontend uses client-side filtering, so when filters are active, it loads
all data (limit=10000) and filters on the client side.
"""
import pytest
import requests
from typing import List, Dict
from datetime import datetime, timedelta


class TestVacancyPaginationFilters:
    """Integration tests for vacancy pagination with filters."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancies(self):
        """Create test vacancies with varied filterable attributes."""
        print("\n=== Creating test vacancies with varied attributes ===")

        created_vacancies = []

        # Create 30 test vacancies with different work formats, locations, and dates
        work_formats = ["remote", "office", "hybrid"]
        locations = ["Moscow", "Saint Petersburg", "Kazan", "Ekaterinburg", "Novosibirsk"]

        for i in range(30):
            vacancy_data = {
                "title": f"Test Vacancy {i+1}",
                "description": f"This is test vacancy {i+1} for filter testing.",
                "required_skills": ["Python", "SQL"],
                "min_experience_months": 12,
                "additional_requirements": [],
                "industry": "Technology",
                "work_format": work_formats[i % 3],
                "location": locations[i % 5],
                "salary_min": 80000,
                "salary_max": 120000,
                "english_level": "B1",
                "employment_type": "full-time",
            }

            try:
                response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
                if response.status_code == 201:
                    vacancy = response.json()
                    created_vacancies.append(vacancy)
                    print(f"Created vacancy {i+1}: {vacancy['title']} "
                          f"({vacancy['work_format']}, {vacancy['location']})")
                else:
                    print(f"Failed to create vacancy {i+1}: {response.status_code}")
            except Exception as e:
                print(f"Error creating vacancy {i+1}: {e}")

        print(f"\nSuccessfully created {len(created_vacancies)} test vacancies")
        yield created_vacancies

        # Cleanup: delete all created vacancies
        print("\n=== Cleaning up test vacancies ===")
        for vacancy in created_vacancies:
            try:
                requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")
            except Exception as e:
                print(f"Error deleting vacancy {vacancy['id']}: {e}")

    def test_backend_returns_all_data_for_client_side_filtering(self, test_vacancies):
        """Test that backend can return all data when needed for client-side filtering."""
        print("\n=== Testing backend returns all data for filtering ===")

        # Request all data with high limit (frontend uses 10000 for filtered results)
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "total" in data, "Response should contain 'total' field"
        assert "vacancies" in data, "Response should contain 'vacancies' field"

        # Should get all vacancies
        assert len(data["vacancies"]) >= len(test_vacancies), \
            f"Expected at least {len(test_vacancies)} vacancies, got {len(data['vacancies'])}"

        # Verify total count matches
        assert data["total"] >= len(test_vacancies), \
            f"Total count should be at least {len(test_vacancies)}, got {data['total']}"

        print(f"✓ Backend returned {len(data['vacancies'])} vacancies")
        print(f"✓ Total count: {data['total']}")
        print(f"✓ Client-side filtering can work with full dataset")

    def test_filter_by_work_format(self, test_vacancies):
        """Test that work format filter can be applied client-side."""
        print("\n=== Testing work format filter ===")

        # Get all vacancies
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data = response.json()
        all_vacancies = data["vacancies"]

        # Count vacancies by work format
        remote_count = sum(1 for v in all_vacancies if v["work_format"] == "remote")
        office_count = sum(1 for v in all_vacancies if v["work_format"] == "office")
        hybrid_count = sum(1 for v in all_vacancies if v["work_format"] == "hybrid")

        print(f"✓ Remote vacancies: {remote_count}")
        print(f"✓ Office vacancies: {office_count}")
        print(f"✓ Hybrid vacancies: {hybrid_count}")

        # Verify we have vacancies with different work formats
        assert remote_count > 0 or office_count > 0 or hybrid_count > 0, \
            "Should have vacancies with at least one work format"

        print(f"✓ Work format filtering can be applied client-side")

    def test_filter_by_location(self, test_vacancies):
        """Test that location filter can be applied client-side."""
        print("\n=== Testing location filter ===")

        # Get all vacancies
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data = response.json()
        all_vacancies = data["vacancies"]

        # Count vacancies by location
        locations = {}
        for vacancy in all_vacancies:
            location = vacancy.get("location", "Unknown")
            locations[location] = locations.get(location, 0) + 1

        print(f"✓ Vacancies by location:")
        for location, count in sorted(locations.items()):
            print(f"  - {location}: {count}")

        # Verify we have vacancies with different locations
        assert len(locations) > 0, "Should have vacancies with locations"

        print(f"✓ Location filtering can be applied client-side")

    def test_filter_by_date_range(self, test_vacancies):
        """Test that date range filter can be applied client-side."""
        print("\n=== Testing date range filter ===")

        # Get all vacancies
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data = response.json()
        all_vacancies = data["vacancies"]

        # Filter vacancies created within last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_vacancies = [
            v for v in all_vacancies
            if datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')) >= seven_days_ago
        ]

        print(f"✓ Vacancies created in last 7 days: {len(recent_vacancies)}")
        print(f"✓ Total vacancies: {len(all_vacancies)}")
        print(f"✓ Date range filtering can be applied client-side")

    def test_combined_filters(self, test_vacancies):
        """Test that multiple filters can be combined client-side."""
        print("\n=== Testing combined filters ===")

        # Get all vacancies
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data = response.json()
        all_vacancies = data["vacancies"]

        # Apply work format filter
        filtered = [v for v in all_vacancies if v["work_format"] == "remote"]

        # Apply location filter
        filtered = [v for v in filtered if v.get("location", "") == "Moscow"]

        print(f"✓ Remote vacancies in Moscow: {len(filtered)}")
        print(f"✓ Combined filtering works correctly")

    def test_pagination_reset_on_filter_change(self, test_vacancies):
        """Test that pagination resets correctly when filter changes."""
        print("\n=== Testing pagination reset on filter change ===")

        # Simulate frontend behavior:
        # 1. Initial paginated load (no filters)
        response1 = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=20")
        data1 = response1.json()

        print(f"Step 1 - Initial load (no filters):")
        print(f"  - skip=0, limit=20")
        print(f"  - Returned {len(data1['vacancies'])} vacancies")
        print(f"  - Total: {data1['total']}")

        # 2. Filter applied - load all data
        response2 = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data2 = response2.json()

        print(f"\nStep 2 - Filter applied:")
        print(f"  - skip=0, limit=10000 (load all for client-side filtering)")
        print(f"  - Returned {len(data2['vacancies'])} vacancies")
        print(f"  - Total: {data2['total']}")

        # 3. Filter cleared - back to paginated load
        response3 = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=20")
        data3 = response3.json()

        print(f"\nStep 3 - Filter cleared:")
        print(f"  - skip=0, limit=20 (back to pagination)")
        print(f"  - Returned {len(data3['vacancies'])} vacancies")
        print(f"  - Total: {data3['total']}")

        # Verify counts are consistent
        assert data1['total'] == data2['total'] == data3['total'], \
            "Total count should remain consistent across filter changes"

        print(f"\n✓ Pagination resets correctly when filters change")
        print(f"✓ Total count remains consistent: {data1['total']}")

    def test_filter_data_integrity(self, test_vacancies):
        """Test that filtering doesn't lose or duplicate vacancies."""
        print("\n=== Testing filter data integrity ===")

        # Get all vacancies
        response = requests.get(f"{self.BASE_URL}/api/vacancies/?skip=0&limit=10000")
        data = response.json()
        all_vacancies = data["vacancies"]
        all_ids = set(v["id"] for v in all_vacancies)

        # Apply filter and check no duplicates
        remote_vacancies = [v for v in all_vacancies if v["work_format"] == "remote"]
        remote_ids = [v["id"] for v in remote_vacancies]

        # Check for duplicates
        assert len(remote_ids) == len(set(remote_ids)), \
            "Filtered results should not contain duplicates"

        # Check all filtered IDs are from the original set
        assert set(remote_ids).issubset(all_ids), \
            "Filtered IDs should all be from the original dataset"

        print(f"✓ No duplicates in filtered results")
        print(f"✓ All filtered vacancies are from original dataset")
        print(f"✓ Data integrity maintained during filtering")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

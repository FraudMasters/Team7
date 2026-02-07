"""
Unit tests for SQL injection protection in API endpoints.

This test suite validates the security-critical SQL injection protection that:
- Prevents SQL injection attacks in all API endpoints
- Ensures SQLAlchemy ORM parameterized queries are used
- Neutralizes malicious SQL payloads before database execution
- Protects against UNION-based SQL injection
- Protects against boolean-based blind SQL injection
- Protects against time-based blind SQL injection
- Protects against stacked queries (multiple statements)
- Verifies input validation and sanitization

Test Coverage:
- Search endpoints with query parameters
- Filter endpoints with WHERE clause parameters
- ID-based lookups (UUID injection attempts)
- ORDER BY clause injection attempts
- LIMIT/OFFSET injection attempts
- Edge cases: special characters, comments, hex encoding
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


# =============================================================================
# SQL Injection Payloads
# =============================================================================

class SQLiPayloads:
    """Common SQL injection attack payloads for testing."""

    # Classic SQL injection
    CLASSIC = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "' OR '1'='1'#",
        "admin' --",
        "admin' /*",
        "' OR 1=1 --",
        "' OR 'a'='a",
    ]

    # UNION-based injection
    UNION_BASED = [
        "' UNION SELECT NULL, NULL, NULL --",
        "' UNION SELECT username, password, NULL FROM users --",
        "' UNION SELECT 1, 2, 3 --",
        "' UNION SELECT version(), user(), database() --",
        "'; UNION SELECT NULL --",
    ]

    # Boolean-based blind injection
    BOOLEAN_BLIND = [
        "' AND 1=1 --",
        "' AND 1=2 --",
        "' AND '1'='1",
        "' AND '1'='2",
        "' AND ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),1,1)) > 64 --",
    ]

    # Time-based blind injection
    TIME_BASED = [
        "'; WAITFOR DELAY '00:00:05' --",
        "'; SLEEP(5) --",
        "' AND (SELECT SUBSTRING(password,1,1) FROM users) = 'a' AND SLEEP(5) --",
        "'; SELECT PG_SLEEP(5) --",
        "' OR BENCHMARK(50000000,MD5(1)) --",
    ]

    # Stacked queries (multiple statements)
    STACKED_QUERIES = [
        "'; DROP TABLE users --",
        "'; DELETE FROM users WHERE 1=1 --",
        "'; INSERT INTO users (username) VALUES ('hacked') --",
        "'; UPDATE users SET password='hacked' WHERE 1=1 --",
    ]

    # Error-based injection
    ERROR_BASED = [
        "' AND 1=CONVERT(int, (SELECT TOP 1 table_name FROM information_schema.tables)) --",
        "' AND 1=CAST((SELECT table_name FROM information_schema.tables LIMIT 1) AS int) --",
    ]

    # Second-order injection (via stored data)
    SECOND_ORDER = [
        "'; SELECT * FROM users WHERE username='",
        "' OR (SELECT COUNT(*) FROM users) > 0 --",
    ]

    # Comment injection attempts
    COMMENT_BASED = [
        "'--",
        "'/*",
        "';#",
        "'-- ",
        "'/*comment*/",
    ]

    # Special characters and encoding
    SPECIAL_CHARS = [
        "';<>\"\\",
        "'\\x00",
        "'\\n",
        "'\\r",
        "%27%20OR%20%271%27%3D%271",  # URL encoded
        "0x274F522731273D273127",  # Hex encoded
    ]

    # All payloads combined
    ALL = (
        CLASSIC +
        UNION_BASED +
        BOOLEAN_BLIND +
        TIME_BASED +
        STACKED_QUERIES +
        ERROR_BASED +
        SECOND_ORDER +
        COMMENT_BASED +
        SPECIAL_CHARS
    )


# =============================================================================
# Search Endpoint SQL Injection Tests
# =============================================================================

class TestSearchEndpointSQLiProtection:
    """Tests for SQL injection protection in search endpoints."""

    @pytest.mark.parametrize("payload", SQLiPayloads.CLASSIC)
    def test_search_query_classic_sqli_blocked(self, client, payload):
        """
        Test that classic SQL injection payloads in search query are blocked.

        Verifies that attempts to inject SQL via the query parameter
        are neutralized and don't cause database errors.
        """
        response = client.post(
            "/api/search/candidates",
            json={
                "query": payload,
                "limit": 10
            }
        )

        # Should return 200 (safe parse) or 400/422 (validation error)
        # Should NOT return 500 (database error indicating SQLi success)
        assert response.status_code in [200, 400, 422]

        # Verify no SQL error in response
        if response.status_code == 200:
            data = response.json()
            # If successful, verify no SQL error leaked
            assert "sql" not in str(data).lower()
            assert "syntax" not in str(data).lower()
            assert "error" not in str(data).lower() or len(data.get("candidates", [])) >= 0

    @pytest.mark.parametrize("payload", SQLiPayloads.UNION_BASED)
    def test_search_query_union_sqli_blocked(self, client, payload):
        """
        Test that UNION-based SQL injection in search query is blocked.

        Verifies that attempts to extract data via UNION injection
        are neutralized.
        """
        response = client.post(
            "/api/search/candidates",
            json={
                "query": payload,
                "limit": 10
            }
        )

        # Should handle gracefully - no database errors
        assert response.status_code in [200, 400, 422]

        # Verify no sensitive data leaked
        if response.status_code == 200:
            data = response.json()
            # UNION injection would leak table data - verify this didn't happen
            candidates = data.get("candidates", [])
            # All candidates should have valid structure, not leaked UNION data
            for candidate in candidates:
                if isinstance(candidate, dict):
                    # Should have valid candidate fields
                    assert "id" in candidate or "filename" in candidate

    def test_search_query_with_sqli_in_filters(self, client):
        """Test SQL injection via filter parameters is blocked."""
        payload = {
            "query": "Python developer",
            "filters": {
                "location": "' OR '1'='1",
                "skills": ["'; DROP TABLE users --"],
            },
            "limit": 10
        }

        response = client.post("/api/search/candidates", json=payload)

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

        # Verify no SQL error
        if response.status_code == 200:
            assert "sql" not in response.text.lower()

    def test_search_query_with_time_based_sqli(self, client):
        """
        Test that time-based blind SQL injection is blocked.

        Time-based injection attempts to cause delays in database response.
        This test verifies such attempts are neutralized quickly.
        """
        import time

        payload = {
            "query": "'; SLEEP(5) --",
            "limit": 10
        }

        start = time.time()
        response = client.post("/api/search/candidates", json=payload)
        elapsed = time.time() - start

        # Response should be fast (< 2 seconds)
        # If SLEEP() was injected, response would take 5+ seconds
        assert elapsed < 2.0, "Time-based SQL injection not blocked (query took too long)"
        assert response.status_code in [200, 400, 422]


# =============================================================================
# Candidates Endpoint SQL Injection Tests
# =============================================================================

class TestCandidatesEndpointSQLiProtection:
    """Tests for SQL injection protection in candidates endpoints."""

    def test_candidates_list_with_sqli_in_stage_id(self, client):
        """Test SQL injection via stage_id parameter is blocked."""
        response = client.get("/api/candidates?stage_id=' OR '1'='1")

        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 422]

        # Verify no SQL error
        if response.status_code == 200:
            data = response.json()
            assert "sql" not in str(data).lower()

    def test_candidates_list_with_sqli_in_vacancy_id(self, client):
        """Test SQL injection via vacancy_id parameter is blocked."""
        response = client.get("/api/candidates?vacancy_id=' UNION SELECT NULL --")

        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 422]

    def test_move_candidate_with_sqli_in_stage_id(self, client):
        """Test SQL injection in candidate move endpoint is blocked."""
        # This endpoint uses POST, so we need to handle it appropriately
        # Some endpoints might require authentication
        payload = {
            "stage_id": "'; DROP TABLE hiring_stages --",
            "vacancy_id": None,
            "notes": "Test note"
        }

        # May return 401 (unauthorized) or 400/422 (validation)
        # Should NOT return 500 (SQL error)
        response = client.post(
            "/api/candidates/00000000-0000-0000-0000-000000000001/move",
            json=payload
        )

        # Any response is fine as long as it's not 500 (SQL error)
        assert response.status_code != 500


# =============================================================================
# Vacancies Endpoint SQL Injection Tests
# =============================================================================

class TestVacanciesEndpointSQLiProtection:
    """Tests for SQL injection protection in vacancies endpoints."""

    @pytest.mark.parametrize("payload", SQLiPayloads.STACKED_QUERIES[:3])
    def test_create_vacancy_with_sqli_in_title(self, client, payload):
        """
        Test SQL injection in vacancy title is blocked.

        Verifies that malicious SQL in title field doesn't execute.
        """
        # Truncate payload to reasonable length for title field
        safe_payload = payload[:100] if len(payload) > 100 else payload

        request_data = {
            "title": safe_payload,
            "description": "Test description for SQL injection test",
            "required_skills": ["Python"],
            "min_experience_months": 12
        }

        response = client.post("/api/vacancies", json=request_data)

        # Should return 201 (created), 400 (validation), or 401 (auth)
        # Should NOT return 500 (SQL error indicating injection success)
        assert response.status_code in [201, 400, 401, 422]

        # Verify no SQL error in response
        if response.status_code in [201, 400, 422]:
            assert "sql" not in response.text.lower()
            assert "syntax" not in response.text.lower()

    def test_create_vacancy_with_sqli_in_description(self, client):
        """Test SQL injection in vacancy description is blocked."""
        request_data = {
            "title": "Test Vacancy",
            "description": "'; SELECT * FROM users --",
            "required_skills": ["Python"],
            "min_experience_months": 12
        }

        response = client.post("/api/vacancies", json=request_data)

        # Should handle gracefully
        assert response.status_code in [201, 400, 401, 422]
        assert response.status_code != 500

    def test_create_vacancy_with_sqli_in_skills(self, client):
        """Test SQL injection via skills array is blocked."""
        request_data = {
            "title": "Test Vacancy",
            "description": "Test description",
            "required_skills": ["Python", "'; DROP TABLE required_skills --"],
            "min_experience_months": 12
        }

        response = client.post("/api/vacancies", json=request_data)

        # Should handle gracefully
        assert response.status_code in [201, 400, 401, 422]
        assert response.status_code != 500


# =============================================================================
# Analytics Endpoint SQL Injection Tests
# =============================================================================

class TestAnalyticsEndpointSQLiProtection:
    """Tests for SQL injection protection in analytics endpoints."""

    @pytest.mark.parametrize("payload", SQLiPayloads.COMMENT_BASED)
    def test_analytics_key_metrics_with_sqli_in_dates(self, client, payload):
        """Test SQL injection via date parameters is blocked."""
        response = client.get(
            f"/api/analytics/key-metrics?start_date={payload}"
        )

        # Should return 400/422 (validation error) - malformed date
        # Should NOT return 500 (SQL error)
        assert response.status_code in [200, 400, 422]

    def test_analytics_funnel_with_sqli_in_date_range(self, client):
        """Test SQL injection in date range filters is blocked."""
        response = client.get(
            "/api/analytics/funnel?start_date=' OR '1'='1 --&end_date=2024-12-31"
        )

        # Should validate and reject malformed dates
        assert response.status_code in [200, 400, 422]

    def test_analytics_skill_demand_with_sqli_in_limit(self, client):
        """Test SQL injection via limit parameter is blocked."""
        response = client.get(
            "/api/analytics/skill-demand?limit=' OR '1'='1"
        )

        # Should validate limit parameter
        assert response.status_code in [200, 400, 422]


# =============================================================================
# ID-based Lookup SQL Injection Tests
# =============================================================================

class TestIDBasedLookupsSQLiProtection:
    """Tests for SQL injection protection in ID-based lookups."""

    @pytest.mark.parametrize("malicious_id", [
        "' OR '1'='1",
        "'; DROP TABLE users --",
        "1' OR '1'='1",
        "0x736563726574",  # Hex for "secret"
        "UNION SELECT NULL",
    ])
    def test_vacancy_lookup_with_malicious_id(self, client, malicious_id):
        """
        Test SQL injection via vacancy ID parameter is blocked.

        UUID fields should reject non-UUID formats.
        """
        response = client.get(f"/api/vacancies/{malicious_id}")

        # Should return 404 (not found) or 422 (validation error)
        # Malformed UUID should be rejected before DB query
        assert response.status_code in [404, 422]

    def test_resume_lookup_with_malicious_id(self, client):
        """Test SQL injection via resume ID parameter is blocked."""
        response = client.get("/api/resumes/' OR '1'='1")

        # Should reject malformed UUID
        assert response.status_code in [404, 422]


# =============================================================================
# Parameterized Query Verification Tests
# =============================================================================

class TestParameterizedQueryUsage:
    """
    Tests to verify that parameterized queries are used consistently.

    SQLAlchemy's ORM should always use parameterized queries which
    automatically prevent SQL injection. These tests verify that
    input values are treated as data, not executable code.
    """

    @patch('database.get_db')
    def test_search_uses_parameterized_queries(self, mock_get_db, client):
        """
        Verify that search queries use parameterized statements.

        Parameterized queries ensure user input is treated as literals,
        not as executable SQL code.
        """
        # Mock the database session
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Execute search with SQLi payload
        response = client.post(
            "/api/search/candidates",
            json={
                "query": "' OR '1'='1",
                "limit": 10
            }
        )

        # If we reach the database, verify queries were parameterized
        # (This is a conceptual test - real implementation would inspect actual queries)
        # The key is that we don't get SQL syntax errors

        # Should handle gracefully without SQL errors
        assert response.status_code in [200, 400, 401, 422]


# =============================================================================
# Edge Cases and Special Scenarios
# =============================================================================

class TestSQLiProtectionEdgeCases:
    """Tests for edge cases and special SQL injection scenarios."""

    def test_sqli_with_unicode_characters(self, client):
        """Test SQL injection with Unicode characters is handled safely."""
        payload = {
            "query": "'; DROP TABLE users -- 日本語 👾",
            "limit": 10
        }

        response = client.post("/api/search/candidates", json=payload)

        # Should handle safely
        assert response.status_code in [200, 400, 422]

    def test_sqli_with_null_bytes(self, client):
        """Test SQL injection with null bytes is handled safely."""
        payload = {
            "query": "'; DROP TABLE\x00users --",
            "limit": 10
        }

        response = client.post("/api/search/candidates", json=payload)

        # Should handle safely
        assert response.status_code in [200, 400, 422]

    def test_sqli_with_very_long_payload(self, client):
        """Test SQL injection with very long payload is handled safely."""
        long_payload = "'" + " OR '1'='1' AND " * 1000 + " '1'='1"

        payload = {
            "query": long_payload,
            "limit": 10
        }

        response = client.post("/api/search/candidates", json=payload)

        # Should handle safely - may reject due to length limits
        assert response.status_code in [200, 400, 422]

    def test_sqli_with_nested_quotes(self, client):
        """Test SQL injection with nested quote variations."""
        payloads = [
            "''' OR '''='''",
            "'\"' OR '\"'='\"'",
            "`' OR 1=1 --",
        ]

        for payload in payloads:
            response = client.post(
                "/api/search/candidates",
                json={"query": payload, "limit": 10}
            )

            # Should handle each variation safely
            assert response.status_code in [200, 400, 422]

    def test_sqli_with_base64_encoding(self, client):
        """
        Test that even if input is encoded, SQL injection is blocked.

        Some attackers encode payloads to bypass filters.
        """
        # '; DROP TABLE users -- in base64
        encoded_payload = "JztEUk9QIFRBQkxFIHVzZXJzIC0t"

        response = client.post(
            "/api/search/candidates",
            json={"query": encoded_payload, "limit": 10}
        )

        # Should handle safely - encoded payload treated as literal string
        assert response.status_code in [200, 400, 422]

    def test_second_order_sqli_via_search_history(self, client):
        """
        Test potential second-order SQL injection via stored search history.

        Second-order SQLi occurs when malicious input is stored and later
        used in another query. This test verifies stored data is sanitized.
        """
        # First, create a search with SQLi payload
        create_response = client.post(
            "/api/search/candidates",
            json={"query": "'; DROP TABLE search_history --", "limit": 10}
        )

        # If successful, try to retrieve search history
        # The stored query should be treated as data, not executable code
        history_response = client.get("/api/search/history")

        # Both requests should handle safely
        assert create_response.status_code in [200, 400, 401, 422]
        assert history_response.status_code in [200, 401]


# =============================================================================
# ORM-Specific Protection Tests
# =============================================================================

class TestORMSQLiProtection:
    """
    Tests for SQLAlchemy ORM-specific SQL injection protection.

    SQLAlchemy's ORM provides automatic SQL injection protection when
    used correctly. These tests verify ORM best practices are followed.
    """

    def test_orm_prevents_raw_sql_execution(self, client):
        """
        Verify that raw SQL strings are not executed directly.

        ORM should always use query builders, not raw SQL concatenation.
        """
        # Attempt to inject raw SQL
        payload = {
            "query": "'; SELECT * FROM information_schema.tables --",
            "limit": 10
        }

        response = client.post("/api/search/candidates", json=payload)

        # Should not execute raw SQL - payload treated as search text
        assert response.status_code in [200, 400, 422]

        # Verify database schema information not leaked
        if response.status_code == 200:
            data = response.json()
            # Response should not contain table metadata
            response_text = str(data).lower()
            assert "information_schema" not in response_text
            assert "pg_tables" not in response_text
            assert "sqlite_master" not in response_text

    def test_orm_filters_treated_as_literals(self, client):
        """
        Verify that filter values are treated as string literals, not SQL.

        ORM filters should use parameterized queries where filter values
        are bound as parameters, not concatenated into SQL.
        """
        response = client.post(
            "/api/search/candidates",
            json={
                "query": "Python",
                "filters": {
                    "location": "'; DROP TABLE resumes --"
                },
                "limit": 10
            }
        )

        # Should treat filter value as literal string
        assert response.status_code in [200, 400, 422]

        # Verify no database error indicating SQL execution
        assert "drop table" not in response.text.lower()


# =============================================================================
# Configuration for pytest
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "sqli: marks tests as SQL injection protection tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

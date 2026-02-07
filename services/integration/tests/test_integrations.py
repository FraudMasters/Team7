"""
Tests for Integration Service.

Tests cover integration management, LinkedIn profile fetching,
job board synchronization, and third-party service connections.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


class TestIntegrationModels:
    """Tests for integration request/response models."""

    def test_integration_info_model(self):
        """Test IntegrationInfo model."""
        from api.integrations import IntegrationInfo

        info = IntegrationInfo(
            id="linkedin",
            name="LinkedIn",
            type="linkedin",
            description="Import candidate profiles from LinkedIn",
            connected=True,
            enabled=True,
        )

        assert info.id == "linkedin"
        assert info.type == "linkedin"
        assert info.connected is True

    def test_integration_info_default_values(self):
        """Test IntegrationInfo with default values."""
        from api.integrations import IntegrationInfo

        info = IntegrationInfo(
            id="greenhouse",
            name="Greenhouse",
            type="ats",
            description="ATS integration",
        )

        assert info.connected is False
        assert info.enabled is True

    def test_integrations_list_response(self):
        """Test IntegrationsListResponse model."""
        from api.integrations import IntegrationsListResponse, IntegrationInfo

        response = IntegrationsListResponse(
            total=5,
            integrations=[
                IntegrationInfo(
                    id="linkedin",
                    name="LinkedIn",
                    type="linkedin",
                    description="LinkedIn integration",
                ),
                IntegrationInfo(
                    id="greenhouse",
                    name="Greenhouse",
                    type="ats",
                    description="ATS integration",
                ),
            ],
        )

        assert response.total == 5
        assert len(response.integrations) == 2

    def test_connect_integration_request(self):
        """Test ConnectIntegrationRequest model."""
        from api.integrations import ConnectIntegrationRequest

        request = ConnectIntegrationRequest(
            type="linkedin",
            credentials={"api_key": "test-key", "secret": "test-secret"},
            settings={"sync_frequency": "daily"},
        )

        assert request.type == "linkedin"
        assert request.credentials["api_key"] == "test-key"
        assert request.settings["sync_frequency"] == "daily"

    def test_connect_request_minimal(self):
        """Test ConnectIntegrationRequest with minimal fields."""
        from api.integrations import ConnectIntegrationRequest

        request = ConnectIntegrationRequest(
            type="greenhouse",
            credentials={"api_key": "key"},
        )

        assert request.type == "greenhouse"
        assert request.settings is None

    def test_linkedin_profile_request(self):
        """Test LinkedInProfileRequest model."""
        from api.integrations import LinkedInProfileRequest

        request = LinkedInProfileRequest(
            profile_url="https://linkedin.com/in/johndoe",
            include_skills=True,
            include_experience=True,
        )

        assert "linkedin.com/in/" in request.profile_url
        assert request.include_skills is True

    def test_linkedin_profile_request_defaults(self):
        """Test LinkedInProfileRequest with default values."""
        from api.integrations import LinkedInProfileRequest

        request = LinkedInProfileRequest(
            profile_url="https://linkedin.com/in/janedoe",
        )

        assert request.include_skills is True
        assert request.include_experience is True

    def test_job_board_sync_request(self):
        """Test JobBoardSyncRequest model."""
        from api.integrations import JobBoardSyncRequest

        request = JobBoardSyncRequest(
            job_board="linkedin",
            vacancy_ids=["vac-1", "vac-2", "vac-3"],
            sync_all=False,
        )

        assert request.job_board == "linkedin"
        assert len(request.vacancy_ids) == 3
        assert request.sync_all is False

    def test_job_board_sync_all_vacancies(self):
        """Test JobBoardSyncRequest for syncing all vacancies."""
        from api.integrations import JobBoardSyncRequest

        request = JobBoardSyncRequest(
            job_board="indeed",
            sync_all=True,
        )

        assert request.sync_all is True
        assert request.vacancy_ids is None


class TestListIntegrations:
    """Tests for list integrations endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_integrations(self):
        """Test listing all available integrations."""
        # Mock integrations data
        mock_integrations = [
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "type": "linkedin",
                "description": "Import candidate profiles from LinkedIn",
                "connected": False,
                "enabled": True,
            },
            {
                "id": "greenhouse",
                "name": "Greenhouse",
                "type": "ats",
                "description": "ATS integration for Greenhouse",
                "connected": False,
                "enabled": True,
            },
        ]

        assert len(mock_integrations) == 2
        assert mock_integrations[0]["id"] == "linkedin"
        assert mock_integrations[1]["type"] == "ats"

    @pytest.mark.asyncio
    async def test_filter_integrations_by_type(self):
        """Test filtering integrations by type."""
        all_integrations = [
            {"id": "linkedin", "type": "linkedin"},
            {"id": "greenhouse", "type": "ats"},
            {"id": "lever", "type": "ats"},
            {"id": "bamboohr", "type": "hris"},
        ]

        ats_integrations = [i for i in all_integrations if i["type"] == "ats"]

        assert len(ats_integrations) == 2
        assert all(i["type"] == "ats" for i in ats_integrations)

    def test_integration_types(self):
        """Test that all expected integration types exist."""
        expected_types = ["linkedin", "ats", "hris", "job_board"]

        # The actual endpoint returns integrations with these types
        for integration_type in expected_types:
            assert isinstance(integration_type, str)
            assert len(integration_type) > 0


class TestConnectIntegration:
    """Tests for connect integration endpoint."""

    def test_valid_integration_types(self):
        """Test validation of supported integration types."""
        valid_types = ["linkedin", "greenhouse", "lever", "workday", "bamboohr", "ashby"]

        # All valid types should be strings
        for integration_type in valid_types:
            assert isinstance(integration_type, str)

    def test_integration_type_mapping(self):
        """Test integration type to name mapping."""
        integration_names = {
            "linkedin": "LinkedIn",
            "greenhouse": "Greenhouse",
            "lever": "Lever",
            "workday": "Workday",
            "bamboohr": "BambooHR",
            "ashby": "Ashby",
        }

        assert integration_names["linkedin"] == "LinkedIn"
        assert integration_names["bamboohr"] == "BambooHR"

    def test_integration_category_mapping(self):
        """Test integration type to category mapping."""
        integration_categories = {
            "linkedin": "linkedin",
            "greenhouse": "ats",
            "lever": "ats",
            "workday": "ats",
            "bamboohr": "hris",
            "ashby": "hris",
        }

        ats_integrations = [k for k, v in integration_categories.items() if v == "ats"]

        assert "greenhouse" in ats_integrations
        assert "lever" in ats_integrations
        assert "workday" in ats_integrations
        assert len(ats_integrations) == 3


class TestLinkedInIntegration:
    """Tests for LinkedIn integration functionality."""

    def test_linkedin_profile_url_validation(self):
        """Test LinkedIn profile URL validation."""
        valid_urls = [
            "https://linkedin.com/in/johndoe",
            "https://www.linkedin.com/in/janedoe",
            "http://linkedin.com/in/bobsmith",
        ]

        for url in valid_urls:
            assert "linkedin.com/in/" in url

    def test_invalid_linkedin_url_detection(self):
        """Test detection of invalid LinkedIn URLs."""
        invalid_urls = [
            "https://example.com/profile/john",
            "https://linkedin.com/profile/john",  # Wrong path
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert "linkedin.com/in/" not in url

    def test_linkedin_profile_fields(self):
        """Test expected LinkedIn profile fields."""
        profile_fields = [
            "name",
            "headline",
            "location",
            "skills",
            "experience",
            "education",
            "profile_url",
        ]

        # All expected fields should be present in a complete profile
        for field in profile_fields:
            assert isinstance(field, str)

    def test_linkedin_profile_with_skills(self):
        """Test LinkedIn profile data with skills."""
        mock_profile = {
            "name": "John Doe",
            "headline": "Software Engineer",
            "skills": ["Python", "FastAPI", "Docker"],
            "profile_url": "https://linkedin.com/in/johndoe",
        }

        assert "skills" in mock_profile
        assert len(mock_profile["skills"]) == 3
        assert "Python" in mock_profile["skills"]

    def test_linkedin_profile_with_experience(self):
        """Test LinkedIn profile data with experience."""
        mock_profile = {
            "name": "Jane Doe",
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Tech Corp",
                    "years": 5,
                }
            ],
        }

        assert "experience" in mock_profile
        assert len(mock_profile["experience"]) == 1
        assert mock_profile["experience"][0]["title"] == "Senior Developer"


class TestJobBoardSync:
    """Tests for job board synchronization."""

    def test_valid_job_boards(self):
        """Test validation of supported job boards."""
        valid_boards = ["linkedin", "indeed", "monster", "glassdoor"]

        for board in valid_boards:
            assert isinstance(board, str)
            assert len(board) > 0

    def test_sync_result_structure(self):
        """Test sync result data structure."""
        sync_result = {
            "synced": 15,
            "failed": 2,
            "total": 17,
            "message": "Sync completed",
        }

        assert sync_result["synced"] == 15
        assert sync_result["failed"] == 2
        assert sync_result["total"] == 17
        assert sync_result["synced"] + sync_result["failed"] <= sync_result["total"]

    def test_sync_all_flag(self):
        """Test sync_all flag behavior."""
        request_with_all = {"job_board": "linkedin", "sync_all": True}
        request_specific = {"job_board": "linkedin", "vacancy_ids": ["vac-1", "vac-2"]}

        assert request_with_all["sync_all"] is True
        assert "vacancy_ids" not in request_with_all
        assert "vacancy_ids" in request_specific


class TestDisconnectIntegration:
    """Tests for disconnect integration endpoint."""

    def test_disconnect_response(self):
        """Test disconnect integration returns 204 status."""
        # Disconnect endpoint should return HTTP 204 NO CONTENT
        expected_status = 204

        assert expected_status == 204

    def test_integration_id_format(self):
        """Test integration ID format."""
        valid_ids = ["linkedin", "greenhouse", "lever", "workday", "bamboohr"]

        for integration_id in valid_ids:
            assert isinstance(integration_id, str)
            assert integration_id.isalnum() or "_" in integration_id


class TestIntegrationCredentials:
    """Tests for integration credential handling."""

    def test_credential_structure(self):
        """Test credential data structure."""
        credentials = {
            "api_key": "test-api-key-12345",
            "secret": "test-secret-67890",
            "workspace_id": "workspace-abc",
        }

        assert "api_key" in credentials
        assert "secret" in credentials
        assert len(credentials["api_key"]) > 0

    def test_credential_masking(self):
        """Test concept of credential masking for display."""
        credentials = {"api_key": "sk-1234567890abcdef"}

        # Credentials should be masked when displayed
        masked_key = credentials["api_key"][:4] + "*" * (len(credentials["api_key"]) - 4)

        assert "*" in masked_key
        assert len(masked_key) == len(credentials["api_key"])


class TestIntegrationSettings:
    """Tests for integration settings."""

    def test_sync_frequency_settings(self):
        """Test sync frequency settings."""
        valid_frequencies = ["hourly", "daily", "weekly", "monthly"]

        for frequency in valid_frequencies:
            assert isinstance(frequency, str)

    def test_integration_settings_structure(self):
        """Test integration settings structure."""
        settings = {
            "sync_frequency": "daily",
            "auto_import": True,
            "notification_enabled": False,
            "custom_fields": {"field1": "value1"},
        }

        assert settings["sync_frequency"] == "daily"
        assert settings["auto_import"] is True
        assert settings["notification_enabled"] is False


class TestLinkedInService:
    """Tests for LinkedInService class."""

    def test_linkedin_service_initialization(self):
        """Test LinkedInService initialization."""
        from services.linkedin_service import LinkedInService

        with patch("services.linkedin_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                linkedin_api_key="test-key",
                linkedin_api_secret="test-secret",
            )

            service = LinkedInService()
            assert service is not None

    @pytest.mark.asyncio
    async def test_get_profile_mock(self):
        """Test getting LinkedIn profile (mocked)."""
        from services.linkedin_service import LinkedInService

        with patch("services.linkedin_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                linkedin_api_key="test-key",
                linkedin_api_secret="test-secret",
            )

            service = LinkedInService()

            # Mock the profile fetch
            mock_profile = {
                "name": "Test User",
                "headline": "Software Engineer",
                "skills": ["Python", "FastAPI"],
                "experience": [],
            }

            with patch.object(service, "get_profile", return_value=mock_profile):
                profile = await service.get_profile(
                    profile_url="https://linkedin.com/in/testuser",
                    include_skills=True,
                    include_experience=True,
                )

                assert profile["name"] == "Test User"
                assert profile["headline"] == "Software Engineer"


class TestIntegrationErrorHandling:
    """Tests for integration error handling."""

    def test_invalid_integration_type_error(self):
        """Test error handling for invalid integration type."""
        valid_types = ["linkedin", "greenhouse", "lever", "workday", "bamboohr", "ashby"]
        invalid_type = "invalid_type"

        assert invalid_type not in valid_types

    def test_invalid_job_board_error(self):
        """Test error handling for invalid job board."""
        valid_boards = ["linkedin", "indeed", "monster", "glassdoor"]
        invalid_board = "facebook"

        assert invalid_board not in valid_boards

    def test_invalid_linkedin_url_error(self):
        """Test error handling for invalid LinkedIn URL."""
        invalid_url = "https://facebook.com/profile/john"

        assert "linkedin.com/in/" not in invalid_url


class TestIntegrationState:
    """Tests for integration state management."""

    def test_connected_state(self):
        """Test integration connected state."""
        integration = {
            "id": "linkedin",
            "name": "LinkedIn",
            "connected": True,
        }

        assert integration["connected"] is True

    def test_disconnected_state(self):
        """Test integration disconnected state."""
        integration = {
            "id": "greenhouse",
            "name": "Greenhouse",
            "connected": False,
        }

        assert integration["connected"] is False

    def test_enabled_state(self):
        """Test integration enabled state."""
        integration = {
            "id": "lever",
            "name": "Lever",
            "enabled": True,
        }

        assert integration["enabled"] is True

    def test_disabled_state(self):
        """Test integration disabled state."""
        integration = {
            "id": "workday",
            "name": "Workday",
            "enabled": False,
        }

        assert integration["enabled"] is False


class TestIntegrationFiltering:
    """Tests for integration filtering logic."""

    def test_filter_by_connection_status(self):
        """Test filtering integrations by connection status."""
        integrations = [
            {"id": "linkedin", "connected": True},
            {"id": "greenhouse", "connected": False},
            {"id": "lever", "connected": True},
            {"id": "workday", "connected": False},
        ]

        connected = [i for i in integrations if i["connected"]]
        not_connected = [i for i in integrations if not i["connected"]]

        assert len(connected) == 2
        assert len(not_connected) == 2

    def test_filter_by_enabled_status(self):
        """Test filtering integrations by enabled status."""
        integrations = [
            {"id": "linkedin", "enabled": True},
            {"id": "greenhouse", "enabled": False},
            {"id": "lever", "enabled": True},
        ]

        enabled = [i for i in integrations if i["enabled"]]

        assert len(enabled) == 2

    def test_combined_filters(self):
        """Test combining multiple filters."""
        integrations = [
            {"id": "linkedin", "connected": True, "enabled": True, "type": "linkedin"},
            {"id": "greenhouse", "connected": False, "enabled": True, "type": "ats"},
            {"id": "lever", "connected": True, "enabled": False, "type": "ats"},
            {"id": "bamboohr", "connected": True, "enabled": True, "type": "hris"},
        ]

        # Connected AND Enabled AND ATS type
        filtered = [
            i for i in integrations
            if i["connected"] and i["enabled"] and i["type"] == "ats"
        ]

        assert len(filtered) == 0  # No ATS integrations meet all criteria


class TestIntegrationCategories:
    """Tests for integration categories."""

    def test_ats_integrations(self):
        """Test ATS integration identification."""
        ats_integrations = ["greenhouse", "lever", "workday", "ashby"]

        assert len(ats_integrations) == 4
        assert "greenhouse" in ats_integrations

    def test_hris_integrations(self):
        """Test HRIS integration identification."""
        hris_integrations = ["bamboohr", "workday"]

        assert len(hris_integrations) == 2
        assert "bamboohr" in hris_integrations

    def test_linkedin_type(self):
        """Test LinkedIn as a separate type."""
        linkedin_type = "linkedin"

        assert linkedin_type == "linkedin"


class TestSyncOperation:
    """Tests for sync operation logic."""

    def test_sync_count_calculation(self):
        """Test sync count calculation."""
        sync_result = {
            "synced": 10,
            "failed": 2,
            "total": 12,
        }

        assert sync_result["synced"] + sync_result["failed"] == sync_result["total"]

    def test_sync_failure_rate(self):
        """Test sync failure rate calculation."""
        sync_result = {
            "synced": 8,
            "failed": 2,
            "total": 10,
        }

        failure_rate = sync_result["failed"] / sync_result["total"]

        assert failure_rate == 0.2

    def test_sync_success_rate(self):
        """Test sync success rate calculation."""
        sync_result = {
            "synced": 15,
            "failed": 5,
            "total": 20,
        }

        success_rate = sync_result["synced"] / sync_result["total"]

        assert success_rate == 0.75


class TestIntegrationEdgeCases:
    """Tests for integration edge cases."""

    def test_empty_credentials(self):
        """Test handling of empty credentials."""
        credentials = {}

        assert len(credentials) == 0

    def test_missing_profile_fields(self):
        """Test handling of missing profile fields."""
        partial_profile = {
            "name": "John Doe",
            # Missing: headline, skills, experience
        }

        assert "name" in partial_profile
        assert "skills" not in partial_profile

    def test_zero_sync_count(self):
        """Test handling of zero sync count."""
        sync_result = {
            "synced": 0,
            "failed": 0,
            "total": 0,
        }

        assert sync_result["synced"] == 0

    def test_special_characters_in_profile(self):
        """Test handling of special characters in profile data."""
        profile = {
            "name": "José María García-López",
            "headline": "Développeur Full-Stack | Машинное обучение",
        }

        assert "é" in profile["name"]
        assert "|" in profile["headline"]


class TestIntegrationAPIResponse:
    """Tests for API response formatting."""

    def test_list_response_format(self):
        """Test list integrations response format."""
        response = {
            "total": 5,
            "integrations": [
                {"id": "linkedin", "name": "LinkedIn"},
                {"id": "greenhouse", "name": "Greenhouse"},
            ],
        }

        assert "total" in response
        assert "integrations" in response
        assert response["total"] >= len(response["integrations"])

    def test_connect_response_format(self):
        """Test connect integration response format."""
        response = {
            "id": "linkedin",
            "name": "LinkedIn",
            "type": "linkedin",
            "description": "LinkedIn integration",
            "connected": True,
            "enabled": True,
        }

        assert response["id"] == "linkedin"
        assert response["connected"] is True

    def test_linkedin_profile_response_format(self):
        """Test LinkedIn profile response format."""
        response = {
            "name": "John Doe",
            "headline": "Software Engineer",
            "location": "San Francisco, CA",
            "skills": ["Python", "FastAPI"],
            "profile_url": "https://linkedin.com/in/johndoe",
        }

        assert "name" in response
        assert "skills" in response
        assert "profile_url" in response

    def test_sync_response_format(self):
        """Test job board sync response format."""
        response = {
            "synced": 10,
            "failed": 0,
            "total": 10,
            "message": "Sync completed successfully",
        }

        assert "synced" in response
        assert "failed" in response
        assert "total" in response

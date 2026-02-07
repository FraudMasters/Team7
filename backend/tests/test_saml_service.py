"""
Unit Tests for SAML Service

This test module verifies the core SAML service functionality including
configuration handling, metadata generation, certificate validation, and
SAML request/response processing.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from base64 import b64encode
from xml.etree import ElementTree as ET

from services.saml_service import SAMLService, get_saml_service


# Valid test certificate
VALID_CERT = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL0UG+mRKqzMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMjYwMjA0MDAwMDAwWhcNMjcwMjA0MDAwMDAwWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAuHr1pz8HKPLrBh9tAA2MqJBWQ7X7uZN9A8p6mjk+qPd3gKNnZPBzVypp
-----END CERTIFICATE-----"""


# Invalid certificate (no PEM headers)
INVALID_CERT = "not a valid certificate"


class TestSAMLService:
    """Test suite for SAMLService class."""

    def test_initialization_with_config(self):
        """Test SAML service initialization with explicit configuration."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
            slo_url="https://test.com/slo",
            certificate_path=None,
            key_path=None,
            want_assertions_signed=True,
            want_response_signed=True,
            allowed_clock_skew=60,
        )

        assert service.sp_entity_id == "https://test.com/entityid"
        assert service.acs_url == "https://test.com/acs"
        assert service.slo_url == "https://test.com/slo"
        assert service.want_assertions_signed is True
        assert service.want_response_signed is True
        assert service.allowed_clock_skew == 60
        assert service.enabled is True

    def test_initialization_without_required_config(self):
        """Test that SAML service without required config is disabled."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        assert service.enabled is False

    def test_validate_certificate_valid(self):
        """Test certificate validation with valid PEM certificate."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        result = service.validate_certificate(VALID_CERT)
        assert result is True

    def test_validate_certificate_invalid_no_header(self):
        """Test certificate validation rejects certificates without PEM header."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        result = service.validate_certificate(INVALID_CERT)
        assert result is False

    def test_validate_certificate_invalid_no_footer(self):
        """Test certificate validation rejects certificates without PEM footer."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        invalid_cert = "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAg"
        result = service.validate_certificate(invalid_cert)
        assert result is False

    def test_health_check_enabled(self):
        """Test health check returns healthy status when properly configured."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
            certificate_path="/path/to/cert.pem",
            key_path="/path/to/key.pem",
        )

        health = service.health_check()

        assert health["status"] == "healthy"
        assert health["enabled"] is True
        assert health["configured"] is True
        assert health["sp_entity_id"] == "https://test.com/entityid"
        assert health["acs_url"] == "https://test.com/acs"
        assert health["error"] is None

    def test_health_check_disabled(self):
        """Test health check returns unhealthy status when disabled."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        health = service.health_check()

        assert health["status"] == "unhealthy"
        assert health["enabled"] is False
        assert health["configured"] is False
        assert health["error"] is not None
        assert "not enabled" in health["error"].lower()

    def test_health_check_incomplete_config(self):
        """Test health check with incomplete configuration."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
            certificate_path=None,  # Missing certificate
        )

        health = service.health_check()

        assert health["status"] == "unhealthy"
        assert health["enabled"] is True
        assert health["configured"] is False
        assert "incomplete" in health["error"].lower()

    def test_build_saml_config_success(self):
        """Test successful SAML config building."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
            slo_url="https://test.com/slo",
            certificate_path=None,
            key_path=None,
        )

        # Mock the Saml2Config load to return a mock config
        with patch('services.saml_service.Saml2Config') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value.load.return_value = mock_config

            result = service._build_saml_config(
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
                idp_sls_url="https://idp.com/slo",
            )

            assert result is not None

    def test_build_saml_config_missing_required_fields(self):
        """Test that missing required fields raise ValueError."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        with pytest.raises(ValueError) as exc_info:
            service._build_saml_config(
                idp_entity_id="",  # Empty entity_id
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

        assert "required" in str(exc_info.value).lower()

    def test_build_saml_config_when_disabled(self):
        """Test that building config when service is disabled raises ValueError."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        with pytest.raises(ValueError) as exc_info:
            service._build_saml_config(
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

        assert "not enabled" in str(exc_info.value).lower()

    @patch('services.saml_service.Saml2Client')
    @patch('services.saml_service.Saml2Config')
    def test_get_login_redirect_url_success(self, mock_config_class, mock_client_class):
        """Test successful generation of login redirect URL."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value.load.return_value = mock_config

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.create_authn_request.return_value = ("req_id", "authn_request_xml")
        mock_client.apply_binding.return_value = "https://idp.com/sso?SAMLRequest=..."

        result = service.get_login_redirect_url(
            idp_entity_id="https://idp.com/entityid",
            idp_sso_url="https://idp.com/sso",
            idp_certificate=VALID_CERT,
            relay_state="/dashboard",
        )

        assert result == "https://idp.com/sso?SAMLRequest=..."
        mock_client.create_authn_request.assert_called_once()
        mock_client.apply_binding.assert_called_once()

    def test_get_login_redirect_url_when_disabled(self):
        """Test that login redirect fails when service is disabled."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        with pytest.raises(ValueError) as exc_info:
            service.get_login_redirect_url(
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

        assert "not enabled" in str(exc_info.value).lower()

    @patch('services.saml_service.Saml2Client')
    @patch('services.saml_service.Saml2Config')
    def test_process_saml_response_success(self, mock_config_class, mock_client_class):
        """Test successful processing of SAML response."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value.load.return_value = mock_config

        mock_response = Mock()
        mock_response.name_id = "test@example.com"
        mock_response.session_index = "session123"
        mock_response.issuer.return_value = "https://idp.com/entityid"
        mock_response.ava = {
            "email": ["test@example.com"],
            "displayName": ["Test User"],
            "firstName": ["Test"],
            "lastName": ["User"],
            "department": ["Engineering"],
        }

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.parse_authn_request_response.return_value = mock_response

        # Mock SAML response
        saml_response = b64encode(b"<saml>response</saml>").decode()

        result = service.process_saml_response(
            saml_response=saml_response,
            idp_entity_id="https://idp.com/entityid",
            idp_sso_url="https://idp.com/sso",
            idp_certificate=VALID_CERT,
        )

        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"
        assert result["department"] == "Engineering"
        assert result["name_id"] == "test@example.com"
        assert result["session_index"] == "session123"

    @patch('services.saml_service.Saml2Client')
    @patch('services.saml_service.Saml2Config')
    def test_process_saml_response_missing_email(self, mock_config_class, mock_client_class):
        """Test that SAML response without email raises ValueError."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value.load.return_value = mock_config

        mock_response = Mock()
        mock_response.name_id = "test@example.com"
        mock_response.ava = {}  # No email attribute

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.parse_authn_request_response.return_value = mock_response

        saml_response = b64encode(b"<saml>response</saml>").decode()

        with pytest.raises(ValueError) as exc_info:
            service.process_saml_response(
                saml_response=saml_response,
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

        assert "email" in str(exc_info.value).lower()

    def test_process_saml_response_when_disabled(self):
        """Test that SAML response processing fails when service is disabled."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        with pytest.raises(ValueError) as exc_info:
            service.process_saml_response(
                saml_response="base64_response",
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

        assert "not enabled" in str(exc_info.value).lower()

    @patch('services.saml_service.entity_descriptor')
    @patch('services.saml_service.Saml2Config')
    def test_generate_metadata_success(self, mock_config_class, mock_entity_descriptor):
        """Test successful metadata generation."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
            slo_url="https://test.com/slo",
            certificate_path=None,
            key_path=None,
        )

        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value.load.return_value = mock_config

        mock_entity_descriptor.return_value = "<?xml version=\"1.0\"?><md:EntityDescriptor>...</md:EntityDescriptor>"

        result = service.generate_metadata()

        assert result is not None
        assert "<?xml" in result

    def test_generate_metadata_when_disabled(self):
        """Test that metadata generation fails when service is disabled."""
        service = SAMLService(
            sp_entity_id=None,
            acs_url=None,
        )

        with pytest.raises(ValueError) as exc_info:
            service.generate_metadata()

        assert "not enabled" in str(exc_info.value).lower()

    def test_get_saml_service_singleton(self):
        """Test that get_saml_service returns singleton instance."""
        # Reset global service
        import services.saml_service
        services.saml_service._saml_service = None

        service1 = get_saml_service()
        service2 = get_saml_service()

        assert service1 is service2

    def test_attribute_mapping_defaults(self):
        """Test default attribute mapping configuration."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        assert service.ATTRIBUTE_EMAIL == "email"
        assert service.ATTRIBUTE_NAME == "displayName"
        assert service.ATTRIBUTE_FIRST_NAME == "firstName"
        assert service.ATTRIBUTE_LAST_NAME == "lastName"
        assert service.ATTRIBUTE_DEPARTMENT == "department"


class TestSAMLServiceEdgeCases:
    """Test edge cases and error conditions."""

    def test_process_response_with_list_attributes(self):
        """Test handling of SAML attributes that are lists."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        with patch('services.saml_service.Saml2Client') as mock_client_class, \
             patch('services.saml_service.Saml2Config') as mock_config_class:

            mock_config = Mock()
            mock_config_class.return_value.load.return_value = mock_config

            # Mock response with list attributes
            mock_response = Mock()
            mock_response.name_id = "test@example.com"
            mock_response.session_index = "session123"
            mock_response.issuer.return_value = "https://idp.com/entityid"
            mock_response.ava = {
                "email": ["test@example.com"],
                "displayName": ["Test User"],
            }

            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.parse_authn_request_response.return_value = mock_response

            saml_response = b64encode(b"<saml>response</saml>").decode()

            result = service.process_saml_response(
                saml_response=saml_response,
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
            )

            # Should extract first value from lists
            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"

    def test_process_response_with_custom_attribute_mapping(self):
        """Test processing with custom attribute mapping."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/acs",
        )

        with patch('services.saml_service.Saml2Client') as mock_client_class, \
             patch('services.saml_service.Saml2Config') as mock_config_class:

            mock_config = Mock()
            mock_config_class.return_value.load.return_value = mock_config

            # Mock response with custom attributes
            mock_response = Mock()
            mock_response.name_id = "test@example.com"
            mock_response.session_index = "session123"
            mock_response.issuer.return_value = "https://idp.com/entityid"
            mock_response.ava = {
                "userEmail": ["custom@example.com"],
                "fullName": ["Custom User"],
            }

            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.parse_authn_request_response.return_value = mock_response

            saml_response = b64encode(b"<saml>response</saml>").decode()

            result = service.process_saml_response(
                saml_response=saml_response,
                idp_entity_id="https://idp.com/entityid",
                idp_sso_url="https://idp.com/sso",
                idp_certificate=VALID_CERT,
                attribute_mapping={
                    "email": "userEmail",
                    "name": "fullName",
                },
            )

            assert result["email"] == "custom@example.com"
            assert result["name"] == "Custom User"


class TestSAMLIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_okta_integration_scenario(self):
        """Test Okta-specific configuration scenario."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/saml/acs",
            slo_url="https://test.com/saml/slo",
            certificate_path="/certs/sp-cert.pem",
            key_path="/certs/sp-key.pem",
            want_assertions_signed=True,
            want_response_signed=False,  # Okta default
            allowed_clock_skew=60,
        )

        assert service.enabled is True
        health = service.health_check()
        assert health["status"] == "unhealthy"  # Cert files don't exist

    def test_azure_ad_integration_scenario(self):
        """Test Azure AD-specific configuration scenario."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/saml/acs",
            slo_url="https://test.com/saml/slo",
            certificate_path="/certs/sp-cert.pem",
            key_path="/certs/sp-key.pem",
            want_assertions_signed=True,
            want_response_signed=True,  # Azure AD requires
            allowed_clock_skew=300,  # 5 minutes for Azure
        )

        assert service.enabled is True
        assert service.allowed_clock_skew == 300

    def test_google_workspace_scenario(self):
        """Test Google Workspace-specific configuration scenario."""
        service = SAMLService(
            sp_entity_id="https://test.com/entityid",
            acs_url="https://test.com/saml/acs",
            slo_url=None,  # Google Workspace may not support SLO
            certificate_path="/certs/sp-cert.pem",
            key_path="/certs/sp-key.pem",
            want_assertions_signed=True,
            want_response_signed=True,
        )

        assert service.enabled is True
        assert service.slo_url is None

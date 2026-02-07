"""
Email rendering service with template engine and organization branding.

This module provides email template rendering functionality using Jinja2,
supporting organization-specific branding, custom templates, and fallback
to default templates when needed.

The service handles:
- Template variable substitution using Jinja2
- Organization branding integration (logo, colors)
- HTML and plain text email rendering
- Fallback to default templates when custom templates don't exist
- Template caching for performance
- Error handling and validation

Template Variables:
- {{candidate_name}}: Name of the candidate
- {{recruiter_name}}: Name of the recruiter
- {{feedback_id}}: Feedback identifier
- {{match_score}}: Match percentage
- {{organization_name}}: Organization name
- {{organization_logo}}: URL to organization logo
- Any custom variables defined in the template

Example:
    >>> from services.email_rendering import render_email_template
    >>> subject, html_body, text_body = render_email_template(
    ...     db=session,
    ...     organization_id="org-123",
    ...     template_type="candidate_feedback",
    ...     context={
    ...         "candidate_name": "John Doe",
    ...         "match_score": 85
    ...     }
    ... )
    >>> print(subject)  # "Candidate Feedback: John Doe"
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from jinja2 import Environment, BaseLoader, TemplateSyntaxError, TemplateError
from sqlalchemy.orm import Session

from config import get_settings
from models.email_template import EmailTemplate
from models.branding_settings import BrandingSettings
from models.organization import Organization

logger = logging.getLogger(__name__)
settings = get_settings()


# Default templates for fallback when no custom template exists
DEFAULT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "candidate_feedback": {
        "subject": "Candidate Feedback: {{candidate_name}}",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidate Feedback</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid {{primary_color}}; padding-bottom: 20px; margin-bottom: 20px; }
        .logo { max-height: 50px; }
        .content { margin: 20px 0; }
        .footer { border-top: 1px solid #ddd; padding-top: 20px; margin-top: 20px; font-size: 12px; color: #666; }
        .score { font-size: 24px; font-weight: bold; color: {{primary_color}}; }
        .label { font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        {% if organization_logo %}
        <div class="header">
            <img src="{{organization_logo}}" alt="{{organization_name}}" class="logo">
        </div>
        {% endif %}
        <div class="content">
            <h2>Candidate Feedback: {{candidate_name}}</h2>
            <p><span class="label">Feedback ID:</span> {{feedback_id}}</p>
            <p><span class="label">Match Score:</span> <span class="score">{{match_score}}%</span></p>

            {% if skills_feedback %}
            <h3>Skills Feedback</h3>
            <p>{{skills_feedback}}</p>
            {% endif %}

            {% if recommendations %}
            <h3>Recommendations</h3>
            <ul>
            {% for recommendation in recommendations %}
                <li>{{recommendation}}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
        <div class="footer">
            <p>This is an automated email from {{organization_name}} Resume Analysis System.</p>
        </div>
    </div>
</body>
</html>
        """.strip(),
        "text": """
Feedback for Candidate: {{candidate_name}}
Feedback ID: {{feedback_id}}

Match Score: {{match_score}}%

{% if skills_feedback %}
Skills Feedback:
{{skills_feedback}}

{% endif %}
{% if recommendations %}
Recommendations:
{% for recommendation in recommendations %}
- {{recommendation}}
{% endfor %}

{% endif %}
---
This is an automated email from {{organization_name}} Resume Analysis System.
        """.strip(),
    },
    "batch_notification": {
        "subject": "{{title}}",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid {{primary_color}}; padding-bottom: 20px; margin-bottom: 20px; }
        .logo { max-height: 50px; }
        .content { margin: 20px 0; }
        .footer { border-top: 1px solid #ddd; padding-top: 20px; margin-top: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        {% if organization_logo %}
        <div class="header">
            <img src="{{organization_logo}}" alt="{{organization_name}}" class="logo">
        </div>
        {% endif %}
        <div class="content">
            <h2>{{title}}</h2>
            <p>{{message}}</p>
            {% if details %}
            <h3>Details</h3>
            <pre>{{details}}</pre>
            {% endif %}
        </div>
        <div class="footer">
            <p>This is an automated email from {{organization_name}}.</p>
        </div>
    </div>
</body>
</html>
        """.strip(),
        "text": """
{{title}}

{{message}}

{% if details %}
Details:
{{details}}
{% endif %}

---
This is an automated email from {{organization_name}}.
        """.strip(),
    },
}


class EmailRenderingService:
    """
    Email rendering service with Jinja2 template engine.

    This service provides methods for rendering email templates with
    organization branding and custom template support.

    Attributes:
        env: Jinja2 environment for template rendering
        default_primary_color: Default primary color for branding
        default_secondary_color: Default secondary color for branding
        default_accent_color: Default accent color for branding

    Example:
        >>> service = EmailRenderingService()
        >>> subject, html, text = service.render_template(
        ...     db=session,
        ...     organization_id="org-123",
        ...     template_type="candidate_feedback",
        ...     context={"candidate_name": "John Doe"}
        ... )
    """

    def __init__(
        self,
        default_primary_color: str = "#3B82F6",
        default_secondary_color: str = "#10B981",
        default_accent_color: str = "#F59E0B",
    ) -> None:
        """
        Initialize the email rendering service.

        Args:
            default_primary_color: Default primary color (hex format)
            default_secondary_color: Default secondary color (hex format)
            default_accent_color: Default accent color (hex format)
        """
        self.env = Environment(loader=BaseLoader())
        self.default_primary_color = default_primary_color
        self.default_secondary_color = default_secondary_color
        self.default_accent_color = default_accent_color

        logger.info("EmailRenderingService initialized")

    def _get_organization_branding(
        self,
        db: Session,
        organization_id: str,
    ) -> Dict[str, Any]:
        """
        Get organization branding settings.

        Args:
            db: Database session
            organization_id: Organization ID

        Returns:
            Dictionary containing branding settings:
            - logo_url: URL to organization logo
            - primary_color: Primary brand color
            - secondary_color: Secondary brand color
            - accent_color: Accent color
            - organization_name: Organization name
        """
        try:
            # Get organization
            organization = db.query(Organization).filter(
                Organization.id == organization_id,
                Organization.is_active == True
            ).first()

            logo_url = None
            organization_name = "AgentHR"

            if organization:
                logo_url = organization.logo_url
                organization_name = organization.name

            # Get branding settings
            branding = db.query(BrandingSettings).filter(
                BrandingSettings.organization_id == organization_id,
                BrandingSettings.is_active == True
            ).first()

            primary_color = self.default_primary_color
            secondary_color = self.default_secondary_color
            accent_color = self.default_accent_color

            if branding:
                primary_color = branding.primary_color
                secondary_color = branding.secondary_color
                accent_color = branding.accent_color
                if branding.logo_url:
                    logo_url = branding.logo_url

            return {
                "logo_url": logo_url,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "accent_color": accent_color,
                "organization_name": organization_name,
            }

        except Exception as e:
            logger.error(f"Error getting organization branding: {e}", exc_info=True)
            return {
                "logo_url": None,
                "primary_color": self.default_primary_color,
                "secondary_color": self.default_secondary_color,
                "accent_color": self.default_accent_color,
                "organization_name": "AgentHR",
            }

    def _get_custom_template(
        self,
        db: Session,
        organization_id: str,
        template_type: str,
    ) -> Optional[EmailTemplate]:
        """
        Get custom email template for organization.

        Args:
            db: Database session
            organization_id: Organization ID
            template_type: Type of template (e.g., 'candidate_feedback')

        Returns:
            EmailTemplate if found, None otherwise
        """
        try:
            template = db.query(EmailTemplate).filter(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.template_type == template_type,
                EmailTemplate.is_active == True
            ).order_by(EmailTemplate.is_default.desc()).first()

            if template:
                logger.debug(
                    f"Found custom template for org={organization_id}, "
                    f"type={template_type}"
                )

            return template

        except Exception as e:
            logger.error(f"Error getting custom template: {e}", exc_info=True)
            return None

    def _render_jinja_template(
        self,
        template_string: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a Jinja2 template string with context.

        Args:
            template_string: Jinja2 template string
            context: Dictionary of template variables

        Returns:
            Rendered template string

        Raises:
            TemplateError: If template syntax is invalid
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}", exc_info=True)
            raise TemplateError(f"Invalid template syntax: {e}")

        except TemplateError as e:
            logger.error(f"Template rendering error: {e}", exc_info=True)
            raise

    def render_template(
        self,
        db: Session,
        organization_id: str,
        template_type: str,
        context: Dict[str, Any],
    ) -> Tuple[str, str, str]:
        """
        Render email template with organization branding.

        This method retrieves the custom template for the organization
        (if available) or falls back to the default template, then
        renders it with the provided context and organization branding.

        Args:
            db: Database session
            organization_id: Organization ID
            template_type: Type of template (e.g., 'candidate_feedback')
            context: Dictionary of template variables

        Returns:
            Tuple containing:
            - subject: Rendered email subject
            - html_body: Rendered HTML email body
            - text_body: Rendered plain text email body

        Raises:
            ValueError: If template type is invalid
            TemplateError: If template rendering fails

        Example:
            >>> subject, html, text = service.render_template(
            ...     db=session,
            ...     organization_id="org-123",
            ...     template_type="candidate_feedback",
            ...     context={"candidate_name": "John Doe", "match_score": 85}
            ... )
        """
        logger.info(
            f"Rendering email template for org={organization_id}, "
            f"type={template_type}"
        )

        # Get organization branding
        branding = self._get_organization_branding(db, organization_id)

        # Merge branding with context
        full_context = {
            **context,
            "organization_logo": branding["logo_url"],
            "organization_name": branding["organization_name"],
            "primary_color": branding["primary_color"],
            "secondary_color": branding["secondary_color"],
            "accent_color": branding["accent_color"],
        }

        # Try to get custom template
        custom_template = self._get_custom_template(db, organization_id, template_type)

        if custom_template:
            logger.debug(f"Using custom template for {template_type}")
            subject_template = custom_template.subject
            html_template = custom_template.body
            # Generate text version from HTML (strip tags)
            text_template = self._html_to_text(custom_template.body)
        else:
            # Use default template
            if template_type not in DEFAULT_TEMPLATES:
                raise ValueError(f"Unknown template type: {template_type}")

            logger.debug(f"Using default template for {template_type}")
            default = DEFAULT_TEMPLATES[template_type]
            subject_template = default["subject"]
            html_template = default["html"]
            text_template = default["text"]

        try:
            # Render templates
            subject = self._render_jinja_template(subject_template, full_context)
            html_body = self._render_jinja_template(html_template, full_context)
            text_body = self._render_jinja_template(text_template, full_context)

            logger.info(
                f"Successfully rendered template for org={organization_id}, "
                f"type={template_type}"
            )

            return subject, html_body, text_body

        except Exception as e:
            logger.error(
                f"Failed to render template for org={organization_id}, "
                f"type={template_type}: {e}",
                exc_info=True
            )
            raise

    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text (basic conversion).

        Args:
            html: HTML string

        Returns:
            Plain text version
        """
        import re

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '\n', html)
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.strip()

        return text

    def preview_template(
        self,
        db: Session,
        organization_id: str,
        template_type: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Preview email template without sending.

        This method renders the template and returns a preview with
        metadata about the template used.

        Args:
            db: Database session
            organization_id: Organization ID
            template_type: Type of template
            context: Dictionary of template variables

        Returns:
            Dictionary containing:
            - subject: Email subject
            - html_body: HTML email body
            - text_body: Plain text email body
            - template_source: 'custom' or 'default'
            - branding: Organization branding info used

        Example:
            >>> preview = service.preview_template(
            ...     db=session,
            ...     organization_id="org-123",
            ...     template_type="candidate_feedback",
            ...     context={"candidate_name": "John Doe"}
            ... )
            >>> print(preview['template_source'])  # 'custom' or 'default'
        """
        logger.info(
            f"Previewing email template for org={organization_id}, "
            f"type={template_type}"
        )

        # Get organization branding
        branding = self._get_organization_branding(db, organization_id)

        # Check if custom template exists
        custom_template = self._get_custom_template(db, organization_id, template_type)
        template_source = "custom" if custom_template else "default"

        # Render template
        subject, html_body, text_body = self.render_template(
            db=db,
            organization_id=organization_id,
            template_type=template_type,
            context=context,
        )

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "template_source": template_source,
            "branding": branding,
        }


# Global service instance
_email_rendering_service: Optional[EmailRenderingService] = None


def get_email_rendering_service() -> EmailRenderingService:
    """
    Get or create the global email rendering service instance.

    Returns:
        EmailRenderingService instance

    Example:
        >>> service = get_email_rendering_service()
        >>> subject, html, text = service.render_template(...)
    """
    global _email_rendering_service

    if _email_rendering_service is None:
        _email_rendering_service = EmailRenderingService()

    return _email_rendering_service


def render_email_template(
    db: Session,
    organization_id: str,
    template_type: str,
    context: Dict[str, Any],
) -> Tuple[str, str, str]:
    """
    Convenience function to render email template.

    This is a shortcut for using the EmailRenderingService class directly.

    Args:
        db: Database session
        organization_id: Organization ID
        template_type: Type of template (e.g., 'candidate_feedback')
        context: Dictionary of template variables

    Returns:
        Tuple containing (subject, html_body, text_body)

    Raises:
        ValueError: If template type is invalid
        TemplateError: If template rendering fails

    Example:
        >>> from services.email_rendering import render_email_template
        >>> subject, html, text = render_email_template(
        ...     db=session,
        ...     organization_id="org-123",
        ...     template_type="candidate_feedback",
        ...     context={"candidate_name": "John Doe", "match_score": 85}
        ... )
    """
    service = get_email_rendering_service()
    return service.render_template(
        db=db,
        organization_id=organization_id,
        template_type=template_type,
        context=context,
    )

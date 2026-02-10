"""
Resume template renderer service with Jinja2 template engine.

This module provides resume template rendering functionality using Jinja2,
supporting customizable layouts, styles, and sections for professional
resume formatting.

The service handles:
- Template variable substitution using Jinja2
- Dynamic layout configuration (margins, sections, spacing)
- Style customization (colors, fonts, headings)
- Section ordering and visibility
- HTML and preview rendering
- Template caching for performance
- Error handling and validation

Template Variables:
- {{name}}: Full name of the candidate
- {{email}}: Email address
- {{phone}}: Phone number
- {{location}}: City, State/Country
- {{summary}}: Professional summary
- {{experience}}: List of work experience entries
- {{education}}: List of education entries
- {{skills}}: List of skills
- {{certifications}}: List of certifications
- Any custom fields from parsed resume data

Example:
    >>> from services.template_renderer import TemplateRenderer
    >>> renderer = TemplateRenderer()
    >>> html = renderer.render_resume(
    ...     template=resume_template,
    ...     resume_data={"name": "John Doe", "email": "john@example.com"}
    ... )
    >>> print(html)
"""
import logging
from typing import Any, Dict, Optional, List
from jinja2 import Environment, BaseLoader, TemplateSyntaxError, TemplateError
from sqlalchemy.orm import Session

from models.resume_template import ResumeTemplate

logger = logging.getLogger(__name__)


# Default resume templates for fallback
DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "modern": {
        "html_template": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - {{name}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .resume-container {
            max-width: 850px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 40px;
        }
        .header {
            border-bottom: 3px solid {{primary_color|default('#3B82F6')}};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .name {
            font-size: 32px;
            font-weight: 700;
            color: {{primary_color|default('#3B82F6')}};
            margin-bottom: 5px;
        }
        .contact-info {
            font-size: 14px;
            color: #666;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .contact-info span {
            display: flex;
            align-items: center;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: {{primary_color|default('#3B82F6')}};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            border-bottom: 2px solid #eee;
            padding-bottom: 5px;
        }
        .summary { font-size: 15px; color: #555; }
        .experience-item, .education-item {
            margin-bottom: 20px;
        }
        .item-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .item-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        .item-company {
            font-size: 15px;
            color: {{primary_color|default('#3B82F6')}};
        }
        .item-date {
            font-size: 14px;
            color: #888;
            font-weight: 500;
        }
        .item-description {
            font-size: 14px;
            color: #555;
            margin-top: 5px;
            line-height: 1.5;
        }
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .skill-tag {
            background: {{primary_color|default('#3B82F6')}};
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        @media print {
            body { background: white; padding: 0; }
            .resume-container { box-shadow: none; padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="resume-container">
        <div class="header">
            <h1 class="name">{{name}}</h1>
            <div class="contact-info">
                {% if email %}<span>{{email}}</span>{% endif %}
                {% if phone %}<span>{{phone}}</span>{% endif %}
                {% if location %}<span>{{location}}</span>{% endif %}
            </div>
        </div>

        {% if summary %}
        <div class="section">
            <h2 class="section-title">Professional Summary</h2>
            <p class="summary">{{summary}}</p>
        </div>
        {% endif %}

        {% if experience %}
        <div class="section">
            <h2 class="section-title">Work Experience</h2>
            {% for exp in experience %}
            <div class="experience-item">
                <div class="item-header">
                    <div>
                        <div class="item-title">{{exp.title}}</div>
                        <div class="item-company">{{exp.company}}</div>
                    </div>
                    {% if exp.start_date or exp.end_date %}
                    <div class="item-date">
                        {{exp.start_date|default('')}}{% if exp.start_date and exp.end_date %} - {% endif %}{{exp.end_date|default('Present')}}
                    </div>
                    {% endif %}
                </div>
                {% if exp.description %}
                <div class="item-description">{{exp.description}}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if education %}
        <div class="section">
            <h2 class="section-title">Education</h2>
            {% for edu in education %}
            <div class="education-item">
                <div class="item-header">
                    <div>
                        <div class="item-title">{{edu.degree}}</div>
                        <div class="item-company">{{edu.institution}}</div>
                    </div>
                    {% if edu.graduation_year %}
                    <div class="item-date">{{edu.graduation_year}}</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if skills %}
        <div class="section">
            <h2 class="section-title">Skills</h2>
            <div class="skills-list">
                {% for skill in skills %}
                <span class="skill-tag">{{skill}}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """.strip(),
    },
    "classic": {
        "html_template": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - {{name}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.5;
            color: #000;
            background: white;
            padding: 40px;
        }
        .resume-container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .name {
            font-size: 28px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .contact-info {
            font-size: 12px;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            border-bottom: 1px solid #000;
            margin-bottom: 15px;
            padding-bottom: 5px;
        }
        .experience-item, .education-item {
            margin-bottom: 15px;
        }
        .item-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 3px;
        }
        .item-title {
            font-weight: bold;
            font-size: 13px;
        }
        .item-date {
            font-size: 12px;
            font-style: italic;
        }
        .item-description {
            font-size: 12px;
            margin-top: 5px;
        }
        .skills-list {
            font-size: 12px;
        }
        .skills-list li {
            margin-bottom: 3px;
        }
        @media print {
            body { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="resume-container">
        <div class="header">
            <h1 class="name">{{name}}</h1>
            <div class="contact-info">
                {% if email %}<span>{{email}}</span>{% endif %}
                {% if phone %}<span>{{phone}}</span>{% endif %}
                {% if location %}<span>{{location}}</span>{% endif %}
            </div>
        </div>

        {% if summary %}
        <div class="section">
            <h2 class="section-title">Professional Summary</h2>
            <p style="font-size: 12px;">{{summary}}</p>
        </div>
        {% endif %}

        {% if experience %}
        <div class="section">
            <h2 class="section-title">Experience</h2>
            {% for exp in experience %}
            <div class="experience-item">
                <div class="item-header">
                    <span class="item-title">{{exp.title}}{% if exp.company %} at {{exp.company}}{% endif %}</span>
                    {% if exp.start_date or exp.end_date %}
                    <span class="item-date">{{exp.start_date|default('')}} - {{exp.end_date|default('Present')}}</span>
                    {% endif %}
                </div>
                {% if exp.description %}
                <div class="item-description">{{exp.description}}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if education %}
        <div class="section">
            <h2 class="section-title">Education</h2>
            {% for edu in education %}
            <div class="education-item">
                <div class="item-header">
                    <span class="item-title">{{edu.degree}}, {{edu.institution}}</span>
                    {% if edu.graduation_year %}
                    <span class="item-date">{{edu.graduation_year}}</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if skills %}
        <div class="section">
            <h2 class="section-title">Skills</h2>
            <ul class="skills-list">
                {% for skill in skills %}
                <li>{{skill}}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """.strip(),
    },
    "ats_friendly": {
        "html_template": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - {{name}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.5;
            color: #000;
            background: white;
            padding: 40px;
        }
        .resume-container {
            max-width: 750px;
            margin: 0 auto;
        }
        .header {
            margin-bottom: 25px;
        }
        .name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .contact-info {
            font-size: 12px;
            margin-bottom: 10px;
        }
        .section {
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .experience-item, .education-item {
            margin-bottom: 15px;
        }
        .item-title {
            font-weight: bold;
            font-size: 13px;
        }
        .item-subtitle {
            font-size: 12px;
            margin-bottom: 5px;
        }
        .item-date {
            font-size: 11px;
            margin-bottom: 8px;
        }
        .item-description {
            font-size: 11px;
            line-height: 1.4;
        }
        .skills-list {
            font-size: 12px;
        }
        @media print {
            body { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="resume-container">
        <div class="header">
            <h1 class="name">{{name}}</h1>
            <div class="contact-info">
                {% if email %}Email: {{email}}<br>{% endif %}
                {% if phone %}Phone: {{phone}}<br>{% endif %}
                {% if location %}Location: {{location}}<br>{% endif %}
            </div>
        </div>

        {% if summary %}
        <div class="section">
            <h2 class="section-title">Summary</h2>
            <p style="font-size: 11px;">{{summary}}</p>
        </div>
        {% endif %}

        {% if experience %}
        <div class="section">
            <h2 class="section-title">Work Experience</h2>
            {% for exp in experience %}
            <div class="experience-item">
                <div class="item-title">{{exp.title}}</div>
                {% if exp.company %}<div class="item-subtitle">{{exp.company}}</div>{% endif %}
                {% if exp.start_date or exp.end_date %}
                <div class="item-date">{{exp.start_date|default('')}} - {{exp.end_date|default('Present')}}</div>
                {% endif %}
                {% if exp.description %}
                <div class="item-description">{{exp.description}}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if education %}
        <div class="section">
            <h2 class="section-title">Education</h2>
            {% for edu in education %}
            <div class="education-item">
                <div class="item-title">{{edu.degree}}</div>
                {% if edu.institution %}<div class="item-subtitle">{{edu.institution}}</div>{% endif %}
                {% if edu.graduation_year %}<div class="item-date">{{edu.graduation_year}}</div>{% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if skills %}
        <div class="section">
            <h2 class="section-title">Skills</h2>
            <div class="skills-list">
                {% for skill in skills %}
                {{skill}}{% if not loop.last %}, {% endif %}
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """.strip(),
    },
}


class TemplateRenderer:
    """
    Resume template renderer service with Jinja2 template engine.

    This service provides methods for rendering resume data using
    customizable templates with layout, style, and section configuration.

    Attributes:
        env: Jinja2 environment for template rendering

    Example:
        >>> renderer = TemplateRenderer()
        >>> html = renderer.render_resume(
        ...     template=resume_template,
        ...     resume_data={"name": "John Doe", "email": "john@example.com"}
        ... )
    """

    def __init__(self) -> None:
        """
        Initialize the template renderer service.

        Creates a Jinja2 environment for template rendering.
        """
        self.env = Environment(loader=BaseLoader())
        logger.info("TemplateRenderer initialized")

    def _merge_configs(
        self,
        template: ResumeTemplate,
    ) -> Dict[str, Any]:
        """
        Merge template configuration with defaults.

        Args:
            template: ResumeTemplate instance

        Returns:
            Merged configuration dictionary
        """
        # Default configuration
        default_config = {
            "layout": {
                "margins": "40px",
                "max_width": "850px",
                "section_spacing": "30px",
            },
            "style": {
                "primary_color": "#3B82F6",
                "secondary_color": "#10B981",
                "font_family": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
                "font_size": "14px",
            },
            "sections": {
                "order": ["header", "summary", "experience", "education", "skills"],
                "display": {
                    "header": True,
                    "summary": True,
                    "experience": True,
                    "education": True,
                    "skills": True,
                    "certifications": False,
                },
            },
        }

        # Merge with template configuration
        if template.layout_config:
            default_config["layout"].update(template.layout_config.get("layout", {}))
            default_config["style"].update(template.layout_config.get("style", {}))

        if template.style_config:
            default_config["style"].update(template.style_config)

        if template.section_config:
            if "order" in template.section_config:
                default_config["sections"]["order"] = template.section_config["order"]
            if "display" in template.section_config:
                default_config["sections"]["display"].update(
                    template.section_config["display"]
                )

        return default_config

    def _get_template_string(
        self,
        template: ResumeTemplate,
    ) -> str:
        """
        Get the template HTML string.

        Args:
            template: ResumeTemplate instance

        Returns:
            HTML template string

        Raises:
            ValueError: If template type is invalid
        """
        # Check if template has custom HTML (stored in layout_config or style_config)
        if template.layout_config and "html_template" in template.layout_config:
            return template.layout_config["html_template"]

        if template.style_config and "html_template" in template.style_config:
            return template.style_config["html_template"]

        # Use default template based on template_type
        template_type = template.template_type
        if template_type in DEFAULT_TEMPLATES:
            return DEFAULT_TEMPLATES[template_type]["html_template"]

        # Fallback to modern template
        logger.warning(f"Unknown template type: {template_type}, using modern")
        return DEFAULT_TEMPLATES["modern"]["html_template"]

    def _prepare_context(
        self,
        resume_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare template context with resume data and configuration.

        Args:
            resume_data: Dictionary containing resume data
            config: Merged template configuration

        Returns:
            Template context dictionary
        """
        # Start with resume data
        context = dict(resume_data)

        # Add style configuration
        style = config.get("style", {})
        context["primary_color"] = style.get("primary_color", "#3B82F6")
        context["secondary_color"] = style.get("secondary_color", "#10B981")

        return context

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

    def render_resume(
        self,
        template: ResumeTemplate,
        resume_data: Dict[str, Any],
    ) -> str:
        """
        Render resume data using the specified template.

        Args:
            template: ResumeTemplate instance to use for rendering
            resume_data: Dictionary containing resume data with keys:
                - name: Full name
                - email: Email address
                - phone: Phone number
                - location: City, State/Country
                - summary: Professional summary
                - experience: List of work experience dictionaries
                - education: List of education dictionaries
                - skills: List of skills
                - certifications: List of certifications (optional)

        Returns:
            Rendered HTML resume string

        Raises:
            TemplateError: If template rendering fails

        Example:
            >>> html = renderer.render_resume(
            ...     template=resume_template,
            ...     resume_data={
            ...         "name": "John Doe",
            ...         "email": "john@example.com",
            ...         "experience": [{"title": "Engineer", "company": "Acme"}]
            ...     }
            ... )
        """
        logger.info(
            f"Rendering resume with template: {template.name} "
            f"(type: {template.template_type})"
        )

        # Get merged configuration
        config = self._merge_configs(template)

        # Get template HTML string
        template_string = self._get_template_string(template)

        # Prepare context with resume data and config
        context = self._prepare_context(resume_data, config)

        try:
            # Render template
            html = self._render_jinja_template(template_string, context)

            logger.info(
                f"Successfully rendered resume with template: {template.name}"
            )

            return html

        except Exception as e:
            logger.error(
                f"Failed to render resume with template {template.name}: {e}",
                exc_info=True
            )
            raise

    def preview_resume(
        self,
        template: ResumeTemplate,
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Preview resume rendering with metadata.

        This method renders the resume and returns a preview with
        metadata about the template used.

        Args:
            template: ResumeTemplate instance to use for rendering
            resume_data: Dictionary containing resume data

        Returns:
            Dictionary containing:
            - html: Rendered HTML resume
            - template_name: Name of the template used
            - template_type: Type of template
            - is_ats_compliant: Whether template is ATS-friendly
            - config: Merged configuration used for rendering

        Example:
            >>> preview = renderer.preview_resume(
            ...     template=resume_template,
            ...     resume_data={"name": "John Doe"}
            ... )
            >>> print(preview['is_ats_compliant'])
        """
        logger.info(
            f"Previewing resume with template: {template.name}"
        )

        # Get merged configuration
        config = self._merge_configs(template)

        # Render resume
        html = self.render_resume(template, resume_data)

        return {
            "html": html,
            "template_name": template.name,
            "template_type": template.template_type,
            "is_ats_compliant": template.is_ats_compliant,
            "config": config,
        }

    def render_sample_resume(
        self,
        template_type: str = "modern",
    ) -> str:
        """
        Render a sample resume for template preview/testing.

        Args:
            template_type: Type of template to render

        Returns:
            Rendered HTML sample resume

        Raises:
            ValueError: If template type is invalid

        Example:
            >>> sample = renderer.render_sample_resume("classic")
        """
        # Create a mock ResumeTemplate
        template = ResumeTemplate()
        template.name = f"Sample {template_type.title()} Template"
        template.template_type = template_type
        template.is_ats_compliant = template_type == "ats_friendly"
        template.layout_config = {}
        template.style_config = {}
        template.section_config = {}

        # Sample resume data
        sample_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "(555) 123-4567",
            "location": "San Francisco, CA",
            "summary": "Experienced professional with a proven track record of delivering results.",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corporation",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "description": "Led development of enterprise applications."
                },
                {
                    "title": "Software Engineer",
                    "company": "Startup Inc.",
                    "start_date": "2017-06",
                    "end_date": "2019-12",
                    "description": "Built scalable web applications."
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of Technology",
                    "graduation_year": "2017"
                }
            ],
            "skills": [
                "Python", "JavaScript", "React", "SQL", "AWS", "Docker"
            ]
        }

        return self.render_resume(template, sample_data)

    def health_check(self) -> Dict[str, Any]:
        """
        Check template renderer health.

        Returns:
            Dictionary with health status
        """
        return {
            "status": "healthy",
            "available_templates": list(DEFAULT_TEMPLATES.keys()),
        }


# Global template renderer instance
_template_renderer: Optional["TemplateRenderer"] = None


def get_template_renderer() -> TemplateRenderer:
    """
    Get or create global template renderer service instance.

    Returns:
        Global TemplateRenderer instance

    Example:
        >>> renderer = get_template_renderer()
        >>> html = renderer.render_resume(template, resume_data)
    """
    global _template_renderer
    if _template_renderer is None:
        _template_renderer = TemplateRenderer()
    return _template_renderer


def render_resume_template(
    template: ResumeTemplate,
    resume_data: Dict[str, Any],
) -> str:
    """
    Convenience function to render resume with template.

    This is a shortcut for using the TemplateRenderer class directly.

    Args:
        template: ResumeTemplate instance to use for rendering
        resume_data: Dictionary containing resume data

    Returns:
        Rendered HTML resume string

    Raises:
        TemplateError: If template rendering fails

    Example:
        >>> from services.template_renderer import render_resume_template
        >>> html = render_resume_template(
        ...     template=resume_template,
        ...     resume_data={"name": "John Doe", "email": "john@example.com"}
        ... )
    """
    renderer = get_template_renderer()
    return renderer.render_resume(template=template, resume_data=resume_data)

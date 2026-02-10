#!/usr/bin/env python3
"""
Seed ATS-friendly resume templates.

Creates professional, optimized resume templates that are compatible with
Applicant Tracking Systems (ATS). These templates follow best practices for
ATS parsing including simple layouts, standard fonts, and clear sectioning.
"""
import asyncio
import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models.resume_template import ResumeTemplate
from sqlalchemy import select


# ATS-friendly resume templates configuration
RESUME_TEMPLATES = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Modern Professional",
        "description": "Clean and contemporary design for corporate roles with a focus on readability and ATS compatibility",
        "template_type": "modern",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "summary", "experience", "education", "skills", "certifications"],
            "section_order": ["header", "summary", "experience", "education", "skills", "certifications"],
            "line_spacing": 1.15,
            "paragraph_spacing": 6,
        },
        "style_config": {
            "primary_color": "#1976d2",
            "secondary_color": "#1565c0",
            "font_family": "Arial",
            "heading_font": "Arial Bold",
            "body_font": "Arial",
            "font_size": 11,
            "heading_font_size": 14,
            "name_font_size": 18,
            "accent_color": "#42a5f5",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "title", "email", "phone", "location", "linkedin"],
            },
            "summary": {"enabled": True, "position": "main", "max_lines": 4},
            "experience": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "education": {"enabled": True, "position": "main", "show_gpa": False},
            "skills": {"enabled": True, "position": "main", "group_by": "category"},
            "certifications": {"enabled": True, "position": "main"},
        },
        "preview_url": "/templates/modern-professional.png",
        "is_default": True,
        "is_active": True,
        "is_ats_compliant": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Executive",
        "description": "Sophisticated layout for senior professionals with emphasis on leadership achievements and strategic impact",
        "template_type": "executive",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "executive_summary", "leadership_experience", "education", "board_memberships", "skills"],
            "section_order": ["header", "executive_summary", "leadership_experience", "education", "board_memberships", "skills"],
            "line_spacing": 1.2,
            "paragraph_spacing": 8,
        },
        "style_config": {
            "primary_color": "#2e7d32",
            "secondary_color": "#1b5e20",
            "font_family": "Georgia",
            "heading_font": "Georgia Bold",
            "body_font": "Georgia",
            "font_size": 11,
            "heading_font_size": 13,
            "name_font_size": 20,
            "accent_color": "#4caf50",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "title", "email", "phone", "location"],
            },
            "executive_summary": {"enabled": True, "position": "main", "max_lines": 6},
            "leadership_experience": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "education": {"enabled": True, "position": "main", "show_gpa": False},
            "board_memberships": {"enabled": True, "position": "main"},
            "skills": {"enabled": True, "position": "main", "group_by": "leadership_competencies"},
        },
        "preview_url": "/templates/executive.png",
        "is_default": False,
        "is_active": True,
        "is_ats_compliant": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Creative Designer",
        "description": "Bold and artistic template for creative industries while maintaining ATS compatibility through clean structure",
        "template_type": "creative",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "profile", "portfolio", "experience", "skills", "education"],
            "section_order": ["header", "profile", "portfolio", "experience", "skills", "education"],
            "line_spacing": 1.1,
            "paragraph_spacing": 6,
        },
        "style_config": {
            "primary_color": "#9c27b0",
            "secondary_color": "#7b1fa2",
            "font_family": "Helvetica",
            "heading_font": "Helvetica Bold",
            "body_font": "Helvetica",
            "font_size": 11,
            "heading_font_size": 14,
            "name_font_size": 22,
            "accent_color": "#ba68c8",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "title", "email", "phone", "location", "portfolio", "behance"],
            },
            "profile": {"enabled": True, "position": "main", "max_lines": 5},
            "portfolio": {"enabled": True, "position": "main", "show_links": True},
            "experience": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "skills": {"enabled": True, "position": "main", "group_by": "category"},
            "education": {"enabled": True, "position": "main", "show_gpa": False},
        },
        "preview_url": "/templates/creative-designer.png",
        "is_default": False,
        "is_active": True,
        "is_ats_compliant": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "name": "Tech Developer",
        "description": "Optimized for software engineering roles with skills highlight and projects section for technical work",
        "template_type": "technical",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "summary", "technical_skills", "experience", "projects", "education"],
            "section_order": ["header", "summary", "technical_skills", "experience", "projects", "education"],
            "line_spacing": 1.15,
            "paragraph_spacing": 6,
        },
        "style_config": {
            "primary_color": "#f57c00",
            "secondary_color": "#e65100",
            "font_family": "Consolas",
            "heading_font": "Arial Bold",
            "body_font": "Arial",
            "font_size": 10,
            "heading_font_size": 13,
            "name_font_size": 18,
            "accent_color": "#ff9800",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "title", "email", "phone", "location", "github", "linkedin"],
            },
            "summary": {"enabled": True, "position": "main", "max_lines": 4},
            "technical_skills": {
                "enabled": True,
                "position": "main",
                "group_by": "category",
                "categories": ["languages", "frameworks", "databases", "tools", "cloud"],
            },
            "experience": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "projects": {"enabled": True, "position": "main", "show_tech_stack": True},
            "education": {"enabled": True, "position": "main", "show_gpa": False},
        },
        "preview_url": "/templates/tech-developer.png",
        "is_default": False,
        "is_active": True,
        "is_ats_compliant": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
        "name": "Data Scientist",
        "description": "Perfect for analytics and ML roles with emphasis on quantitative skills, research, and publications",
        "template_type": "technical",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "summary", "technical_skills", "research_experience", "projects", "publications", "education"],
            "section_order": ["header", "summary", "technical_skills", "research_experience", "projects", "publications", "education"],
            "line_spacing": 1.15,
            "paragraph_spacing": 6,
        },
        "style_config": {
            "primary_color": "#0097a7",
            "secondary_color": "#006064",
            "font_family": "Arial",
            "heading_font": "Arial Bold",
            "body_font": "Arial",
            "font_size": 10,
            "heading_font_size": 13,
            "name_font_size": 18,
            "accent_color": "#00bcd4",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "title", "email", "phone", "location", "github", "linkedin", "kaggle"],
            },
            "summary": {"enabled": True, "position": "main", "max_lines": 5},
            "technical_skills": {
                "enabled": True,
                "position": "main",
                "group_by": "category",
                "categories": ["languages", "ml_frameworks", "databases", "tools", "visualization"],
            },
            "research_experience": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "projects": {"enabled": True, "position": "main", "show_metrics": True},
            "publications": {"enabled": True, "position": "main"},
            "education": {"enabled": True, "position": "main", "show_gpa": True, "show_thesis": True},
        },
        "preview_url": "/templates/data-scientist.png",
        "is_default": False,
        "is_active": True,
        "is_ats_compliant": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000006"),
        "name": "Entry Level",
        "description": "Great template for recent graduates with education focus and internship section to showcase early career experience",
        "template_type": "entry_level",
        "layout_config": {
            "margins": "normal",
            "page_size": "letter",
            "sections": ["header", "objective", "education", "internships", "projects", "skills", "activities"],
            "section_order": ["header", "objective", "education", "internships", "projects", "skills", "activities"],
            "line_spacing": 1.15,
            "paragraph_spacing": 6,
        },
        "style_config": {
            "primary_color": "#546e7a",
            "secondary_color": "#455a64",
            "font_family": "Arial",
            "heading_font": "Arial Bold",
            "body_font": "Arial",
            "font_size": 11,
            "heading_font_size": 13,
            "name_font_size": 18,
            "accent_color": "#78909c",
        },
        "section_config": {
            "header": {
                "enabled": True,
                "position": "top",
                "fields": ["name", "email", "phone", "location", "linkedin"],
            },
            "objective": {"enabled": True, "position": "main", "max_lines": 3},
            "education": {
                "enabled": True,
                "position": "main",
                "show_gpa": True,
                "show_coursework": True,
                "show_honors": True,
            },
            "internships": {
                "enabled": True,
                "position": "main",
                "show_description": True,
                "format": "reverse_chronological",
            },
            "projects": {"enabled": True, "position": "main", "show_description": True},
            "skills": {"enabled": True, "position": "main", "group_by": "category"},
            "activities": {"enabled": True, "position": "main", "show_leadership": True},
        },
        "preview_url": "/templates/entry-level.png",
        "is_default": False,
        "is_active": True,
        "is_ats_compliant": True,
    },
]


async def seed_templates():
    """Seed ATS-friendly resume templates."""
    print("=" * 70)
    print("SEEDING ATS-FRIENDLY RESUME TEMPLATES")
    print("=" * 70)
    print()

    async with async_session_maker() as db:
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for template_data in RESUME_TEMPLATES:
            template_id = template_data["id"]
            template_name = template_data["name"]

            # Check if template already exists
            existing = await db.execute(
                select(ResumeTemplate).where(ResumeTemplate.id == template_id)
            )
            existing_template = existing.scalar_one_or_none()

            if existing_template:
                # Update existing template
                for key, value in template_data.items():
                    if key != "id" and hasattr(existing_template, key):
                        setattr(existing_template, key, value)

                print(f"  ~ Updated: {template_name}")
                updated_count += 1
            else:
                # Create new template
                template = ResumeTemplate(**template_data)
                db.add(template)
                await db.flush()

                print(f"  + Created: {template_name}")
                print(f"    Type: {template_data['template_type']}")
                print(f"    ATS Compliant: {template_data['is_ats_compliant']}")
                print(f"    Font: {template_data['style_config']['font_family']} ({template_data['style_config']['font_size']}pt)")
                print()
                created_count += 1

        await db.commit()

        print("=" * 70)
        print(f"COMPLETE: {created_count} created, {updated_count} updated, {skipped_count} skipped")
        print("=" * 70)


async def list_templates():
    """List all resume templates."""
    print("\nCurrent resume templates:")
    print("-" * 70)

    async with async_session_maker() as db:
        result = await db.execute(
            select(ResumeTemplate)
            .where(ResumeTemplate.is_active == True)
            .order_by(ResumeTemplate.name)
        )
        templates = result.scalars().all()

        if templates:
            for template in templates:
                print(f"\n{template.name} ({template.template_type})")
                print(f"  ID: {template.id}")
                print(f"  Description: {template.description}")
                print(f"  ATS Compliant: {template.is_ats_compliant}")
                print(f"  Default: {template.is_default}")
                print(f"  Active: {template.is_active}")
                if template.style_config:
                    font = template.style_config.get("font_family", "N/A")
                    size = template.style_config.get("font_size", "N/A")
                    print(f"  Style: {font} {size}pt")
        else:
            print("  No resume templates found")


async def main():
    """Main function."""
    await seed_templates()
    await list_templates()


if __name__ == "__main__":
    asyncio.run(main())

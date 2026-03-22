"""
Скрипт для создания дефолтных email шаблонов.

# Русский комментарий:
Этот скрипт создает начальный набор email шаблонов для типичных
сценариев взаимодействия с кандидатами в процессе рекрутинга.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path to import modules / Добавление родительской директории в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_engine, async_session_maker
from models.email_template import EmailTemplate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_TEMPLATES = [
    {
        "name": "application_received",
        "subject": "Application Received - {{position_title}}",
        "body": """Dear {{candidate_name}},

Thank you for your application for the position of {{position_title}} at {{company_name}}.

We have received your application and our team is currently reviewing it. We will get back to you within {{response_time}} with an update on your application status.

If you have any questions in the meantime, please don't hesitate to reach out.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
        "variables": [
            "candidate_name",
            "position_title",
            "company_name",
            "response_time",
            "recruiter_name",
        ],
        "template_blocks": {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "header",
                    "content": "Application Received",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Thank you for your application for the position of {{position_title}} at {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "We have received your application and our team is currently reviewing it.",
                },
                {
                    "id": "block-4",
                    "type": "footer",
                    "content": "Best regards,\n{{recruiter_name}}\n{{company_name}} Recruitment Team",
                },
            ]
        },
        "category": "application",
        "pipeline_stage": "applied",
        "is_active": True,
        "language": "en",
        "description": "Sent automatically when a candidate submits their application",
    },
    {
        "name": "interview_invitation",
        "subject": "Interview Invitation - {{position_title}}",
        "body": """Dear {{candidate_name}},

We are pleased to invite you for an interview for the position of {{position_title}} at {{company_name}}.

Interview Details:
- Date: {{interview_date}}
- Time: {{interview_time}}
- Location: {{interview_location}}
- Duration: {{interview_duration}}
- Interviewer(s): {{interviewer_names}}

Please confirm your availability by replying to this email or clicking the link below:
{{confirmation_link}}

If you have any questions or need to reschedule, please let us know as soon as possible.

We look forward to meeting you!

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
        "variables": [
            "candidate_name",
            "position_title",
            "company_name",
            "interview_date",
            "interview_time",
            "interview_location",
            "interview_duration",
            "interviewer_names",
            "confirmation_link",
            "recruiter_name",
        ],
        "template_blocks": {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "header",
                    "content": "Interview Invitation",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "We are pleased to invite you for an interview for the position of {{position_title}}.",
                },
                {
                    "id": "block-3",
                    "type": "info-box",
                    "content": "Date: {{interview_date}}\nTime: {{interview_time}}\nLocation: {{interview_location}}",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Confirm Attendance",
                    "link": "{{confirmation_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "Best regards,\n{{recruiter_name}}\n{{company_name}} Recruitment Team",
                },
            ]
        },
        "category": "interview",
        "pipeline_stage": "interview",
        "is_active": True,
        "language": "en",
        "description": "Sent to invite candidates to an interview",
    },
    {
        "name": "rejection",
        "subject": "Application Update - {{position_title}}",
        "body": """Dear {{candidate_name}},

Thank you for your interest in the position of {{position_title}} at {{company_name}} and for taking the time to go through our recruitment process.

After careful consideration, we regret to inform you that we have decided to move forward with other candidates whose qualifications more closely match our current needs.

We appreciate the time and effort you invested in your application. Your skills and experience are impressive, and we encourage you to apply for future openings that match your profile.

We wish you the best of luck in your job search and future career endeavors.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
        "variables": [
            "candidate_name",
            "position_title",
            "company_name",
            "recruiter_name",
        ],
        "template_blocks": {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "header",
                    "content": "Application Update",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Thank you for your interest in the position of {{position_title}} at {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "After careful consideration, we have decided to move forward with other candidates.",
                },
                {
                    "id": "block-4",
                    "type": "text",
                    "content": "We encourage you to apply for future openings that match your profile.",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "Best regards,\n{{recruiter_name}}\n{{company_name}} Recruitment Team",
                },
            ]
        },
        "category": "decision",
        "pipeline_stage": "rejected",
        "is_active": True,
        "language": "en",
        "description": "Sent to inform candidates that their application was not successful",
    },
    {
        "name": "offer",
        "subject": "Job Offer - {{position_title}} at {{company_name}}",
        "body": """Dear {{candidate_name}},

Congratulations! We are delighted to offer you the position of {{position_title}} at {{company_name}}.

Offer Details:
- Position: {{position_title}}
- Department: {{department}}
- Start Date: {{start_date}}
- Salary: {{salary}}
- Benefits: {{benefits_summary}}

Please find the detailed offer letter attached to this email. We would appreciate if you could review the offer and respond by {{offer_deadline}}.

To accept this offer, please sign the attached document and return it to us, or click the link below:
{{offer_acceptance_link}}

If you have any questions about the offer or need clarification on any points, please don't hesitate to contact me.

We are excited about the possibility of you joining our team!

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
        "variables": [
            "candidate_name",
            "position_title",
            "company_name",
            "department",
            "start_date",
            "salary",
            "benefits_summary",
            "offer_deadline",
            "offer_acceptance_link",
            "recruiter_name",
        ],
        "template_blocks": {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "header",
                    "content": "Congratulations!",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "We are delighted to offer you the position of {{position_title}} at {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "info-box",
                    "content": "Position: {{position_title}}\nDepartment: {{department}}\nStart Date: {{start_date}}\nSalary: {{salary}}",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Accept Offer",
                    "link": "{{offer_acceptance_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "Best regards,\n{{recruiter_name}}\n{{company_name}} Recruitment Team",
                },
            ]
        },
        "category": "decision",
        "pipeline_stage": "offer",
        "is_active": True,
        "language": "en",
        "description": "Sent to extend a job offer to a candidate",
    },
    {
        "name": "feedback_request",
        "subject": "We'd Love Your Feedback - {{company_name}}",
        "body": """Dear {{candidate_name}},

Thank you for participating in our recruitment process for the position of {{position_title}} at {{company_name}}.

We are constantly working to improve our recruitment experience, and your feedback is invaluable to us. We would greatly appreciate if you could take a few minutes to share your thoughts about your experience with our recruitment process.

Please click the link below to complete our brief survey:
{{survey_link}}

Your responses will be kept confidential and will help us enhance our process for future candidates.

Thank you for your time and for considering {{company_name}}.

Best regards,
{{recruiter_name}}
{{company_name}} Recruitment Team""",
        "variables": [
            "candidate_name",
            "position_title",
            "company_name",
            "survey_link",
            "recruiter_name",
        ],
        "template_blocks": {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "header",
                    "content": "We'd Love Your Feedback",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Thank you for participating in our recruitment process for {{position_title}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "We would greatly appreciate if you could share your thoughts about your experience.",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Complete Survey",
                    "link": "{{survey_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "Best regards,\n{{recruiter_name}}\n{{company_name}} Recruitment Team",
                },
            ]
        },
        "category": "feedback",
        "pipeline_stage": None,
        "is_active": True,
        "language": "en",
        "description": "Sent to request feedback from candidates about their recruitment experience",
    },
]


async def seed_default_templates() -> None:
    """
    Создать дефолтные email шаблоны в базе данных.

    Функция проверяет наличие каждого шаблона и создает его, если он отсутствует.
    Существующие шаблоны не изменяются.
    """
    try:
        async with async_session_maker() as session:
            for template_data in DEFAULT_TEMPLATES:
                # Check if template already exists / Проверка наличия шаблона
                result = await session.execute(
                    select(EmailTemplate).where(
                        EmailTemplate.name == template_data["name"]
                    )
                )
                existing_template = result.scalar_one_or_none()

                if existing_template:
                    logger.info(
                        f"Template '{template_data['name']}' already exists, skipping"
                    )
                    continue

                # Create new template / Создание нового шаблона
                template = EmailTemplate(**template_data)
                session.add(template)
                logger.info(f"Created template: {template_data['name']}")

            # Commit all changes / Коммит всех изменений
            await session.commit()
            logger.info("Default templates seeded successfully")

    except Exception as e:
        logger.error(f"Error seeding default templates: {e}")
        raise


async def main() -> None:
    """Главная функция для запуска скрипта."""
    logger.info("Starting default templates seeding...")

    try:
        # Test database connection / Проверка соединения с БД
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection successful")

        # Seed templates / Создание шаблонов
        await seed_default_templates()

        logger.info("Seeding completed successfully")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    finally:
        # Close database connections / Закрытие соединений с БД
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

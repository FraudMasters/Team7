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
    # Russian variants / Русские варианты
    {
        "name": "application_received",
        "subject": "Заявка получена - {{position_title}}",
        "body": """Уважаемый(ая) {{candidate_name}},

Благодарим вас за отклик на вакансию {{position_title}} в компании {{company_name}}.

Мы получили вашу заявку и наша команда в данный момент рассматривает её. Мы свяжемся с вами в течение {{response_time}} и сообщим об обновлении статуса вашей заявки.

Если у вас возникнут вопросы, пожалуйста, не стесняйтесь обращаться к нам.

С уважением,
{{recruiter_name}}
Команда рекрутинга {{company_name}}""",
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
                    "content": "Заявка получена",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Благодарим вас за отклик на вакансию {{position_title}} в компании {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "Мы получили вашу заявку и наша команда в данный момент рассматривает её.",
                },
                {
                    "id": "block-4",
                    "type": "footer",
                    "content": "С уважением,\n{{recruiter_name}}\nКоманда рекрутинга {{company_name}}",
                },
            ]
        },
        "category": "application",
        "pipeline_stage": "applied",
        "is_active": True,
        "language": "ru",
        "description": "Отправляется автоматически при подаче заявки кандидатом",
    },
    {
        "name": "interview_invitation",
        "subject": "Приглашение на собеседование - {{position_title}}",
        "body": """Уважаемый(ая) {{candidate_name}},

Мы рады пригласить вас на собеседование на позицию {{position_title}} в компании {{company_name}}.

Детали собеседования:
- Дата: {{interview_date}}
- Время: {{interview_time}}
- Место: {{interview_location}}
- Продолжительность: {{interview_duration}}
- Интервьюер(ы): {{interviewer_names}}

Пожалуйста, подтвердите вашу доступность, ответив на это письмо или перейдя по ссылке ниже:
{{confirmation_link}}

Если у вас есть вопросы или необходимо перенести встречу, пожалуйста, сообщите нам как можно скорее.

Мы с нетерпением ждем встречи с вами!

С уважением,
{{recruiter_name}}
Команда рекрутинга {{company_name}}""",
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
                    "content": "Приглашение на собеседование",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Мы рады пригласить вас на собеседование на позицию {{position_title}}.",
                },
                {
                    "id": "block-3",
                    "type": "info-box",
                    "content": "Дата: {{interview_date}}\nВремя: {{interview_time}}\nМесто: {{interview_location}}",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Подтвердить участие",
                    "link": "{{confirmation_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "С уважением,\n{{recruiter_name}}\nКоманда рекрутинга {{company_name}}",
                },
            ]
        },
        "category": "interview",
        "pipeline_stage": "interview",
        "is_active": True,
        "language": "ru",
        "description": "Отправляется для приглашения кандидатов на собеседование",
    },
    {
        "name": "rejection",
        "subject": "Обновление статуса заявки - {{position_title}}",
        "body": """Уважаемый(ая) {{candidate_name}},

Благодарим вас за интерес к позиции {{position_title}} в компании {{company_name}} и за время, уделенное процессу рекрутинга.

После тщательного рассмотрения, мы вынуждены сообщить, что приняли решение продолжить работу с другими кандидатами, чья квалификация более точно соответствует нашим текущим потребностям.

Мы ценим время и усилия, которые вы вложили в вашу заявку. Ваши навыки и опыт впечатляют, и мы рекомендуем вам откликаться на будущие вакансии, которые соответствуют вашему профилю.

Желаем вам успехов в поиске работы и карьерном развитии.

С уважением,
{{recruiter_name}}
Команда рекрутинга {{company_name}}""",
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
                    "content": "Обновление статуса заявки",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Благодарим вас за интерес к позиции {{position_title}} в компании {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "После тщательного рассмотрения, мы приняли решение продолжить работу с другими кандидатами.",
                },
                {
                    "id": "block-4",
                    "type": "text",
                    "content": "Мы рекомендуем вам откликаться на будущие вакансии, которые соответствуют вашему профилю.",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "С уважением,\n{{recruiter_name}}\nКоманда рекрутинга {{company_name}}",
                },
            ]
        },
        "category": "decision",
        "pipeline_stage": "rejected",
        "is_active": True,
        "language": "ru",
        "description": "Отправляется для информирования кандидатов об отклонении заявки",
    },
    {
        "name": "offer",
        "subject": "Предложение о работе - {{position_title}} в {{company_name}}",
        "body": """Уважаемый(ая) {{candidate_name}},

Поздравляем! Мы рады предложить вам позицию {{position_title}} в компании {{company_name}}.

Детали предложения:
- Позиция: {{position_title}}
- Отдел: {{department}}
- Дата начала: {{start_date}}
- Зарплата: {{salary}}
- Льготы: {{benefits_summary}}

Пожалуйста, ознакомьтесь с подробным предложением о работе во вложении к этому письму. Мы будем благодарны, если вы рассмотрите предложение и ответите до {{offer_deadline}}.

Для принятия этого предложения, пожалуйста, подпишите прилагаемый документ и верните его нам, или перейдите по ссылке ниже:
{{offer_acceptance_link}}

Если у вас есть вопросы о предложении или требуются разъяснения по любым пунктам, пожалуйста, не стесняйтесь связаться со мной.

Мы с нетерпением ждем возможности вашего присоединения к нашей команде!

С уважением,
{{recruiter_name}}
Команда рекрутинга {{company_name}}""",
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
                    "content": "Поздравляем!",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Мы рады предложить вам позицию {{position_title}} в компании {{company_name}}.",
                },
                {
                    "id": "block-3",
                    "type": "info-box",
                    "content": "Позиция: {{position_title}}\nОтдел: {{department}}\nДата начала: {{start_date}}\nЗарплата: {{salary}}",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Принять предложение",
                    "link": "{{offer_acceptance_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "С уважением,\n{{recruiter_name}}\nКоманда рекрутинга {{company_name}}",
                },
            ]
        },
        "category": "decision",
        "pipeline_stage": "offer",
        "is_active": True,
        "language": "ru",
        "description": "Отправляется для предложения работы кандидату",
    },
    {
        "name": "feedback_request",
        "subject": "Мы будем рады вашему отзыву - {{company_name}}",
        "body": """Уважаемый(ая) {{candidate_name}},

Благодарим вас за участие в нашем процессе рекрутинга на позицию {{position_title}} в компании {{company_name}}.

Мы постоянно работаем над улучшением процесса подбора персонала, и ваш отзыв для нас бесценен. Мы будем очень признательны, если вы уделите несколько минут и поделитесь своими мыслями о вашем опыте прохождения нашего процесса рекрутинга.

Пожалуйста, перейдите по ссылке ниже, чтобы пройти наш короткий опрос:
{{survey_link}}

Ваши ответы будут конфиденциальными и помогут нам улучшить процесс для будущих кандидатов.

Благодарим вас за ваше время и за рассмотрение {{company_name}}.

С уважением,
{{recruiter_name}}
Команда рекрутинга {{company_name}}""",
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
                    "content": "Мы будем рады вашему отзыву",
                },
                {
                    "id": "block-2",
                    "type": "text",
                    "content": "Благодарим вас за участие в нашем процессе рекрутинга на позицию {{position_title}}.",
                },
                {
                    "id": "block-3",
                    "type": "text",
                    "content": "Мы будем очень признательны, если вы поделитесь своими мыслями о вашем опыте.",
                },
                {
                    "id": "block-4",
                    "type": "button",
                    "content": "Пройти опрос",
                    "link": "{{survey_link}}",
                },
                {
                    "id": "block-5",
                    "type": "footer",
                    "content": "С уважением,\n{{recruiter_name}}\nКоманда рекрутинга {{company_name}}",
                },
            ]
        },
        "category": "feedback",
        "pipeline_stage": None,
        "is_active": True,
        "language": "ru",
        "description": "Отправляется для запроса обратной связи от кандидатов об опыте рекрутинга",
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
                        EmailTemplate.name == template_data["name"],
                        EmailTemplate.language == template_data["language"]
                    )
                )
                existing_template = result.scalar_one_or_none()

                if existing_template:
                    logger.info(
                        f"Template '{template_data['name']}' ({template_data['language']}) already exists, skipping"
                    )
                    continue

                # Create new template / Создание нового шаблона
                template = EmailTemplate(**template_data)
                session.add(template)
                logger.info(f"Created template: {template_data['name']} ({template_data['language']})")

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

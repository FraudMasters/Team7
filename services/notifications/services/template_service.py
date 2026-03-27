"""
Сервис управления шаблонами уведомлений.

# Русский комментарий:
Этот модуль предоставляет функциональность для CRUD операций с шаблонами,
подстановки переменных и вычисления условных блоков.
"""
import logging
import re
from typing import Optional, List, Dict, Any, Union

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.email_template import EmailTemplate
from models.sms_template import SMSTemplate

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Сервис управления шаблонами уведомлений.

    Предоставляет методы для создания, чтения, обновления, удаления шаблонов,
    а также для подстановки переменных и вычисления условных блоков.

    Методы работают как с EmailTemplate, так и с SMSTemplate.
    """

    def __init__(self):
        """Инициализация сервиса."""
        logger.debug("TemplateService initialized")

    async def get_template(
        self,
        db: AsyncSession,
        template_id: str,
        template_type: str = "email",
    ) -> Optional[Union[EmailTemplate, SMSTemplate]]:
        """
        Получить шаблон по ID.

        Args:
            db: Сессия базы данных
            template_id: ID шаблона
            template_type: Тип шаблона ("email" или "sms")

        Returns:
            Шаблон или None если не найден

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     template = await service.get_template(db, "abc-123", "email")
        """
        try:
            model = EmailTemplate if template_type == "email" else SMSTemplate

            result = await db.execute(
                select(model).where(model.id == template_id)
            )
            template = result.scalar_one_or_none()

            if template:
                logger.info(f"Retrieved template: id={template_id}, type={template_type}")
            else:
                logger.warning(f"Template not found: id={template_id}, type={template_type}")

            return template

        except Exception as e:
            logger.error(f"Error retrieving template {template_id}: {e}", exc_info=True)
            raise

    async def get_template_by_name(
        self,
        db: AsyncSession,
        name: str,
        template_type: str = "email",
        language: str = "en",
    ) -> Optional[Union[EmailTemplate, SMSTemplate]]:
        """
        Получить шаблон по имени.

        Args:
            db: Сессия базы данных
            name: Название шаблона
            template_type: Тип шаблона ("email" или "sms")
            language: Язык шаблона

        Returns:
            Шаблон или None если не найден

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     template = await service.get_template_by_name(
            ...         db, "welcome_email", "email", "en"
            ...     )
        """
        try:
            model = EmailTemplate if template_type == "email" else SMSTemplate

            result = await db.execute(
                select(model).where(
                    and_(
                        model.name == name,
                        model.language == language,
                        model.is_active == True,
                    )
                )
            )
            template = result.scalar_one_or_none()

            if template:
                logger.info(f"Retrieved template by name: name={name}, type={template_type}, lang={language}")
            else:
                logger.warning(f"Template not found: name={name}, type={template_type}, lang={language}")

            return template

        except Exception as e:
            logger.error(f"Error retrieving template by name {name}: {e}", exc_info=True)
            raise

    async def list_templates(
        self,
        db: AsyncSession,
        template_type: str = "email",
        category: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        language: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Union[EmailTemplate, SMSTemplate]]:
        """
        Получить список шаблонов с фильтрацией.

        Args:
            db: Сессия базы данных
            template_type: Тип шаблона ("email" или "sms")
            category: Фильтр по категории
            pipeline_stage: Фильтр по этапу pipeline
            language: Фильтр по языку
            is_active: Фильтр по активности
            skip: Количество пропускаемых записей
            limit: Максимальное количество возвращаемых записей

        Returns:
            Список шаблонов

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     templates = await service.list_templates(
            ...         db, template_type="email", category="recruitment"
            ...     )
        """
        try:
            model = EmailTemplate if template_type == "email" else SMSTemplate

            # Построение фильтров
            filters = []
            if category is not None:
                filters.append(model.category == category)
            if pipeline_stage is not None:
                filters.append(model.pipeline_stage == pipeline_stage)
            if language is not None:
                filters.append(model.language == language)
            if is_active is not None:
                filters.append(model.is_active == is_active)

            # Выполнение запроса
            query = select(model)
            if filters:
                query = query.where(and_(*filters))

            query = query.offset(skip).limit(limit).order_by(model.created_at.desc())

            result = await db.execute(query)
            templates = result.scalars().all()

            logger.info(
                f"Retrieved {len(templates)} templates: type={template_type}, "
                f"category={category}, stage={pipeline_stage}"
            )

            return list(templates)

        except Exception as e:
            logger.error(f"Error listing templates: {e}", exc_info=True)
            raise

    async def create_template(
        self,
        db: AsyncSession,
        template_type: str,
        name: str,
        body: str,
        subject: Optional[str] = None,
        variables: Optional[List[str]] = None,
        template_blocks: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        language: str = "en",
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> Union[EmailTemplate, SMSTemplate]:
        """
        Создать новый шаблон.

        Args:
            db: Сессия базы данных
            template_type: Тип шаблона ("email" или "sms")
            name: Название шаблона (уникальное)
            body: Тело шаблона
            subject: Тема (только для email)
            variables: Список переменных для подстановки
            template_blocks: JSON-структура для drag-drop построителя
            category: Категория шаблона
            pipeline_stage: Этап pipeline
            language: Язык шаблона
            description: Описание шаблона
            is_active: Флаг активности

        Returns:
            Созданный шаблон

        Raises:
            ValueError: Если шаблон с таким именем уже существует

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     template = await service.create_template(
            ...         db, "email", "welcome", "Hello {name}!",
            ...         subject="Welcome", variables=["name"]
            ...     )
        """
        try:
            # Проверка существования шаблона с таким именем
            model = EmailTemplate if template_type == "email" else SMSTemplate
            existing = await db.execute(
                select(model).where(model.name == name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Template with name '{name}' already exists")

            # Создание шаблона
            if template_type == "email":
                if not subject:
                    raise ValueError("Subject is required for email templates")

                template = EmailTemplate(
                    name=name,
                    subject=subject,
                    body=body,
                    variables=variables,
                    template_blocks=template_blocks,
                    category=category,
                    pipeline_stage=pipeline_stage,
                    language=language,
                    description=description,
                    is_active=is_active,
                )
            else:
                template = SMSTemplate(
                    name=name,
                    body=body,
                    variables=variables,
                    template_blocks=template_blocks,
                    category=category,
                    pipeline_stage=pipeline_stage,
                    language=language,
                    description=description,
                    is_active=is_active,
                )

            db.add(template)
            await db.commit()
            await db.refresh(template)

            logger.info(f"Created template: name={name}, type={template_type}, id={template.id}")

            return template

        except ValueError as e:
            logger.warning(f"Validation error creating template: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating template: {e}", exc_info=True)
            await db.rollback()
            raise

    async def update_template(
        self,
        db: AsyncSession,
        template_id: str,
        template_type: str = "email",
        **updates,
    ) -> Optional[Union[EmailTemplate, SMSTemplate]]:
        """
        Обновить существующий шаблон.

        Args:
            db: Сессия базы данных
            template_id: ID шаблона
            template_type: Тип шаблона ("email" или "sms")
            **updates: Поля для обновления

        Returns:
            Обновленный шаблон или None если не найден

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     template = await service.update_template(
            ...         db, "abc-123", "email",
            ...         body="Updated body", is_active=False
            ...     )
        """
        try:
            template = await self.get_template(db, template_id, template_type)
            if not template:
                logger.warning(f"Cannot update - template not found: id={template_id}")
                return None

            # Обновление полей
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            await db.commit()
            await db.refresh(template)

            logger.info(f"Updated template: id={template_id}, type={template_type}, fields={list(updates.keys())}")

            return template

        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}", exc_info=True)
            await db.rollback()
            raise

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: str,
        template_type: str = "email",
        soft_delete: bool = True,
    ) -> bool:
        """
        Удалить шаблон.

        Args:
            db: Сессия базы данных
            template_id: ID шаблона
            template_type: Тип шаблона ("email" или "sms")
            soft_delete: Использовать мягкое удаление (is_active=False)

        Returns:
            True если удаление успешно, False если шаблон не найден

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     deleted = await service.delete_template(db, "abc-123", "email")
        """
        try:
            template = await self.get_template(db, template_id, template_type)
            if not template:
                logger.warning(f"Cannot delete - template not found: id={template_id}")
                return False

            if soft_delete:
                # Мягкое удаление
                template.is_active = False
                await db.commit()
                logger.info(f"Soft deleted template: id={template_id}, type={template_type}")
            else:
                # Жесткое удаление
                await db.delete(template)
                await db.commit()
                logger.info(f"Hard deleted template: id={template_id}, type={template_type}")

            return True

        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}", exc_info=True)
            await db.rollback()
            raise

    def substitute_variables(
        self,
        text: str,
        variables: Dict[str, Any],
    ) -> str:
        """
        Подстановка переменных в текст шаблона.

        Поддерживает переменные в формате {variable_name}.

        Args:
            text: Текст с переменными
            variables: Словарь переменных для подстановки

        Returns:
            Текст с подставленными значениями

        Examples:
            >>> service = TemplateService()
            >>> result = service.substitute_variables(
            ...     "Hello {name}, your job is {job_title}",
            ...     {"name": "John", "job_title": "Developer"}
            ... )
            >>> print(result)
            Hello John, your job is Developer
        """
        if not variables:
            return text

        result = text
        for key, value in variables.items():
            # Замена {key} на значение
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        logger.debug(f"Substituted {len(variables)} variables in template")
        return result

    def evaluate_conditional_blocks(
        self,
        template_blocks: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Вычислить условные блоки шаблона.

        Обрабатывает блоки с условиями (if/else) на основе контекста.

        Args:
            template_blocks: JSON-структура блоков шаблона
            context: Контекст для вычисления условий

        Returns:
            Список активных блоков после вычисления условий

        Examples:
            >>> service = TemplateService()
            >>> blocks = {
            ...     "blocks": [
            ...         {"type": "text", "content": "Hello"},
            ...         {
            ...             "type": "conditional",
            ...             "condition": {"field": "status", "operator": "eq", "value": "accepted"},
            ...             "true_block": {"type": "text", "content": "Congratulations!"},
            ...             "false_block": {"type": "text", "content": "Thank you for applying"}
            ...         }
            ...     ]
            ... }
            >>> result = service.evaluate_conditional_blocks(blocks, {"status": "accepted"})
        """
        if not template_blocks or "blocks" not in template_blocks:
            return []

        active_blocks = []

        for block in template_blocks.get("blocks", []):
            if block.get("type") == "conditional":
                # Вычисление условия
                condition = block.get("condition", {})
                if self._evaluate_condition(condition, context):
                    # Условие истинно - добавляем true_block
                    true_block = block.get("true_block")
                    if true_block:
                        active_blocks.append(true_block)
                else:
                    # Условие ложно - добавляем false_block
                    false_block = block.get("false_block")
                    if false_block:
                        active_blocks.append(false_block)
            else:
                # Обычный блок - добавляем как есть
                active_blocks.append(block)

        logger.debug(f"Evaluated {len(template_blocks.get('blocks', []))} blocks, {len(active_blocks)} active")
        return active_blocks

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Вычислить одно условие.

        Поддерживаемые операторы: eq, ne, gt, lt, gte, lte, in, not_in, contains.

        Args:
            condition: Описание условия
            context: Контекст с данными

        Returns:
            True если условие истинно, False иначе
        """
        field = condition.get("field")
        operator = condition.get("operator", "eq")
        expected_value = condition.get("value")

        # Получение значения из контекста
        actual_value = context.get(field)

        # Вычисление условия
        if operator == "eq":
            return actual_value == expected_value
        elif operator == "ne":
            return actual_value != expected_value
        elif operator == "gt":
            return actual_value > expected_value
        elif operator == "lt":
            return actual_value < expected_value
        elif operator == "gte":
            return actual_value >= expected_value
        elif operator == "lte":
            return actual_value <= expected_value
        elif operator == "in":
            return actual_value in expected_value if expected_value else False
        elif operator == "not_in":
            return actual_value not in expected_value if expected_value else True
        elif operator == "contains":
            return expected_value in actual_value if actual_value else False
        else:
            logger.warning(f"Unknown operator '{operator}', defaulting to False")
            return False

    async def render_template(
        self,
        db: AsyncSession,
        template_id: str,
        template_type: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Отрендерить шаблон с подстановкой переменных и вычислением условий.

        Args:
            db: Сессия базы данных
            template_id: ID шаблона
            template_type: Тип шаблона ("email" или "sms")
            variables: Переменные для подстановки и вычисления условий

        Returns:
            Словарь с отрендеренным контентом:
            - subject: Тема с подставленными переменными (для email)
            - body: Тело с подставленными переменными
            - active_blocks: Вычисленные активные блоки

        Raises:
            ValueError: Если шаблон не найден

        Examples:
            >>> async with get_db() as db:
            ...     service = TemplateService()
            ...     result = await service.render_template(
            ...         db, "abc-123", "email",
            ...         {"name": "John", "status": "accepted"}
            ...     )
        """
        try:
            template = await self.get_template(db, template_id, template_type)
            if not template:
                raise ValueError(f"Template not found: id={template_id}, type={template_type}")

            # Подстановка переменных в тело
            rendered_body = self.substitute_variables(template.body, variables)

            result = {
                "body": rendered_body,
                "active_blocks": self.evaluate_conditional_blocks(
                    template.template_blocks, variables
                ),
            }

            # Для email также подставляем переменные в subject
            if template_type == "email" and hasattr(template, "subject"):
                result["subject"] = self.substitute_variables(template.subject, variables)

            logger.info(f"Rendered template: id={template_id}, type={template_type}")

            return result

        except ValueError as e:
            logger.warning(f"Validation error rendering template: {e}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_id}: {e}", exc_info=True)
            raise


# Singleton instance / Синглтон сервиса
_template_service_instance = None


def get_template_service() -> TemplateService:
    """
    Получить экземпляр TemplateService (singleton).

    Returns:
        TemplateService: Экземпляр сервиса

    Examples:
        >>> service = get_template_service()
    """
    global _template_service_instance
    if _template_service_instance is None:
        _template_service_instance = TemplateService()
    return _template_service_instance

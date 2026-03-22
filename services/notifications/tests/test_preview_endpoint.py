"""
Тесты для эндпоинта предпросмотра шаблонов.

# Русский комментарий:
Этот модуль тестирует POST /api/templates/preview эндпоинт.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from services.template_service import get_template_service


@pytest.mark.asyncio
async def test_preview_template_success(db_session: AsyncSession):
    """
    Тест успешного предпросмотра шаблона.

    Проверяет:
    - Создание шаблона
    - Предпросмотр с переменными
    - Подстановка переменных работает корректно
    """
    service = get_template_service()

    # Создать тестовый шаблон
    template = await service.create_template(
        db=db_session,
        template_type="email",
        name="test_preview_template",
        subject="Hello {name}",
        body="Welcome {name}, your status is {status}",
        variables=["name", "status"],
    )

    # Тестовые данные для предпросмотра
    preview_data = {
        "template_id": template.id,
        "template_type": "email",
        "variables": {
            "name": "John",
            "status": "active"
        }
    }

    # Тест через HTTP client
    client = TestClient(app)
    response = client.post("/api/templates/preview", json=preview_data)

    assert response.status_code == 200
    data = response.json()

    assert "subject" in data
    assert "body" in data
    assert "active_blocks" in data

    assert data["subject"] == "Hello John"
    assert data["body"] == "Welcome John, your status is active"


@pytest.mark.asyncio
async def test_preview_template_not_found(db_session: AsyncSession):
    """
    Тест предпросмотра несуществующего шаблона.

    Проверяет:
    - Возврат 404 для несуществующего шаблона
    """
    preview_data = {
        "template_id": "nonexistent-id",
        "template_type": "email",
        "variables": {"name": "John"}
    }

    client = TestClient(app)
    response = client.post("/api/templates/preview", json=preview_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_preview_template_with_conditional_blocks(db_session: AsyncSession):
    """
    Тест предпросмотра шаблона с условными блоками.

    Проверяет:
    - Вычисление условных блоков
    - Правильный выбор true_block или false_block
    """
    service = get_template_service()

    # Создать шаблон с условными блоками
    template_blocks = {
        "blocks": [
            {"type": "text", "content": "Hello"},
            {
                "type": "conditional",
                "condition": {"field": "status", "operator": "eq", "value": "accepted"},
                "true_block": {"type": "text", "content": "Congratulations!"},
                "false_block": {"type": "text", "content": "Thank you for applying"}
            }
        ]
    }

    template = await service.create_template(
        db=db_session,
        template_type="email",
        name="test_conditional_template",
        subject="Application Update",
        body="Hello {name}",
        variables=["name", "status"],
        template_blocks=template_blocks,
    )

    # Тест с accepted status
    preview_data = {
        "template_id": template.id,
        "template_type": "email",
        "variables": {
            "name": "Jane",
            "status": "accepted"
        }
    }

    client = TestClient(app)
    response = client.post("/api/templates/preview", json=preview_data)

    assert response.status_code == 200
    data = response.json()

    # Проверить что активные блоки содержат true_block
    active_blocks = data["active_blocks"]
    assert len(active_blocks) == 2
    assert active_blocks[0]["content"] == "Hello"
    assert active_blocks[1]["content"] == "Congratulations!"


@pytest.mark.asyncio
async def test_preview_sms_template(db_session: AsyncSession):
    """
    Тест предпросмотра SMS шаблона.

    Проверяет:
    - SMS шаблоны работают корректно
    - Нет subject в ответе для SMS
    """
    service = get_template_service()

    # Создать SMS шаблон
    template = await service.create_template(
        db=db_session,
        template_type="sms",
        name="test_sms_template",
        body="Hi {name}, your code is {code}",
        variables=["name", "code"],
    )

    preview_data = {
        "template_id": template.id,
        "template_type": "sms",
        "variables": {
            "name": "Bob",
            "code": "123456"
        }
    }

    client = TestClient(app)
    response = client.post("/api/templates/preview", json=preview_data)

    assert response.status_code == 200
    data = response.json()

    assert data["body"] == "Hi Bob, your code is 123456"
    assert data["subject"] is None  # SMS не имеет subject

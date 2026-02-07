"""
Сервис отправки email уведомлений.

# Русский комментарий:
Этот модуль предоставляет функциональность для отправки email уведомлений
через SMTP или email API (SendGrid, AWS SES, Mailgun).
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailNotificationService:
    """
    Сервис отправки email уведомлений.

    Предоставляет методы для отправки email через SMTP с поддержкой
    TLS и аутентификации.

    Attributes:
        smtp_host: Хост SMTP сервера
        smtp_port: Порт SMTP сервера
        smtp_username: Имя пользователя SMTP
        smtp_password: Пароль SMTP
        smtp_use_tls: Использовать TLS
        default_from: Email отправителя по умолчанию
    """

    def __init__(self):
        """Инициализация сервиса с настройками из конфигурации."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.default_from = settings.smtp_default_from

    def send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html: bool = False,
        from_address: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Отправить email уведомление.

        Args:
            to: Email получателя или список получателей
            subject: Тема письма
            body: Тело письма
            html: Флаг HTML формата (по умолчанию False - обычный текст)
            from_address: Email отправителя (по умолчанию из настроек)
            reply_to: Email для ответа

        Returns:
            Словарь с результатом отправки:
            - success: True если отправка успешна
            - message: Сообщение об ошибке или успехе
            - recipients_count: Количество получателей

        Raises:
            smtplib.SMTPException: При ошибке SMTP

        Examples:
            >>> service = EmailNotificationService()
            >>> result = service.send_email(
            ...     to="test@example.com",
            ...     subject="Test Subject",
            ...     body="Test Body"
            ... )
            >>> print(result['success'])
            True
        """
        try:
            # Нормализация списка получателей
            if isinstance(to, str):
                recipients = [to]
            else:
                recipients = to

            logger.info(
                f"Sending email: from={from_address or self.default_from}, "
                f"to={len(recipients)} recipients, subject='{subject}'"
            )

            # Проверка настроек SMTP
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, using placeholder mode")
                # Placeholder режим для разработки
                return {
                    "success": True,
                    "message": "Email logged (placeholder mode - no SMTP configured)",
                    "recipients_count": len(recipients),
                }

            # Создание сообщения
            msg = MIMEMultipart("alternative")
            msg["From"] = from_address or self.default_from
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            if reply_to:
                msg["Reply-To"] = reply_to

            # Добавление тела письма
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type, _charset="utf-8"))

            # Подключение к SMTP серверу и отправка
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                    logger.debug("TLS started")

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                    logger.debug("Authenticated to SMTP server")

                server.send_message(msg)
                logger.debug("Email sent via SMTP")

            logger.info(
                f"Email sent successfully: to={len(recipients)} recipients, "
                f"subject='{subject}'"
            )

            return {
                "success": True,
                "message": "Email sent successfully",
                "recipients_count": len(recipients),
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication error: {e}")
            return {
                "success": False,
                "message": f"SMTP authentication failed: {str(e)}",
                "recipients_count": len(recipients) if recipients else 0,
            }

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"SMTP error: {str(e)}",
                "recipients_count": len(recipients) if recipients else 0,
            }

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "recipients_count": len(recipients) if recipients else 0,
            }

    def send_html_email(
        self,
        to: str | List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Отправить HTML email с альтернативным текстовым представлением.

        Args:
            to: Email получателя или список получателей
            subject: Тема письма
            html_body: HTML тело письма
            text_body: Опциональное текстовое тело (для клиентов без HTML)
            from_address: Email отправителя

        Returns:
            Словарь с результатом отправки

        Examples:
            >>> service = EmailNotificationService()
            >>> result = service.send_html_email(
            ...     to="test@example.com",
            ...     subject="HTML Email",
            ...     html_body="<h1>Hello</h1>",
            ...     text_body="Hello"
            ... )
        """
        try:
            # Нормализация списка получателей
            if isinstance(to, str):
                recipients = [to]
            else:
                recipients = to

            logger.info(
                f"Sending HTML email: from={from_address or self.default_from}, "
                f"to={len(recipients)} recipients, subject='{subject}'"
            )

            # Проверка настроек SMTP
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, using placeholder mode")
                return {
                    "success": True,
                    "message": "HTML email logged (placeholder mode - no SMTP configured)",
                    "recipients_count": len(recipients),
                }

            # Создание сообщения
            msg = MIMEMultipart("alternative")
            msg["From"] = from_address or self.default_from
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            # Добавление текстовой части (если предоставлена)
            if text_body:
                msg.attach(MIMEText(text_body, "plain", _charset="utf-8"))

            # Добавление HTML части
            msg.attach(MIMEText(html_body, "html", _charset="utf-8"))

            # Подключение к SMTP серверу и отправка
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                    logger.debug("TLS started")

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                    logger.debug("Authenticated to SMTP server")

                server.send_message(msg)
                logger.debug("HTML email sent via SMTP")

            logger.info(
                f"HTML email sent successfully: to={len(recipients)} recipients, "
                f"subject='{subject}'"
            )

            return {
                "success": True,
                "message": "HTML email sent successfully",
                "recipients_count": len(recipients),
            }

        except Exception as e:
            logger.error(f"Error sending HTML email: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "recipients_count": len(recipients) if recipients else 0,
            }

    def validate_email_address(self, email: str) -> bool:
        """
        Проверить валидность email адреса.

        Args:
            email: Email адрес для проверки

        Returns:
            True если email валиден, иначе False

        Examples:
            >>> service = EmailNotificationService()
            >>> service.validate_email_address("test@example.com")
            True
            >>> service.validate_email_address("invalid-email")
            False
        """
        import re

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return bool(re.match(pattern, email))


# Глобальный экземпляр сервиса
_email_service: Optional[EmailNotificationService] = None


def get_email_service() -> EmailNotificationService:
    """
    Получить или создать глобальный экземпляр EmailNotificationService.

    Returns:
        Экземпляр EmailNotificationService

    Examples:
        >>> service = get_email_service()
        >>> result = service.send_email("test@example.com", "Test", "Body")
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailNotificationService()
        logger.info("EmailNotificationService initialized")
    return _email_service

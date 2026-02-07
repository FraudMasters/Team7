"""
LinkedIn Service для Integration Service.

# Русский комментарий:
Этот модуль предоставляет сервис для интеграции с LinkedIn API,
включая получение профилей кандидатов, извлечение навыков и опыта работы.
"""
import logging
import re
from typing import Optional, Dict, Any, List

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LinkedInService:
    """
    Сервис для работы с LinkedIn API.

    Предоставляет методы для получения профилей кандидатов,
    извлечения навыков, опыта работы и другой информации.

    Attributes:
        client_id: Client ID для LinkedIn API
        client_secret: Client Secret для LinkedIn API
        redirect_uri: Redirect URI для OAuth
        timeout: Таймаут запросов к API
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Инициализация LinkedIn Service.

        Args:
            client_id: Client ID для LinkedIn API (если None, берется из настроек)
            client_secret: Client Secret для LinkedIn API (если None, берется из настроек)
            redirect_uri: Redirect URI для OAuth (если None, берется из настроек)
            timeout: Таймаут запросов (если None, берется из настроек)
        """
        self.client_id = client_id or settings.linkedin_client_id
        self.client_secret = client_secret or settings.linkedin_client_secret
        self.redirect_uri = redirect_uri or settings.linkedin_redirect_uri
        self.timeout = timeout or settings.linkedin_api_timeout

        # HTTP клиент для запросов к API
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Закрытие HTTP клиента."""
        await self.client.aclose()

    async def get_profile(
        self,
        profile_url: str,
        include_skills: bool = True,
        include_experience: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить профиль кандидата из LinkedIn.

        Извлекает информацию о профиле кандидата по указанному URL.

        Args:
            profile_url: URL профиля LinkedIn
            include_skills: Включить навыки в ответ
            include_experience: Включить опыт работы в ответ

        Returns:
            Словарь с данными профиля или None, если профиль не найден

        Raises:
            ValueError: Если URL профиля некорректен

        Example:
            >>> service = LinkedInService()
            >>> profile = await service.get_profile("https://linkedin.com/in/johndoe")
            >>> print(profile.get("name"))
            "John Doe"
        """
        try:
            logger.info(f"Fetching LinkedIn profile: {profile_url}")

            # Валидация URL
            if not self._validate_profile_url(profile_url):
                raise ValueError(f"Invalid LinkedIn profile URL: {profile_url}")

            # Извлечение публичного ID профиля из URL
            profile_id = self._extract_profile_id(profile_url)

            # TODO: Реализовать фактический запрос к LinkedIn API
            # В настоящее время возвращаем заглушку, так как для реального
            # запроса необходим OAuth токен

            profile_data = {
                "id": profile_id,
                "name": "Candidate Name",
                "headline": "Professional Headline",
                "location": "City, Country",
                "profile_url": profile_url,
                "summary": "Professional summary...",
            }

            if include_skills:
                profile_data["skills"] = ["Python", "FastAPI", "SQL", "Docker"]

            if include_experience:
                profile_data["experience"] = [
                    {
                        "title": "Software Engineer",
                        "company": "Company Name",
                        "duration": "2020 - Present",
                        "description": "Job description...",
                    }
                ]

            logger.info(f"Successfully fetched profile: {profile_data.get('name')}")

            return profile_data

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile: {e}", exc_info=True)
            return None

    def _validate_profile_url(self, profile_url: str) -> bool:
        """
        Проверить корректность URL профиля LinkedIn.

        Args:
            profile_url: URL профиля для проверки

        Returns:
            True если URL корректен, иначе False
        """
        pattern = r"^https?://(www\.)?linkedin\.com/in/[\w-]+/?$"
        return bool(re.match(pattern, profile_url))

    def _extract_profile_id(self, profile_url: str) -> str:
        """
        Извлечь публичный ID профиля из URL.

        Args:
            profile_url: URL профиля LinkedIn

        Returns:
            Публичный ID профиля
        """
        # Удаляем завершающий слеш
        url = profile_url.rstrip("/")

        # Извлекаем ID из URL
        parts = url.split("/in/")
        if len(parts) > 1:
            return parts[-1]
        return "unknown"

    async def get_oauth_url(self, state: Optional[str] = None) -> str:
        """
        Сгенерировать URL для OAuth авторизации.

        Args:
            state: Опциональный параметр state для защиты от CSRF

        Returns:
            URL для перенаправления пользователя на страницу авторизации LinkedIn
        """
        from urllib.parse import urlencode

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "r_liteprofile r_emailaddress",  # Basic profile scopes
        }

        if state:
            params["state"] = state

        base_url = "https://www.linkedin.com/oauth/v2/authorization"
        return f"{base_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        Обменять код авторизации на access token.

        Args:
            code: Код авторизации, полученный от LinkedIn

        Returns:
            Access token или None в случае ошибки
        """
        try:
            logger.info("Exchanging authorization code for access token")

            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            response = await self.client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                logger.info("Successfully obtained access token")
                return access_token
            else:
                logger.error(f"Failed to get access token: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}", exc_info=True)
            return None

    async def get_profile_by_token(
        self,
        access_token: str,
        include_skills: bool = True,
        include_experience: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить профиль кандидата используя access token.

        Args:
            access_token: OAuth access token
            include_skills: Включить навыки в ответ
            include_experience: Включить опыт работы в ответ

        Returns:
            Словарь с данными профиля или None в случае ошибки
        """
        try:
            logger.info("Fetching LinkedIn profile using access token")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Connection": "Keep-Alive",
            }

            # Запрос базового профиля
            response = await self.client.get(
                "https://api.linkedin.com/v2/me",
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch profile: {response.text}")
                return None

            profile_data = response.json()

            # TODO: Дополнительные запросы для навыков и опыта
            # LinkedIn API требует отдельных запросов для разных секций

            result = {
                "id": profile_data.get("id"),
                "name": f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}",
            }

            if include_skills:
                result["skills"] = []  # TODO: Fetch from /skill endpoints

            if include_experience:
                result["experience"] = []  # TODO: Fetch from /positions endpoint

            logger.info(f"Successfully fetched profile: {result.get('name')}")

            return result

        except Exception as e:
            logger.error(f"Error fetching profile by token: {e}", exc_info=True)
            return None

    async def search_candidates(
        self,
        keywords: str,
        location: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Поиск кандидатов в LinkedIn (требует Recruiter license).

        Args:
            keywords: Ключевые слова для поиска
            location: Опциональная локация
            limit: Максимальное количество результатов

        Returns:
            Список найденных кандидатов

        Note:
            Эта функциональность требует LinkedIn Recruiter license
            и специальных API прав доступа.
        """
        logger.warning(
            "Candidate search requires LinkedIn Recruiter license and special API access. "
            "Returning empty list."
        )
        return []

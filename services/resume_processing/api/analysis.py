"""
Эндпоинты анализа резюме, интегрирующие все анализаторы.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для анализа загруженных резюме с
использованием нескольких ML/NLP анализаторов, включая извлечение ключевых слов,
распознавание именованных сущностей, проверку грамматики и вычисление опыта.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Добавить родительскую директорию в путь для импорта из backend
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

# Импорт анализаторов из backend (пока не мигрированы полностью)
from analyzers import (
    extract_resume_keywords_hf as extract_resume_keywords,
    extract_resume_entities,
    check_grammar_resume,
)
from i18n.backend_translations import get_error_message, get_success_message

# Локальные анализаторы (уже мигрированы)
from analyzers.experience_extractor import extract_work_experience

# Импорт парсеров для извлечения текста
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx

logger = logging.getLogger(__name__)

router = APIRouter()

# Директория где хранятся загруженные резюме
UPLOAD_DIR = Path("data/uploads")


def _extract_locale(request: Optional[Request]) -> str:
    """
    Извлечь заголовок Accept-Language из запроса.

    Аргументы:
        request: Входящий запрос FastAPI (опционально)

    Возвращает:
        Код языка (например, 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


class AnalysisRequest(BaseModel):
    """Модель запроса для эндпоинта анализа резюме."""

    resume_id: str = Field(..., description="Уникальный идентификатор резюме для анализа")
    extract_experience: bool = Field(
        default=True, description="Извлекать ли и рассчитывать информацию об опыте"
    )
    check_grammar: bool = Field(
        default=True, description="Выполнять ли проверку грамматики и орфографии"
    )


class KeywordAnalysis(BaseModel):
    """Результаты извлечения ключевых слов."""

    keywords: List[str] = Field(..., description="Извлеченные ключевые слова")
    keyphrases: List[str] = Field(..., description="Извлеченные ключевые фразы")
    scores: List[float] = Field(..., description="Оценки уверенности для каждого ключевого слова")


class EntityAnalysis(BaseModel):
    """Результаты распознавания именованных сущностей."""

    organizations: List[str] = Field(..., description="Извлеченные названия организаций")
    dates: List[str] = Field(..., description="Извлеченные выражения дат")
    persons: List[str] = Field(default=[], description="Извлеченные имена людей")
    locations: List[str] = Field(default=[], description="Извлеченные локации")
    technical_skills: List[str] = Field(..., description="Извлеченные технические навыки")


class GrammarError(BaseModel):
    """Отдельная грамматическая/орфографическая ошибка."""

    type: str = Field(..., description="Тип ошибки (grammar, spelling, punctuation, style)")
    severity: str = Field(..., description="Уровень серьезности (error, warning)")
    message: str = Field(..., description="Сообщение об ошибке")
    context: str = Field(..., description="Контекст текста где произошла ошибка")
    suggestions: List[str] = Field(..., description="Предлагаемые исправления")
    position: Dict[str, int] = Field(..., description="Позиция символа ошибки")


class GrammarAnalysis(BaseModel):
    """Результаты проверки грамматики."""

    total_errors: int = Field(..., description="Общее количество найденных ошибок")
    errors_by_category: Dict[str, int] = Field(
        ..., description="Разбивка ошибок по типам"
    )
    errors_by_severity: Dict[str, int] = Field(
        ..., description="Разбивка ошибок по серьезности"
    )
    errors: List[GrammarError] = Field(..., description="Список отдельных ошибок")


class ExperienceEntry(BaseModel):
    """Отдельная запись об опыте работы."""

    company: str = Field(..., description="Название компании")
    position: str = Field(..., description="Должность/название позиции")
    start_date: str = Field(..., description="Начальная дата (формат ISO)")
    end_date: Optional[str] = Field(..., description="Конечная дата (формат ISO) или None если текущая")
    duration_months: int = Field(..., description="Продолжительность в месяцах")


class ExperienceAnalysis(BaseModel):
    """Результаты расчета опыта."""

    total_months: int = Field(..., description="Общий опыт в месяцах")
    total_years: float = Field(..., description="Общий опыт в годах")
    total_years_formatted: str = Field(..., description="Человекочитаемая сводка опыта")
    entries: List[ExperienceEntry] = Field(..., description="Отдельные записи опыта")


class AnalysisResponse(BaseModel):
    """Полный ответ анализа."""

    resume_id: str = Field(..., description="Идентификатор резюме")
    status: str = Field(..., description="Статус анализа")
    language: str = Field(..., description="Обнаруженный язык (en, ru)")
    keywords: KeywordAnalysis = Field(..., description="Результаты извлечения ключевых слов")
    entities: EntityAnalysis = Field(..., description="Результаты распознавания сущностей")
    grammar: Optional[GrammarAnalysis] = Field(
        None, description="Результаты проверки грамматики (если включено)"
    )
    experience: Optional[ExperienceAnalysis] = Field(
        None, description="Результаты расчета опыта (если включено)"
    )
    processing_time_ms: float = Field(..., description="Время обработки анализа в миллисекундах")


def find_resume_file(resume_id: str, locale: str = "en") -> Path:
    """
    Найти файл резюме по ID.

    Аргументы:
        resume_id: Уникальный идентификатор резюме
        locale: Код языка для перевода сообщений об ошибках

    Возвращает:
        Путь к файлу резюме

    Исключения:
        HTTPException: Если файл резюме не найден
    """
    # Попытка распространенных расширений файлов
    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
        file_path = UPLOAD_DIR / f"{resume_id}{ext}"
        if file_path.exists():
            return file_path

    # Если не найдено, вызвать ошибку
    error_msg = get_error_message("file_not_found", locale)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_msg,
    )


def extract_text_from_file(file_path: Path, locale: str = "en") -> str:
    """
    Извлечь текст из файла резюме (PDF или DOCX).

    Аргументы:
        file_path: Путь к файлу резюме
        locale: Код языка для перевода сообщений об ошибках

    Возвращает:
        Извлеченное текстовое содержимое

    Исключения:
        HTTPException: Если не удалось извлечь текст
    """
    try:
        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            result = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            result = extract_text_from_docx(file_path)
        else:
            error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=".pdf, .docx")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=error_msg,
            )

        # Проверка на ошибки извлечения
        if result.get("error"):
            error_msg = get_error_message("extraction_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        text = result.get("text", "")
        if not text or len(text.strip()) < 10:
            error_msg = get_error_message("file_corrupted", locale)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        logger.info(f"Извлечено {len(text)} символов из {file_path.name}")
        return text

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка извлечения текста из {file_path}: {e}", exc_info=True)
        error_msg = get_error_message("extraction_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def analyze_resume(http_request: Request, request: AnalysisRequest) -> JSONResponse:
    """
    Проанализировать резюме используя интегрированные ML/NLP анализаторы.

    Этот эндпоинт выполняет комплексный анализ резюме, включая:
    - Извлечение ключевых слов (KeyBERT)
    - Распознавание именованных сущностей (SpaCy)
    - Проверку грамматики и орфографии (LanguageTool)
    - Вычисление опыта

    Аргументы:
        http_request: Объект запроса FastAPI (для заголовка Accept-Language)
        request: Запрос анализа с resume_id и опциями анализа

    Возвращает:
        JSON ответ с полными результатами анализа

    Исключения:
        HTTPException(404): Если файл резюме не найден
        HTTPException(422): Если не удалось извлечь текст
        HTTPException(500): Если не удалось выполнить анализ

    Примеры:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8001/api/analysis",
        ...     json={"resume_id": "abc123", "check_grammar": True, "extract_experience": True}
        ... )
        >>> response.json()
        {
            "resume_id": "abc123",
            "status": "completed",
            "language": "en",
            "keywords": {...},
            "entities": {...},
            "grammar": {...},
            "experience": {...},
            "processing_time_ms": 1234.56
        }
    """
    import time

    # Извлечь локаль из заголовка Accept-Language
    locale = _extract_locale(http_request)

    start_time = time.time()

    try:
        logger.info(f"Начало анализа для resume_id: {request.resume_id}")

        # Шаг 1: Найти файл резюме
        file_path = find_resume_file(request.resume_id, locale)
        logger.info(f"Найден файл резюме: {file_path}")

        # Шаг 2: Извлечь текст из файла
        resume_text = extract_text_from_file(file_path, locale)

        # Шаг 3: Обнаружить язык из текста
        try:
            from langdetect import detect, LangDetectException

            try:
                detected_lang = detect(resume_text)
                # Нормализация к поддерживаемым языкам
                language = "ru" if detected_lang == "ru" else "en"
            except LangDetectException:
                logger.warning("Обнаружение языка не удалось, используется английский по умолчанию")
                language = "en"
        except ImportError:
            logger.warning("langdetect не установлен, используется английский по умолчанию")
            language = "en"

        logger.info(f"Обнаружен язык: {language}")

        # Шаг 4: Выполнить извлечение ключевых слов
        logger.info("Выполняется извлечение ключевых слов...")
        keywords_result = extract_resume_keywords(
            resume_text, language=language
        )

        # Обработка разных форматов возврата от экстракторов
        # HF экстрактор возвращает: single_words, keyphrases, all_keywords (как кортежи с оценками)
        # Старый формат возвращает: keywords, keyphrases, scores
        if "single_words" in keywords_result:
            # HF формат - конвертировать в ожидаемый формат
            single_words = keywords_result.get("single_words", [])
            keywords_list = [word[0] if isinstance(word, (list, tuple)) else word for word in single_words]

            # Keyphrases также кортежи (phrase, score) - извлечь только фразы
            keyphrases_raw = keywords_result.get("keyphrases", [])
            keyphrases_list = [kp[0] if isinstance(kp, (list, tuple)) else kp for kp in keyphrases_raw]

            keyword_analysis = KeywordAnalysis(
                keywords=keywords_list,
                keyphrases=keyphrases_list,
                scores=[],  # Оценки недоступны в этом формате
            )
        else:
            # Старый формат
            keyword_analysis = KeywordAnalysis(
                keywords=keywords_result.get("keywords", []),
                keyphrases=keywords_result.get("keyphrases", []),
                scores=keywords_result.get("scores", []),
            )

        # Шаг 5: Выполнить распознавание именованных сущностей
        logger.info("Выполняется распознавание именованных сущностей...")
        entities_result = extract_resume_entities(resume_text, language=language)

        # Обработка обоих имен полей 'skills' и 'technical_skills' от разных экстракторов
        skills = entities_result.get("technical_skills") or entities_result.get("skills") or []

        entity_analysis = EntityAnalysis(
            organizations=entities_result.get("organizations") or [],
            dates=entities_result.get("dates") or [],
            persons=entities_result.get("persons") or [],
            locations=entities_result.get("locations") or [],
            technical_skills=skills,
        )

        # Шаг 6: Проверка грамматики (опционально)
        grammar_analysis = None
        if request.check_grammar:
            logger.info("Выполняется проверка грамматики...")
            try:
                grammar_result = check_grammar_resume(resume_text, language=language)

                # Конвертировать ошибки грамматики в модели ответа
                error_models = []
                for error in grammar_result.get("errors", []):
                    error_models.append(
                        GrammarError(
                            type=error.get("type", "unknown"),
                            severity=error.get("severity", "warning"),
                            message=error.get("message", ""),
                            context=error.get("context", ""),
                            suggestions=error.get("suggestions", []),
                            position=error.get("position", {}),
                        )
                    )

                grammar_analysis = GrammarAnalysis(
                    total_errors=grammar_result.get("count", 0),
                    errors_by_category=grammar_result.get("error_summary", {}),
                    errors_by_severity={
                        "error": grammar_result.get("critical_errors", 0),
                        "warning": grammar_result.get("warning_errors", 0),
                    },
                    errors=error_models,
                )

                logger.info(
                    f"Найдено {grammar_analysis.total_errors} грамматических/орфографических ошибок"
                )
            except Exception as e:
                logger.warning(f"Проверка грамматики не удалась: {e}")
                # Продолжить без результатов грамматики вместо сбоя всего анализа

        # Шаг 7: Извлечение опыта (опционально)
        experience_analysis = None
        if request.extract_experience:
            logger.info("Извлечение опыта работы...")
            try:
                # Использовать экстрактор опыта для парсинга структурированного опыта из текста резюме
                experience_result = extract_work_experience(
                    resume_text, language=language, min_confidence=0.2
                )

                if experience_result.get("experiences"):
                    # Конвертировать извлеченный опыт в формат ответа
                    experience_entries = []
                    for exp in experience_result.get("experiences", []):
                        # Рассчитать продолжительность в месяцах
                        start_str = exp.get("start")
                        end_str = exp.get("end")
                        duration_months = 0

                        if start_str:
                            from datetime import datetime
                            try:
                                start_date = datetime.fromisoformat(start_str)
                                end_date = datetime.fromisoformat(end_str) if end_str else datetime.now()
                                # Рассчитать разницу в месяцах
                                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                                duration_months = max(0, months)
                            except:
                                pass

                        experience_entries.append(
                            ExperienceEntry(
                                company=exp.get("company") or "Unknown",
                                position=exp.get("title") or "Unknown",
                                start_date=exp.get("start") or "",
                                end_date=exp.get("end"),
                                duration_months=duration_months,
                            )
                        )

                    # Рассчитать итоги
                    total_months = sum(e.duration_months for e in experience_entries)
                    total_years = round(total_months / 12, 1) if total_months > 0 else 0

                    # Форматирование сводки
                    years = int(total_months // 12)
                    months = total_months % 12
                    if years > 0 and months > 0:
                        formatted = f"{years} years {months} months"
                    elif years > 0:
                        formatted = f"{years} years"
                    elif months > 0:
                        formatted = f"{months} months"
                    else:
                        formatted = "No experience data"

                    experience_analysis = ExperienceAnalysis(
                        total_months=total_months,
                        total_years=total_years,
                        total_years_formatted=formatted,
                        entries=experience_entries,
                    )

                    logger.info(f"Извлечено {len(experience_entries)} записей опыта работы")
                else:
                    # Опыт не найден
                    experience_analysis = ExperienceAnalysis(
                        total_months=0,
                        total_years=0.0,
                        total_years_formatted="No work experience found",
                        entries=[],
                    )

            except Exception as e:
                logger.warning(f"Извлечение опыта не удалось: {e}", exc_info=True)
                # Вернуть пустой анализ опыта при сбое
                experience_analysis = ExperienceAnalysis(
                    total_months=0,
                    total_years=0.0,
                    total_years_formatted="Experience extraction failed",
                    entries=[],
                )

        # Рассчитать время обработки
        processing_time_ms = (time.time() - start_time) * 1000

        # Сформировать ответ
        response_data = {
            "resume_id": request.resume_id,
            "status": "completed",
            "language": language,
            "keywords": keyword_analysis.model_dump(),
            "entities": entity_analysis.model_dump(),
            "grammar": grammar_analysis.model_dump() if grammar_analysis else None,
            "experience": experience_analysis.model_dump() if experience_analysis else None,
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Анализ завершен для resume_id {request.resume_id} за {processing_time_ms:.2f}мс"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Перебросить HTTP исключения
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа резюме: {e}", exc_info=True)
        error_msg = get_error_message("analysis_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/{resume_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def get_analysis_result(
    http_request: Request, resume_id: str
) -> JSONResponse:
    """
    Получить результат анализа для конкретного резюме.

    Этот эндпоинт возвращает результаты анализа для резюме.
    В настоящее время возвращает плейсхолдер данных, так как полная интеграция БД ожидается.

    Аргументы:
        http_request: Объект запроса FastAPI (для заголовка Accept-Language)
        resume_id: ID резюме для получения анализа

    Возвращает:
        JSON ответ с результатами анализа

    Исключения:
        HTTPException(404): Если резюме не найдено

    Примеры:
        >>> import requests
        >>> response = requests.get("http://localhost:8001/api/analysis/abc123")
        >>> response.json()
        {
            "resume_id": "abc123",
            "status": "pending",
            "errors": [],
            "grammar_errors": [],
            "keywords": [],
            "technical_skills": []
        }
    """
    locale = _extract_locale(http_request)
    logger.info(f"Получение анализа для resume_id: {resume_id}")

    # TODO: Реализовать поиск в БД в будущей подзадаче
    # Пока вернуть плейсхолдер ответ с правильной структурой
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "resume_id": resume_id,
            "status": "pending",
            "message": "Analysis not found - please run analysis first",
            "errors": [],
            "grammar_errors": [],
            "keywords": [],
            "technical_skills": [],
            "total_experience_months": 0,
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0,
        },
    )

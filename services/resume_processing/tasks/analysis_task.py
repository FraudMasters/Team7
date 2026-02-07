"""
Асинхронная задача анализа резюме с отслеживанием прогресса.

# Русский комментарий:
Этот модуль предоставляет задачи Celery для асинхронного анализа резюме с
обновлением прогресса в реальном времени. Интегрирует все ML/NLP анализаторы
и обеспечивает отслеживание статуса на протяжении всего процесса анализа.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Добавляем путь к корню сервиса для импортов / Add path to service root for imports
# Поднимаемся на три уровня вверх от tasks/analysis_task.py к корню репозитория
# Go up three levels from tasks/analysis_task.py to repository root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Импортируем из родительского бэкенда (для миграции) / Import from parent backend (for migration)
# В конечном итоге эти анализаторы будут перемещены в сервис resume_processing
# Eventually these analyzers will be moved to the resume_processing service
try:
    from services.data_extractor.analyzers import (
        extract_resume_keywords_hf as extract_resume_keywords,
        extract_resume_entities,
        check_grammar_resume,
        calculate_total_experience,
        format_experience_summary,
        detect_resume_errors,
        extract_work_experience,
    )
except ImportError:
    # Резервный импорт для этапа миграции / Fallback import for migration phase
    try:
        from backend.services.data_extractor.analyzers import (
            extract_resume_keywords_hf as extract_resume_keywords,
            extract_resume_entities,
            check_grammar_resume,
            calculate_total_experience,
            format_experience_summary,
            detect_resume_errors,
            extract_work_experience,
        )
    except ImportError:
        # Если не удалось импортировать, будем использовать заглушки / If import fails, use stubs
        extract_resume_keywords = None
        extract_resume_entities = None
        check_grammar_resume = None
        calculate_total_experience = None
        format_experience_summary = None
        detect_resume_errors = None
        extract_work_experience = None

# Импортируем настройки сервиса / Import service settings
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_settings
    settings = get_settings()
except ImportError:
    # Резервные значения / Fallback values
    class Settings:
        processing_timeout_seconds = 300
        models_cache_path = Path("./models_cache")
    settings = Settings()

logger = logging.getLogger(__name__)

# Директория для хранения загруженных резюме / Directory for uploaded resumes
UPLOAD_DIR = Path("data/uploads")


def convert_numpy_types(obj: Any) -> Any:
    """
    Convert numpy types to Python native types for JSON serialization.

    Преобразует типы numpy в собственные типы Python для JSON-сериализации.

    This recursively converts numpy arrays, scalars, and other numpy types
    to their Python equivalents.

    Args:
        obj: Объект для преобразования / Object to convert

    Returns:
        JSON-сериализуемая версия объекта / JSON-serializable version of the object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj


def find_resume_file(resume_id: str) -> Path:
    """
    Find the resume file by ID.

    Найти файл резюме по идентификатору.

    Args:
        resume_id: Уникальный идентификатор резюме / Unique identifier of the resume

    Returns:
        Path: Путь к файлу резюме / Path to the resume file

    Raises:
        FileNotFoundError: Если файл резюме не найден / If resume file is not found
    """
    # Пытаемся найти файл с распространенными расширениями
    # Try to find file with common extensions
    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
        file_path = UPLOAD_DIR / f"{resume_id}{ext}"
        if file_path.exists():
            return file_path

    # Если файл не найден, вызываем ошибку / If not found, raise error
    raise FileNotFoundError(f"Resume file with ID '{resume_id}' not found / Файл резюме с ID '{resume_id}' не найден")


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from resume file (PDF or DOCX).

    Извлечь текст из файла резюме (PDF или DOCX).

    Args:
        file_path: Путь к файлу резюме / Path to the resume file

    Returns:
        str: Извлеченное текстовое содержимое / Extracted text content

    Raises:
        ValueError: Если извлечение текста не удалось или вернуло пустой текст
                   If text extraction fails or returns empty text
    """
    try:
        # Импортируем функции извлечения текста / Import text extraction functions
        from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            result = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            result = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext} / Неподдерживаемый тип файла: {file_ext}")

        # Проверяем наличие ошибок извлечения / Check for extraction errors
        if result.get("error"):
            raise ValueError(f"Text extraction failed: {result['error']} / Ошибка извлечения текста: {result['error']}")

        text = result.get("text", "")
        if not text or len(text.strip()) < 10:
            raise ValueError(
                "Extracted text is too short or empty. The file may be corrupted or scanned. "
                "Извлеченный текст слишком короткий или пустой. Файл может быть поврежден или отсканирован."
            )

        logger.info(f"Extracted {len(text)} characters from {file_path.name} / Извлечено {len(text)} символов из {file_path.name}")
        return text

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e} / Ошибка извлечения текста из {file_path}: {e}", exc_info=True)
        raise


def analyze_resume_core(
    resume_id: str,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Core resume analysis logic without Celery dependencies.

    Основная логика анализа резюме без зависимостей от Celery.

    This function can be called directly or wrapped in a Celery task.
    Эта функция может быть вызвана напрямую или обернута в задачу Celery.

    Args:
        resume_id: Уникальный идентификатор резюме для анализа
                   Unique identifier of the resume to analyze
        check_grammar: Выполнять ли проверку грамматики / Whether to perform grammar checking
        extract_experience: Вычислять ли опыт работы / Whether to calculate experience
        detect_errors: Обнаруживать ли ошибки в резюме / Whether to detect resume errors

    Returns:
        Dict[str, Any]: Словарь с результатами анализа / Dictionary containing analysis results
    """
    start_time = time.time()

    try:
        logger.info(f"Starting core resume analysis for resume_id: {resume_id} / "
                    f"Начало основного анализа резюме для resume_id: {resume_id}")

        # Шаг 1: Найти и извлечь текст / Step 1: Find and extract text
        try:
            file_path = find_resume_file(resume_id)
        except FileNotFoundError as e:
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Извлечь текст / Extract text
        try:
            resume_text = extract_text_from_file(file_path)
        except ValueError as e:
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Проверяем, доступны ли анализаторы / Check if analyzers are available
        if not all([extract_resume_keywords, extract_resume_entities]):
            return {
                "resume_id": resume_id,
                "status": "failed",
                "error": "ML analyzers not available. Please ensure data_extractor service is running. "
                         "ML-анализаторы недоступны. Убедитесь, что сервис data_extractor запущен.",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Определяем язык / Detect language
        from langdetect import detect
        try:
            lang_code = detect(resume_text[:1000])
            detected_language = 'ru' if lang_code == 'ru' else 'en' if lang_code == 'en' else lang_code
        except Exception:
            detected_language = "en"

        # Извлекаем ключевые слова и сущности / Extract keywords and entities
        keywords_result = extract_resume_keywords(resume_text, language=detected_language)
        keywords = keywords_result.get("all_keywords") or keywords_result.get("keywords", [])

        entities_result = extract_resume_entities(resume_text)
        language = entities_result.get("language", detected_language)
        entities = entities_result.get("technical_skills", [])

        # Опциональный анализ / Optional analysis
        grammar_result = None
        experience_result = None
        errors_result = None

        if check_grammar:
            try:
                grammar_result = check_grammar_resume(resume_text)
            except Exception as e:
                logger.warning(f"Grammar checking failed: {e} / Сбой грамматической проверки: {e}")

        if extract_experience:
            try:
                # Сначала извлекаем структурированные записи об опыте из текста резюме
                # First extract structured experience entries from resume text
                extracted = extract_work_experience(resume_text, language=detected_language, min_confidence=0.2)

                if extracted.get("experiences"):
                    # Преобразуем извлеченный опыт в формат, ожидаемый калькулятором
                    # Convert extracted experiences to format expected by calculator
                    experience_entries = []
                    for exp in extracted["experiences"]:
                        entry = {
                            "start": exp.get("start"),
                            "end": exp.get("end"),
                            "company": exp.get("company"),
                            "position": exp.get("title"),
                            "description": exp.get("description"),
                        }
                        experience_entries.append(entry)

                    # Вычисляем общий опыт из структурированных записей
                    # Calculate total experience from structured entries
                    calc_result = calculate_total_experience(experience_entries)
                    experience_months = calc_result.get("total_months", 0)

                    experience_result = {
                        "total_months": experience_months,
                        "total_years": round(experience_months / 12, 1) if experience_months else 0,
                        "total_years_formatted": format_experience_summary(calc_result),
                        "entries": extracted["experiences"],
                        "entry_count": extracted["total_count"],
                    }
                else:
                    # Структурированный опыт не найден, возвращаем нули
                    # No structured experiences found, return zeros
                    experience_result = {
                        "total_months": 0,
                        "total_years": 0,
                        "total_years_formatted": "No experience data found / Данные об опыте не найдены",
                        "entries": None,
                        "entry_count": 0,
                    }
                    if extracted.get("error"):
                        logger.warning(f"Experience extraction error: {extracted['error']} / "
                                       f"Ошибка извлечения опыта: {extracted['error']}")

            except Exception as e:
                logger.warning(f"Experience calculation failed: {e} / Сбой вычисления опыта: {e}")
                experience_result = {
                    "total_months": 0,
                    "total_years": 0,
                    "total_years_formatted": "Experience calculation failed / Сбой вычисления опыта",
                    "entries": None,
                    "entry_count": 0,
                }

        if detect_errors:
            try:
                errors_result = detect_resume_errors(resume_text)
            except Exception as e:
                logger.warning(f"Error detection failed: {e} / Сбой обнаружения ошибок: {e}")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "resume_id": resume_id,
            "status": "completed",
            "language": language,
            "keywords": keywords_result,
            "entities": {"technical_skills": entities},
            "grammar": grammar_result,
            "experience": experience_result,
            "errors": errors_result,
            "processing_time_ms": processing_time_ms,
        }

        # Преобразуем типы numpy в собственные типы Python для JSON-сериализации
        # Convert numpy types to Python native types for JSON serialization
        result = convert_numpy_types(result)

        logger.info(f"Resume core analysis completed in {processing_time_ms}ms / "
                    f"Основной анализ резюме завершен за {processing_time_ms}мс")
        return result

    except Exception as e:
        logger.error(f"Unexpected error in resume core analysis: {e} / "
                     f"Неожиданная ошибка в основном анализе резюме: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.analysis_task.analyze_resume_async",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def analyze_resume_async(
    self,
    resume_id: str,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Asynchronously analyze a resume with progress tracking.

    Асинхронно проанализировать резюме с отслеживанием прогресса.

    This is a Celery wrapper around analyze_resume_core that provides
    progress updates via Celery's update_state mechanism.
    Это обертка Celery вокруг analyze_resume_core, которая предоставляет
    обновления прогресса через механизм update_state Celery.

    Args:
        self: Экземпляр задачи Celery (bind=True) / Celery task instance (bind=True)
        resume_id: Уникальный идентификатор резюме для анализа
                   Unique identifier of the resume to analyze
        check_grammar: Выполнять ли проверку грамматики / Whether to perform grammar checking
        extract_experience: Вычислять ли опыт работы / Whether to calculate experience
        detect_errors: Обнаруживать ли ошибки в резюме / Whether to detect resume errors

    Returns:
        Dict[str, Any]: Словарь с результатами анализа / Dictionary containing analysis results
    """
    total_steps = 3

    try:
        # Шаг 1: Поиск резюме / Step 1: Finding resume
        progress = {
            "current": 1,
            "total": total_steps,
            "percentage": 33,
            "status": "finding_resume",
            "message": "Locating resume file... / Поиск файла резюме...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Шаг 2: Анализ / Step 2: Analyzing
        progress = {
            "current": 2,
            "total": total_steps,
            "percentage": 66,
            "status": "analyzing",
            "message": "Analyzing resume... / Анализ резюме...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Вызываем функцию основного анализа / Call core analysis function
        result = analyze_resume_core(
            resume_id=resume_id,
            check_grammar=check_grammar,
            extract_experience=extract_experience,
            detect_errors=detect_errors,
        )

        # Шаг 3: Завершение / Step 3: Complete
        progress = {
            "current": 3,
            "total": total_steps,
            "percentage": 100,
            "status": "complete",
            "message": "Analysis complete / Анализ завершен",
        }
        self.update_state(state="PROGRESS", meta=progress)

        return result

    except SoftTimeLimitExceeded:
        # Обработка превышения мягкого лимита времени / Handle soft time limit exceeded
        logger.error(f"Resume analysis task exceeded time limit for resume_id: {resume_id}")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Analysis timeout / Превышено время анализа",
            "processing_time_ms": 0,
        }
    except Exception as e:
        logger.error(f"Unexpected error in resume analysis: {e} / "
                     f"Неожиданная ошибка при анализе резюме: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": 0,
        }


@shared_task(
    name="tasks.analysis_task.batch_analyze_resumes",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
)
def batch_analyze_resumes(
    self,
    resume_ids: List[str],
    check_grammar: bool = True,
    extract_experience: bool = True,
) -> Dict[str, Any]:
    """
    Asynchronously analyze multiple resumes in batch.

    Асинхронно проанализировать несколько резюме пакетом.

    This task processes multiple resumes sequentially, tracking progress
    across the entire batch. Useful for analyzing multiple resumes at once.
    Эта задача обрабатывает несколько резюме последовательно, отслеживая прогресс
    по всему пакету. Полезно для одновременного анализа нескольких резюме.

    Args:
        self: Экземпляр задачи Celery (bind=True) / Celery task instance (bind=True)
        resume_ids: Список идентификаторов резюме для анализа
                    List of resume identifiers to analyze
        check_grammar: Выполнять ли проверку грамматики / Whether to perform grammar checking (default: True)
        extract_experience: Вычислять ли опыт работы / Whether to calculate experience (default: True)

    Returns:
        Dict[str, Any]: Словарь с результатами пакетного анализа:
                       Dictionary containing batch analysis results:
        - total_resumes: Общее количество резюме для обработки / Total number of resumes to process
        - successful: Количество успешно проанализированных резюме / Number of successfully analyzed resumes
        - failed: Количество неудачных анализов / Number of failed analyses
        - results: Список индивидуальных результатов анализа / List of individual analysis results

    Example:
        >>> from tasks import batch_analyze_resumes
        >>> task = batch_analyze_resumes.delay(["abc123", "def456"])
        >>> result = task.get()
        >>> print(result['successful'])
        2
    """
    logger.info(f"Starting batch analysis for {len(resume_ids)} resumes / "
                f"Начало пакетного анализа {len(resume_ids)} резюме")

    results = []
    successful = 0
    failed = 0

    for i, resume_id in enumerate(resume_ids):
        logger.info(f"Processing resume {i + 1}/{len(resume_ids)}: {resume_id} / "
                    f"Обработка резюме {i + 1}/{len(resume_ids)}: {resume_id}")

        # Обновляем прогресс для пакета (безопасно - игнорируем, если task_id недоступен)
        # Update progress for batch (safe - ignore if task_id is not available)
        try:
            progress = {
                "current": i + 1,
                "total": len(resume_ids),
                "percentage": int((i + 1) / len(resume_ids) * 100),
                "status": "processing_batch",
                "message": f"Analyzing resume {i + 1}/{len(resume_ids)}... / "
                          f"Анализ резюме {i + 1}/{len(resume_ids)}...",
            }
            self.update_state(state="PROGRESS", meta=progress)
        except (ValueError, AttributeError):
            # У задачи может не быть валидного ID (например, при вызове как подзадачи)
            # Task might not have a valid ID (e.g., when called as subtask)
            pass

        # Анализируем отдельное резюме / Analyze individual resume
        try:
            # Вызываем функцию основного анализа напрямую (не как задачу Celery)
            # Call the core analysis function directly (not as Celery task)
            result = analyze_resume_core(
                resume_id=resume_id,
                check_grammar=check_grammar,
                extract_experience=extract_experience,
                detect_errors=True,
            )
            results.append(result)

            if result.get("status") == "completed":
                successful += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Failed to analyze resume {resume_id}: {e} / "
                        f"Не удалось проанализировать резюме {resume_id}: {e}", exc_info=True)
            results.append({
                "resume_id": resume_id,
                "status": "failed",
                "error": str(e),
            })
            failed += 1

    logger.info(f"Batch analysis completed: {successful} successful, {failed} failed / "
                f"Пакетный анализ завершен: {successful} успешно, {failed} с ошибкой")

    return {
        "total_resumes": len(resume_ids),
        "successful": successful,
        "failed": failed,
        "results": results,
    }

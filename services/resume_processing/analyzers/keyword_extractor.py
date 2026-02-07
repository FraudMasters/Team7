"""
Извлечение ключевых слов из текста резюме с использованием KeyBERT.

# Русский комментарий:
Этот модуль предоставляет функции для извлечения релевантных ключевых слов
и ключевых фраз из текста резюме с использованием BERT-встраиваний
для контекстуального понимания.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Глобальный экземпляр модели для избежания перезагрузки при каждом вызове
_kw_model: Optional["KeyBERT"] = None


def _get_model(model_name: str = "distilbert-base-nli-mean-tokens") -> "KeyBERT":
    """
    Получить или инициализировать модель KeyBERT.

    Аргументы:
        model_name: Имя модели sentence-transformers для использования

    Возвращает:
        Инициализированный экземпляр модели KeyBERT

    Исключения:
        ImportError: Если keybert не установлен
        RuntimeError: Если не удалось загрузить модель
    """
    global _kw_model

    if _kw_model is None:
        try:
            from keybert import KeyBERT

            logger.info(f"Загрузка модели KeyBERT: {model_name}")
            _kw_model = KeyBERT(model=model_name)
            logger.info("Модель KeyBERT успешно загружена")
        except ImportError as e:
            raise ImportError(
                "KeyBERT не установлен. Установите его: pip install keybert"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить модель KeyBERT: {e}") from e

    return _kw_model


def extract_keywords(
    text: str,
    *,
    keyphrase_ngram_range: Tuple[int, int] = (1, 2),
    stop_words: Union[str, List[str], None] = "english",
    top_n: int = 20,
    min_score: float = 0.0,
    use_maxsum: bool = False,
    use_mmr: bool = True,
    diversity: float = 0.5,
    model_name: str = "distilbert-base-nli-mean-tokens",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Извлечь ключевые слова из текста с использованием KeyBERT.

    KeyBERT использует BERT-встраивания для поиска наиболее релевантных
    ключевых слов и ключевых фраз в документе. Извлекает кандидатов на основе
    косинусного сходства между документом и кандидатами в ключевые слова/фразы.

    Аргументы:
        text: Входной текст для извлечения ключевых слов
        keyphrase_ngram_range: Минимальный и максимальный размер n-gram для ключевых фраз
            - (1, 1) только отдельные слова
            - (1, 2) отдельные слова и биграммы (по умолчанию)
            - (2, 3) только биграммы и триграммы
        stop_words: Стоп-слова для удаления
            - 'english' для английских стоп-слов (по умолчанию)
            - 'russian' для русских стоп-слов
            - None для отключения удаления стоп-слов
            - Пользовательский список стоп-слов
        top_n: Количество возвращаемых топ ключевых слов
        min_score: Минимальный порог сходства (0.0 - 1.0)
        use_maxsum: Использовать Max Sum Similarity для разнообразных ключевых слов
        use_mmr: Использовать Maximal Marginal Relevance (по умолчанию: True)
        diversity: Параметр разнообразия MMR (0.0 - 1.0), выше = более разнообразно
        model_name: Имя модели sentence-transformers

    Возвращает:
        Словарь содержащий:
            - keywords: Список извлеченных ключевых слов (без оценок)
            - keywords_with_scores: Список кортежей (ключевое слово, оценка)
            - count: Количество извлеченных ключевых слов
            - model: Использованная модель
            - error: Сообщение об ошибке, если извлечение не удалось

    Исключения:
        ValueError: Если текст пустой или переданы неверные параметры
        RuntimeError: Если не удалось загрузить модель или извлечь ключевые слова

    Примеры:
        >>> text = "Иван Иванов - Python разработчик с опытом работы в Django..."
        >>> result = extract_keywords(text, top_n=5)
        >>> print(result["keywords"])
        ['Python', 'Django', 'разработчик', 'опыт']
        >>> print(result["keywords_with_scores"])
        [('Python', 0.85), ('Django', 0.78), ('разработчик', 0.72)]

        Извлечение ключевых фраз вместо отдельных слов:
        >>> result = extract_keywords(text, keyphrase_ngram_range=(2, 3), top_n=5)

        Извлечение из русского текста:
        >>> result = extract_keywords(russian_text, stop_words='russian')
    """
    # Валидация входных данных
    if not text or not isinstance(text, str):
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Текст должен быть непустой строкой",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Текст слишком короткий для извлечения ключевых слов (минимум 10 символов)",
        }

    # Валидация параметров
    if not isinstance(keyphrase_ngram_range, tuple) or len(keyphrase_ngram_range) != 2:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "keyphrase_ngram_range должен быть кортежем (min, max)",
        }

    if keyphrase_ngram_range[0] < 1 or keyphrase_ngram_range[1] < keyphrase_ngram_range[0]:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Неверные значения keyphrase_ngram_range",
        }

    if top_n < 1:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "top_n должен быть не менее 1",
        }

    if not 0.0 <= min_score <= 1.0:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "min_score должен быть между 0.0 и 1.0",
        }

    if not 0.0 <= diversity <= 1.0:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "diversity должен быть между 0.0 и 1.0",
        }

    try:
        # Получить или инициализировать модель
        model = _get_model(model_name)

        # Извлечь ключевые слова
        logger.info(
            f"Извлечение ключевых слов из текста (длина={len(text)}, top_n={top_n}, "
            f"ngram_range={keyphrase_ngram_range})"
        )

        keywords_with_scores = model.extract_keywords(
            text,
            keyphrase_ngram_range=keyphrase_ngram_range,
            stop_words=stop_words,
            top_n=top_n,
            use_maxsum=use_maxsum,
            use_mmr=use_mmr,
            diversity=diversity,
        )

        # Фильтрация по min_score (KeyBERT не всегда учитывает параметр min_score)
        if min_score > 0.0:
            keywords_with_scores = [
                (kw, score) for kw, score in keywords_with_scores if score >= min_score
            ]

        # Извлечь только ключевые слова без оценок
        keywords = [kw for kw, _ in keywords_with_scores]

        logger.info(f"Извлечено {len(keywords)} ключевых слов из текста")

        return {
            "keywords": keywords if keywords else None,
            "keywords_with_scores": keywords_with_scores if keywords_with_scores else None,
            "count": len(keywords),
            "model": model_name,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Ошибка импорта при извлечении ключевых слов: {e}")
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Ошибка импорта: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Не удалось извлечь ключевые слова: {e}")
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Извлечение не удалось: {str(e)}",
        }


def extract_top_skills(
    text: str,
    top_n: int = 10,
    min_score: float = 0.3,
    language: str = "english",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Извлечь топ навыков из текста резюме с использованием извлечения ключевых слов.

    Это удобная функция, оптимизированная для извлечения навыков из резюме.
    Она использует биграммы и триграммы для захвата многословных навыков
    (например, "machine learning", "natural language processing").

    Аргументы:
        text: Текст резюме для извлечения навыков
        top_n: Количество возвращаемых топ навыков (по умолчанию: 10)
        min_score: Минимальная оценка сходства (по умолчанию: 0.3)
        language: Язык для стоп-слов ('english' или 'russian')

    Возвращает:
        Словарь содержащий:
            - skills: Список извлеченных навыков (без оценок)
            - skills_with_scores: Список кортежей (навык, оценка)
            - count: Количество извлеченных навыков
            - error: Сообщение об ошибке, если извлечение не удалось

    Примеры:
        >>> text = "Навыки: Python, Django, PostgreSQL, Machine Learning..."
        >>> result = extract_top_skills(text, top_n=5)
        >>> print(result["skills"])
        ['Machine Learning', 'Python', 'Django', 'PostgreSQL']
    """
    # Отображение языка на стоп-слова
    stop_words_map = {
        "english": "english",
        "russian": "russian",
        "en": "english",
        "ru": "russian",
    }

    stop_words = stop_words_map.get(language.lower(), "english")

    result = extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),  # Включить многословные навыки
        stop_words=stop_words,
        top_n=top_n,
        min_score=min_score,
        use_mmr=True,
        diversity=0.5,
    )

    # Адаптировать формат результата
    return {
        "skills": result.get("keywords"),
        "skills_with_scores": result.get("keywords_with_scores"),
        "count": result.get("count", 0),
        "error": result.get("error"),
    }


def extract_resume_keywords(
    resume_text: str,
    language: str = "english",
    include_keyphrases: bool = True,
) -> Dict[str, Optional[Union[List[str], Dict[str, List[Tuple[str, float]]], str]]]:
    """
    Извлечь ключевые слова, оптимизированные для анализа резюме.

    Эта функция выполняет несколько стратегий извлечения для захвата:
    - Отдельных технических навыков
    - Многословных ключевых фраз
    - Инструментов и технологий

    Аргументы:
        resume_text: Полный текст резюме
        language: Язык документа ('english' или 'russian')
        include_keyphrases: Включать ли многословные фразы

    Возвращает:
        Словарь содержащий:
            - single_words: Список однословных ключевых слов с оценками
            - keyphrases: Список многословных фраз с оценками
            - all_keywords: Объединенный список всех извлеченных ключевых слов
            - error: Сообщение об ошибке, если извлечение не удалось

    Примеры:
        >>> result = extract_resume_keywords(resume_text, language="english")
        >>> print(result["all_keywords"])
        ['Python', 'Machine Learning', 'Django', 'REST API']
    """
    try:
        # Извлечь отдельные слова (униграммы)
        single_result = extract_keywords(
            resume_text,
            keyphrase_ngram_range=(1, 1),
            stop_words=language,
            top_n=15,
            min_score=0.25,
            use_mmr=True,
            diversity=0.4,
        )

        if single_result.get("error"):
            return {
                "single_words": None,
                "keyphrases": None,
                "all_keywords": None,
                "error": single_result["error"],
            }

        single_words = single_result.get("keywords_with_scores") or []

        keyphrases = []
        if include_keyphrases:
            # Извлечь многословные фразы (биграммы и триграммы)
            phrase_result = extract_keywords(
                resume_text,
                keyphrase_ngram_range=(2, 3),
                stop_words=language,
                top_n=10,
                min_score=0.3,
                use_mmr=True,
                diversity=0.5,
            )

            if phrase_result.get("error"):
                logger.warning(f"Извлечение фраз не удалось: {phrase_result['error']}")
            else:
                keyphrases = phrase_result.get("keywords_with_scores") or []

        # Объединить и удалить дубликаты
        all_keywords = [kw for kw, _ in single_words] + [
            kw for kw, _ in keyphrases
        ]

        # Удалить дубликаты с сохранением порядка
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)

        return {
            "single_words": single_words,
            "keyphrases": keyphrases,
            "all_keywords": unique_keywords,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Извлечение ключевых слов резюме не удалось: {e}")
        return {
            "single_words": None,
            "keyphrases": None,
            "all_keywords": None,
            "error": f"Извлечение не удалось: {str(e)}",
        }

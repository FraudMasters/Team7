"""
Извлечение опыта работы из текста резюме с использованием NLP и сопоставления шаблонов.

# Русский комментарий:
Этот модуль предоставляет функции для извлечения структурированных записей об опыте работы
из текста резюме, включая названия компаний, должности, даты и описания.
Использует SpaCy NER для извлечения сущностей и сопоставление шаблонов для структуры резюме.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Шаблоны для идентификации заголовков секций опыта работы
_EXPERIENCE_SECTION_PATTERNS = [
    r"work\s+experience",
    r"employment\s+history",
    r"professional\s+experience",
    r"work\s+history",
    r"experience",
    r"career\s+history",
    r"professional\s+background",
    # Русские шаблоны
    r"опыт\s+работы",
    r"трудовая\s+биография",
    r"профессиональный\s+опыт",
    r"опыт",
]

# Скомпилированный regex для секций опыта
_EXPERIENCE_SECTION_REGEX = re.compile(
    "|".join(_EXPERIENCE_SECTION_PATTERNS),
    re.IGNORECASE | re.MULTILINE
)

# Шаблоны для диапазонов дат в записях об опыте
# ВАЖНО: Более специфичные шаблоны должны идти ПЕРЕД менее специфичными
# например, MM/YYYY перед YYYY чтобы избежать совпадения только года
_DATE_RANGE_PATTERNS = [
    # Английские форматы - более специфичные сначала
    r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*(?:–|-|to|—)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|present|current|now)",
    r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\s*(?:–|-|to|—)\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|present|current|now)",
    r"(\d{4}-\d{2})\s*(?:–|-|to|—)\s*(\d{4}-\d{2}|present|current|now)",  # YYYY-MM - YYYY-MM
    r"(\d{1,2}/\d{4})\s*(?:–|-|to|—)\s*(\d{1,2}/\d{4}|present|current|now)",  # MM/YYYY - MM/YYYY
    r"(\d{4})\s{2,}(\d{4}|present|current|now)",  # YYYY  YYYY (double space, no dash)
    r"(\d{4})\s*(?:–|-|to|—)\s*(\d{4}|present|current|now)",  # YYYY - YYYY

    # Русские форматы - более специфичные сначала
    r"(\d{1,2}\.\d{4})\s*(?:–|-|—)\s*(\d{1,2}\.\d{4}|по настоящее время|настоящее|сейчас)",  # MM.YYYY - MM.YYYY (Russian)
    r"(?:с|по)\s+(\d{1,2})\s+(?:мес\.|месяцев)\.?\s*(\d{4})",  # с 5 мес. 2021 (since X months YYYY)
    r"(\d{4})\s{2,}(\d{4}|по настоящее время|настоящее|сейчас)",  # YYYY  YYYY (Russian)
    r"(\d{4})\s*(?:–|-|—)\s*(\d{4}|по настоящее время|настоящее|сейчас)",  # YYYY - YYYY (Russian)
]

_DATE_RANGE_REGEX = re.compile(
    "|".join(_DATE_RANGE_PATTERNS),
    re.IGNORECASE
)

# Шаблоны для обнаружения встроенных строк опыта (дата + должность + компания на одной строке)
_INLINE_EXPERIENCE_PATTERNS = [
    # YYYY  now/present/current Title, Company (location)
    r"^(\d{4})\s{2,}(now|present|current|настоящ|сейчас)\s+(.+?),\s*([^,(]+?)(?:\s*\(|$)",
    # YYYY - YYYY/present/current Title, Company (location)
    r"^(\d{4})\s*(?:–|-|—)\s*(\d{4}|now|present|current|настоящ)\s+(.+?),\s*([^,(]+?)(?:\s*\(|$)",
    # MM/YYYY - MM/YYYY Title, Company
    r"^(\d{1,2}/\d{4})\s*(?:–|-|—)\s*(\d{1,2}/\d{4}|now|present|current)\s+(.+?),\s*([^,(]+?)(?:\s*\(|$)",
    # Russian: MM.YYYY - MM.YYYY Title, Company
    r"^(\d{1,2}\.\d{4})\s*(?:–|-|—)\s*(\d{1,2}\.\d{4}|по настоящее время|настоящее|сейчас)\s+(.+?),\s*([^,(]+?)(?:\s*\(|$)",
    # YYYY  YYYY (double space) Title, Company
    r"^(\d{4})\s{2,}(\d{4})\s+(.+?),\s*([^,(]+?)(?:\s*\(|$)",
]

_INLINE_EXPERIENCE_REGEX = re.compile(
    "|".join(_INLINE_EXPERIENCE_PATTERNS),
    re.IGNORECASE
)

# Шаблон для извлечения должности и компании из строки после даты
# Совпадает: "Title, Company (location)" или "Title, Company"
_TITLE_COMPANY_PATTERN = re.compile(
    r"^(.+?),\s*([^,(]+?)(?:\s*\(|$)",
    re.IGNORECASE
)

# Глобальный кэш модели SpaCy
_nlp_model: Optional["spacy.language.Language"] = None


def _get_spacy_model(language: str = "en") -> "spacy.language.Language":
    """
    Получить или инициализировать модель SpaCy для указанного языка.

    Аргументы:
        language: Код языка ('en' для английского, 'ru' для русского)

    Возвращает:
        Инициализированный экземпляр модели SpaCy

    Исключения:
        ImportError: Если spaCy не установлен
        RuntimeError: Если не удалось загрузить модель
    """
    global _nlp_model

    # Нормализация кода языка
    lang_map = {
        "english": "en",
        "en": "en",
        "russian": "ru",
        "ru": "ru",
    }
    lang = lang_map.get(language.lower(), "en")

    if _nlp_model is None:
        try:
            import spacy

            # Отображение имен моделей
            model_names = {
                "en": "en_core_web_sm",
                "ru": "ru_core_news_sm",
            }

            model_name = model_names.get(lang, "en_core_web_sm")

            logger.info(f"Загрузка модели SpaCy: {model_name} для языка: {lang}")

            try:
                _nlp_model = spacy.load(model_name)
            except OSError:
                raise RuntimeError(
                    f"Модель SpaCy '{model_name}' не найдена. "
                    f"Загрузите её: python -m spacy download {model_name}"
                )

            logger.info(f"Модель SpaCy {model_name} успешно загружена")

        except ImportError as e:
            raise ImportError(
                "SpaCy не установлен. Установите его: pip install spacy"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить модель SpaCy: {e}") from e

    return _nlp_model


def _identify_experience_sections(
    text: str
) -> List[Tuple[int, int]]:
    """
    Идентифицировать начальные и конечные позиции секций опыта работы в тексте резюме.

    Аргументы:
        text: Текст резюме для поиска

    Возвращает:
        Список кортежей (start_pos, end_pos) для каждой найденной секции опыта
    """
    sections = []

    # Найти все заголовки секций опыта
    for match in _EXPERIENCE_SECTION_REGEX.finditer(text):
        start = match.start()

        # Найти конец этой секции (следующий заголовок секции или конец текста)
        remaining_text = text[match.end():]
        next_match = _EXPERIENCE_SECTION_REGEX.search(remaining_text)

        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(text)

        sections.append((start, end))

    return sections


def _parse_experience_date(date_str: Optional[str]) -> Optional[str]:
    """
    Парсить различные форматы дат в формат ISO (YYYY-MM-DD).

    Поддерживаемые форматы:
    - MM/YYYY, MM.YYYY (русский)
    - YYYY-MM, YYYY
    - Month YYYY (например, "May 2020", "Май 2020")
    - YYYY
    - "Present", "Current", "Now" (возвращает None)
    - Русский: "по настоящее время", "настоящее", "сейчас"

    Аргументы:
        date_str: Строка даты для парсинга

    Возвращает:
        Строка даты в формате ISO (YYYY-MM-DD) или None для текущих позиций

    Примеры:
        >>> _parse_experience_date("01/2020")
        '2020-01-01'
        >>> _parse_experience_date("May 2020")
        '2020-05-01'
        >>> _parse_experience_date("present")
        None
        >>> _parse_experience_date("сейчас")
        None
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # Проверка индикаторов текущего времени (английский и русский)
    current_indicators = [
        "present", "current", "now",
        "сейчас", "настоящее", "по настоящее время",  # Russian
        "по сей день",  # Русский альтернативный вариант
    ]
    current_regex = "|".join(map(re.escape, current_indicators))
    if re.match(f"^({current_regex})$", date_str, re.IGNORECASE):
        return None

    # Удалить общие русские суффиксы
    date_str = re.sub(r"\s+г\.$", "", date_str)  # Удалить " г." в конце

    # Список форматов дат для попытки (английский и русский)
    formats = [
        "%Y-%m-%d",  # 2023-02-01
        "%Y-%m",    # 2023-02
        "%m/%Y",    # 02/2023
        "%m.%Y",    # 02.2023 (русский)
        "%b %Y",    # Feb 2023
        "%B %Y",    # February 2023
        "%Y",        # 2023
    ]

    # Русские названия месяцев (все строчные префиксы для сопоставления)
    ru_months = [
        ("январ", "January"),
        ("феврал", "February"),
        ("март", "March"),
        ("апрел", "April"),
        ("май", "May"),
        ("июн", "June"),
        ("июл", "July"),
        ("август", "August"),
        ("сентяб", "September"),
        ("октяб", "October"),
        ("нояб", "November"),
        ("декаб", "December"),
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            # Попытка с русскими названиями месяцев
            for ru_month, en_month in ru_months:
                if ru_month.lower() in date_str.lower():
                    try:
                        translated = date_str.lower().replace(ru_month.lower(), en_month.lower())
                        parsed_date = datetime.strptime(translated, fmt)
                        return parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            continue

    logger.warning(f"Не удалось распарсить дату: {date_str}")
    return None


def _extract_date_range(text: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Извлечь начальную и конечную даты из строки текста.

    Аргументы:
        text: Строка текста содержащая информацию о дате

    Возвращает:
        Словарь с 'start' и 'end' строками даты или None если даты не найдены
    """
    match = _DATE_RANGE_REGEX.search(text)
    if not match:
        return None

    # Извлечь две группы дат
    # Поскольку у нас несколько шаблонов объединенных через |, группы находятся на разных позициях
    # Нужно отфильтровать значения None для получения реальных захваченных групп
    groups = [g for g in match.groups() if g is not None]

    if len(groups) >= 2:
        start_date = _parse_experience_date(groups[0])
        end_date = _parse_experience_date(groups[1])

        return {
            "start": start_date,
            "end": end_date,
        }

    return None


def _calculate_confidence_score(
    entry: Dict[str, Optional[str]],
    has_org_entity: bool,
    has_date_entity: bool
) -> float:
    """
    Вычислить оценку уверенности для извлеченной записи об опыте.

    Оценка основана на полноте сущностей (компания, должность, даты, описание)
    и увеличивается когда NER подтверждает типы сущностей.

    Система оценки:
    - Компания: 0.3 (полная), 0.15 (частичная/короткая)
    - Должность: 0.3 (полная), 0.15 (частичная/короткая)
    - Даты: 0.2 (start + end), 0.1 (только start)
    - Описание: 0.2 (существенное), 0.1 (минимальное)
    - Бонус NER: +0.05 за каждый подтвержденный тип сущности

    Аргументы:
        entry: Словарь записи об опыте с ключами: company, title, start, end, description
        has_org_entity: Найдена ли сущность ORG NER
        has_date_entity: Найдена ли сущность DATE NER

    Возвращает:
        Оценка уверенности между 0.0 и 1.0

    Примеры:
        >>> entry = {"company": "Google", "title": "Senior Engineer", "start": "2020-01-01", "end": None, "description": "Руководил командой..."}
        >>> score = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)
        >>> >>> 0.85 < score < 1.0  # Высокая уверенность для полной записи с подтверждением NER
        >>> entry2 = {"company": "G", "title": "Eng", "start": "2020-01-01", "end": None, "description": ""}
        >>> score2 = _calculate_confidence_score(entry2, has_org_entity=False, has_date_entity=False)
        >>> >>> 0.3 < score2 < 0.5  # Нижняя уверенность для частичной записи
    """
    score = 0.0

    # Оценка компании (0.3 max)
    company = entry.get("company")
    if company:
        company_len = len(company.strip())
        if company_len > 2:
            score += 0.3  # Полные баллы за существенное название компании
        elif company_len > 0:
            score += 0.15  # Частичные баллы за очень короткое название

    # Оценка должности (0.3 max)
    title = entry.get("title")
    if title:
        title_len = len(title.strip())
        if title_len > 2:
            score += 0.3  # Полные баллы за существующую должность
        elif title_len > 0:
            score += 0.15  # Частичные баллы за очень короткую должность

    # Оценка дат (0.2 max)
    if entry.get("start"):
        score += 0.1  # Начальная дата
        if entry.get("end") is not None:  # Может быть None для текущих позиций
            score += 0.1  # Конечная дата (когда присутствует)
    elif entry.get("end") is not None:
        # Есть конечная дата но нет начальной (необычно но возможно)
        score += 0.05

    # Оценка описания (0.2 max)
    description = entry.get("description")
    if description:
        desc_len = len(description.strip())
        if desc_len > 50:
            score += 0.2  # Полные баллы за существенное описание
        elif desc_len > 20:
            score += 0.15  # Большинство баллов за умеренное описание
        elif desc_len > 0:
            score += 0.1  # Частичные баллы за минимальное описание

    # Бонусы подтверждения NER (до 0.1 всего)
    if has_org_entity:
        score += 0.05
    if has_date_entity:
        score += 0.05

    # Ограничить до 1.0
    return min(1.0, score)


def _extract_experience_entries(
    section_text: str,
    nlp: "spacy.language.Language"
) -> List[Dict[str, Optional[str]]]:
    """
    Извлечь отдельные записи об опыте из секции опыта работы.

    Обрабатывает несколько форматов резюме:
    - Встроенный: "2021  now Full-Stack Developer, Inetex (Rehovot, Israel)"
    - Многострочный: Дата на одной строке, должность/компания на следующих строках
    - Русские форматы: "2019  2021 Java Developer, Company"

    Аргументы:
        section_text: Текст секции опыта работы
        nlp: Модель NLP SpaCy

    Возвращает:
        Список словарей записей об опыте
    """
    entries = []

    # Разбить на строки и обработать
    lines = section_text.split("\n")
    current_entry: Dict[str, Optional[str]] = {}
    description_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            # Пустая строка может указывать на конец записи
            if current_entry:
                if description_lines:
                    current_entry["description"] = " ".join(description_lines).strip()
                if current_entry.get("company") or current_entry.get("title"):
                    entries.append(current_entry)
                current_entry = {}
                description_lines = []
            continue

        # Сначала попытаться сопоставить встроенные шаблоны опыта (дата + должность + компания на одной строке)
        inline_match = _INLINE_EXPERIENCE_REGEX.search(line)
        if inline_match:
            # Сохранить предыдущую запись если существует
            if current_entry:
                if description_lines:
                    current_entry["description"] = " ".join(description_lines).strip()
                if current_entry.get("company") or current_entry.get("title"):
                    entries.append(current_entry)

            # Извлечь группы из совпадения
            groups = [g for g in inline_match.groups() if g is not None]

            start_date = None
            end_date = None
            title = None
            company = None

            if len(groups) >= 4:
                # Первые две группы - даты, третья - должность, четвертая - компания
                start_date = _parse_experience_date(groups[0])
                end_date = _parse_experience_date(groups[1])
                title = groups[2].strip() if groups[2] else None
                company = groups[3].strip() if groups[3] else None

            current_entry = {
                "start": start_date,
                "end": end_date,
                "title": title,
                "company": company,
            }
            description_lines = []
            continue

        # Проверить диапазон дат (может быть началом новой записи)
        date_range = _extract_date_range(line)

        if date_range:
            # Сохранить предыдущую запись если существует
            if current_entry:
                if description_lines:
                    current_entry["description"] = " ".join(description_lines).strip()
                if current_entry.get("company") or current_entry.get("title"):
                    entries.append(current_entry)

            # Начать новую запись с датами
            current_entry = {
                "start": date_range["start"],
                "end": date_range["end"],
            }
            description_lines = []

            # Попытаться извлечь должность/компанию из той же строки после дат
            date_match = _DATE_RANGE_REGEX.search(line)
            if date_match:
                after_date = line[date_match.end():].strip()

                # Попытка шаблона должность/компания
                title_company_match = _TITLE_COMPANY_PATTERN.search(after_date)
                if title_company_match:
                    potential_title = title_company_match.group(1).strip()
                    potential_company = title_company_match.group(2).strip()
                    if len(potential_title) > 2 and len(potential_company) > 2:
                        current_entry["title"] = potential_title
                        current_entry["company"] = potential_company
                        continue

            # Использовать NER для идентификации организаций если встроенный шаблон не сработал
            doc = nlp(line)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                current_entry["company"] = orgs[0]
        else:
            # Не строка с датой, может быть должность, компания или описание
            doc = nlp(line)

            # Проверка шаблона "Title at Company" (распространено в функциональных резюме)
            if " at " in line.lower() and not current_entry.get("company") and not current_entry.get("title"):
                parts = line.split(" at ", 1)
                if len(parts) == 2:
                    potential_title = parts[0].strip()
                    potential_company = parts[1].strip()
                    # Базовая валидация: обе части должны иметь разумную длину
                    if len(potential_title) > 2 and len(potential_company) > 2:
                        current_entry["title"] = potential_title
                        current_entry["company"] = potential_company
                        # Продолжить к следующей строке (не обрабатывать как ORG/description)
                        continue

            # Проверка шаблона "Title, Company"
            if ", " in line and not current_entry.get("company") and not current_entry.get("title"):
                title_company_match = _TITLE_COMPANY_PATTERN.search(line)
                if title_company_match:
                    potential_title = title_company_match.group(1).strip()
                    potential_company = title_company_match.group(2).strip()
                    if len(potential_title) > 2 and len(potential_company) > 2:
                        current_entry["title"] = potential_title
                        current_entry["company"] = potential_company
                        continue

            # Проверка сущностей организаций
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

            # Эвристика: если в строке есть org и в записи еще нет компании, это компания
            if orgs and not current_entry.get("company"):
                current_entry["company"] = orgs[0]

                # Остальное может быть должностью
                line_without_org = line.replace(orgs[0], "").strip()
                if line_without_org and len(line_without_org) > 3:
                    current_entry["title"] = line_without_org
            elif not current_entry.get("title") and not current_entry.get("company"):
                # Нет компании yet, это может быть строка должности
                # Поиск общих шаблонов должностей (английский и русский)
                title_keywords = [
                    "senior", "junior", "lead", "manager", "engineer", "developer",
                    "director", "analyst", "specialist", "consultant", "architect",
                    "старший", "младший", "руководитель", "менеджер", "разработчик",
                    "директор", "аналитик", "специалист", "консультант", "архитектор",
                ]
                if any(word in line.lower() for word in title_keywords):
                    current_entry["title"] = line
                else:
                    # Рассматривать как описание или компания/должность
                    if len(line) < 60:  # Вероятно должность/компания
                        if not current_entry.get("company"):
                            current_entry["company"] = line
                        else:
                            current_entry["title"] = line
                    else:
                        description_lines.append(line)
            else:
                # Добавить к описанию
                description_lines.append(line)

    # Не забыть последнюю запись
    if current_entry:
        if description_lines:
            current_entry["description"] = " ".join(description_lines).strip()
        if current_entry.get("company") or current_entry.get("title"):
            entries.append(current_entry)

    return entries


def extract_work_experience(
    text: str,
    *,
    language: str = "en",
    min_confidence: float = 0.3
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, float, None]]], str]]]:
    """
    Извлечь структированные записи об опыте работы из текста резюме.

    Эта функция использует SpaCy NER для извлечения организаций и дат,
    объединенных с сопоставлением шаблонов для идентификации секций опыта
    и парсинга отдельных записей. Возвращает список записей опыта с
    компанией, должностью, датами, описанием и оценками уверенности.

    Аргументы:
        text: Текст резюме для извлечения опыта
        language: Язык документа ('en', 'english', 'ru', 'russian')
        min_confidence: Минимальная оценка уверенности (0-1) для включения записей

    Возвращает:
        Словарь содержащий:
            - experiences: Список словарей записей опыта с:
                - company: Название компании (str или None)
                - title: Должность (str или None)
                - start: Начальная дата в формате ISO (str или None)
                - end: Конечная дата в формате ISO (str или None) - None для текущих позиций
                - description: Описание работы (str или None)
                - confidence: Оценка уверенности (float 0-1)
            - total_count: Количество извлеченных записей опыта
            - language: Использованный код языка
            - error: Сообщение об ошибке если извлечение не удалось

    Исключения:
        ValueError: Если текст пустой
        RuntimeError: Если не удалось загрузить модель

    Примеры:
        >>> text = '''
        ... Work Experience
        ...
        ... Senior Software Engineer at Google
        ... 05/2020 - Present
        ... Руководил разработкой облачной инфраструктуры...
        ...
        ... Software Developer at Microsoft
        ... 06/2018 - 04/2020
        ... Разрабатывал веб-приложения с использованием React...
        ... '''
        >>> result = extract_work_experience(text)
        >>> print(result["experiences"][0]["company"])
        'Google'
        >>> print(result["experiences"][0]["title"])
        'Senior Software Engineer'
        >>> print(result["experiences"][0]["start"])
        '2020-05-01'

        Извлечение из русского текста:
        >>> result = extract_work_experience(russian_text, language='ru')
    """
    # Валидация входных данных
    if not text or not isinstance(text, str):
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": "Текст должен быть непустой строкой",
        }

    text = text.strip()
    if len(text) < 50:
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": "Текст слишком короткий для извлечения опыта (минимум 50 символов)",
        }

    try:
        # Получить модель SpaCy
        nlp = _get_spacy_model(language)

        logger.info(
            f"Извлечение опыта работы из текста (длина={len(text)}, язык={language})"
        )

        # Идентифицировать секции опыта
        sections = _identify_experience_sections(text)

        if not sections:
            # Явная секция не найдена, попытаться извлечь из всего текста
            logger.info("Заголовки секций опыта не найдены, попытка извлечения из полного текста")
            sections = [(0, len(text))]

        all_entries = []

        # Извлечь записи из каждой секции
        for start, end in sections:
            section_text = text[start:end]
            entries = _extract_experience_entries(section_text, nlp)

            # Вычислить оценки уверенности
            for entry in entries:
                # Проверить найдены ли сущности NER
                entry_text = " ".join(filter(None, [
                    entry.get("company", ""),
                    entry.get("title", ""),
                    entry.get("description", "")
                ]))

                doc = nlp(entry_text)
                has_org = any(ent.label_ == "ORG" for ent in doc.ents)
                has_date = any(ent.label_ == "DATE" for ent in doc.ents)

                confidence = _calculate_confidence_score(entry, has_org, has_date)
                entry["confidence"] = confidence

            all_entries.extend(entries)

        # Фильтрация по минимальной уверенности
        filtered_entries = [
            entry for entry in all_entries
            if entry.get("confidence", 0) >= min_confidence
        ]

        logger.info(f"Извлечено {len(filtered_entries)} записей опыта работы")

        return {
            "experiences": filtered_entries if filtered_entries else None,
            "total_count": len(filtered_entries),
            "language": language,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Ошибка импорта при извлечении опыта: {e}")
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": f"Ошибка импорта: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Не удалось извлечь опыт работы: {e}")
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": f"Извлечение не удалось: {str(e)}",
        }


def _dates_overlap(
    period1_start: datetime,
    period1_end: Optional[datetime],
    period2_start: datetime,
    period2_end: Optional[datetime],
) -> bool:
    """
    Проверить пересекаются ли два временных периода.

    Аргументы:
        period1_start: Начальная дата периода 1
        period1_end: Конечная дата периода 1 (None означает текущую дату)
        period2_start: Начальная дата периода 2
        period2_end: Конечная дата периода 2 (None означает текущую дату)

    Возвращает:
        True если периоды пересекаются, иначе False

    Примеры:
        >>> from datetime import datetime
        >>> p1_start = datetime(2020, 1, 1)
        >>> p1_end = datetime(2020, 6, 1)
        >>> p2_start = datetime(2020, 5, 1)
        >>> p2_end = datetime(2020, 12, 1)
        >>> _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        True
    """
    if period1_end is None:
        period1_end = datetime.now()
    if period2_end is None:
        period2_end = datetime.now()

    # Проверка пересечения: max(start1, start2) <= min(end1, end2)
    latest_start = max(period1_start, period2_start)
    earliest_end = min(period1_end, period2_end)

    return latest_start <= earliest_end


def detect_overlaps(
    experiences: List[Dict[str, Optional[str]]]
) -> Dict[str, Union[int, List[Dict]]]:
    """
    Обнаружить пересекающиеся периоды работы в записях опыта.

    Аргументы:
        experiences: Список словарей записей опыта с начальными и конечными датами

    Возвращает:
        Словарь содержащий:
            - overlap_count: Количество найденных пересекающихся пар
            - overlaps: Список информации о пересечениях
            - concurrent_periods: Список периодов с параллельными позициями
            - error: Сообщение об ошибке если обнаружение не удалось

    Примеры:
        >>> experiences = [
        ...     {"start": "2020-01-01", "end": "2021-01-01"},
        ...     {"start": "2020-06-01", "end": "2021-06-01"},
        ... ]
        >>> result = detect_overlaps(experiences)
        >>> result["overlap_count"]
        1
    """
    try:
        if not experiences or len(experiences) < 2:
            return {
                "overlap_count": 0,
                "overlaps": [],
                "concurrent_periods": [],
                "error": None,
            }

        overlaps = []
        concurrent_periods = []

        # Конвертировать строковые даты в объекты datetime
        parsed_experiences = []
        for idx, exp in enumerate(experiences):
            start_str = exp.get("start")
            end_str = exp.get("end")

            if not start_str:
                continue

            try:
                start_date = datetime.fromisoformat(start_str) if start_str else None
                end_date = datetime.fromisoformat(end_str) if end_str else None
            except (ValueError, TypeError):
                continue

            parsed_experiences.append({
                "index": idx,
                "start": start_date,
                "end": end_date,
                "company": exp.get("company"),
                "title": exp.get("title"),
            })

        # Проверка пересечений
        for i, exp1 in enumerate(parsed_experiences):
            for exp2 in parsed_experiences[i + 1:]:
                # Получить даты (None означает текущее)
                start1 = exp1["start"]
                end1 = exp1.get("end") or datetime.now()
                start2 = exp2["start"]
                end2 = exp2.get("end") or datetime.now()

                # Проверка пересечения с использованием вспомогательной функции
                if _dates_overlap(start1, exp1.get("end"), start2, exp2.get("end")):
                    # Вычислить период пересечения
                    latest_start = max(start1, start2)
                    earliest_end = min(end1, end2)

                    overlap_info = {
                        "entry1": {
                            "index": exp1["index"],
                            "company": exp1.get("company"),
                            "title": exp1.get("title"),
                            "start": exp1["start"].isoformat(),
                            "end": exp1.get("end").isoformat() if exp1.get("end") else None,
                        },
                        "entry2": {
                            "index": exp2["index"],
                            "company": exp2.get("company"),
                            "title": exp2.get("title"),
                            "start": exp2["start"].isoformat(),
                            "end": exp2.get("end").isoformat() if exp2.get("end") else None,
                        },
                        "overlap_start": latest_start.isoformat(),
                        "overlap_end": earliest_end.isoformat(),
                    }
                    overlaps.append(overlap_info)

                    # Проверить представляет ли это параллельные позиции (разные компании)
                    if exp1.get("company") and exp2.get("company"):
                        if exp1.get("company") != exp2.get("company"):
                            concurrent_periods.append(overlap_info)

        return {
            "overlap_count": len(overlaps),
            "overlaps": overlaps,
            "concurrent_periods": concurrent_periods,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Не удалось обнаружить пересечения: {e}")
        return {
            "overlap_count": 0,
            "overlaps": [],
            "concurrent_periods": [],
            "error": str(e),
        }

# ML/NLP Pipeline — Детальное описание

Документ описывает, как система анализирует резюме и сопоставляет с вакансиями.

## Обзор пайплайна

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  PDF/DOCX      │───▶│ Text Extraction │───▶│   Analysis     │
│  Resume        │    │ (services/)     │    │   (Celery)      │
└────────────────┘    └────────────────┘    └────────────────┘
                                                   │
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │   Save Results to Database    │
                                    └──────────────────────────────┘
```

---

## 1. Извлечение текста (Text Extraction)

**Модуль**: `services/data_extractor/extract.py`

### Поддерживаемые форматы
- **PDF**: PyPDF2 (основной), pdfplumber (fallback)
- **DOCX**: python-docx

### Процесс

```python
# PDF извлечение
def extract_text_from_pdf(file_path):
    1. Проверяет существование файла
    2. Пробует PyPDF2
    3. Если текста мало → использует pdfplumber
    4. Возвращает {text, method, pages, error}

# DOCX извлечение
def extract_text_from_docx(file_path):
    1. Открывает документ через python-docx
    2. Извлекает все параграфы по порядку
    3. Возвращает {text, error}
```

### Обработка ошибок

| Ошибка | Действие |
|--------|----------|
| Файл не найден | FileNotFoundError |
| Повреждённый PDF | Возвращает пустой текст + error |
| Пустой документ | Возвращает warning |

---

## 2. Определение языка (Language Detection)

**Модуль**: `langdetect`

### Зачем нужно?

Разные языки требуют разных ML-моделей:
- **Английский**: `en_core_web_sm` SpaCy модель
- **Русский**: `ru_core_news_sm` SpaCy модель
- **Grammar**: разные правила LanguageTool

### Процесс

```python
from langdetect import detect

lang = detect(resume_text)  # 'en' или 'ru'
```

### Точность

- На коротких текстах (< 50 символов) может ошибаться
- На резюме обычно > 1000 символов → точность > 99%

---

## 3. Извлечение ключевых слов (Keyword Extraction)

**Модуль**: `backend/analyzers/keyword_extractor.py`

### Используемый метод: KeyBERT

KeyBERT использует BERT embeddings для поиска наиболее релевантных слов в документе.

### Процесс

```python
from keybert import KeyBERT

# 1. Загрузка модели (кешируется)
kw_model = KeyBERT(model='all-MiniLM-L6-v2')

# 2. Извлечение ключевых слов
keywords = kw_model.extract_keywords(
    text,
    keyphrase_ngram_range=(1, 2),  # 1-2 слова
    stop_words='english',  # или 'russian'
    top_n=10  # топ-10 ключевых слов
)
# Результат: [('python', 0.8), ('machine learning', 0.75), ...]
```

### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `keyphrase_ngram_range` | (1, 2) | Извлекать 1-2 слова |
| `stop_words` | multi | Учитывает стоп-слова |
| `top_n` | 10 | Количество ключевых слов |

### Фильтрация

После извлечения ключевые слова фильтруются:
- Убираются стоп-слова (and, or, the, и, или)
- Убираются цифры и спецсимволы
- Убираются слишком короткие (< 2 символов)

---

## 4. Named Entity Recognition (NER)

**Модуль**: `backend/analyzers/ner_extractor.py`

### Используемые модели

| Язык | SpaCy модель | Компоненты |
|-------|-------------|-------------|
| English | `en_core_web_sm` | PERSON, ORG, DATE, GPE |
| Russian | `ru_core_news_sm` | PERSON, ORG, DATE, LOC |

### Извлекаемые сущности

```python
# Пример для английского
doc = nlp("John Doe worked at Google from 2020 to 2023")

entities = {
    'persons': ['John Doe'],
    'organizations': ['Google'],
    'dates': ['2020', '2023'],
    'locations': []
}
```

### Процесс

1. **Токенизация**: Текст разбивается на предложения и токены
2. **POS Tagging**: Определяется часть речи каждого слова
3. **NER**: Модель помечает сущности (PER, ORG, DATE, ...)
4. **Пост-обработка**: Группируются дубликаты, очищаются артефакты

### Детектируемые сущности

| Тип | Примеры | Использование |
|-----|---------|---------------|
| PERSON | John Doe, Иванов Иван | Контактное лицо |
| ORG | Google, МТС | Компании |
| DATE | 2020-2023, Январь 2023 | Периоды работы |
| GPE/LOC | Москва, London | Локации |

---

## 5. Расчёт опыта работы (Experience Calculation)

**Модуль**: `backend/analyzers/experience_calculator.py`

### Алгоритм

```
1. Найти все даты в резюме
2. Сгруппировать в пары (from_date, to_date)
3. Рассчитать overlapping periods
4. Суммировать месяцы опыта
```

### Пример

```
Резюме:
- Google: 2020-01 — 2022-06 (2.5 года)
- Yandex:  2022-03 — 2023-12 (1.75 года)

Пересечение: март-июнь 2022 (4 месяца)

Общий опыт:
2.5 + 1.75 - 0.33 = 3.92 года = 47 месяцев
```

### Ключевые функции

```python
def calculate_experience(dates: List[Dict]) -> Dict:
    """
    Args:
        dates: [{'from': '2020-01', 'to': '2022-06', ...}]

    Returns:
        {
            'total_years': 3.92,
            'total_months': 47,
            'periods': [...],
            'overlap_months': 4
        }
    """
```

---

## 6. Проверка грамматики (Grammar Checking)

**Модуль**: `backend/analyzers/grammar_checker.py`

### Используемый сервис: LanguageTool

**API**: https://languagetool.org/api/v2/check

### Проверяемые ошибки

| Тип | Пример | Исправление |
|-----|--------|-------------|
| Grammar | "skills include Java Python" | "skills include Java, Python" |
| Spelling | "experiance" | "experience" |
| Style | "very good" | "excellent" |
| Punctuation | "Java,Python" | "Java, Python" |

### Процесс

```python
import requests

def check_grammar(text: str, lang: str):
    url = "https://api.languagetool.org/v2/check"
    response = requests.post(url, data={
        'text': text,
        'language': lang,  # 'en-US' или 'ru-RU'
        'enabledRules': 'GRAMMAR,SPELLING'
    })
    return response.json()['matches']
```

---

## 7. Обнаружение ошибок (Error Detection)

**Модуль**: `backend/analyzers/error_detector.py`

### Проверяемые проблемы

| Ошибка | Условие | Severity |
|--------|---------|----------|
| Missing email | Нет @ в тексте | error |
| Missing phone | Нет номера телефона | error |
| Too short | < 500 символов | warning |
| No portfolio | Junior + нет ссылки | warning |
| Date gaps | Пропуски > 6 месяцев | warning |

### Пример

```python
def detect_errors(resume_data: Dict) -> List[Dict]:
    errors = []

    # Проверка email
    if '@' not in resume_data['text']:
        errors.append({
            'type': 'missing_email',
            'severity': 'error',
            'message': 'Укажите email для связи'
        })

    # Проверка длины
    if len(resume_data['text']) < 500:
        errors.append({
            'type': 'too_short',
            'severity': 'warning',
            'message': 'Резюме слишком короткое'
        })

    return errors
```

---

## 8. Подбор вакансий (Job Matching)

**Модуль**: `backend/analyzers/enhanced_matcher.py`

### Алгоритм

```
┌─────────────────────────────────────────────────┐
│            SKILL NORMALIZATION                 │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│         COMPARE WITH VACANCY REQUIREMENTS       │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │ 1. Direct match (точное совпадение) │      │
│  │    "Java" === "Java"                  │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │ 2. Synonym match (синонимы)          │      │
│  │    "ReactJS" === "React"             │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │ 3. Related skills (связанные навыки) │      │
│  │    "Spring" → "Java"                 │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│              EXPERIENCE VERIFICATION            │
│                                                 │
│  Vacancy: "3+ years Java required"           │
│  Candidate: "5 years Java experience"         │
│  Result: ✅ Meets requirement                │
└─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│              MATCH PERCENTAGE CALCULATION        │
│                                                 │
│  matched_skills / total_required * 100         │
│  adjusted for experience and related skills    │
└─────────────────────────────────────────────────┘
```

### База синонимов

**Модуль**: `backend/api/skill_taxonomies.py`

Примеры синонимов:

| Канонический навык | Синонимы |
|-------------------|----------|
| SQL | PostgreSQL, Postgres, psql, mysql |
| React | ReactJS, React.js, ReactJS |
| JavaScript | JS, javascript, ECMAScript |
| Python | Python 3, py3 |
| Java | Java 8, Java 11, Java 17, J2EE |

### Формула расчёта

```python
def calculate_match(resume, vacancy):
    # 1. Прямое совпадение навыков
    direct_matches = vacancy.skills & resume.skills

    # 2. Синонимы
    synonym_matches = find_synonym_matches(vacancy.skills, resume.skills)

    # 3. Связанные навыки (опционально)
    related_matches = find_related_skills(vacancy.skills, resume.skills)

    # 4. Базовый процент
    base_percent = (direct_matches + synonym_matches) / vacancy.total_skills

    # 5. Корректировка на опыт
    for skill in vacancy.skills:
        required_years = get_required_years(skill)
        candidate_years = get_candidate_years(skill, resume)
        if candidate_years < required_years:
            base_percent -= 0.1  # штраф за недостаток опыта

    # 6. Бонус за связанные навыки
    base_percent += len(related_matches) * 0.05

    return max(0, min(100, base_percent * 100))
```

---

## 9. Асинхронная обработка (Celery)

**Конфигурация**: `backend/celery_app.py`

### Задачи (Tasks)

| Задача | Файл | Описание |
|-------|------|----------|
| `analyze_resume` | `tasks/analysis_task.py` | Полный анализ резюме |
| `send_email` | `tasks/email_task.py` | Отправка email |

### Процесс

```python
# 1. Создаём задачу
from celery_app.celery_app import celery_app

@celery_app.task
def analyze_resume_task(resume_id: str):
    # 2. Извлекаем текст
    resume = get_resume(resume_id)
    text = extract_text(resume.file_path)

    # 3. Запускаем анализ (может занять 1-2 минуты)
    result = run_full_analysis(text)

    # 4. Сохраняем результат
    save_analysis_result(resume_id, result)

    return result

# 5. API возвращает task_id
task = analyze_resume_task.delay(resume_id)
```

### Мониторинг

**Flower**: http://localhost:5555

- Вид активных задач
- Статистику выполнения
- Логи ошибок

---

## Настройка ML-модей

### Установка SpaCy моделей

```bash
# Английская модель
python -m spacy download en_core_web_sm

# Русская модель
python -m spacy download ru_core_news_sm
```

### Кеширование моделей

**Место**: `backend/models_cache/`

```python
# Модели загружаются один раз и кешируются
SPACY_MODELS = {
    'en': spacy.load('en_core_web_sm'),
    'ru': spacy.load('ru_core_news_sm')
}
```

---

## Оптимизация производительности

### 1. Кеширование SpaCy моделей

```python
import functools

@functools.lru_cache(maxsize=1)
def get_spacy_model(lang):
    return spacy.load(f'{lang}_core_web_sm')
```

### 2. Пакетная обработка (Batching)

Для большого количества резюме:

```python
# Обработка по 10 резюме за раз
results = process_batch(resume_ids, batch_size=10)
```

### 3. Приоритезация Celery

```python
# High priority для платных пользователей
@celery_app.task(priority=5)
def analyze_resume_premium(resume_id):
    pass

# Low priority для бесплатных
@celery_app.task(priority=9)
def analyze_resume_free(resume_id):
    pass
```

---

## Мониторинг и логирование

### Логи пайплайна

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Starting analysis for resume {resume_id}")
logger.debug(f"Detected language: {lang}")
logger.error(f"Failed to extract text: {error}")
```

### Метрики

| Метрика | Цель | Текущее |
|---------|------|---------|
| Точность NER | > 90% | ~92% |
| Точность matching | > 85% | ~88% |
| Время анализа | < 30 сек | ~15 сек |
| Грамматика | > 80% | ~85% |

---

## Troubleshooting

### KeyBERT не работает

```bash
# Проверьте установку
pip install keybert

# Попробуйте другой метод
pip install keybert[all]
```

### SpaCy модели не загружаются

```bash
# Скачайте модели заново
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm

# Проверьте путь
python -c "import spacy; print(spacy.load('en_core_web_sm'))"
```

### LanguageTool не отвечает

```bash
# Проверьте API
curl "https://api.languagetool.org/v2/check?text=test&language=en-US"

# Используйте fallback (базовая проверка)
# В коде настроено отключение при ошибке
```

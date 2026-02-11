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

---

## 10. Автоматическое переобучение моделей (Automated Model Retraining)

**Модуль**: `backend/tasks/model_retraining.py`

### Обзор

Система автоматического переобучения обеспечивает непрерывное улучшение ML-моделей на основе обратной связи от рекрутеров и мониторинга производительности.

```
┌────────────────────────────────────────────────────────────────────┐
│                    RETRAINING TRIGGERS                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Feedback Volume  │  │   Performance    │  │   Scheduled     │  │
│  │  (1000+ items)   │  │   Degradation    │  │   (Weekly)      │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘  │
│           │                     │                     │            │
│           └─────────────────────┼─────────────────────┘            │
└─────────────────────────────────┼──────────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                    RETRAINING PIPELINE                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Collect Feedback │─▶│   Train Model    │─▶│  A/B Testing    │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT DECISION                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Canary Deploy   │─▶│   Performance    │─▶│  Promote/Rollback│ │
│  │   (10% traffic)  │  │   Validation     │  │                 │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Триггеры переобучения

| Триггер | Условие | Описание |
|---------|---------|----------|
| Feedback Volume Trigger | ≥ 1000 новых feedback | Автоматический запуск при накоплении данных |
| Performance Degradation | > 5% drop in F1 | Переобучение при падении качества |
| Scheduled Retraining | Еженедельно | Регулярное обновление модели |
| Manual Trigger | Через API | Ручной запуск администратором |

### Feedback Volume Trigger

**Модуль**: `backend/analyzers/feedback_accumulator.py`

Система отслеживает объем обратной связи для каждой версии модели:

```python
from analyzers.feedback_accumulator import FeedbackAccumulator

# 1. Инициализация аккумулятора
accumulator = FeedbackAccumulator(threshold=1000)

# 2. Регистрация feedback
accumulator.record_feedback(
    model_name='skill_matching',
    model_version_id='v2.1.0',
    feedback_type='positive'  # или 'negative', 'neutral'
)

# 3. Проверка порога
if accumulator.check_threshold(model_version_id):
    trigger_retraining(model_name)
```

#### Параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `threshold` | 1000 | Минимальное количество feedback для триггера |
| `window_days` | 30 | Окно для подсчета feedback (дней) |
| `min_positive_ratio` | 0.3 | Минимальный % положительного feedback |

#### Статистика Feedback

```python
# Получение статистики
stats = accumulator.get_stats(model_version_id)
# {
#     'total_count': 1500,
#     'positive_count': 1200,
#     'negative_count': 200,
#     'neutral_count': 100,
#     'positive_ratio': 0.80,
#     'threshold_reached': True
# }
```

---

## 11. Мониторинг производительности (Performance Monitoring)

**Модуль**: `backend/analyzers/performance_tracker.py`

### Метрики

| Метрика | Описание | Целевое значение |
|---------|----------|------------------|
| Accuracy | Общая точность | > 85% |
| Precision | Точность положительных прогнозов | > 80% |
| Recall | Полнота обнаружения | > 75% |
| F1 Score | Гармоническое среднее | > 80% |
| AUC-ROC | Area Under Curve | > 0.85 |

### Расчёт метрик

```python
from analyzers.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()

# Расчёт метрик
metrics = tracker.calculate_metrics(
    y_true=ground_truth_labels,
    y_pred=model_predictions,
    y_scores=probability_scores  # опционально для AUC
)

# Результат:
# {
#     'accuracy': 0.875,
#     'precision': 0.842,
#     'recall': 0.798,
#     'f1_score': 0.819,
#     'auc_score': 0.891
# }
```

### Детекция деградации

```python
# Проверка деградации производительности
degradation = tracker.detect_degradation(
    model_version_id=current_version,
    threshold=0.05  # 5% падение
)

if degradation['is_degraded']:
    # Автоматический триггер переобучения
    trigger_retraining(
        model_name='skill_matching',
        reason='performance_degradation',
        details=degradation
    )
```

### История производительности

```python
# Запись в историю
tracker.record_performance(
    model_version_id='v2.1.0',
    metrics=metrics,
    dataset_type='production'
)

# Получение истории
history = tracker.get_performance_history(
    model_version_id='v2.1.0',
    limit=30  # последние 30 записей
)
```

---

## 12. Версионирование моделей (Model Versioning)

**Модуль**: `backend/analyzers/model_versioning.py`

### Управление версиями

```python
from analyzers.model_versioning import ModelVersionManager

manager = ModelVersionManager()

# Получение активной модели
active = manager.get_active_model('skill_matching', db_session)
# {
#     'id': 'uuid-here',
#     'version': 'v2.0.0',
#     'performance_score': 85.5,
#     'is_active': True
# }

# Получение всех версий
versions = manager.get_all_model_versions('skill_matching', db_session)
```

### Canary Deployment

Canary deployment позволяет постепенно выкатывать новые модели:

```python
# Создание canary (10% трафика)
canary = manager.create_canary_deployment(
    model_name='skill_matching',
    canary_version_id='new-version-uuid',
    initial_traffic_percentage=10
)

# Увеличение трафика
manager.increase_canary_traffic(
    model_name='skill_matching',
    increment_percentage=10  # +10% = 20% total
)

# Продвижение в production
manager.promote_canary_to_production('skill_matching')

# Откат при проблемах
manager.rollback_canary(
    model_name='skill_matching',
    reason='Performance degradation detected'
)
```

### Стадии Canary

| Трафик | Стадия | Описание |
|--------|--------|----------|
| 10% | initial | Начальное тестирование |
| 10-25% | early | Ранний мониторинг |
| 25-40% | mid | Расширенное тестирование |
| 40-50% | advanced | Финальная валидация |
| 50%+ | pre_promotion | Подготовка к promotion |

---

## 13. A/B Тестирование (A/B Testing)

**Модуль**: `backend/tasks/ab_testing.py`

### Процесс A/B тестирования

```
┌─────────────────────────────────────────────────────────────────┐
│                    A/B TEST WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────┐     ┌───────────────────┐
│  Control Model    │     │ Treatment Model   │
│   (Production)    │     │   (Candidate)     │
└─────────┬─────────┘     └─────────┬─────────┘
          │                         │
          ▼                         ▼
┌─────────────────────────────────────────────────┐
│              Collect Feedback Data              │
│          (minimum 100 samples per model)        │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│         Statistical Significance Testing        │
│  ┌─────────────────────────────────────────┐   │
│  │  • Z-test for accuracy comparison       │   │
│  │  • P-value calculation (threshold 0.05) │   │
│  │  • Effect size (Cohen's d)              │   │
│  │  • Confidence intervals (95%)           │   │
│  └─────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│               DECISION                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │   Deploy   │ │    Keep    │ │ Insufficient│ │
│  │ Treatment  │ │  Control   │ │  Evidence  │  │
│  └────────────┘ └────────────┘ └────────────┘  │
└─────────────────────────────────────────────────┘
```

### Запуск A/B теста

```python
from tasks.ab_testing import evaluate_ab_test

# Асинхронный запуск теста
task = evaluate_ab_test.delay(
    control_version_id='production-version-id',
    treatment_version_id='candidate-version-id',
    days_back=30,  # анализировать последние 30 дней
    auto_activate_if_better=True
)

# Получение результата
result = task.get()
```

### Результаты A/B теста

```python
# Структура результата
{
    'status': 'completed',
    'control_version': 'v2.0.0',
    'treatment_version': 'v2.1.0',
    'control_metrics': {
        'accuracy': 0.85,
        'sample_size': 500
    },
    'treatment_metrics': {
        'accuracy': 0.88,
        'sample_size': 500
    },
    'comparison': {
        'accuracy_improvement': 0.03,  # +3%
        'z_score': 2.45,
        'p_value': 0.0142,
        'is_statistically_significant': True,
        'effect_size': 0.25,
        'recommendation': 'deploy_treatment'
    },
    'activated': True  # если auto_activate_if_better=True
}
```

### Статистические параметры

| Параметр | Значение | Описание |
|----------|---------|----------|
| `MIN_AB_TEST_SAMPLE_SIZE` | 100 | Минимальная выборка |
| `STATISTICAL_SIGNIFICANCE_THRESHOLD` | 0.05 | P-value порог |
| `MIN_IMPROVEMENT_THRESHOLD` | 0.02 | Минимальное улучшение (2%) |
| `DEFAULT_CONFIDENCE_LEVEL` | 0.95 | Уровень доверия (95%) |

### Интерпретация рекомендаций

| Рекомендация | Условие | Действие |
|--------------|---------|----------|
| `deploy_treatment` | p < 0.05 AND improvement ≥ 2% | Разворачивать новую модель |
| `keep_control` | p < 0.05 AND improvement < -2% | Оставить текущую модель |
| `insufficient_evidence` | p ≥ 0.05 | Продолжить сбор данных |

---

## 14. Rollback и восстановление

### One-Click Rollback

```python
# Быстрый откат к предыдущей версии
from tasks.model_retraining import rollback_to_version

result = rollback_to_version(
    model_name='skill_matching',
    target_version_id='previous-version-uuid',
    reason='Performance drop detected'
)

# Результат:
# {
#     'status': 'success',
#     'rolled_back_from': 'v2.1.0',
#     'rolled_back_to': 'v2.0.0',
#     'traffic_restored': 100
# }
```

### Rollback Canary

```python
# Откат canary deployment
manager.rollback_canary(
    model_name='skill_matching',
    reason='Error rate increased by 15%'
)
```

---

## 15. Конфигурация переобучения

**Модель**: `backend/models/retraining_config.py`

### Управление через БД

```python
# Приостановка переобучения
config = RetrainingConfig(
    model_name='skill_matching',
    paused=True,
    pause_reason='Manual maintenance',
    paused_by='admin@example.com'
)
db.add(config)
db.commit()

# Проверка статуса
if not config.paused:
    run_retraining_pipeline()
```

### Параметры окружения

```bash
# .env
RETRAINING_FEEDBACK_THRESHOLD=1000
RETRAINING_SCHEDULE_ENABLED=true
RETRAINING_SCHEDULE_CRON="0 2 * * 0"  # Каждое воскресенье в 2:00
RETRAINING_AUTO_PROMOTE=false
CANARY_INITIAL_TRAFFIC=10
CANARY_MAX_TRAFFIC=50
```

---

## 16. MLflow интеграция

**Модуль**: `backend/analyzers/mlflow_tracker.py`

### Эксперимент трекинг

```python
from analyzers.mlflow_tracker import get_mlflow_tracker

tracker = get_mlflow_tracker()

# Логирование эксперимента
with tracker.start_run('skill_matching_v2.1'):
    tracker.log_params({
        'learning_rate': 0.001,
        'batch_size': 32,
        'epochs': 100
    })

    tracker.log_metrics({
        'accuracy': 0.88,
        'f1_score': 0.85
    })

    tracker.log_model(model, 'model')
```

### Метрики экспериментов

| Метрика | Описание |
|---------|----------|
| `training_loss` | Loss на обучении |
| `val_loss` | Loss на валидации |
| `training_accuracy` | Accuracy на обучении |
| `val_accuracy` | Accuracy на валидации |
| `training_time_sec` | Время обучения |

---

## Troubleshooting (Retraining)

### Переобучение не запускается

```bash
# Проверьте статус конфигурации
SELECT * FROM retraining_config WHERE model_name = 'skill_matching';

# Если paused=true, снимите паузу
UPDATE retraining_config SET paused = false WHERE model_name = 'skill_matching';
```

### A/B тест не завершается

```bash
# Проверьте количество feedback
SELECT model_version_id, COUNT(*) FROM skill_feedback
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY model_version_id;

# Нужно минимум 100 samples для каждого варианта
```

### Canary не продвигается

```bash
# Проверьте статистическую значимость
curl -X GET "http://localhost:8000/api/v1/models/skill_matching/ab-test/status"

# Если p-value > 0.05, нужно больше данных
```

### Rollback не работает

```bash
# Проверьте существование предыдущей версии
SELECT * FROM ml_model_versions
WHERE model_name = 'skill_matching'
ORDER BY created_at DESC;

# Активируйте нужную версию вручную
UPDATE ml_model_versions SET is_active = true
WHERE id = 'previous-version-uuid';
```

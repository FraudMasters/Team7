# Performance Optimization and Tuning Guide

Comprehensive guide to optimizing and tuning the AgentHR resume analysis platform for maximum performance and resource efficiency.

## Overview

The AgentHR platform is a complex, multi-layered system with several performance-critical components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│                   Vite + Code Splitting                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                      │
│              Connection Pooling + Caching                   │
└──────┬──────────────────────────────────────────┬───────────┘
       │                                          │
       ▼                                          ▼
┌─────────────────────┐              ┌──────────────────────────┐
│  Celery Workers     │              │      PostgreSQL          │
│  - ML Processing    │              │    + Indexing            │
│  - Async Tasks      │              └──────────────────────────┘
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Redis Cache                             │
│              - Model Caching - Result Cache                 │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   ML Models Layer                           │
│  - KeyBERT (sentence-transformers)                          │
│  - spaCy NER (en_core_web_sm, ru_core_news_sm)              │
│  - LanguageTool Grammar Checker                             │
└─────────────────────────────────────────────────────────────┘
```

### Performance Characteristics

| Component | Performance Impact | Typical Bottlenecks |
|-----------|-------------------|---------------------|
| **ML Models** | High (CPU/Memory) | Model loading time, memory usage, batch processing |
| **Celery Workers** | High (Concurrency) | Queue backups, worker count, task duration |
| **Redis Cache** | Medium (Hit Rate) | Cache misses, memory limits, eviction policy |
| **PostgreSQL** | Medium (Query Speed) | Missing indexes, N+1 queries, connection pool size |
| **Frontend** | Medium (Load Time) | Bundle size, rendering performance, API calls |
| **Docker** | Low-Medium (Resources) | CPU/memory limits, container overhead |

## Table of Contents

1. **Prerequisites** (This section)
2. [ML Model Optimization](#ml-model-optimization)
   - Model selection and sizing
   - Batching strategies
   - Model preloading and caching
   - Memory management
3. [Celery Worker Tuning](#celery-worker-tuning)
   - Concurrency configuration
   - Prefetch limits
   - Queue separation
   - Task priorities
4. [Redis Caching Strategies](#redis-caching-strategies)
   - Memory limits and eviction policies
   - Cache patterns for different data types
   - Cache warming strategies
   - Monitoring cache performance
5. [PostgreSQL Optimization](#postgresql-optimization)
   - Indexing strategies
   - Connection pooling
   - Query optimization
   - Database vacuuming and maintenance
6. [Frontend Performance](#frontend-performance)
   - Code splitting and lazy loading
   - Virtualization for large lists
   - Bundle optimization
   - API call optimization
7. [Docker Resource Tuning](#docker-resource-tuning)
   - CPU and memory limits
   - Container optimization
   - Multi-stage builds
8. [Performance Monitoring](#performance-monitoring)
   - Metrics collection (Prometheus/Grafana)
   - Logging and tracing
   - Performance benchmarking
   - Alert setup
9. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)
   - Common bottlenecks
   - Diagnostic tools
   - Performance tuning checklist

---

## Prerequisites

Before optimizing performance, ensure you have:

### Required Tools

- **Docker Desktop** or Docker + Docker Compose installed
- **Basic monitoring setup**: Prometheus + Grafana (see [monitoring/README.md](monitoring/README.md))
- **Access to logs**: `docker-compose logs -f [service]`
- **Database access**: `docker-compose exec db psql -U agenthr -d agenthr`

### Knowledge Requirements

This guide assumes familiarity with:

- **Docker basics**: Container management, resource limits
- **Python ML stack**: Celery, Redis, sentence-transformers, spaCy
- **PostgreSQL**: Indexes, query planning, connection pooling
- **React**: Virtualization, code splitting, lazy loading
- **Performance profiling**: Using metrics to identify bottlenecks

### Environment Setup

Ensure your environment is properly configured:

```bash
# 1. Check current resource limits
docker-compose ps
docker stats $(docker-compose ps -q)

# 2. Review current configuration
cat .env | grep -E '(CELERY_WORKERS|REDIS_MEMORY|POSTGRES_POOL)'

# 3. Verify monitoring is running
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000            # Grafana
```

### Baseline Metrics

Before making changes, establish baseline performance metrics:

| Metric | How to Measure | Target Value |
|--------|----------------|--------------|
| **Resume analysis time** | API logs / Flower dashboard | < 30 seconds |
| **API response time (p95)** | Prometheus metrics | < 500ms |
| **Frontend load time** | Browser DevTools | < 3 seconds |
| **Celery queue depth** | Flower dashboard | < 10 tasks |
| **Redis memory usage** | `docker exec redis redis-cli INFO memory` | < 80% of max |
| **PostgreSQL query time** | Slow query log | < 100ms (avg) |
| **Memory per container** | Docker stats | Within limits |

### Quick Health Check

Run this quick health check before proceeding:

```bash
#!/bin/bash
echo "=== AgentHR Performance Health Check ==="
echo ""

# Check container status
echo "1. Container Status:"
docker-compose ps

echo ""
echo "2. Resource Usage:"
docker stats --no-stream $(docker-compose ps -q)

echo ""
echo "3. Redis Memory:"
docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human

echo ""
echo "4. Celery Queue Depth:"
curl -s http://localhost:5555/api/tasks | jq '.length'

echo ""
echo "5. Database Connections:"
docker-compose exec -T db psql -U agenthr -d agenthr -c "SELECT count(*) FROM pg_stat_activity;"

echo ""
echo "6. Recent Slow Queries:"
docker-compose exec -T db psql -U agenthr -d agenthr -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"
```

---

## When to Use This Guide

Use this guide when:

- **Initial deployment**: Set up optimal configuration from the start
- **Performance degradation**: System slowed down after increased load
- **Scaling preparation**: Optimize before adding more users/data
- **Resource constraints**: Running out of CPU/memory on limited hardware
- **Bottleneck investigation**: Diagnose specific performance issues

## Performance Optimization Philosophy

### Optimization Priority Order

1. **Measure First**: Always collect metrics before making changes
2. **Fix the biggest bottleneck**: Optimize the slowest component first
3. **Test changes**: Verify improvements with benchmarks
4. **Document configs**: Keep track of what works and why

### General Principles

- **Cache everything that's expensive to compute**: ML model results, database queries, API responses
- **Batch when possible**: Process multiple items together instead of one-by-one
- **Use async I/O**: Don't block threads waiting for I/O (database, external APIs)
- **Set appropriate limits**: Prevent any single component from consuming all resources
- **Monitor continuously**: Set up alerts before problems occur

## Next Steps

1. [Start with ML Model Optimization](#ml-model-optimization) - This usually has the biggest impact
2. Then [tune Celery workers](#celery-worker-tuning) for better throughput
3. [Optimize Redis caching](#redis-caching-strategies) to reduce redundant processing
4. Continue through each section based on your specific bottlenecks

---

## ML Model Optimization

ML models are the most resource-intensive components in the AgentHR system. Proper optimization can reduce analysis time by 50-70% and memory usage by 30-50%.

### ML Models Overview

The AgentHR system uses several ML/NLP models for resume analysis:

```
┌─────────────────────────────────────────────────────────────┐
│                     ML Models Stack                         │
├─────────────────────────────────────────────────────────────┤
│  sentence-transformers                                      │
│  └─ all-MiniLM-L6-v2 (~80MB)                               │
│     ├─ KeyBERT: Keyword extraction                         │
│     └─ VectorSimilarityMatcher: Semantic matching          │
├─────────────────────────────────────────────────────────────┤
│  spaCy                                                      │
│  ├─ en_core_web_sm (~12MB) - English NER                   │
│  └─ ru_core_news_sm (~18MB) - Russian NER                  │
├─────────────────────────────────────────────────────────────┤
│  External Services                                          │
│  └─ LanguageTool API - Grammar checking (HTTPS)            │
└─────────────────────────────────────────────────────────────┘
```

### Model Performance Characteristics

| Model | Size | Load Time | Inference | Memory | Use Case |
|-------|------|-----------|-----------|--------|----------|
| **all-MiniLM-L6-v2** | 80MB | 2-5s | 30-50ms | ~500MB | Keyword extraction, semantic matching |
| **en_core_web_sm** | 12MB | 200-500ms | 10-30ms | ~50MB | English NER (names, dates, orgs) |
| **ru_core_news_sm** | 18MB | 300-600ms | 15-40ms | ~70MB | Russian NER |
| **LanguageTool API** | N/A | 0 (external) | 500-2000ms | 0 | Grammar checking |

### 1. Model Selection and Sizing

#### Current Model Choices

**sentence-transformers (all-MiniLM-L6-v2)**

**Why this model?**
- Small size (80MB vs 400MB+ for larger models)
- Fast inference (30-50ms per text)
- Good quality for short text (resumes, job descriptions)
- Multilingual support (English + Russian + 100+ languages)

**Alternatives considered:**

| Model | Size | Speed | Quality | Verdict |
|-------|------|-------|---------|---------|
| **all-MiniLM-L6-v2** | 80MB | ⚡⚡⚡ | 🎯🎯🎯 | ✅ Best balance |
| all-mpnet-base-v2 | 420MB | ⚡⚡ | 🎯🎯🎯🎯 | ❌ Too large, 4x slower |
| paraphrase-multilingual-mpnet-base-v2 | 1.2GB | ⚡ | 🎯🎯🎯🎯🎯 | ❌ Prohibitively large |

**spaCy Models**

**Why `sm` (small) models?**
- Fast inference (10-40ms)
- Low memory footprint (~50-70MB per model)
- Good accuracy for NER tasks (90%+)

**When to upgrade to `md` or `lg` models:**

| Model | Size | Speed | Accuracy | Use when... |
|-------|------|-------|----------|-------------|
| `en_core_web_sm` | 12MB | ⚡⚡⚡ | 90% | ✅ Current - sufficient for resumes |
| `en_core_web_md` | 45MB | ⚡⚡ | 92% | Need higher accuracy, have memory |
| `en_core_web_lg` | 550MB | ⚡ | 94% | ❌ Too large, minimal gain |

#### Model Sizing Guidelines

**For low-resource systems (2-4GB RAM):**
- Use only `en_core_web_sm` (skip Russian if not needed)
- Reduce KeyBERT `top_n` from 10 to 5
- Disable vector matching if not critical

**For standard systems (8-16GB RAM):**
- Keep current setup (all models loaded)
- Enable result caching (see section 1.3)

**For high-throughput systems (32GB+ RAM):**
- Consider upgrading to `md` models for 2-3% accuracy gain
- Increase batch size (see section 1.2)

---

### 2. Batching Strategies

Batching processes multiple items together to improve throughput and reduce model loading overhead.

#### Current Implementation

The system already uses batching in several places:

```python
# KeyBERT with batching (recommended)
from keybert import KeyBERT

kw_model = KeyBERT(model='all-MiniLM-L6-v2')

# Process multiple resumes at once
resumes = ["resume text 1...", "resume text 2...", ...]
results = kw_model.extract_keywords(
    resumes,
    keyphrase_ngram_range=(1, 2),
    top_n=10
)
```

#### Batching Configuration

**Optimal batch sizes by resource level:**

| RAM Available | Recommended Batch Size | Throughput | Latency |
|---------------|------------------------|------------|---------|
| 2-4GB | 1-3 | Low | Fast (per item) |
| 8GB (default) | 5-10 | Medium | Medium |
| 16GB+ | 10-20 | High | Higher latency |

**Environment variables:**

```bash
# .env
BATCH_SIZE=10              # Number of resumes to process per batch
KEYBERT_TOP_N=10           # Keywords to extract per resume
MAX_BATCH_QUEUE_SIZE=100   # Max items waiting for batch
```

#### Batch Processing Best Practices

**1. Use Celery for async batching:**

```python
# backend/tasks/analysis_task.py
@celery_app.task(bind=True, max_retries=3)
def analyze_resume_batch(self, resume_ids: List[str]):
    """Process multiple resumes in a single task"""
    try:
        # Load models once (cached)
        nlp = get_spacy_model('en')
        kw_model = get_keybert_model()

        results = []
        for resume_id in resume_ids:
            text = get_resume_text(resume_id)

            # Extract keywords (batched internally)
            keywords = kw_model.extract_keywords(text, top_n=10)

            # NER processing
            doc = nlp(text)
            entities = extract_entities(doc)

            results.append({
                'resume_id': resume_id,
                'keywords': keywords,
                'entities': entities
            })

        return results

    except Exception as exc:
        # Retry with smaller batch on failure
        if len(resume_ids) > 1:
            return self.retry(exc=exc, countdown=60)
        raise
```

**2. Batch size adaptation:**

```python
def adaptive_batch_size(available_memory_mb: int) -> int:
    """Determine optimal batch size based on available memory"""
    if available_memory_mb < 2048:
        return 1  # Very low memory, process one at a time
    elif available_memory_mb < 8192:
        return 5  # Standard configuration
    else:
        return min(20, available_memory_mb // 512)  # High memory
```

**3. Batching for vector similarity:**

```python
# VectorSimilarityMatcher - batch embedding
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode multiple texts at once (more efficient)
texts = [resume_text, job_title, job_description]
embeddings = model.encode(texts, batch_size=3)

# Split results
resume_embedding = embeddings[0]
job_title_embedding = embeddings[1]
job_description_embedding = embeddings[2]
```

#### Monitoring Batch Performance

Track these metrics to optimize batch size:

```bash
# Flower dashboard - http://localhost:5555
# Monitor:
# - Average task runtime
# - Queue depth
# - Worker memory usage

# Target metrics:
# - Task runtime: 10-30 seconds per batch
# - Queue depth: < 10 tasks
# - Memory usage: < 80% of container limit
```

---

### 3. Model Preloading and Caching

Loading ML models is expensive (2-5 seconds). Preload and cache them to avoid repeated loading.

#### Caching Strategy

```
┌────────────────────────────────────────────────────────────┐
│                  Model Caching Architecture                │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Application Start                                          │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Load ML Models  │ ───▶ In-memory cache (singleton)      │
│  └─────────────────┘                                        │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────┐                │
│  │  functools.lru_cache() or global cache  │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
│  Request 1 ──▶ Cache Hit ──▶ Use cached model (~0ms)        │
│  Request 2 ──▶ Cache Hit ──▶ Use cached model (~0ms)        │
│  Request N ──▶ Cache Hit ──▶ Use cached model (~0ms)        │
└────────────────────────────────────────────────────────────┘
```

#### Implementation Pattern

**1. Module-level caching (singleton pattern):**

```python
# backend/analyzers/model_cache.py
import functools
import spacy
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

# spaCy models - cached at module level
_SPACY_MODELS = {}

@functools.lru_cache(maxsize=2)
def get_spacy_model(lang: str):
    """Get cached spaCy model"""
    if lang not in _SPACY_MODELS:
        model_name = f'{lang}_core_web_sm' if lang == 'en' else 'ru_core_news_sm'
        _SPACY_MODELS[lang] = spacy.load(model_name)
    return _SPACY_MODELS[lang]

# KeyBERT - cached at module level
_KEYBERT_MODEL = None

def get_keybert_model():
    """Get cached KeyBERT model"""
    global _KEYBERT_MODEL
    if _KEYBERT_MODEL is None:
        _KEYBERT_MODEL = KeyBERT(model='all-MiniLM-L6-v2')
    return _KEYBERT_MODEL

# sentence-transformers - cached at module level
_VECTOR_MODEL = None

def get_vector_model():
    """Get cached sentence-transformers model"""
    global _VECTOR_MODEL
    if _VECTOR_MODEL is None:
        _VECTOR_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return _VECTOR_MODEL
```

**2. Application startup preloading:**

```python
# backend/main.py (FastAPI app)
@app.on_event("startup")
async def startup_event():
    """Preload ML models on application startup"""
    logger.info("Preloading ML models...")

    # Preload English spaCy
    get_spacy_model('en')
    logger.info("✓ Loaded en_core_web_sm")

    # Preload Russian spaCy
    get_spacy_model('ru')
    logger.info("✓ Loaded ru_core_news_sm")

    # Preload KeyBERT
    get_keybert_model()
    logger.info("✓ Loaded KeyBERT (all-MiniLM-L6-v2)")

    # Preload sentence-transformers
    get_vector_model()
    logger.info("✓ Loaded sentence-transformers (all-MiniLM-L6-v2)")

    logger.info("All ML models loaded and cached")
```

**3. Redis caching for model results:**

```python
# backend/analyzers/cache.py
import redis
import hashlib
import json

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_key(text: str, model: str) -> str:
    """Generate cache key for text + model"""
    content = f"{model}:{text}"
    return f"ml_cache:{hashlib.md5(content.encode()).hexdigest()}"

def get_cached_result(text: str, model: str):
    """Get cached result if available"""
    key = cache_key(text, model)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cached_result(text: str, model: str, result: dict, ttl: int = 3600):
    """Cache result with TTL (default 1 hour)"""
    key = cache_key(text, model)
    redis_client.setex(key, ttl, json.dumps(result))
```

**4. Usage in analysis tasks:**

```python
# backend/analyzers/keyword_extractor.py
from .model_cache import get_keybert_model
from .cache import get_cached_result, set_cached_result

def extract_keywords(text: str, lang: str = 'en'):
    """Extract keywords with caching"""
    # Check cache first
    cached = get_cached_result(text, 'keybert')
    if cached:
        return cached

    # Load model (cached after first call)
    kw_model = get_keybert_model()

    # Extract keywords
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words='english' if lang == 'en' else 'russian',
        top_n=10
    )

    result = [{'keyword': k, 'score': s} for k, s in keywords]

    # Cache result
    set_cached_result(text, 'keybert', result, ttl=3600)

    return result
```

#### Cache Configuration

```bash
# .env
# Redis cache for ML model results
REDIS_ML_CACHE_DB=0           # Database number for ML cache
REDIS_ML_CACHE_TTL=3600       # Cache TTL in seconds (1 hour)
REDIS_ML_CACHE_MAX_MEMORY=256mb  # Max memory for ML cache
```

#### Cache Invalidation

**When to invalidate cache:**

| Trigger | Action |
|---------|--------|
| Model update | Flush entire cache: `redis-cli FLUSHDB` |
| Resume update | Delete specific key: `redis-cli DEL ml_cache:<hash>` |
| Periodic | Let Redis auto-expire with TTL |

**Manual cache management:**

```bash
# View ML cache size
docker-compose exec redis redis-cli DBSIZE

# View cache keys
docker-compose exec redis redis-cli KEYS "ml_cache:*"

# Clear all ML cache
docker-compose exec redis redis-cli FLUSHDB

# View memory usage
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

---

### 4. Memory Management

ML models consume significant memory. Proper management prevents OOM (Out of Memory) errors.

#### Memory Usage Breakdown

**Per-container memory usage:**

```
┌────────────────────────────────────────────────────────┐
│          Celery Worker Memory Breakdown               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Base Python Runtime:     ~100MB                       │
│  sentence-transformers:   ~500MB                       │
│  en_core_web_sm:         ~50MB                        │
│  ru_core_news_sm:        ~70MB                        │
│  KeyBERT overhead:       ~50MB (shares with transformers) │
│  Processing data:        ~100-200MB                    │
│  ─────────────────────────────────────────────────────  │
│  Total (idle):           ~900MB                       │
│  Total (processing):     ~1-1.5GB                     │
└────────────────────────────────────────────────────────┘
```

#### Docker Memory Limits

**docker-compose.yml configuration:**

```yaml
services:
  celery:
    build: ./backend
    command: celery -A celery_app.celery_app worker --loglevel=info
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Limit to 2 CPU cores
          memory: 2G       # Limit to 2GB RAM
        reservations:
          cpus: '1.0'      # Reserve 1 CPU core
          memory: 1G       # Reserve 1GB RAM
    environment:
      - CELERY_WORKER_PREFETCH_MULTIPLIER=1
      - CELERY_WORKER_MAX_TASKS_PER_CHILD=100
```

**Memory limits by system size:**

| System Size | Worker Memory | Workers per Host | Total Memory |
|-------------|---------------|------------------|--------------|
| Small (4GB) | 1GB | 1 | 1-2GB |
| Medium (8GB) | 2GB | 2 | 4GB |
| Large (16GB+) | 2GB | 4-8 | 8-16GB |

#### Memory Optimization Techniques

**1. Lazy model loading (only load needed models):**

```python
# backend/analyzers/model_loader.py
MODELS_LOADED = set()

def ensure_model_loaded(model_name: str):
    """Load model only if not already loaded"""
    if model_name not in MODELS_LOADED:
        if model_name == 'spacy_en':
            get_spacy_model('en')
        elif model_name == 'spacy_ru':
            get_spacy_model('ru')
        elif model_name == 'keybert':
            get_keybert_model()
        MODELS_LOADED.add(model_name)

def load_models_for_language(lang: str):
    """Load only models needed for specific language"""
    if lang == 'en':
        ensure_model_loaded('spacy_en')
    elif lang == 'ru':
        ensure_model_loaded('spacy_ru')
    ensure_model_loaded('keybert')
```

**2. Unload unused models (for very constrained systems):**

```python
def unload_model(model_name: str):
    """Unload model to free memory (use with caution)"""
    global _SPACY_MODELS, _KEYBERT_MODEL, _VECTOR_MODEL

    if model_name == 'spacy_ru' and 'ru' in _SPACY_MODELS:
        del _SPACY_MODELS['ru']
        MODELS_LOADED.discard('spacy_ru')
        gc.collect()  # Force garbage collection
```

**3. Process restart on memory limit:**

```python
# celery configuration
worker_max_tasks_per_child = 100  # Restart worker after 100 tasks
worker_prefetch_multiplier = 1     # Don't prefetch too many tasks
```

#### Monitoring Memory Usage

**Real-time monitoring:**

```bash
# Docker stats
watch -n 1 'docker stats --no-stream $(docker-compose ps -q celery)'

# Detailed memory info
docker-compose exec celery cat /proc/meminfo

# Python memory profiling
pip install memory_profiler
python -m memory_profiler your_script.py
```

**Prometheus metrics:**

```python
# backend/monitoring/metrics.py
from prometheus_client import Gauge

memory_usage = Gauge('celery_worker_memory_bytes', 'Memory usage in bytes')

def update_memory_metrics():
    """Update memory usage metrics"""
    import psutil
    process = psutil.Process()
    memory_usage.set(process.memory_info().rss)
```

---

## Quick Reference: ML Model Optimization

### Checklist

- [ ] **Models preloaded** on application startup
- [ ] **Caching enabled** for model instances (lru_cache)
- [ ] **Result caching** configured in Redis (TTL: 1 hour)
- [ ] **Batch size** set according to available memory
- [ ] **Memory limits** configured in docker-compose.yml
- [ ] **Worker restart** configured (max_tasks_per_child)
- [ ] **Monitoring** set up for memory usage

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Slow first request | Model loading on first use | Enable preload on startup |
| High memory usage | All models loaded | Use lazy loading per language |
| OOM errors | No memory limits | Set limits in docker-compose.yml |
| Cache not working | Redis misconfigured | Check REDIS_HOST in .env |
| Slow batch processing | Batch size too small | Increase BATCH_SIZE in .env |

### Environment Variables

```bash
# .env - ML Model Configuration
BATCH_SIZE=10
KEYBERT_TOP_N=10
REDIS_ML_CACHE_TTL=3600
CELERY_WORKER_MAX_TASKS_PER_CHILD=100

# Optional: Skip specific models if not needed
ENABLE_SPACY_EN=true
ENABLE_SPACY_RU=true
ENABLE_KEYBERT=true
ENABLE_VECTOR_MATCHER=true
```

---

## Celery Worker Tuning

Celery workers handle all asynchronous processing in the AgentHR system, including resume analysis, ML model training, backups, and scheduled tasks. Proper tuning is critical for maximizing throughput and preventing queue backups.

### Celery Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  (FastAPI submits tasks to queues)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Redis Broker                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ analysis │  │ learning │  │  audit   │  │   default│   │
│  │  queue   │  │  queue   │  │  queue   │  │   queue  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼────────────┼────────────┼────────────┼────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Workers                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Worker 1     │  │ Worker 2     │  │ Worker N     │     │
│  │ - analysis   │  │ - learning   │  │ - audit      │     │
│  │ - learning   │  │ - audit      │  │ - default    │     │
│  │ (concurrency)│  │ (concurrency)│  │ (concurrency)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Current Celery Configuration

The system uses the following Celery configuration (from `backend/celery_config.py`):

| Setting | Current Value | Description |
|---------|---------------|-------------|
| `broker_url` | `redis://redis:6379/0` | Redis as message broker |
| `result_backend` | `redis://redis:6379/0` | Redis for task results |
| `task_serializer` | `json` | JSON serialization |
| `task_acks_late` | `True` | Ack after execution (reliability) |
| `task_reject_on_worker_lost` | `True` | Requeue if worker dies |
| `task_time_limit` | `3600` (1 hour) | Hard limit for tasks |
| `task_soft_time_limit` | `3300` (55 min) | Soft limit for graceful shutdown |
| `worker_prefetch_multiplier` | `1` | Disable prefetching |
| `worker_max_tasks_per_child` | `100` | Restart after 100 tasks |
| `task_default_priority` | `5` | Default task priority (0-9) |

### 1. Concurrency Configuration

Concurrency determines how many tasks a worker can process simultaneously. Proper configuration prevents CPU/memory exhaustion while maximizing throughput.

#### Understanding Concurrency

**What is concurrency?**
- Number of parallel task processes per worker
- Each concurrency unit = separate process
- More concurrency = more parallel processing = more resource usage

**Default concurrency:**
```bash
# Celery defaults to CPU count
# 4-core CPU = 4 concurrent processes
```

#### Concurrency Tuning Guidelines

**For ML-heavy workloads (resume analysis):**

| CPU Cores | Recommended Concurrency | Workers | Total Processes | Memory Required |
|-----------|------------------------|---------|-----------------|-----------------|
| 2 | 1 | 1 | 1 | 1-2GB |
| 4 | 2 | 1-2 | 2-4 | 2-4GB |
| 8 | 2-4 | 2 | 4-8 | 4-8GB |
| 16+ | 4 | 4 | 16 | 8-16GB |

**Why lower concurrency for ML tasks?**
- ML models are CPU-intensive (not I/O bound)
- Each task loads models into memory (~500MB-1GB)
- Too much concurrency causes CPU thrashing and OOM errors

**For I/O-heavy workloads (emails, backups, database):**

| CPU Cores | Recommended Concurrency | Workers | Total Processes |
|-----------|------------------------|---------|-----------------|
| 2 | 4 | 1 | 4 |
| 4 | 8 | 1-2 | 8-16 |
| 8 | 16 | 2 | 32 |
| 16+ | 16-32 | 4 | 64-128 |

**Why higher concurrency for I/O tasks?**
- I/O tasks spend most time waiting (database, HTTP API)
- CPU is idle during I/O wait
- Higher concurrency keeps CPU utilized

#### Configuration Examples

**docker-compose.yml - Single worker with custom concurrency:**

```yaml
services:
  celery-worker:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --max-tasks-per-child=100
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**Multiple workers (recommended for production):**

```yaml
services:
  # Analysis worker (ML-heavy, low concurrency)
  celery-analysis:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --queues=analysis
      --hostname=analysis-worker@%h
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  # Learning worker (I/O-heavy, higher concurrency)
  celery-learning:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=4
      --queues=learning
      --hostname=learning-worker@%h
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### Environment Variables

**.env configuration:**

```bash
# Celery Worker Concurrency
CELERY_WORKER_CONCURRENCY=2          # Number of processes per worker
CELERY_WORKER_MAX_TASKS_PER_CHILD=100 # Restart worker after N tasks
```

**Dynamic configuration in code:**

```python
# backend/celery_config.py
import os

celery_config = {
    # Calculate concurrency based on CPU count
    # For ML-heavy tasks: use 50% of CPU cores
    # For I/O tasks: use 200% of CPU cores
    "worker_concurrency": int(os.cpu_count() * 0.5),
    # ... rest of config
}
```

#### Monitoring Concurrency

**Check current worker concurrency:**

```bash
# Flower dashboard - http://localhost:5555
# View:
# - Worker count
# - Concurrency per worker
# - Active tasks
# - Available processes

# Or via Celery command
docker-compose exec celery celery -A celery_app.celery_app inspect active
```

**Target metrics:**

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| **CPU usage per worker** | < 80% | Reduce concurrency |
| **Memory per worker** | < 80% of limit | Reduce concurrency or increase memory |
| **Queue depth** | < 10 tasks | Add more workers |
| **Task wait time** | < 30 seconds | Add workers or increase concurrency |

---

### 2. Prefetch Limits

Prefetching determines how many tasks a worker reserves before processing. Proper tuning prevents task starvation and reduces memory usage.

#### What is Prefetching?

```
Without Prefetch (multiplier=1):
┌────────────────────────────────────────────────────────┐
│  Worker pulls 1 task at a time                         │
│  ┌──────┐                                              │
│  │Task 1│ ← Processing now                            │
│  └──────┘                                              │
│  Queue: [Task 2] [Task 3] [Task 4]                     │
└────────────────────────────────────────────────────────┘

With Prefetch (multiplier=4):
┌────────────────────────────────────────────────────────┐
│  Worker pulls 4 tasks at once                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│  │Task 1│ │Task 2│ │Task 3│ │Task 4│ ← Reserved       │
│  │Proc. │ │Wait  │ │Wait  │ │Wait  │                  │
│  └──────┘ └──────┘ └──────┘ └──────┘                  │
│  Queue: [Task 5] [Task 6]                              │
└────────────────────────────────────────────────────────┘
```

**Benefits of prefetching:**
- Reduces queue communication overhead
- Improves throughput for short tasks
- Worker always has tasks ready

**Drawbacks of prefetching:**
- Other workers may starve if one worker hogs tasks
- Higher memory usage (reserved tasks held in memory)
- Not suitable for long-running tasks

#### Current Configuration

**AgentHR configuration:**

```python
# backend/celery_config.py
celery_config = {
    "worker_prefetch_multiplier": 1,  # Disabled prefetching
    # ...
}
```

**Why prefetch is disabled:**
- Resume analysis tasks are **long-running** (10-30 seconds)
- Tasks are **CPU-intensive** (not I/O bound)
- Prefetching would waste memory reserving tasks
- Better to let workers pull tasks as needed

#### When to Enable Prefetching

**Enable prefetching (multiplier > 1) for:**

| Task Type | Duration | Recommended Multiplier |
|-----------|----------|------------------------|
| **Short I/O tasks** | < 1 second | 4-8 |
| **Database queries** | < 5 seconds | 2-4 |
| **Email sending** | 1-3 seconds | 4 |
| **API callbacks** | < 2 seconds | 4-8 |

**Disable prefetching (multiplier = 1) for:**

| Task Type | Duration | Recommended Multiplier |
|-----------|----------|------------------------|
| **ML processing** | 10-60 seconds | 1 |
| **Resume analysis** | 10-30 seconds | 1 |
| **Model training** | 5-60 minutes | 1 |
| **Batch processing** | > 5 minutes | 1 |

#### Configuration Examples

**Enable prefetching for I/O worker:**

```yaml
# docker-compose.yml
services:
  celery-io-worker:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=4
      --prefetch-multiplier=4
      --queues=io,emails,notifications
    environment:
      - CELERY_WORKER_PREFETCH_MULTIPLIER=4
```

**Keep prefetch disabled for ML worker:**

```yaml
# docker-compose.yml
services:
  celery-ml-worker:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --prefetch-multiplier=1
      --queues=analysis,ml
    environment:
      - CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

#### Environment Variables

```bash
# .env
# Prefetch multiplier (1 = disabled, 4-8 = enabled for I/O tasks)
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

#### Monitoring Prefetch Impact

**Check if prefetching is causing issues:**

```bash
# Monitor queue distribution across workers
curl -s http://localhost:5555/api/workers | jq '.'

# Look for:
# - One worker with many reserved tasks
# - Other workers with no tasks
# - This indicates prefetching is unfair

# Check worker memory usage
docker stats $(docker-compose ps -q celery)
```

**Signs prefetch multiplier is too high:**
- One worker has many reserved tasks, others idle
- High memory usage per worker
- Queue appears empty but tasks aren't starting

**Solution:** Reduce `worker_prefetch_multiplier` or set to 1

---

### 3. Queue Separation

Queue separation ensures different task types are processed by dedicated workers, preventing resource conflicts and prioritization issues.

#### Current Queue Architecture

**Defined queues in `backend/celery_config.py`:**

```python
celery_config = {
    "task_routes": {
        # Resume analysis tasks
        "tasks.analysis_task.analyze_resume_async": {"queue": "analysis"},
        "tasks.analysis_task.*": {"queue": "analysis"},

        # Learning and feedback tasks
        "tasks.learning_tasks.aggregate_feedback_and_generate_synonyms": {"queue": "learning"},
        "tasks.learning_tasks.review_and_activate_synonyms": {"queue": "learning"},
        "tasks.learning_tasks.periodic_feedback_aggregation": {"queue": "learning"},
        "tasks.learning_tasks.*": {"queue": "learning"},

        # Performance monitoring tasks
        "tasks.performance_monitoring.*": {"queue": "learning"},

        # Model retraining tasks
        "tasks.model_retraining.*": {"queue": "learning"},

        # Audit and cleanup tasks
        "tasks.audit_tasks.cleanup_old_audit_logs": {"queue": "audit"},
        "tasks.audit_tasks.*": {"queue": "audit"},
    },
}
```

**Queue definitions:**

| Queue | Purpose | Task Type | Resource Usage |
|-------|---------|-----------|----------------|
| **analysis** | Resume analysis | ML-heavy | CPU: High, Memory: High |
| **learning** | Feedback aggregation, model training | Mixed | CPU: Medium, Memory: Medium |
| **audit** | Log cleanup, maintenance | I/O-heavy | CPU: Low, Memory: Low |
| **default** | Uncategorized tasks | Varies | Varies |

#### Queue Separation Benefits

**Without queue separation (all workers process all tasks):**

```
┌────────────────────────────────────────────────────────┐
│  Problem: ML analysis tasks hog all workers             │
│                                                         │
│  Queue: [Analysis] [Analysis] [Analysis] [Email]       │
│           ▼         ▼         ▼         ▼              │
│  Worker 1: [Analysis - Processing...]                  │
│  Worker 2: [Analysis - Processing...]                  │
│  Worker 3: [Analysis - Processing...]                  │
│  Worker 4: [Analysis - Processing...]                  │
│                                                         │
│  Result: Email task waits 30+ seconds                  │
└────────────────────────────────────────────────────────┘
```

**With queue separation (dedicated workers per queue):**

```
┌────────────────────────────────────────────────────────┐
│  Solution: Dedicated workers for each queue            │
│                                                         │
│  Analysis Queue: [Analysis] [Analysis] [Analysis]      │
│                    ▼         ▼         ▼               │
│           Analysis Worker 1, 2, 3 (ML-optimized)       │
│                                                         │
│  Email Queue:    [Email] [Email]                       │
│                    ▼         ▼                         │
│           Email Worker (I/O-optimized, high concurrency)│
│                                                         │
│  Result: Email processed immediately                   │
└────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Isolation**: Heavy tasks don't block light tasks
- **Optimization**: Workers tuned for specific task types
- **Priority**: Critical queues get dedicated resources
- **Scaling**: Scale queues independently based on load

#### Implementation Examples

**Option 1: Single worker, multiple queues (simple setup)**

```yaml
# docker-compose.yml
services:
  celery-worker:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --queues=analysis,learning,audit,default
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
```

**Option 2: Dedicated workers per queue (recommended for production)**

```yaml
# docker-compose.yml
services:
  # Analysis worker (ML-heavy, low concurrency, high memory)
  celery-analysis:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --queues=analysis
      --hostname=analysis-worker@%h
      --max-tasks-per-child=50
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_WORKER_PREFETCH_MULTIPLIER=1

  # Learning worker (medium load, balanced concurrency)
  celery-learning:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=4
      --queues=learning
      --hostname=learning-worker@%h
      --max-tasks-per-child=100
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_WORKER_PREFETCH_MULTIPLIER=2

  # Audit worker (I/O-heavy, high concurrency, low resources)
  celery-audit:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=4
      --queues=audit
      --hostname=audit-worker@%h
      --max-tasks-per-child=200
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_WORKER_PREFETCH_MULTIPLIER=4
```

#### Adding New Queues

**Step 1: Define queue routing in celery_config.py**

```python
# backend/celery_config.py
celery_config = {
    "task_routes": {
        # Add new queue for email notifications
        "tasks.email_tasks.send_email_notification": {"queue": "emails"},
        "tasks.email_tasks.*": {"queue": "emails"},
        # ... existing routes
    },
}
```

**Step 2: Create dedicated worker in docker-compose.yml**

```yaml
# docker-compose.yml
services:
  celery-emails:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=8
      --queues=emails
      --hostname=email-worker@%h
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_WORKER_PREFETCH_MULTIPLIER=4
```

**Step 3: Deploy and verify**

```bash
# Deploy new worker
docker-compose up -d celery-emails

# Verify queue is being processed
curl -s http://localhost:5555/api/workers | jq '.'
docker-compose logs -f celery-emails
```

#### Queue Monitoring

**Monitor queue depths in Flower:**

```bash
# Flower dashboard - http://localhost:5555
# Check each queue:
# - Current queue depth
# - Task processing rate
# - Worker availability

# Via API
curl -s http://localhost:5555/api/queues | jq '.'
```

**Target queue depths:**

| Queue | Target Depth | Action if Exceeded |
|-------|--------------|-------------------|
| **analysis** | < 5 | Add more analysis workers |
| **learning** | < 10 | Add more learning workers |
| **audit** | < 20 | Add more audit workers |
| **emails** | < 50 | Add more email workers |

---

### 4. Task Priorities

Task priorities ensure critical tasks are processed first when queues are backed up.

#### Priority Configuration

**Current configuration:**

```python
# backend/celery_config.py
celery_config = {
    "task_default_priority": 5,  # Default priority (0-9 scale)
    # ...
}
```

**Priority scale (0-9):**
- **9**: Highest priority (urgent)
- **7-8**: High priority
- **5**: Default priority
- **3-4**: Low priority
- **0-2**: Lowest priority (background tasks)

#### When to Use Priorities

**Use high priorities (7-9) for:**
- User-initiated resume analysis
- Real-time user-facing operations
- Time-sensitive notifications

**Use default priority (5) for:**
- Scheduled batch processing
- Periodic maintenance tasks
- Standard background operations

**Use low priorities (0-2) for:**
- Log cleanup
- Backup operations
- Data aggregation
- Non-critical reports

#### Implementation Examples

**Define task with priority:**

```python
# backend/tasks/analysis_task.py
from celery import shared_task

@shared_task(bind=True, priority=7)  # High priority
def analyze_resume_async(self, resume_id: str, ...):
    """Urgent resume analysis"""
    # Task implementation
    pass

@shared_task(bind=True, priority=2)  # Low priority
def cleanup_old_logs(self, days: int = 30):
    """Background log cleanup"""
    # Task implementation
    pass
```

**Override priority at runtime:**

```python
# Submit task with custom priority
from tasks.analysis_task import analyze_resume_async

# High priority analysis
task = analyze_resume_async.apply_async(
    args=['resume-123'],
    priority=8  # Override default priority
)

# Low priority batch
task = analyze_resume_async.apply_async(
    args=['resume-456'],
    priority=3  # Lower than default
)
```

**Priority-based queue routing:**

```python
# backend/celery_config.py
celery_config = {
    "task_routes": {
        # High-priority analysis tasks
        "tasks.analysis_task.analyze_resume_async": {
            "queue": "analysis",
            "priority": 7
        },
        # Low-priority cleanup
        "tasks.audit_tasks.cleanup_old_audit_logs": {
            "queue": "audit",
            "priority": 2
        },
    },
}
```

#### Monitoring Priorities

**Check task priorities in queue:**

```bash
# Via Redis CLI
docker-compose exec redis redis-cli

# List all tasks in analysis queue with priorities
LPREFIX analysis
# View all tasks (encoded, priority included)

# Or via Flower
curl -s http://localhost:5555/api/tasks | jq '.[] | {name: .name, args: .args, kwargs: .kwargs, priority: .priority}'
```

**Priority effectiveness metrics:**

| Metric | How to Measure | Target |
|--------|----------------|--------|
| **High-priority task wait time** | Flower dashboard | < 5 seconds |
| **Low-priority task wait time** | Flower dashboard | < 5 minutes |
| **Priority inversion frequency** | Logs (low-priority before high-priority) | 0 |

---

## Quick Reference: Celery Worker Tuning

### Configuration Checklist

- [ ] **Concurrency set** based on task type (ML: low, I/O: high)
- [ ] **Prefetch disabled** for long-running ML tasks (multiplier=1)
- [ ] **Queue separation** configured for different task types
- [ ] **Dedicated workers** for each major queue (analysis, learning, audit)
- [ ] **Resource limits** set in docker-compose.yml
- [ ] **Worker restart** configured (max_tasks_per_child)
- [ ] **Priorities defined** for critical vs non-critical tasks
- [ ] **Monitoring enabled** (Flower dashboard)

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Queue backup** | Insufficient workers or low concurrency | Add more workers or increase concurrency |
| **High memory usage** | Prefetch multiplier too high | Set `worker_prefetch_multiplier=1` |
| **CPU at 100%** | Concurrency too high for ML tasks | Reduce concurrency to CPU count / 2 |
| **Slow critical tasks** | No priority separation | Enable task priorities (7-9 for critical) |
| **Worker starvation** | One queue consuming all resources | Separate queues with dedicated workers |
| **OOM errors** | Memory limit too low or concurrency too high | Increase memory limit or reduce concurrency |

### Environment Variables

```bash
# .env - Celery Worker Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_MAX_TASKS_PER_CHILD=100
CELERY_TASK_DEFAULT_PRIORITY=5

# Queue-specific (set in docker-compose.yml)
CELERY_QUEUES=analysis,learning,audit,default
```

### Docker Compose Example

```yaml
# Recommended production setup
services:
  celery-analysis:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=2
      --queues=analysis
      --prefetch-multiplier=1
      --max-tasks-per-child=50
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - CELERY_WORKER_PREFETCH_MULTIPLIER=1

  celery-learning:
    build: ./backend
    command: >
      celery -A celery_app.celery_app worker
      --loglevel=info
      --concurrency=4
      --queues=learning
      --prefetch-multiplier=2
      --max-tasks-per-child=100
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Monitoring Commands

```bash
# Check worker status
curl -s http://localhost:5555/api/workers | jq '.'

# Check queue depths
curl -s http://localhost:5555/api/queues | jq '.'

# Check active tasks
curl -s http://localhost:5555/api/tasks | jq '.'

# Check worker resources
docker stats $(docker-compose ps -q celery-*)

# View worker logs
docker-compose logs -f celery-analysis
docker-compose logs -f celery-learning
```

---

## Redis Caching Strategies

Redis is a critical performance component in the AgentHR system, serving as both a cache for expensive operations and a message broker for Celery. Proper tuning ensures high cache hit rates while preventing memory exhaustion.

### Redis Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Redis Cache Layer                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Cache Namespaces                        │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  candidate:   Resume profiles, candidate lists       │  │
│  │  vacancy:     Job descriptions, requirements         │  │
│  │  match:       Matching results, scores               │  │
│  │  analytics:   Aggregated statistics, reports         │  │
│  │  taxonomy:    Skills, industries, categories         │  │
│  │  session:     User sessions, authentication          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Cache Key Format: {prefix}:{namespace}:{key}              │
│  Example: agenthr:candidate:profile:abc-123-def            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Celery Broker (DB 0)                    │  │
│  │  - Task queues (analysis, learning, audit)           │  │
│  │  - Task results storage                              │  │
│  │  - Worker coordination                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Memory Management:                                          │
│  - Max memory: 512MB (configurable)                         │
│  - Eviction policy: allkeys-lru                             │
│  - Persistence: AOF enabled                                 │
└─────────────────────────────────────────────────────────────┘
```

### Current Redis Configuration

**From `docker-compose.yml`:**

```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Configuration breakdown:**

| Setting | Value | Purpose |
|---------|-------|---------|
| `--maxmemory` | 512mb | Maximum memory Redis can use before eviction |
| `--maxmemory-policy` | allkeys-lru | Evict least recently used keys when memory limit reached |
| `--appendonly` | yes | Enable AOF persistence for durability |
| `memory limit` | 1G | Docker container memory limit (higher than Redis max) |
| `cpu limit` | 1.0 | Maximum CPU cores Redis can use |

**Cache service configuration (from `backend/services/cache_service.py`):**

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `key_prefix` | `agenthr` | Prefix for all cache keys |
| `default_ttl` | 3600 (1 hour) | Default time-to-live for cached entries |
| `max_connections` | 50 | Maximum connections in pool |
| `enabled` | `True` | Whether caching is enabled |

---

## 1. Memory Limits and Eviction Policies

### Understanding Redis Memory Management

**Redis memory usage components:**

```
┌────────────────────────────────────────────────────────────┐
│              Redis Memory Breakdown                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Total Memory: 512MB (maxmemory setting)                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Dataset: ~400MB (78%)                             │   │
│  │  - Cached ML model results                         │   │
│  │  - Candidate profiles                              │   │
│  │  - Match results                                   │   │
│  │  - Analytics aggregations                          │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  Overhead: ~100MB (20%)                            │   │
│  │  - Key metadata (expirations, access counts)       │   │
│  │  - Connection buffers                              │   │
│  │  - Data structure overhead                         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  When dataset + overhead > 512MB:                          │
│  → Eviction policy activates                               │
│  → Least recently used (LRU) keys removed                  │
│  → Memory freed for new data                              │
└────────────────────────────────────────────────────────────┘
```

### Eviction Policies

**Available eviction policies:**

| Policy | Behavior | Use Case |
|--------|----------|----------|
| **noeviction** | Return errors when memory limit reached | Development/testing only |
| **allkeys-lru** | Evict least recently used keys from all datasets | ✅ **Recommended for AgentHR** |
| **volatile-lru** | Evict LRU keys with TTL set only | When some data must never be evicted |
| **allkeys-random** | Evict random keys | Simple but less efficient |
| **volatile-random** | Evict random keys with TTL set only | Rarely used |
| **allkeys-lfu** | Evict least frequently used keys | When access frequency matters more than recency |
| **volatile-lfu** | Evict LFU keys with TTL set only | Specialized use cases |
| **volatile-ttl** | Evict keys with shortest TTL first | When TTL is the primary concern |

**Why `allkeys-lru` is recommended:**

- **Cache-intensive workload**: AgentHR primarily uses Redis for caching
- **No critical data**: All cached data can be recomputed if needed
- **Better hit rates**: LRU keeps frequently accessed data in memory
- **No TTL management overhead**: Don't need to set TTL on every key

### Memory Limit Sizing

**Guidelines for setting `maxmemory`:**

| Total System RAM | Recommended maxmemory | Rationale |
|------------------|----------------------|-----------|
| 2GB | 256mb | Conservative, leave room for OS and other services |
| 4GB | 512mb | ✅ **Current default** - good balance |
| 8GB | 1-2gb | More cache for larger datasets |
| 16GB+ | 2-4gb | High-throughput systems |

**Configuration examples:**

```yaml
# docker-compose.yml

# Small system (2GB RAM)
redis:
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        memory: 512M

# Medium system (4-8GB RAM) - Current default
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        memory: 1G

# Large system (16GB+ RAM)
redis:
  command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        memory: 3G
```

### Monitoring Memory Usage

**Check current memory usage:**

```bash
# View memory statistics
docker-compose exec redis redis-cli INFO memory

# Key metrics to watch:
# - used_memory_human: Current memory usage (e.g., "400M")
# - used_memory_peak_human: Peak memory usage
# - used_memory_percentage: % of maxmemory used
# - maxmemory_human: Configured memory limit

# Quick check
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

**Target metrics:**

| Metric | Target | Action |
|--------|--------|--------|
| **Memory usage** | < 80% of maxmemory | Normal operation |
| **Memory usage** | 80-90% of maxmemory | Monitor closely, consider increasing limit |
| **Memory usage** | > 90% of maxmemory | ⚠️ Increase maxmemory or reduce cache size |
| **Eviction rate** | < 10 keys/sec | Normal |
| **Eviction rate** | > 100 keys/sec | ⚠️ High eviction, cache churn - increase memory |

**Set up monitoring alerts:**

```python
# backend/monitoring/redis_metrics.py
from prometheus_client import Gauge

redis_memory_usage = Gauge('redis_memory_bytes', 'Redis memory usage')
redis_memory_max = Gauge('redis_memory_max_bytes', 'Redis max memory limit')
redis_eviction_rate = Gauge('redis_evictions_total', 'Redis evictions')

def update_redis_metrics():
    """Update Redis metrics for Prometheus"""
    import redis
    r = redis.Redis(host='redis', port=6379)

    info = r.info('memory')
    redis_memory_usage.set(info['used_memory'])
    redis_memory_max.set(info['maxmemory'])

    stats = r.info('stats')
    redis_eviction_rate.set(stats.get('evicted_keys', 0))
```

---

## 2. Cache Patterns for Different Data Types

### Cache Namespaces and Use Cases

**AgentHR cache namespace organization:**

```
agenthr:candidate:{type}:{id}
├─ profile:abc-123         → Candidate profile (TTL: 1 hour)
├─ list:filter_hash        → Filtered candidate list (TTL: 30 min)
└─ stats:daily:2024-02-04  → Daily statistics (TTL: 24 hours)

agenthr:vacancy:{type}:{id}
├─ details:vac-456         → Vacancy details (TTL: 1 hour)
└─ requirements:vac-456    → Extracted requirements (TTL: 6 hours)

agenthr:match:{type}:{resume_id}:{vacancy_id}
├─ score:abc-123:vac-456   → Match score (TTL: 2 hours)
└─ ranking:vac-456         → Ranked candidates for vacancy (TTL: 1 hour)

agenthr:analytics:{type}:{params}
├─ skills:popular          → Popular skills (TTL: 12 hours)
└─ placements:monthly      → Monthly placement stats (TTL: 24 hours)

agenthr:taxonomy:{type}:{id}
├─ skill:python            → Skill taxonomy (TTL: 7 days)
└─ industry:it             → Industry taxonomy (TTL: 7 days)

agenthr:session:{user_id}
└─ active:abc-123          → User session (TTL: 24 hours)
```

### Cache Pattern Examples

**Pattern 1: Cache-Aside (Lazy Loading)**

Most common pattern - load from cache, compute if miss.

```python
# backend/services/cache_service.py (simplified)
from services.cache_service import get_cache_service

def get_candidate_profile(candidate_id: str):
    """Get candidate profile with cache-aside pattern"""
    cache = get_cache_service()

    # Try cache first
    cached = cache.get('candidate', f'profile:{candidate_id}')
    if cached:
        logger.debug(f"Cache hit: candidate {candidate_id}")
        return cached

    # Cache miss - compute from database
    logger.debug(f"Cache miss: candidate {candidate_id}")
    profile = db.query(Candidate).filter_by(id=candidate_id).first()

    if profile:
        # Store in cache for next time
        cache.set('candidate', f'profile:{candidate_id}', profile.to_dict(), ttl=3600)

    return profile
```

**Pattern 2: Write-Through**

Write to cache and database simultaneously.

```python
def update_candidate_profile(candidate_id: str, data: dict):
    """Update candidate with write-through caching"""
    cache = get_cache_service()

    # Update database
    profile = db.query(Candidate).filter_by(id=candidate_id).first()
    profile.update(**data)
    db.commit()

    # Update cache immediately
    cache.set('candidate', f'profile:{candidate_id}', profile.to_dict(), ttl=3600)

    return profile
```

**Pattern 3: Write-Behind (Write-Back)**

Queue writes and apply asynchronously (advanced pattern).

```python
from celery import shared_task

@shared_task
def invalidate_candidate_cache_async(candidate_id: str):
    """Invalidate cache in background after database write"""
    cache = get_cache_service()
    cache.delete('candidate', f'profile:{candidate_id}')

def update_candidate_profile_async(candidate_id: str, data: dict):
    """Update candidate with cache invalidation in background"""
    # Update database immediately
    profile = db.query(Candidate).filter_by(id=candidate_id).first()
    profile.update(**data)
    db.commit()

    # Invalidate cache asynchronously
    invalidate_candidate_cache_async.delay(candidate_id)

    return profile
```

**Pattern 4: Cache Invalidation on Updates**

```python
# backend/services/cache_service.py (existing helper)
def invalidate_candidate_cache(candidate_id: str) -> int:
    """
    Invalidate all cache entries related to a specific candidate.

    This removes:
    - Candidate profile cache
    - All candidate list caches that may include this candidate
    """
    cache = get_cache_service()
    invalidated = 0

    # Invalidate candidate profile
    if cache.delete(CacheService.NAMESPACE_CANDIDATE, f"profile:{candidate_id}"):
        invalidated += 1

    # Invalidate all candidate list caches
    invalidated += cache.delete_pattern(CacheService.NAMESPACE_CANDIDATE, "list:*")

    return invalidated

# Usage in application
@app.put("/api/candidates/{candidate_id}")
def update_candidate(candidate_id: str, data: CandidateUpdate):
    """Update candidate and invalidate cache"""
    # Update database
    profile = update_candidate_in_db(candidate_id, data)

    # Invalidate cache
    invalidate_candidate_cache(candidate_id)

    return profile
```

### TTL Configuration Guidelines

**Recommended TTL by data type:**

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| **Candidate profiles** | 1 hour (3600s) | Profiles change occasionally, medium freshness required |
| **Candidate lists (filtered)** | 30 min (1800s) | Lists change frequently as candidates are added/updated |
| **Match results** | 2 hours (7200s) | Matching scores are stable for moderate periods |
| **Vacancy details** | 1 hour (3600s) | Similar to candidate profiles |
| **Analytics aggregations** | 12-24 hours | Slow-changing, can tolerate staleness |
| **Taxonomy data** | 7 days (604800s) | Rarely changes, long-lived cache |
| **User sessions** | 24 hours | Security + convenience balance |
| **ML model results** | 1 hour (3600s) | Recomputable but expensive |

**Configuration:**

```python
# backend/services/cache_service.py
class CacheService:
    # Namespace-specific TTL defaults
    NAMESPACE_TTL = {
        'candidate': 3600,      # 1 hour
        'vacancy': 3600,        # 1 hour
        'match': 7200,          # 2 hours
        'analytics': 43200,     # 12 hours
        'taxonomy': 604800,     # 7 days
        'session': 86400,       # 24 hours
    }

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache value with namespace-specific TTL"""
        if ttl is None:
            ttl = self.NAMESPACE_TTL.get(namespace, self.default_ttl)

        # ... rest of implementation
```

---

## 3. Cache Warming Strategies

Cache warming preloads frequently accessed data to avoid cold start penalties.

### When to Warm Cache

**Cache warming scenarios:**

| Scenario | Strategy | Example Data to Warm |
|----------|----------|---------------------|
| **Application startup** | Preload critical data | Popular candidates, active vacancies |
| **Scheduled updates** | Refresh after data changes | After analytics aggregation runs |
| **Deployments** | Warm after deployment | Rebuild cache from database |
| **Low-traffic periods** | Prepare for peak load | Pre-warm before business hours |

### Implementation Examples

**Startup cache warming:**

```python
# backend/main.py (FastAPI startup)
@app.on_event("startup")
async def warm_cache():
    """Warm cache on application startup"""
    logger.info("Starting cache warming...")

    cache = get_cache_service()

    # Warm popular candidates (most accessed in last 24 hours)
    popular_candidates = db.query(Candidate)\
        .order_by(Candidate.last_accessed.desc())\
        .limit(100)\
        .all()

    for candidate in popular_candidates:
        cache.set('candidate', f'profile:{candidate.id}', candidate.to_dict(), ttl=3600)

    logger.info(f"Warmed {len(popular_candidates)} candidate profiles")

    # Warm active vacancies
    active_vacancies = db.query(Vacancy)\
        .filter(Vacancy.status == 'active')\
        .all()

    for vacancy in active_vacancies:
        cache.set('vacancy', f'details:{vacancy.id}', vacancy.to_dict(), ttl=3600)

    logger.info(f"Warmed {len(active_vacancies)} vacancy details")
```

**Celery task for scheduled warming:**

```python
# backend/tasks/cache_tasks.py
from celery import shared_task

@shared_task
def warm_analytics_cache():
    """Warm analytics cache after aggregation"""
    cache = get_cache_service()

    # Popular skills (computationally expensive)
    popular_skills = get_popular_skills(limit=100)
    cache.set('analytics', 'skills:popular', popular_skills, ttl=43200)

    # Placement statistics
    placements = get_placement_stats(days=30)
    cache.set('analytics', 'placements:monthly', placements, ttl=86400)

    logger.info("Analytics cache warmed")
```

**Manual cache warming script:**

```bash
# scripts/warm_cache.sh
#!/bin/bash

echo "Starting manual cache warm..."

# Warm popular candidates
curl -X POST http://localhost:8000/api/cache/warm/candidates \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# Warm active vacancies
curl -X POST http://localhost:8000/api/cache/warm/vacancies

echo "Cache warming complete"
```

### Cache Warming Best Practices

**Do:**
- Warm during low-traffic periods (e.g., 3 AM)
- Prioritize frequently accessed data
- Monitor memory usage during warming
- Use batch operations for efficiency
- Log warming progress

**Don't:**
- Warm entire database (defeats caching purpose)
- Warm during peak traffic (adds load)
- Forget to invalidate stale data
- Overwhelm Redis with concurrent writes

---

## 4. Monitoring Cache Performance

### Key Performance Indicators

**Track these metrics:**

| Metric | How to Measure | Target | Alert Threshold |
|--------|----------------|--------|-----------------|
| **Cache hit rate** | `(keyspace_hits / (keyspace_hits + keyspace_misses)) * 100` | > 80% | < 70% |
| **Memory usage** | `used_memory / maxmemory * 100` | < 80% | > 90% |
| **Eviction rate** | `evicted_keys per second` | < 10/sec | > 100/sec |
| **Response time** | Redis command latency (p95) | < 1ms | > 5ms |
| **Connection pool** | Active connections / max_connections | < 80% | > 90% |

### Monitoring Commands

**Real-time monitoring:**

```bash
# 1. Overall cache statistics
docker-compose exec redis redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses|evicted_keys)'

# 2. Memory usage
docker-compose exec redis redis-cli INFO memory | grep -E '(used_memory|maxmemory)'

# 3. Calculate cache hit rate
#!/bin/bash
HITS=$(docker-compose exec redis redis-cli INFO stats | grep keyspace_hits | awk '{print $2}')
MISSES=$(docker-compose exec redis redis-cli INFO stats | grep keyspace_misses | awk '{print $2}')
TOTAL=$((HITS + MISSES))
if [ $TOTAL -gt 0 ]; then
  HIT_RATE=$(awk "BEGIN {printf \"%.2f\", ($HITS / $TOTAL) * 100}")
  echo "Cache hit rate: ${HIT_RATE}%"
else
  echo "No cache activity yet"
fi

# 4. Monitor in real-time
watch -n 1 'docker-compose exec redis redis-cli INFO stats | grep -E "(keyspace_hits|keyspace_misses)"'
```

**Grafana dashboard queries:**

```promql
# Cache hit rate
(rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))) * 100

# Memory usage percentage
(redis_memory_used_bytes / redis_memory_max_bytes) * 100

# Eviction rate
rate(redis_evicted_keys_total[5m])

# Command latency (p95)
histogram_quantile(0.95, rate(redis_command_duration_seconds_bucket[5m]))
```

### Health Check Endpoint

```python
# backend/api/health.py
from fastapi import APIResponse
from services.cache_service import get_cache_service

@app.get("/api/health/cache")
def cache_health():
    """Check Redis cache health"""
    cache = get_cache_service()
    health = cache.health_check()

    status_code = 200 if health['status'] == 'healthy' else 503

    # Add performance metrics
    redis_client = cache.redis_client
    if redis_client:
        info = redis_client.info()
        stats = redis_client.info('stats')

        hits = stats.get('keyspace_hits', 0)
        misses = stats.get('keyspace_misses', 0)
        total = hits + misses

        health.update({
            'hit_rate': f"{(hits / total * 100):.2f}%" if total > 0 else "N/A",
            'total_keys': health['key_count'],
            'evicted_keys': stats.get('evicted_keys', 0),
            'connections': redis_client.client_list().__len__(),
        })

    return JSONResponse(
        status_code=status_code,
        content=health
    )
```

### Troubleshooting Cache Issues

**Common cache problems:**

| Issue | Symptoms | Diagnosis | Solution |
|-------|----------|-----------|----------|
| **Low cache hit rate** | High database load, slow API responses | Hit rate < 70% | Increase TTL, check cache key generation, warm cache |
| **High memory usage** | Frequent evictions, OOM warnings | Memory > 90% of max | Increase maxmemory, reduce cache size, optimize data |
| **Connection pool exhaustion** | "Connection pool exhausted" errors | Active connections ≈ max | Increase max_connections, check for connection leaks |
| **Slow cache operations** | Cache API calls > 5ms | High latency | Check Redis CPU, reduce data size, use pipelining |
| **Cache stampede** | Cache misses cause database overload | Many identical misses | Use cache locking, extend TTL, implement request coalescing |

**Diagnostic script:**

```bash
#!/bin/bash
# scripts/diagnose_cache.sh

echo "=== Redis Cache Diagnostics ==="
echo ""

# 1. Basic info
echo "1. Redis Version:"
docker-compose exec redis redis-cli INFO server | grep redis_version

echo ""
echo "2. Memory Usage:"
docker-compose exec redis redis-cli INFO memory | grep -E '(used_memory|maxmemory|used_memory_percentage)'

echo ""
echo "3. Cache Performance:"
docker-compose exec redis redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses|evicted_keys)'

echo ""
echo "4. Connected Clients:"
docker-compose exec redis redis-cli CLIENT LIST | wc -l

echo ""
echo "5. Slowest Operations:"
docker-compose exec redis redis-cli SLOWLOG GET 10

echo ""
echo "6. Key Distribution by Namespace:"
for ns in candidate vacancy match analytics taxonomy session; do
  count=$(docker-compose exec redis redis-cli --scan --pattern "agenthr:${ns}:*" | wc -l)
  echo "  ${ns}: ${count} keys"
done
```

---

## Quick Reference: Redis Caching Strategies

### Configuration Checklist

- [ ] **maxmemory** set appropriately for system RAM (512mb default for 4GB systems)
- [ ] **Eviction policy** configured to `allkeys-lru`
- [ ] **Namespace separation** implemented for different data types
- [ ] **TTL values** configured per data type (see guidelines above)
- [ ] **Connection pooling** configured (max_connections: 50)
- [ ] **Cache warming** implemented for critical data
- [ ] **Monitoring** set up for hit rate, memory, evictions
- [ ] **Health checks** configured and tested

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Low hit rate (< 70%)** | TTL too short, cold cache, poor key design | Increase TTL, warm cache, check key generation |
| **High eviction rate** | Memory limit too low | Increase maxmemory, reduce cached data size |
| **OOM errors** | No memory limit set | Set maxmemory in redis command |
| **Stale data** | TTL too long, invalidation missing | Reduce TTL, implement invalidation on updates |
| **Cache avalanche** | All keys expire at once | Add random jitter to TTL (±10%) |
| **Connection pool exhausted** | Too many concurrent requests, leaks | Increase max_connections, check for leaks |

### Environment Variables

```bash
# .env - Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_KEY_PREFIX=agenthr
REDIS_CACHE_DEFAULT_TTL=3600
REDIS_CACHE_MAX_CONNECTIONS=50

# Memory limits (set in docker-compose.yml)
REDIS_MAXMEMORY=512mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Monitoring Commands

```bash
# Check cache performance
docker-compose exec redis redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses|evicted_keys)'

# Check memory usage
docker-compose exec redis redis-cli INFO memory | grep used_memory_human

# View cache keys by namespace
docker-compose exec redis redis-cli --scan --pattern "agenthr:candidate:*"

# Monitor in real-time
watch -n 1 'docker-compose exec redis redis-cli INFO stats'

# Health check
curl http://localhost:8000/api/health/cache
```

---

## PostgreSQL Optimization

PostgreSQL is the primary data store for the AgentHR system, handling all persistent data for resumes, candidates, vacancies, analytics, and more. Proper optimization ensures fast query performance and efficient resource utilization.

### PostgreSQL Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                            │
│  (FastAPI + SQLAlchemy ORM)                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection Pool (SQLAlchemy)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  pool_size=10, max_overflow=20                        │   │
│  │  pool_pre_ping=True (connection health checks)         │   │
│  │  asyncpg driver (async PostgreSQL)                     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Server                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Query Executor (with plan cache)                     │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  Index Scan (B-tree)                            │   │   │
│  │  │  Sequential Scan (full table)                   │   │   │
│  │  │  Bitmap Index Scan                             │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Shared Buffers (cache: ~25% of RAM)                  │   │
│  │  WAL (Write-Ahead Log)                                │   │
│  │  Autovacuum (maintenance worker)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Current PostgreSQL Configuration

**From `backend/database.py`:**

```python
engine = create_async_engine(
    settings.get_db_url_async(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,         # Verify connections before use
    pool_size=10,               # Base pool size
    max_overflow=20,            # Additional connections under load
)
```

**Configuration breakdown:**

| Setting | Value | Purpose |
|---------|-------|---------|
| `pool_size` | 10 | Number of persistent connections to maintain |
| `max_overflow` | 20 | Additional connections allowed under load (max 30 total) |
| `pool_pre_ping` | True | Test connections before using them (detect stale connections) |
| `echo` | False | Log SQL queries (True for DEBUG) |
| `future=True` | True | Use SQLAlchemy 2.0 style |

**Connection monitoring:**
The system includes automatic query performance monitoring via SQLAlchemy event listeners:
- Tracks query execution time
- Records metrics to Prometheus
- Categorizes queries by operation (SELECT, INSERT, UPDATE, DELETE)

---

## 1. Indexing Strategies

Indexes are the most impactful optimization for PostgreSQL. Proper indexes can improve query performance by 10-1000x.

### Understanding Index Types

**B-tree Index (Default)**

- **Use for**: Equality and range queries
- **Example**: `WHERE candidate_id = 'abc-123'` or `WHERE created_at > '2024-01-01'`
- **Best for**: Most queries including foreign keys, dates, IDs

```sql
-- B-tree index (default)
CREATE INDEX idx_resumes_candidate_id ON resumes(candidate_id);
CREATE INDEX idx_vacancies_created_at ON vacancies(created_at);
```

**GIN Index (Generalized Inverted Index)**

- **Use for**: JSON/JSONB columns, array columns, full-text search
- **Example**: `WHERE skills @> '["Python"]'` or `WHERE text_vector @@ to_tsquery('engineer')`
- **Best for**: Unstructured data, tag searches

```sql
-- GIN index for JSONB
CREATE INDEX idx_candidates_skills ON candidates USING GIN (skills);

-- GIN index for full-text search
CREATE INDEX idx_resumes_text_vector ON resumes USING GIN (to_tsvector('english', resume_text));
```

**Partial Index**

- **Use for**: Frequently queried subset of data
- **Example**: `WHERE status = 'active'` (most queries only need active records)
- **Benefit**: Smaller index size, faster maintenance

```sql
-- Partial index (only active vacancies)
CREATE INDEX idx_active_vacancies ON vacancies(created_at)
WHERE status = 'active';
```

**Composite Index**

- **Use for**: Queries with multiple conditions
- **Example**: `WHERE candidate_id = 'abc-123' AND created_at > '2024-01-01'`
- **Column order**: Most selective column first

```sql
-- Composite index
CREATE INDEX idx_matches_candidate_vacancy ON match_results(candidate_id, vacancy_id);
```

### Current Schema Index Recommendations

**High-Priority Indexes**

| Table | Column(s) | Type | Query Pattern |
|-------|-----------|------|---------------|
| **resumes** | `candidate_id` | B-tree | `WHERE candidate_id = ?` (get resumes for candidate) |
| **parsed_resumes** | `resume_id` | B-tree | `WHERE resume_id = ?` (join with resumes) |
| **resume_analyses** | `resume_id` | B-tree | `WHERE resume_id = ?` (get analysis for resume) |
| **candidates** | `created_at` | B-tree | `ORDER BY created_at DESC` (list candidates) |
| **job_vacancies** | `(status, created_at)` | Composite | `WHERE status = 'active' ORDER BY created_at` |
| **match_results** | `(candidate_id, vacancy_id)` | Composite | `WHERE candidate_id = ? AND vacancy_id = ?` |
| **match_results** | `match_score` | B-tree | `ORDER BY match_score DESC` (ranking) |
| **candidates** | `skills` | GIN | `WHERE skills @> '["Python"]'` (skill search) |

**Implementation script:**

```sql
-- File: backend/database/migrations/add_performance_indexes.py

-- Resume table indexes
CREATE INDEX IF NOT EXISTS idx_resumes_candidate_id ON resumes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON resumes(created_at DESC);

-- Parsed resume indexes
CREATE INDEX IF NOT EXISTS idx_parsed_resumes_resume_id ON parsed_resumes(resume_id);

-- Candidate indexes
CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates USING GIN (skills);

-- Vacancy indexes
CREATE INDEX IF NOT EXISTS idx_vacancies_status_created ON job_vacancies(status, created_at DESC);

-- Match result indexes
CREATE INDEX IF NOT EXISTS idx_match_results_candidate_vacancy ON match_results(candidate_id, vacancy_id);
CREATE INDEX IF NOT EXISTS idx_match_results_score ON match_results(match_score DESC);

-- Analysis result indexes
CREATE INDEX IF NOT EXISTS idx_resume_analyses_resume_id ON resume_analyses(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_created_at ON resume_analyses(created_at DESC);

-- Full-text search index (if using text search)
CREATE INDEX IF NOT EXISTS idx_resumes_fulltext ON resumes USING GIN (to_tsvector('english', resume_text));
```

### Index Maintenance

**Check for missing indexes:**

```sql
-- Find tables with no indexes (except system tables)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
    AND NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = pg_tables.schemaname
        AND tablename = pg_tables.tablename
    )
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Find unused indexes:**

```sql
-- Indexes that haven't been used (safe to drop)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Analyze index usage:**

```sql
-- Most frequently used indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

### Index Best Practices

**Do:**
- Index foreign keys (joans will be faster)
- Index columns used in WHERE clauses
- Index columns used in ORDER BY
- Use composite indexes for multi-column queries
- Use partial indexes for filtered subsets
- Run ANALYZE after creating indexes

**Don't::**
- Over-index (indexes slow down INSERT/UPDATE/DELETE)
- Index low-cardinality columns (e.g., boolean flags)
- Index columns rarely queried
- Forget to monitor index usage
- Create indexes without testing query plans

**Index size monitoring:**

```bash
# Check index sizes
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
"
```

---

## 2. Connection Pooling

Connection pooling reuses database connections to avoid the overhead of establishing new connections for each query.

### Current Pool Configuration

**SQLAlchemy pool settings (from `database.py`):**

```python
engine = create_async_engine(
    settings.get_db_url_async(),
    pool_size=10,           # Base pool size
    max_overflow=20,        # Additional connections under load
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600,      # Recycle connections after 1 hour
)
```

**Pool behavior:**

```
┌─────────────────────────────────────────────────────────────┐
│              SQLAlchemy Connection Pool                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Base Pool (pool_size=10):                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                 │
│  │Conn1│ │Conn2│ │Conn3│ │ ... │ │Conn10│                 │
│  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └───┬───┘                 │
│     │       │       │       │       │                      │
│     └───────┴───────┴───────┴───────┘                      │
│                       │                                     │
│                       ▼                                     │
│            Available for requests                          │
│                                                             │
│  Overflow Pool (max_overflow=20):                          │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                 │
│  │Conn11│ │Conn12│ │Conn13│ │ ... │ │Conn30│               │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                 │
│  Created on demand when base pool is exhausted              │
│  Returned to overflow when not needed                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Pool Sizing Guidelines

**Optimal pool size calculation:**

```
pool_size = (number of CPU cores) × (effective_spindle_count) × 2

For most systems:
pool_size = (CPU cores) × 2

With async (FastAPI):
pool_size = (CPU cores) × 4
```

**Recommended pool sizes by system size:**

| System CPU | Concurrent Requests | pool_size | max_overflow | Max Connections |
|------------|---------------------|-----------|--------------|-----------------|
| 2 cores | 10 | 5 | 10 | 15 |
| 4 cores | 50 | 10 | 20 | ✅ **30 (current)** |
| 8 cores | 100 | 16 | 32 | 48 |
| 16+ cores | 500+ | 32 | 64 | 96 |

**Why pool_size=10 for 4-core system?**
- Each connection runs in a separate thread/process
- Too many connections cause context switching overhead
- PostgreSQL has connection overhead (memory, process management)
- Better to queue requests than overload the database

### Connection Pool Configuration Examples

**Small system (2 cores, low traffic):**

```python
# backend/database.py
engine = create_async_engine(
    settings.get_db_url_async(),
    pool_size=5,            # Reduced for 2-core system
    max_overflow=10,        # Allow bursts
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

**Large system (8+ cores, high traffic):**

```python
engine = create_async_engine(
    settings.get_db_url_async(),
    pool_size=20,           # Increased for 8-core system
    max_overflow=30,        # Allow large bursts
    pool_pre_ping=True,
    pool_recycle=1800,      # Recycle more frequently
    pool_timeout=30,        # Wait 30s for connection before error
)
```

### Monitoring Connection Pool

**Check active connections:**

```bash
# Active connections vs max
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT
    count(*) AS active_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections,
    round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 2) AS utilization_percent
FROM pg_stat_activity
WHERE state = 'active';
"
```

**Connection distribution by state:**

```bash
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT
    state,
    count(*) AS connections,
    count(*) FILTER (WHERE query NOT LIKE '%pg_stat_activity%') AS active_queries
FROM pg_stat_activity
GROUP BY state
ORDER BY count(*) DESC;
"
```

**Target metrics:**

| Metric | Target | Action |
|--------|--------|--------|
| **Active connections** | < 50% of pool | Normal |
| **Pool utilization** | < 80% | Monitor |
| **Pool utilization** | > 90% | Increase pool_size |
| **Connection wait time** | < 100ms | Normal |
| **Connection wait time** | > 500ms | Increase pool or reduce queries |

### Connection Pool Best Practices

**1. Use pool_pre_ping in production:**

```python
# Detects and replaces stale connections (e.g., DB restart)
pool_pre_ping=True
```

**2. Set appropriate timeout:**

```python
pool_timeout=30  # Seconds to wait for connection before error
```

**3. Recycle connections periodically:**

```python
pool_recycle=3600  # Recycle after 1 hour (prevents connection leaks)
```

**4. Monitor pool exhaustion:**

```python
# Log warnings when pool is exhausted
from sqlalchemy import event

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.debug(f"New connection created. Pool size: {engine.pool.size()}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    pool_size = engine.pool.size()
    if pool_size >= engine.pool._max_overflow:
        logger.warning(f"Connection pool exhausted! Size: {pool_size}")
```

**5. Use environment-specific settings:**

```python
# config.py
import os

def get_db_pool_settings():
    """Return pool settings based on environment"""
    if os.getenv("ENVIRONMENT") == "production":
        return {
            "pool_size": 20,
            "max_overflow": 30,
            "pool_recycle": 3600,
        }
    else:
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 1800,
        }
```

---

## 3. Query Optimization

Query optimization improves performance by ensuring queries use indexes efficiently and avoid expensive operations.

### Query Analysis Tools

**EXPLAIN ANALYZE**

See how PostgreSQL executes queries:

```sql
-- Basic query plan
EXPLAIN
SELECT * FROM candidates WHERE created_at > '2024-01-01';

-- Detailed plan with actual execution time
EXPLAIN ANALYZE
SELECT * FROM candidates WHERE created_at > '2024-01-01';

-- Format with buffers (shows memory usage)
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM candidates WHERE created_at > '2024-01-01';
```

**Reading EXPLAIN output:**

```
─┬─ Index Scan using idx_candidates_created_at on candidates  (cost=0.42..1234.56 rows=1000 width=500) (actual time=0.123..45.678 rows=987 loops=1)
 │                                           │
 │                                           └─ Actual rows returned
 │                         └─ Estimated rows
 └─ Index used (GOOD!)
```

**Key indicators:**
- ✅ **Index Scan**: Using index (fast)
- ⚠️ **Seq Scan**: Full table scan (slow - need index)
- ⚠️ **high cost**: Expensive query
- ⚠️ **actual time >> estimated time**: Statistics out of date (run ANALYZE)

### Common Query Performance Issues

**Issue 1: N+1 Query Problem**

```python
# ❌ BAD: N+1 queries (1 query to get candidates + N queries for each candidate's skills)
candidates = db.query(Candidate).all()
for candidate in candidates:
    skills = db.query(Skill).filter_by(candidate_id=candidate.id).all()  # Separate query per candidate!

# ✅ GOOD: Use eager loading (2 queries total)
from sqlalchemy.orm import selectinload

candidates = db.query(Candidate)\
    .options(selectinload(Candidate.skills))\
    .all()  # Skills loaded in same query

# Or use joined load for 1 query
from sqlalchemy.orm import joinedload

candidates = db.query(Candidate)\
    .options(joinedload(Candidate.skills))\
    .all()
```

**Issue 2: Missing WHERE clause indexes**

```sql
-- ❌ BAD: Full table scan (no index on email)
SELECT * FROM candidates WHERE email = 'user@example.com';

-- ✅ GOOD: Index scan
CREATE INDEX idx_candidates_email ON candidates(email);
SELECT * FROM candidates WHERE email = 'user@example.com';
```

**Issue 3: SELECT \***

```python
# ❌ BAD: Fetches all columns (more data transfer)
candidates = db.query(Candidate).all()

# ✅ GOOD: Fetch only needed columns
candidates = db.query(Candidate.id, Candidate.name, Candidate.email).all()
```

**Issue 4: Unnecessary ORDER BY**

```sql
-- ❌ BAD: Expensive sort (no index)
SELECT * FROM candidates ORDER BY name LIMIT 10;

-- ✅ GOOD: Use index for sort
CREATE INDEX idx_candidates_name ON candidates(name);
SELECT * FROM candidates ORDER BY name LIMIT 10;
```

**Issue 5: Large IN clauses**

```sql
-- ❌ BAD: IN clause with thousands of values
SELECT * FROM candidates WHERE id IN ('id1', 'id2', ..., 'id10000');

-- ✅ GOOD: Use temporary table or CTE
CREATE TEMP TABLE candidate_ids (id VARCHAR);
COPY candidate_ids FROM '/tmp/ids.csv';
SELECT c.* FROM candidates c JOIN candidate_ids ci ON c.id = ci.id;
```

### Query Optimization Techniques

**1. Use appropriate indexes**

```sql
-- Create indexes for common query patterns
CREATE INDEX idx_candidates_name_email ON candidates(name, email);
CREATE INDEX idx_resumes_status_created ON resumes(status, created_at DESC);
```

**2. Use partial indexes for filtered queries**

```sql
-- Only index active vacancies (most queries)
CREATE INDEX idx_active_vacancies ON vacancies(created_at)
WHERE status = 'active';
```

**3. Use covering indexes (include columns)**

```sql
-- Include columns to avoid table lookup
CREATE INDEX idx_match_results_covering ON match_results(candidate_id, vacancy_id)
INCLUDE (match_score, created_at);
```

**4. Use CTEs for complex queries**

```sql
-- Common Table Expression (CTE) for readability
WITH ranked_candidates AS (
    SELECT
        c.id,
        c.name,
        m.match_score,
        RANK() OVER (ORDER BY m.match_score DESC) as rank
    FROM candidates c
    JOIN match_results m ON c.id = m.candidate_id
    WHERE m.vacancy_id = 'vac-123'
)
SELECT * FROM ranked_candidates WHERE rank <= 10;
```

**5. Use materialized views for expensive aggregations**

```sql
-- Create materialized view (refreshed periodically)
CREATE MATERIALIZED VIEW mv_candidate_stats AS
SELECT
    date_trunc('day', created_at) as date,
    count(*) as new_candidates,
    avg(EXTRACT(YEAR FROM AGE(NOW(), created_at))) as avg_age
FROM candidates
GROUP BY date_trunc('day', created_at);

-- Refresh periodically
REFRESH MATERIALIZED VIEW mv_candidate_stats;

-- Query is instant (no computation)
SELECT * FROM mv_candidate_stats ORDER BY date DESC LIMIT 30;
```

### Slow Query Logging

**Enable slow query logging:**

```sql
-- Log queries taking longer than 1 second
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Reload configuration
SELECT pg_reload_conf();
```

**View slow queries:**

```bash
# Check log file
docker-compose exec db tail -f /var/log/postgresql/postgresql.log | grep "duration:"
```

**Find slow queries in pg_stat_statements:**

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT
    query,
    calls,
    total_exec_time / 1000 as total_time_seconds,
    mean_exec_time / 1000 as avg_time_seconds,
    stddev_exec_time / 1000 as stddev_time_seconds
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### Query Optimization Checklist

Before marking queries as optimized, verify:

- [ ] **All WHERE clauses indexed**: Columns in WHERE, JOIN, ORDER BY have indexes
- [ ] **No N+1 queries**: Use eager loading (selectinload, joinedload)
- [ ] **SELECT specific columns**: Avoid SELECT *
- [ ] **EXPLAIN ANALYZE reviewed**: Query uses index scans, not seq scans
- [ ] **No unnecessary ORDER BY**: Remove if not needed
- [ ] **Pagination used**: LIMIT/OFFSET for large result sets
- [ ] **Connection pooling enabled**: Reusing connections
- [ ] **Prepared statements used**: Parameterized queries (SQLAlchemy does this)

---

## 4. Database Vacuuming and Maintenance

PostgreSQL requires periodic maintenance to reclaim space and update statistics.

### Understanding MVCC and Bloat

**How PostgreSQL works (MVCC):**

```
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL MVCC (Multi-Version Concurrency)    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. UPDATE candidate SET name = 'New Name' WHERE id = 1    │
│                                                             │
│  ┌─────────────┐       ┌─────────────┐                     │
│  │  OLD row    │       │  NEW row    │                     │
│  │  (id=1)     │  ──▶  │  (id=1)     │                     │
│  │  name=Old   │       │  name=New   │                     │
│  │  (dead)     │       │  (live)     │                     │
│  └─────────────┘       └─────────────┘                     │
│        │                                                   │
│        └─ Dead row remains until VACUUM                    │
│                                                             │
│  2. Over time, dead rows accumulate (table bloat)          │
│  3. VACUUM removes dead rows and reclaims space            │
│  4. ANALYZE updates query planning statistics              │
└─────────────────────────────────────────────────────────────┘
```

### Autovacuum Configuration

**Current autovacuum settings (check):**

```sql
-- View autovacuum settings
SELECT name, setting, unit, short_desc
FROM pg_settings
WHERE name LIKE 'autovacuum%'
ORDER BY name;
```

**Recommended autovacuum tuning for AgentHR:**

```sql
-- Aggressive autovacuum for high-write tables
ALTER TABLE candidates SET (
    autovacuum_vacuum_scale_factor = 0.1,      -- Vacuum after 10% changes (default: 20%)
    autovacuum_analyze_scale_factor = 0.05,    -- Analyze after 5% changes (default: 10%)
    autovacuum_vacuum_threshold = 100           -- Min 100 rows before vacuum
);

ALTER TABLE resumes SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE match_results SET (
    autovacuum_vacuum_scale_factor = 0.2,      -- Higher threshold for high-traffic table
    autovacuum_analyze_scale_factor = 0.1
);
```

### Manual Vacuum and Analyze

**When to run manually:**
- After bulk data load/delete
- Before major reporting periods
- When autovacuum isn't keeping up
- After schema changes

**Commands:**

```sql
-- Standard vacuum (reclaims space, doesn't lock table)
VACUUM candidates;

-- Vacuum + analyze (reclaims space + updates statistics)
VACUUM ANALYZE candidates;

-- Full vacuum (locks table, rewrites file completely - use carefully!)
VACUUM FULL candidates;  -- Only during maintenance window!

-- Analyze only (update statistics without vacuum)
ANALYZE candidates;
```

**Automated maintenance script:**

```python
# backend/tasks/maintenance_tasks.py
from celery import shared_task

@shared_task
def weekly_maintenance():
    """Run weekly database maintenance"""
    import asyncio
    from database import get_db
    from sqlalchemy import text

    async def run_maintenance():
        async with get_db() as db:
            # Vacuum frequently updated tables
            await db.execute(text("VACUUM ANALYZE candidates"))
            await db.execute(text("VACUUM ANALYZE resumes"))
            await db.execute(text("VACUUM ANALYZE match_results"))

            # Analyze all tables
            await db.execute(text("ANALYZE"))

        logger.info("Database maintenance completed")

    asyncio.run(run_maintenance())
```

**Schedule with Celery Beat:**

```python
# celerybeat.py
from celery.schedules import crontab

beat_schedule = {
    'weekly-db-maintenance': {
        'task': 'tasks.maintenance_tasks.weekly_maintenance',
        'schedule': crontab(hour=2, day_of_week=0),  # 2 AM every Sunday
    },
}
```

### Monitoring Database Bloat

**Check table bloat:**

```sql
-- Create bloat monitoring function
CREATE OR REPLACE FUNCTION estimate_table_bloat() RETURNS TABLE(
    schemaname TEXT,
    tablename TEXT,
    table_size BIGINT,
    bloat_size BIGINT,
    bloat_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname,
        tablename,
        pg_total_relation_size(schemaname||'.'||tablename) as table_size,
        pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename) as bloat_size,
        100.0 * (pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) /
            NULLIF(pg_total_relation_size(schemaname||'.'||tablename), 0) as bloat_percentage
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY bloat_percentage DESC;
END;
$$ LANGUAGE plpgsql;

-- Check bloat
SELECT * FROM estimate_table_bloat();
```

**Target bloat levels:**

| Table Type | Acceptable Bloat | Action Required |
|------------|------------------|-----------------|
| High-write (candidates, match_results) | < 20% | OK |
| High-write (candidates, match_results) | 20-50% | Schedule vacuum |
| High-write (candidates, match_results) | > 50% | ⚠️ Immediate vacuum needed |
| Low-write (taxonomy, config) | < 10% | OK |
| Low-write (taxonomy, config) | > 20% | Vacuum recommended |

### Database Statistics

**Update statistics after major changes:**

```sql
-- Analyze all tables
ANALYZE;

-- Analyze specific table
ANALYZE candidates;

-- Analyze specific column
ANALYZE candidates (name, email);
```

**Check when statistics were last updated:**

```sql
SELECT
    schemaname,
    tablename,
    last_autovacuum,
    last_autoanalyze,
    last_vacuum,
    last_analyze,
    autovacuum_count,
    autoanalyze_count
FROM pg_stat_user_tables
ORDER BY last_analyze NULLS LAST;
```

### Reindexing

**When to reindex:**
- Index bloat > 30%
- Slow queries despite correct indexes
- After bulk data updates

**Reindex commands:**

```sql
-- Reindex specific index (no locking!)
REINDEX INDEX CONCURRENTLY idx_candidates_created_at;

-- Reindex entire table (locks table - use during maintenance!)
REINDEX TABLE candidates;  -- Only in maintenance window

-- Reindex database (locks all tables - very careful!)
REINDEX DATABASE agenthr;  -- Only in maintenance window!
```

**Check index bloat:**

```sql
-- Find bloated indexes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## Quick Reference: PostgreSQL Optimization

### Configuration Checklist

- [ ] **Indexes created** for all foreign keys, WHERE, JOIN, ORDER BY columns
- [ ] **Connection pool sized** appropriately (pool_size=10, max_overflow=20 default)
- [ ] **pool_pre_ping enabled** to detect stale connections
- [ ] **Slow query logging** enabled (log_min_duration_statement=1000)
- [ ] **Autovacuum tuned** for high-write tables
- [ ] **pg_stat_statements enabled** for query analysis
- [ ] **Regular VACUUM ANALYZE** scheduled (weekly)
- [ ] **EXPLAIN ANALYZE** used for slow queries
- [ ] **N+1 queries eliminated** using eager loading
- [ ] **Monitoring** set up for connection pool, query performance

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Slow query (< 1s)** | Missing index | Create index on WHERE/JOIN columns |
| **Slow query (> 10s)** | Full table scan | Create index, check query plan |
| **N+1 queries** | ORM lazy loading | Use selectinload/joinedload |
| **High CPU usage** | Too many connections | Reduce pool_size, use PgBouncer |
| **Disk I/O high** | Seq scans, no caching | Add indexes, increase shared_buffers |
| **Table bloat** | Insufficient vacuum | Tune autovacuum, run manual VACUUM |
| **Index bloat** | High write/delete | REINDEX INDEX CONCURRENTLY |
| **Connection exhaustion** | Pool too small | Increase pool_size or max_overflow |
| **Stale statistics** | No ANALYZE | Run ANALYZE after data changes |
| **Lock contention** | Long transactions | Keep transactions short, use READ COMMITTED |

### Environment Variables

```bash
# .env - PostgreSQL Configuration
DATABASE_URL=postgresql://agenthr:password@db:5432/agenthr
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_ECHO=false  # Set to true for SQL query logging
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=agenthr
      - POSTGRES_USER=agenthr
      - POSTGRES_PASSWORD=password
      # Performance tuning
      - shared_buffers=256MB          # 25% of RAM (1GB system)
      - effective_cache_size=1GB       # 50-75% of RAM
      - maintenance_work_mem=128MB     # For vacuum/analyze
      - checkpoint_completion_target=0.9
      - wal_buffers=16MB
      - default_statistics_target=100  # Better query plans
      - random_page_cost=1.1           # For SSD storage
      - effective_io_concurrency=200   # For SSD storage
      - work_mem=4MB                   # Per-operation memory
      - min_wal_size=1GB
      - max_wal_size=4GB
      # Logging
      - log_min_duration_statement=1000  # Log slow queries
      - log_line_prefix='%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
      - log_checkpoints=on
      - log_connections=on
      - log_disconnections=on
      - log_lock_waits=on
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Monitoring Commands

```bash
# Check connection pool usage
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT count(*) as active_connections,
    (SELECT setting::int FROM pg_settings WHERE name='max_connections') as max_connections
FROM pg_stat_activity WHERE state='active';
"

# Check slow queries
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check table bloat
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname='public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Check index usage
docker-compose exec db psql -U agenthr -d agenthr -c "
SELECT schemaname, tablename, indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 20;
"

# Run vacuum analyze
docker-compose exec db psql -U agenthr -d agenthr -c "VACUUM ANALYZE;"
```

---

## Frontend Performance

Frontend performance optimization ensures fast load times, smooth interactions, and efficient resource utilization. The AgentHR frontend uses Vite with React and implements several performance optimization strategies.

### Overview

The frontend performance stack includes:

```
┌─────────────────────────────────────────────────────────────┐
│                     React Application                       │
│                   (Component Level)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Performance Optimization                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Code Splitting│  │Lazy Loading  │  │Virtualization│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Vite Build Pipeline                       │
│              Bundle Optimization + Minification              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Browser (Production Build)                  │
│              Optimized Chunks + Caching Strategy            │
└─────────────────────────────────────────────────────────────┘
```

### Performance Characteristics

| Optimization Type | Impact | Use Case |
|-------------------|--------|----------|
| **Code Splitting** | High (Initial Load) | Separate vendor chunks, route-based splitting |
| **Lazy Loading** | High (Initial Load) | Heavy components, modal dialogs, charts |
| **Virtualization** | High (Rendering) | Large lists (100+ items), tables, grids |
| **Bundle Optimization** | Medium (Bundle Size) | Tree shaking, minification, compression |
| **API Call Optimization** | Medium (Response Time) | Request batching, caching, pagination |

---

## 1. Code Splitting and Lazy Loading

Code splitting divides your application into smaller chunks that are loaded on demand, reducing the initial bundle size and improving load times.

### Manual Chunk Splitting

The Vite configuration defines manual chunks for better caching:

**Configuration:** `frontend/vite.config.ts`

```typescript
rollupOptions: {
  output: {
    manualChunks: {
      // Separate vendor chunks for better caching
      'react-vendor': ['react', 'react-dom', 'react-router-dom'],
      'mui-vendor': ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
      'api-vendor': ['axios'],
      'form-vendor': ['react-hook-form', 'zod', '@hookform/resolvers'],
      'i18n-vendor': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
      'dnd-vendor': ['@hello-pangea/dnd', 'react-window'],
    },
  },
}
```

**Benefits:**
- **Better Caching**: Vendor chunks change rarely, so browsers cache them longer
- **Parallel Loading**: Chunks load in parallel, reducing total load time
- **Incremental Updates**: Only changed chunks need to be re-downloaded

### Route-Based Code Splitting

Split routes into separate chunks loaded on navigation:

```tsx
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Lazy load route components
const Dashboard = lazy(() => import('@pages/Dashboard'));
const CandidatesList = lazy(() => import('@pages/CandidatesList'));
const CandidateDetails = lazy(() => import('@pages/CandidateDetails'));
const ResumeAnalysis = lazy(() => import('@pages/ResumeAnalysis'));
const Settings = lazy(() => import('@pages/Settings'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/candidates" element={<CandidatesList />} />
          <Route path="/candidates/:id" element={<CandidateDetails />} />
          <Route path="/analyze" element={<ResumeAnalysis />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

// Loading component
function LoadingSpinner() {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <CircularProgress />
    </Box>
  );
}
```

### Component-Level Lazy Loading

Lazy load heavy components that aren't immediately visible:

```tsx
import { lazy, Suspense, useState } from 'react';

// Lazy load heavy components
const ChartComponent = lazy(() => import('@components/ChartComponent'));
const RichTextEditor = lazy(() => import('@components/RichTextEditor'));
const PdfViewer = lazy(() => import('@components/PdfViewer'));

function ResumeAnalysis() {
  const [showChart, setShowChart] = useState(false);

  return (
    <Box>
      <Button onClick={() => setShowChart(true)}>Show Analysis Chart</Button>

      {showChart && (
        <Suspense fallback={<CircularProgress />}>
          <ChartComponent data={analysisData} />
        </Suspense>
      )}
    </Box>
  );
}
```

### Modal and Dialog Lazy Loading

Lazy load modal content:

```tsx
import { lazy, Suspense } from 'react';
import { Dialog, DialogTitle, DialogContent } from '@mui/material';

// Lazy load modal content
const BulkUploadModal = lazy(() => import('@components/BulkUploadModal'));
const ExportDialog = lazy(() => import('@components/ExportDialog'));

function CandidatesList() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setUploadModalOpen(true)}>Bulk Upload</Button>

      <Dialog open={uploadModalOpen} onClose={() => setUploadModalOpen(false)}>
        <Suspense fallback={<CircularProgress />}>
          <BulkUploadModal onClose={() => setUploadModalOpen(false)} />
        </Suspense>
      </Dialog>
    </>
  );
}
```

---

## 2. Virtualization for Large Lists

Virtualization renders only visible items in a list, dramatically improving performance for large datasets (100+ items).

### react-window Implementation

The application uses `react-window` for efficient list rendering:

```tsx
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

interface Candidate {
  id: string;
  name: string;
  email: string;
  status: string;
}

function VirtualizedCandidateList({ candidates }: { candidates: Candidate[] }) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const candidate = candidates[index];

    return (
      <div style={style} className="candidate-row">
        <ListItemText
          primary={candidate.name}
          secondary={candidate.email}
        />
        <Chip label={candidate.status} size="small" />
      </div>
    );
  };

  return (
    <Box sx={{ height: 600, width: '100%' }}>
      <AutoSizer>
        {({ height, width }) => (
          <FixedSizeList
            height={height}
            width={width}
            itemSize={80} // Height of each row
            itemCount={candidates.length}
            overscanCount={5} // Render 5 extra items above/below viewport
          >
            {Row}
          </FixedSizeList>
        )}
      </AutoSizer>
    </Box>
  );
}
```

### Virtualized Grid for Tables

Use `react-window` for large data tables:

```tsx
import { VariableSizeGrid } from 'react-window';

interface Column {
  key: string;
  label: string;
  width: number;
}

function VirtualizedTable({ data, columns }: { data: any[]; columns: Column[] }) {
  const getColumnWidth = (index: number) => columns[index].width;

  const Cell = ({ columnIndex, rowIndex, style }: { columnIndex: number; rowIndex: number; style: React.CSSProperties }) => {
    const column = columns[columnIndex];
    const value = data[rowIndex][column.key];

    return (
      <div style={style} className="table-cell">
        {value}
      </div>
    );
  };

  return (
    <AutoSizer>
      {({ height, width }) => (
        <VariableSizeGrid
          height={height}
          width={width}
          columnCount={columns.length}
          columnWidth={getColumnWidth}
          rowCount={data.length}
          rowHeight={() => 60} // Fixed row height
          overscanColumnCount={2}
          overscanRowCount={5}
        >
          {Cell}
        </VariableSizeGrid>
      )}
    </AutoSizer>
  );
}
```

### Virtualization Benefits

| Scenario | Without Virtualization | With Virtualization |
|----------|------------------------|---------------------|
| **1,000 items list** | 2-5 seconds render time | < 100ms render time |
| **Memory usage** | 50-100MB | 5-10MB |
| **Scroll performance** | Laggy | Smooth (60 FPS) |
| **Initial load** | Heavy DOM | Light DOM |

### When to Use Virtualization

**Use virtualization when:**
- Lists have 100+ items
- Tables with 50+ rows
- Grid layouts with many cells
- Rendering performance is critical

**Don't use virtualization when:**
- Lists have < 50 items
- Items have variable, unpredictable heights
- You need simple scroll-to-bottom behavior

---

## 3. Bundle Optimization

Optimize bundle size through configuration and best practices.

### Vite Build Configuration

**Configuration:** `frontend/vite.config.ts`

```typescript
build: {
  outDir: 'dist',
  sourcemap: false, // Disable sourcemaps in production for better performance
  minify: 'terser', // Use terser for better minification
  target: 'es2015', // Target modern browsers for smaller bundle size
  cssCodeSplit: true, // Enable CSS code splitting
  chunkSizeWarningLimit: 1000, // Warn for chunks > 1MB

  rollupOptions: {
    output: {
      // Optimize chunk filenames for long-term caching
      chunkFileNames: 'assets/js/[name]-[hash].js',
      entryFileNames: 'assets/js/[name]-[hash].js',
      assetFileNames: (assetInfo) => {
        const name = assetInfo.name || '';
        if (name.endsWith('.css')) {
          return 'assets/css/[name]-[hash][extname]';
        }
        if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(name)) {
          return 'assets/images/[name]-[hash][extname]';
        }
        if (/\.(woff2?|eot|ttf|otf)$/.test(name)) {
          return 'assets/fonts/[name]-[hash][extname]';
        }
        return 'assets/[name]-[hash][extname]';
      },
    },
    // Treeshake console logs in production
    treeshake: {
      moduleSideEffects: false,
    },
  },

  // terser options for better minification
  terserOptions: {
    compress: {
      drop_console: true, // Remove console.* in production
      drop_debugger: true,
      pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
    },
    format: {
      comments: false, // Remove comments
    },
  },
}
```

### Dependency Optimization

Pre-bundle frequently used dependencies:

```typescript
optimizeDeps: {
  include: [
    'react',
    'react-dom',
    'react-router-dom',
    '@mui/material',
    '@mui/icons-material',
    'axios',
    'i18next',
    'react-i18next',
  ],
}
```

### Bundle Analysis

Analyze bundle size to identify optimization opportunities:

```bash
# Install bundle analyzer
npm install --save-dev rollup-plugin-visualizer

# Add to vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: './dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});
```

Run build with analysis:

```bash
npm run build
open dist/stats.html
```

### Bundle Size Targets

| Bundle Type | Target Size | Maximum |
|-------------|-------------|---------|
| **Initial JS** | < 200KB | < 400KB |
| **Per route chunk** | < 100KB | < 200KB |
| **Vendor chunks** | < 300KB each | < 500KB |
| **CSS** | < 50KB | < 100KB |
| **Total (gzipped)** | < 500KB | < 1MB |

### Tree Shaking Best Practices

1. **Use ES modules**: Import specific exports instead of entire libraries

```tsx
// ❌ Bad - imports entire library
import _ from 'lodash';
import * as Icons from '@mui/icons-material';

// ✅ Good - imports specific exports
import debounce from 'lodash/debounce';
import SearchIcon from '@mui/icons-material/Search';
```

2. **Avoid side effects**: Mark pure functions in package.json

```json
{
  "sideEffects": false
}
```

3. **Use modern syntax**: Let Vite handle transpilation

```tsx
// ✅ Use optional chaining
const email = candidate?.contact?.email;

// ✅ Use nullish coalescing
const timeout = config?.timeout ?? 5000;
```

---

## 4. API Call Optimization

Optimize API calls to reduce latency and bandwidth usage.

### Performance Monitoring

The frontend includes automatic API performance tracking:

```tsx
import { apiClient } from '@/api/client';

// Get performance statistics
const stats = apiClient.getPerformanceStats();

console.log(`Average duration: ${stats.averageDuration}ms`);
console.log(`Success rate: ${(stats.successfulCalls / stats.totalCalls * 100).toFixed(1)}%`);
console.log(`Slowest endpoint: ${stats.slowestEndpoint.endpoint}`);
```

**See:** `frontend/PERFORMANCE_TRACKING.md` for complete documentation.

### Request Batching

Batch multiple API calls into a single request:

```tsx
// ❌ Bad - Multiple API calls
const candidate1 = await apiClient.getCandidate('id-1');
const candidate2 = await apiClient.getCandidate('id-2');
const candidate3 = await apiClient.getCandidate('id-3');

// ✅ Good - Batched request
const candidates = await apiClient.getCandidates({
  ids: ['id-1', 'id-2', 'id-3']
});
```

### Request Cancellation

Cancel pending requests when component unmounts:

```tsx
import { useEffect, useState } from 'react';
import axios from 'axios';

function CandidateList() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    const fetchCandidates = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/candidates', {
          signal: controller.signal,
        });
        setCandidates(response.data);
      } catch (error) {
        if (axios.isCancel(error)) {
          console.log('Request canceled');
        } else {
          console.error('Error fetching candidates:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();

    return () => {
      controller.abort(); // Cancel request on unmount
    };
  }, []);

  return <div>{/* render candidates */}</div>;
}
```

### Response Caching

Cache API responses in memory or localStorage:

```tsx
import { useState, useEffect } from 'react';

const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function useCachedFetch<T>(key: string, fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const cached = cache.get(key);

    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setData(cached.data);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await fetcher();
        cache.set(key, { data: result, timestamp: Date.now() });
        setData(result);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [key, fetcher]);

  return { data, loading };
}

// Usage
function CandidateDetails({ id }: { id: string }) {
  const { data: candidate, loading } = useCachedFetch(
    `candidate-${id}`,
    () => apiClient.getCandidate(id)
  );

  if (loading) return <CircularProgress />;
  return <div>{candidate?.name}</div>;
}
```

### Pagination

Implement pagination for large datasets:

```tsx
import { useState } from 'react';

function usePaginatedFetch(fetchFn: (page: number, limit: number) => Promise<any>) {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      const response = await fetchFn(page, 20); // 20 items per page
      setData((prev) => [...prev, ...response.items]);
      setHasMore(response.items.length === 20);
      setPage((prev) => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, hasMore, loadMore };
}

// Usage with infinite scroll
function CandidatesList() {
  const { data, loading, hasMore, loadMore } = usePaginatedFetch(
    (page, limit) => apiClient.listCandidates({ page, limit })
  );

  return (
    <InfiniteScroll
      dataLength={data.length}
      next={loadMore}
      hasMore={hasMore}
      loader={<CircularProgress />}
    >
      {data.map((candidate) => (
        <CandidateCard key={candidate.id} candidate={candidate} />
      ))}
    </InfiniteScroll>
  );
}
```

### Debouncing User Input

Debounce search and filter inputs:

```tsx
import { useState, useEffect } from 'react';
import { useDebouncedCallback } from 'use-debounce';

function CandidateSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // Debounce search with 500ms delay
  const debouncedSearch = useDebouncedCallback(
    async (searchQuery: string) => {
      if (!searchQuery) {
        setResults([]);
        return;
      }

      const response = await apiClient.searchCandidates(searchQuery);
      setResults(response);
    },
    500 // Wait 500ms after user stops typing
  );

  useEffect(() => {
    debouncedSearch(query);
  }, [query, debouncedSearch]);

  return (
    <Box>
      <TextField
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search candidates..."
        fullWidth
      />
      <Box mt={2}>
        {results.map((candidate) => (
          <CandidateCard key={candidate.id} candidate={candidate} />
        ))}
      </Box>
    </Box>
  );
}
```

### Optimistic Updates

Update UI immediately, rollback on error:

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function UpdateCandidateStatus({ candidateId }: { candidateId: string }) {
  const queryClient = useQueryClient();

  const updateStatus = useMutation({
    mutationFn: (status: string) =>
      apiClient.updateCandidate(candidateId, { status }),

    onMutate: async (newStatus) => {
      // Cancel ongoing queries
      await queryClient.cancelQueries({ queryKey: ['candidate', candidateId] });

      // Snapshot previous value
      const previousCandidate = queryClient.getQueryData(['candidate', candidateId]);

      // Optimistically update
      queryClient.setQueryData(['candidate', candidateId], (old: any) => ({
        ...old,
        status: newStatus,
      }));

      // Return context with previous value
      return { previousCandidate };
    },

    onError: (err, newStatus, context) => {
      // Rollback on error
      queryClient.setQueryData(['candidate', candidateId], context?.previousCandidate);
    },

    onSettled: () => {
      // Refetch to ensure server state
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId] });
    },
  });

  return (
    <Button
      onClick={() => updateStatus.mutate('active')}
      disabled={updateStatus.isPending}
    >
      Activate
    </Button>
  );
}
```

---

## 5. Performance Monitoring and Debugging

### Browser DevTools

Use Chrome DevTools for performance profiling:

**Lighthouse Score:**

```bash
# Run Lighthouse audit
npm run build
npx serve dist
# Open Chrome DevTools > Lighthouse > Run audit
```

**Target Scores:**
- Performance: > 90
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Total Blocking Time (TBT): < 200ms
- Cumulative Layout Shift (CLS): < 0.1

### React DevTools Profiler

Profile component render performance:

```tsx
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  if (actualDuration > 100) {
    console.warn(`Slow render: ${id} took ${actualDuration}ms`);
  }
}

function App() {
  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <CandidatesList />
    </Profiler>
  );
}
```

### Network Performance Monitoring

Monitor API performance:

```tsx
import { useEffect } from 'react';
import { apiClient } from '@/api/client';

useEffect(() => {
  const interval = setInterval(() => {
    const stats = apiClient.getPerformanceStats();

    // Alert on performance degradation
    if (stats.averageDuration > 1000) {
      console.warn('API performance degrading:', stats);
    }

    // Alert on high failure rate
    const failureRate = (stats.failedCalls / stats.totalCalls) * 100;
    if (failureRate > 5) {
      console.error('High API failure rate:', failureRate);
    }
  }, 30000); // Check every 30 seconds

  return () => clearInterval(interval);
}, []);
```

---

## Quick Reference: Frontend Performance

### Code Splitting Checklist

- [ ] Route-based splitting with `React.lazy()`
- [ ] Vendor chunks configured in `vite.config.ts`
- [ ] Heavy components lazy-loaded
- [ ] Modals/dialogs lazy-loaded
- [ ] Loading states with `Suspense`

### Virtualization Checklist

- [ ] Lists with 100+ items use `react-window`
- [ ] Tables with 50+ rows virtualized
- [ ] `FixedSizeList` for fixed-height items
- [ ] `VariableSizeList` for variable-height items
- [ ] Overscan configured for smooth scrolling

### Bundle Optimization Checklist

- [ ] Tree shaking enabled
- [ ] Minification with terser
- [ ] Console logs removed in production
- [ ] CSS code splitting enabled
- [ ] Bundle size < 500KB (gzipped)
- [ ] Bundle analyzer run to identify bloat

### API Optimization Checklist

- [ ] Requests cancelled on unmount
- [ ] Response caching implemented
- [ ] Pagination for large datasets
- [ ] Debounced user input
- [ ] Optimistic updates for mutations
- [ ] Performance monitoring enabled

### Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| **Initial load time** | < 2s | < 3s |
| **Time to Interactive (TTI)** | < 3s | < 5s |
| **First Contentful Paint (FCP)** | < 1.5s | < 2.5s |
| **Largest Contentful Paint (LCP)** | < 2.5s | < 4s |
| **Total Blocking Time (TBT)** | < 200ms | < 500ms |
| **API response time (p95)** | < 500ms | < 1000ms |
| **Bundle size (gzipped)** | < 500KB | < 1MB |

### Common Performance Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Large bundle size** | Slow initial load | Code splitting, tree shaking, lazy loading |
| **Unnecessary re-renders** | Janky UI | `React.memo()`, `useMemo()`, `useCallback()` |
| **Slow list rendering** | Freeze on scroll | Virtualization with `react-window` |
| **Too many API calls** | Network congestion | Batching, caching, pagination |
| **Large images** | Slow load times | Image optimization, lazy loading, WebP format |

---

## Docker Resource Tuning

Docker resource tuning ensures optimal performance and resource utilization for all containers. Proper resource limits prevent resource starvation, improve stability, and enable predictable performance under load.

### Overview

The AgentHR platform uses Docker Compose with explicit resource constraints for each service:

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Resource Management                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   CPU Limits │  │ Memory Limits│  │  Healthchecks│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Resource Allocation                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │  Backend  │ │  Celery   │ │PostgreSQL │ │   Redis   │  │
│  │   4-8G    │ │   6-12G   │ │   1-2G    │ │  512M-1G  │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Performance Characteristics

| Resource Type | Impact | Configuration |
|---------------|--------|---------------|
| **CPU Limits** | High (Processing) | Prevents CPU contention, ensures fair scheduling |
| **Memory Limits** | High (Stability) | Prevents OOM kills, enables predictable behavior |
| **CPU Reservations** | Medium (Performance) | Guarantees minimum CPU allocation |
| **Memory Reservations** | Medium (Performance) | Ensures minimum memory availability |
| **Healthchecks** | High (Reliability) | Automatic restart on failure, load balancing |

---

## 1. CPU and Memory Limits

### Current Resource Allocation

The docker-compose.yml defines explicit resource limits for all services:

**Configuration:** `docker-compose.yml`

```yaml
services:
  # PostgreSQL Database
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  # Celery Worker (ML Processing)
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '6.0'
          memory: 12G
        reservations:
          cpus: '3.0'
          memory: 6G
```

### Understanding Limits vs Reservations

| Resource Type | Limits | Reservations |
|---------------|--------|--------------|
| **Purpose** | Maximum resources a container can use | Minimum resources guaranteed to container |
| **When enforced** | When container exceeds limit | When scheduling containers |
| **Effect** | Throttling/OOM kill if exceeded | Pre-allocates resources on host |
| **Use case** | Prevent resource starvation | Ensure performance baseline |

**Example:**

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Container can use up to 4 CPU cores
      memory: 8G       # Container can use up to 8GB RAM
    reservations:
      cpus: '2.0'      # Container guaranteed 2 CPU cores
      memory: 4G       # Container guaranteed 4GB RAM
```

### Resource Allocation by Service

| Service | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation | Profile |
|---------|-----------|--------------|-----------------|-------------------|---------|
| **postgres** | 2.0 | 2G | 1.0 | 1G | Database |
| **redis** | 1.0 | 1G | 0.5 | 512M | Cache |
| **backend** | 4.0 | 8G | 2.0 | 4G | API Server |
| **celery_worker** | 6.0 | 12G | 3.0 | 6G | ML Worker |
| **celery_beat** | 1.0 | 512M | 0.5 | 256M | Scheduler |
| **grafana** | 1.0 | 1G | 0.5 | 512M | Monitoring |
| **prometheus** | 1.0 | 2G | 0.5 | 1G | Metrics |
| **loki** | 1.0 | 1G | 0.5 | 512M | Logging |

### Monitoring Resource Usage

Monitor container resource usage in real-time:

```bash
# Live resource usage for all containers
docker stats

# Resource usage for specific service
docker stats resume_analysis_backend

# Formatted output (no streaming)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

**Example Output:**

```
NAME                    CPU %     MEM USAGE / LIMIT   MEM %
resume_analysis_celery_worker   180.5%    8.2GiB / 12GiB      68.3%
resume_analysis_backend         45.2%     3.1GiB / 8GiB       38.7%
resume_analysis_postgres        12.8%     1.4GiB / 2GiB       70.1%
resume_analysis_redis           2.1%      385MiB / 1GiB       38.5%
resume_analysis_grafana         5.4%      487MiB / 1GiB       48.7%
```

### Adjusting Resource Limits

#### When to Increase Limits

**Symptoms that indicate limits are too low:**

1. **CPU Throttling**: Container consistently at 100% CPU
2. **OOM Kills**: Container exits with code 137
3. **Slow Performance**: Increased response times
4. **Celery Backups**: Tasks queue up faster than processing

```bash
# Check for OOM kills
docker logs resume_analysis_backend 2>&1 | grep -i "out of memory"

# Check CPU throttling
docker inspect resume_analysis_backend | jq '.[0].State.Status'
```

#### When to Decrease Limits

**Symptoms that indicate limits are too high:**

1. **Underutilization**: Consistently low CPU/memory usage
2. **Resource Waste**: Other services starved for resources
3. **Cost**: Paying for unused resources in cloud environments

```bash
# Check average resource usage over time
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | \
  grep resume_analysis
```

### Resource Tuning Guidelines

#### For Development Environments

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Lower for dev machines
      memory: 4G       # Reduce for local development
    reservations:
      cpus: '1.0'
      memory: 2G
```

#### For Production Environments

```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'      # Higher for production workloads
      memory: 16G      # More headroom for ML processing
    reservations:
      cpus: '4.0'      # Guarantee performance
      memory: 8G
```

#### For Resource-Constrained Environments

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Minimal CPU
      memory: 2G       # Minimal memory
    reservations:
      cpus: '0.5'
      memory: 1G
```

---

## 2. Container Optimization

### Healthcheck Configuration

Healthchecks enable Docker to automatically restart unhealthy containers and remove them from load balancer rotation.

**Best Practices:**

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]  # Command to check health
  interval: 10s                                    # Run check every 10 seconds
  timeout: 5s                                      # Fail if check takes > 5 seconds
  retries: 5                                       # Mark unhealthy after 5 consecutive failures
  start_period: 30s                                # Grace period on startup
```

**Healthcheck Examples by Service:**

```yaml
# PostgreSQL
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5

# Redis
redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

# Backend API
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### Container Restart Policies

Configure automatic restart on failure:

```yaml
restart: unless-stopped  # Restart on failure unless manually stopped
```

**Restart Policy Options:**

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `no` | Don't restart | Debugging, one-off tasks |
| `on-failure` | Restart on non-zero exit | Production services |
| `always` | Always restart | Critical services |
| `unless-stopped` | Restart unless manually stopped | Long-running services |

### Dependency Management

Use healthchecks for service dependencies:

```yaml
services:
  backend:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

**Benefits:**
- Backend waits for database to be healthy before starting
- Prevents startup errors from uninitialized dependencies
- Enables graceful startup order

### Volume Optimization

Optimize volume mounts for better performance:

```yaml
volumes:
  # Use named volumes for data persistence
  - backend_models:/app/models_cache

  # Bind mounts for development (live reload)
  - ./backend:/app

  # Read-only bind mounts (security + performance)
  - ./testdata:/app/testdata:ro

  # Use tmpfs for temporary data
  - tmpfs:/tmp
```

**Performance Tips:**

1. **Named Volumes**: Faster than bind mounts on Mac/Windows
2. **Read-Only**: Prevents accidental writes, enables caching
3. **Tmpfs**: Stores temporary data in memory (very fast)

### Network Optimization

```yaml
networks:
  resume_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Network Best Practices:**

1. **Use custom networks**: Better isolation and performance
2. **DNS resolution**: Containers can resolve each other by name
3. **Bridge driver**: Best for most use cases
4. **Avoid host network**: Security risk, no isolation

---

## 3. Environment-Specific Tuning

### Development Environment

**Goals:** Fast feedback, lower resource usage, easier debugging

```yaml
# docker-compose.dev.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - ./backend:/app  # Live reload

  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '3.0'
          memory: 6G
        reservations:
          cpus: '1.5'
          memory: 3G
    command: celery -A celery_app.celery_app worker --loglevel=debug --concurrency=2
```

**Usage:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production Environment

**Goals:** Maximum performance, high availability, resource efficiency

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    environment:
      - DEBUG=false
      - LOG_LEVEL=info
      - WORKERS=4

  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '12.0'
          memory: 24G
        reservations:
          cpus: '6.0'
          memory: 12G
      replicas: 2  # Multiple workers for high availability
    command: celery -A celery_app.celery_app worker --loglevel=info --concurrency=8
```

**Usage:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Resource-Constrained Environment

**Goals:** Fit within limited resources, maintain functionality

```yaml
# docker-compose.low-resource.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    environment:
      - WORKERS=1
      - ML_BATCH_SIZE=4  # Reduce batch size

  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    command: celery -A celery_app.celery_app worker --concurrency=1 --prefetch-multiplier=1

  postgres:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M
    environment:
      - shared_buffers=128MB
      - effective_cache_size=512MB
```

---

## 4. Performance Tuning for Different Workloads

### High-Throughput Scenario

**Use Case:** Processing many resumes quickly (bulk uploads, batch processing)

```yaml
services:
  # Scale Celery workers horizontally
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '6.0'
          memory: 12G
        reservations:
          cpus: '3.0'
          memory: 6G
      replicas: 4  # 4 workers for parallel processing
    command: celery -A celery_app.celery_app worker --concurrency=4 --prefetch-multiplier=4

  # Increase backend capacity
  backend:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
      replicas: 2
```

### Low-Latency Scenario

**Use Case:** Interactive use, need fast response times

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '6.0'
          memory: 12G
        reservations:
          cpus: '4.0'
          memory: 8G
    environment:
      - WORKERS=4  # More workers for concurrent requests
      - KEEP_ALIVE=30

  redis:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G  # More cache for faster responses
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Memory-Intensive ML Workloads

**Use Case:** Large models, complex NLP processing

```yaml
services:
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 24G  # Large memory for ML models
        reservations:
          cpus: '4.0'
          memory: 12G
    environment:
      - ML_BATCH_SIZE=8  # Larger batches for efficiency
      - MODEL_CACHE_SIZE=10  # Cache more models
    command: celery -A celery_app.celery_app worker --concurrency=2  # Lower concurrency, more memory per task
```

---

## 5. Troubleshooting Resource Issues

### Common Symptoms and Solutions

#### Container Exits with Code 137

**Symptom:** Container keeps restarting, logs show exit code 137

**Cause:** Out of memory (OOM) killed

**Solution:** Increase memory limit

```yaml
deploy:
  resources:
    limits:
      memory: 16G  # Increase from 8G
```

#### Container CPU Usage Always at 100%

**Symptom:** CPU throttling, slow response times

**Cause:** CPU limit too low

**Solution:** Increase CPU limit

```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'  # Increase from 4.0
```

#### Intermittent Slowdowns

**Symptom:** Performance varies, sometimes fast, sometimes slow

**Cause:** Resource contention, no reservations set

**Solution:** Add CPU/memory reservations

```yaml
deploy:
  resources:
    reservations:
      cpus: '2.0'   # Guarantee minimum resources
      memory: 4G
```

#### Startup Failures

**Symptom:** Container exits immediately after starting

**Cause:** Dependency not ready, missing healthcheck

**Solution:** Add healthcheck and dependency

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s

depends_on:
  postgres:
    condition: service_healthy
```

### Diagnostic Commands

```bash
# Check container resource usage
docker stats --no-stream

# Inspect container resource limits
docker inspect resume_analysis_backend | jq '.[0].HostConfig.Memory'

# Check OOM kills
docker events --filter 'type=oom' --since 1h

# View healthcheck status
docker inspect resume_analysis_backend | jq '.[0].State.Health'

# Check restart count
docker inspect resume_analysis_backend | jq '.[0].RestartCount'

# View container logs for errors
docker logs resume_analysis_backend --tail 100
```

---

## 6. Monitoring and Alerting

### Key Metrics to Monitor

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| **CPU Usage** | cAdvisor/Prometheus | > 80% for 5 minutes |
| **Memory Usage** | cAdvisor/Prometheus | > 85% for 5 minutes |
| **OOM Kills** | Docker events | Any occurrence |
| **Container Restarts** | Docker/Healthchecks | > 3 in 10 minutes |
| **Healthcheck Status** | Docker | Any unhealthy service |

### Prometheus Metrics

The cAdvisor container collects Docker resource metrics:

```yaml
# cAdvisor is already configured in docker-compose.yml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:v0.49.1
  ports:
    - "8080:8080"
  volumes:
    - /:/rootfs:ro
    - /var/run:/var/run:ro
    - /sys:/sys:ro
    - /var/lib/docker/:/var/lib/docker:ro
```

**Key Metrics:**

- `container_cpu_usage_seconds_total`
- `container_memory_usage_bytes`
- `container_memory_max_usage_bytes`
- `container_spec_memory_limit_bytes`

### Grafana Dashboards

Use the pre-configured Grafana dashboards for monitoring:

```
URL: http://localhost:3001
Dashboard: Docker Container Metrics
```

**Alerts to Configure:**

1. **High CPU Alert**: Container CPU > 80% for 5 minutes
2. **High Memory Alert**: Container memory > 85% for 5 minutes
3. **OOM Kill Alert**: Container killed due to OOM
4. **Unhealthy Service Alert**: Healthcheck fails > 3 times

---

## Quick Reference: Docker Resource Tuning

### Resource Allocation Checklist

- [ ] All services have CPU limits defined
- [ ] All services have memory limits defined
- [ ] All services have CPU reservations defined
- [ ] All services have memory reservations defined
- [ ] Healthchecks configured for all critical services
- [ ] Restart policies configured appropriately
- [ ] Dependencies use healthcheck conditions
- [ ] Resource limits match workload requirements

### Common Resource Limits

| Environment | Backend | Celery Worker | PostgreSQL | Redis |
|-------------|---------|---------------|------------|-------|
| **Development** | 2-4 CPU, 4-8G | 3-6 CPU, 6-12G | 1-2 CPU, 1-2G | 0.5-1 CPU, 512M-1G |
| **Production** | 4-8 CPU, 8-16G | 6-12 CPU, 12-24G | 2-4 CPU, 2-4G | 1-2 CPU, 1-2G |
| **Low Resource** | 1-2 CPU, 2-4G | 2-4 CPU, 4-8G | 0.5-1 CPU, 512M-1G | 0.25-0.5 CPU, 256M-512M |

### Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| **CPU Usage** | < 70% | < 90% |
| **Memory Usage** | < 75% | < 90% |
| **Container Restarts** | 0/hour | < 3/hour |
| **Healthcheck Pass Rate** | 100% | > 95% |
| **OOM Kills** | 0 | 0 |

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **OOM Kill** | Container exits with code 137 | Increase memory limit |
| **CPU Throttling** | CPU at 100%, slow response | Increase CPU limit |
| **Slow Startup** | Long wait before service ready | Adjust healthcheck start_period |
| **Resource Starvation** | One service slows others | Set reservations |
| **High Memory Usage** | Memory near limit | Optimize application, increase limit |

---

## Performance Monitoring

Performance monitoring provides visibility into system behavior, enables early detection of issues, and validates optimization efforts. The AgentHR platform uses Prometheus, Grafana, and structured logging for comprehensive observability.

### Overview

The monitoring stack consists of four layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Application │  │  Metrics     │  │   Alerts     │     │
│  │  Instrument  │  │  Collection  │  │  & Paging    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼─────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Flow                                 │
│  App → Prometheus → Grafana Dashboards → Alertmanager       │
│       ↓               ↓                    ↓                 │
│   Metrics Store   Visualization       Alert Routing         │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Metrics Collection** | Capture performance data | Prometheus + FastAPI middleware |
| **Visualization** | Real-time dashboards | Grafana with pre-built dashboards |
| **Logging** | Structured event tracking | Python structlog + JSON output |
| **Tracing** | Request flow tracking | Correlation IDs + distributed tracing |
| **Alerting** | Proactive issue detection | Alertmanager with PagerDuty/Slack |

## Metrics Collection (Prometheus)

Prometheus collects time-series metrics from all services, providing the foundation for performance monitoring and alerting.

### Key Metrics to Track

#### Application Performance Metrics

```promql
# Request duration (p95, p99)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request rate by endpoint
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Active Celery tasks
celery_tasks_active
```

#### Database Performance Metrics

```promql
# Connection pool usage
pg_stat_database_numbackends / pg_settings_max_connections

# Slow query rate
rate(pg_stat_statements_calls[5m])

# Transaction rate
rate(pg_stat_database_xact_commit[5m])

# Cache hit ratio
sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))
```

#### Cache Performance Metrics

```promql
# Redis memory usage
redis_memory_used_bytes / redis_memory_max_bytes

# Cache hit rate
sum(rate(redis_cache_hits_total[5m])) / sum(rate(redis_cache_operations_total[5m]))

# Cache eviction rate
rate(redis_evicted_keys_total[5m])
```

#### ML Model Performance Metrics

```promql
# Model loading time
histogram_quantile(0.95, ml_model_load_duration_seconds)

# Inference time by model
histogram_quantile(0.95, rate(ml_inference_duration_seconds_bucket{model=~".+"}[5m]))

# Model cache hit rate
ml_model_cache_hits / (ml_model_cache_hits + ml_model_cache_misses)
```

### Prometheus Configuration

The `prometheus.yml` configuration defines scrape targets and intervals:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9540']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Custom Metrics

Add custom metrics in FastAPI using the `prometheus_client` library:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
resume_analysis_duration = Histogram(
    'resume_analysis_duration_seconds',
    'Time spent analyzing resume',
    ['model_type', 'language']
)

active_tasks = Gauge(
    'celery_tasks_active',
    'Number of currently executing Celery tasks'
)

cache_operations = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_name']
)

# Use in code
@router.post("/api/resumes/analyze")
async def analyze_resume(file: UploadFile):
    start_time = time.time()
    try:
        result = await analyze(file)
        return result
    finally:
        duration = time.time() - start_time
        resume_analysis_duration.labels(
            model_type='keybert',
            language='en'
        ).observe(duration)
```

## Grafana Dashboards

Grafana provides real-time visualization of metrics through pre-configured dashboards.

### Available Dashboards

| Dashboard | Purpose | Key Panels |
|-----------|---------|------------|
| **Application Overview** | High-level system health | Request rate, error rate, latency heatmap |
| **API Performance** | Endpoint-specific metrics | Response time, throughput, status codes |
| **Database Performance** | PostgreSQL metrics | Connection pool, query performance, locks |
| **Cache Performance** | Redis effectiveness | Hit rate, memory usage, eviction rate |
| **Celery Tasks** | Background job processing | Queue depth, task duration, worker utilization |
| **ML Model Performance** | Model metrics | Load time, inference time, cache hit rate |
| **Resource Utilization** | Container metrics | CPU, memory, disk I/O per container |

### Accessing Dashboards

```bash
# Start Grafana (if not running)
docker-compose up -d grafana

# Access Grafana web UI
open http://localhost:3000

# Default credentials
Username: admin
Password: admin (change on first login)
```

### Creating Custom Dashboards

1. **Navigate**: Dashboards → New → Import
2. **Enter Dashboard ID** (if importing from Grafana.com)
3. **Or create from scratch**: New Dashboard → Add Panel
4. **Configure Panel**: Select metric, visualization type, and thresholds

Example panel configuration:

```json
{
  "title": "API Response Time (p95)",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
      "legendFormat": "{{endpoint}}"
    }
  ],
  "type": "graph",
  "yaxes": [
    {
      "format": "s",
      "label": "Response Time"
    }
  ],
  "alert": {
    "conditions": [
      {
        "evaluator": {
          "params": [0.5],
          "type": "gt"
        },
        "operator": {
          "type": "and"
        },
        "query": {
          "params": ["A", "5m", "now"]
        },
        "reducer": {
          "params": [],
          "type": "avg"
        },
        "type": "query"
      }
    ]
  }
}
```

## Logging and Tracing

Structured logging with correlation IDs enables end-to-end request tracing across services.

### Log Structure

Logs are structured as JSON for easy parsing and analysis:

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "info",
  "logger": "app.routers.resumes",
  "message": "Resume analysis completed",
  "context": {
    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
    "correlation_id": "abc-123-def",
    "duration_ms": 2450,
    "model": "keybert",
    "language": "en",
    "file_size": 1024000
  },
  "tags": ["resume_analysis", "ml_inference"]
}
```

### Correlation ID Tracking

Correlation IDs trace requests across API, Celery workers, and external services:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Get existing correlation ID or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Add to request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

# Use in logging
logger.info(
    "Processing resume analysis",
    extra={"correlation_id": request.state.correlation_id}
)
```

### Log Aggregation and Querying

```bash
# View logs for all services
docker-compose logs -f --tail=100

# View logs for specific service
docker-compose logs -f backend

# Filter logs by correlation ID
docker-compose logs backend | grep "abc-123-def"

# Filter logs by level
docker-compose logs backend | grep '"level": "error"'

# Export logs for analysis
docker-compose logs --no-color > logs/export.json
```

### Performance Logging

Key performance-related log patterns:

```python
# Log slow operations
if duration > SLOW_THRESHOLD:
    logger.warning(
        "Slow operation detected",
        extra={
            "operation": "resume_analysis",
            "duration_ms": duration,
            "threshold_ms": SLOW_THRESHOLD,
            "correlation_id": correlation_id
        }
    )

# Log cache misses
logger.info(
    "Cache miss",
    extra={
        "cache_name": "candidates",
        "key": candidate_id,
        "reason": "expired"
    }
)

# Log database query performance
logger.debug(
    "Database query executed",
    extra={
        "query": query.statement,
        "duration_ms": query_duration,
        "rows_affected": row_count
    }
)
```

## Performance Benchmarking

Regular benchmarking establishes performance baselines and detects regressions.

### pytest-benchmark Integration

The platform includes automated performance benchmarks using `pytest-benchmark`:

```bash
# Run all performance benchmarks
docker-compose exec backend pytest tests/performance/ \
    --benchmark-only \
    --benchmark-json=benchmark_results.json

# Run specific benchmark group
docker-compose exec backend pytest tests/performance/ \
    -k "candidate_list" \
    --benchmark-only

# Compare against baseline
docker-compose exec backend pytest tests/performance/ \
    --benchmark-only \
    --benchmark-compare-filename=baseline.json
```

### Performance Targets

| Endpoint | Metric | Target | Regression Threshold |
|----------|--------|--------|----------------------|
| `GET /api/candidates/` | p95 latency | < 200ms | +20% |
| `GET /api/candidates/{id}` | p95 latency | < 50ms | +20% |
| `GET /api/vacancies/{id}/matches` | p95 latency | < 500ms | +20% |
| `GET /api/analytics/key-metrics` | p95 latency | < 300ms | +20% |
| Cache GET | p95 latency | < 5ms | +20% |
| Cache SET | p95 latency | < 5ms | +20% |

### Manual Benchmarking

For ad-hoc performance testing:

```bash
# Benchmark with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/candidates/

# Benchmark with wrk
wrk -t4 -c100 -d30s http://localhost:8000/api/candidates/

# Measure cache performance
docker-compose exec backend python -c "
from services.cache_service import get_cache_service
import time

cache = get_cache_service()
data = {'test': 'data' * 1000}

# Benchmark SET
start = time.time()
for _ in range(1000):
    cache.set('test', 'key', data, 3600)
set_time = (time.time() - start) / 1000
print(f'SET: {set_time * 1000:.2f}ms avg')

# Benchmark GET
start = time.time()
for _ in range(1000):
    cache.get('test', 'key')
get_time = (time.time() - start) / 1000
print(f'GET: {get_time * 1000:.2f}ms avg')
"
```

### Monitoring Overhead

Monitoring adds minimal overhead when properly configured:

| Component | Overhead | Mitigation |
|-----------|----------|------------|
| **Prometheus middleware** | 1-2ms per request | Efficient metric aggregation |
| **Correlation ID** | < 1ms per request | UUID generation optimization |
| **Structured logging** | 1-3ms per request | Async logging + buffer sizing |
| **DB query metrics** | < 0.5ms per query | Connection pooling |
| **Total** | **3-6ms per request** | **< 5% of typical response time** |

Validate monitoring overhead:

```bash
./monitoring/validate-monitoring-overhead.sh
```

Expected results:
- ✅ Overhead: < 5%
- ✅ CPU: < 50%
- ✅ Memory increase: < 50 MiB
- ✅ No memory leaks

### Troubleshooting Monitoring Issues

#### High Overhead (> 5%)

If monitoring overhead exceeds 5% of response time:

```bash
# Check current overhead
./monitoring/validate-monitoring-overhead.sh

# Reduce log level to WARNING
# In .env: LOG_LEVEL=WARNING

# Implement metric sampling
# Track every 10th request instead of all
```

Solutions:
- **Reduce log level**: Set `LOG_LEVEL=WARNING` or `ERROR` in `.env`
- **Sample metrics**: Configure Prometheus to scrape less frequently or track fewer metrics
- **Fewer histogram buckets**: Reduce bucket count in histogram metrics
- **Check for blocking I/O**: Ensure logging and metrics collection are async

#### Memory Leaks

If monitoring causes memory growth over time:

```bash
# Monitor memory usage
docker stats $(docker-compose ps -q backend)

# Check for growing metric label cardinality
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '. | length'
```

Solutions:
- **Verify correlation ID cleanup**: Ensure correlation IDs are removed from logs after request completion
- **Check DB connection pooling**: Verify connections are properly returned to pool
- **Review log buffer sizes**: Reduce buffer sizes if logs accumulate in memory
- **Monitor label cardinality**: High cardinality labels (like user IDs) can cause memory bloat

#### High CPU Usage (> 50%)

If monitoring causes high CPU utilization:

```bash
# Profile CPU usage
docker-compose exec backend python -m cProfile -s cumulative -m uvicorn app.main:app

# Check metric computation overhead
curl -s http://localhost:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m]) | jq .
```

Solutions:
- **Implement metric sampling**: Only track metrics for a percentage of requests
- **Reduce logging verbosity**: Use DEBUG only during development, WARNING in production
- **Check string formatting**: Pre-format strings outside hot paths; avoid f-strings in logs
- **Verify async operations**: Ensure metrics collection doesn't block request processing

## Alert Setup

Alerts proactively notify you of performance issues before they impact users.

### AlertManager Configuration

Configure alert routing in `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'

    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<YOUR-PAGERDUTY-KEY>'

  - name: 'slack'
    slack_configs:
      - api_url: '<YOUR-SLACK-WEBHOOK>'
        channel: '#alerts'
```

### Critical Alerts

Define alerts for critical performance issues:

```yaml
groups:
  - name: performance_critical
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow response time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Slow response time on {{ $labels.endpoint }}"
          description: "p95 latency is {{ $value }}s"

      # Database connection pool exhaustion
      - alert: DatabasePoolExhausted
        expr: |
          pg_stat_database_numbackends
          / pg_settings_max_connections > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanizePercentage }} of connections used"

      # Redis memory high
      - alert: RedisMemoryHigh
        expr: |
          redis_memory_used_bytes
          / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Redis memory usage critical"
          description: "{{ $value | humanizePercentage }} of max memory"

      # Celery queue backup
      - alert: CeleryQueueBackup
        expr: |
          celery_queue_length{queue="analysis"}
          > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backup detected"
          description: "{{ $value }} tasks pending"
```

### Warning Alerts

Early warning alerts for potential issues:

```yaml
groups:
  - name: performance_warning
    interval: 1m
    rules:
      # Gradual slowdown
      - alert: GradualSlowdown
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Response time degrading"
          description: "p95 latency increased to {{ $value }}s"

      # Cache hit rate low
      - alert: LowCacheHitRate
        expr: |
          sum(rate(cache_hits_total[5m]))
          / (sum(rate(cache_hits_total[5m]))
             + sum(rate(cache_misses_total[5m]))) < 0.7
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate below 70%"
          description: "Current hit rate: {{ $value | humanizePercentage }}"

      # Memory usage trending high
      - alert: MemoryUsageTrendingHigh
        expr: |
          predict_linear(container_memory_usage_bytes[1h], 3600)
          > container_spec_memory_limit_bytes * 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage trending toward limit"
          description: "Will exceed limit in 1 hour at current rate"
```

### Alert Testing

Test alerts to ensure proper configuration:

```bash
# Test alert rules
docker-compose exec prometheus promtool check config \
    /etc/prometheus/prometheus.yml

# Test alertmanager config
docker-compose exec alertmanager amtool check-config \
    /etc/alertmanager/alertmanager.yml

# Trigger test alert
curl -XPOST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "description": "This is a test alert"
    }
  }
]'
```

## Quick Reference: Performance Monitoring

### Essential Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq .

# Query current metrics
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq .

# Check alert status
curl http://localhost:9090/api/v1/alerts | jq .

# View recent logs
docker-compose logs --tail=100 backend | jq -r 'select(.level=="error")'

# Test alert delivery
./monitoring/test-alerts.sh

# Run performance benchmarks
docker-compose exec backend pytest tests/performance/ --benchmark-only

# Validate monitoring overhead
./monitoring/validate-monitoring-overhead.sh
```

### Key Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **Application Overview** | http://localhost:3000/d/application | System health overview |
| **API Performance** | http://localhost:3000/d/api-performance | Endpoint metrics |
| **Database** | http://localhost:3000/d/database | PostgreSQL performance |
| **Cache** | http://localhost:3000/d/cache | Redis hit rate, memory |
| **Celery** | http://localhost:3000/d/celery | Task processing metrics |

### Performance Checklist

- [ ] Prometheus scraping all targets (check `/targets`)
- [ ] Grafana dashboards displaying data
- [ ] AlertManager routing alerts correctly
- [ ] Monitoring overhead < 5%
- [ ] Benchmark baseline established
- [ ] Critical alerts configured and tested
- [ ] Log aggregation working
- [ ] Correlation IDs present in logs
- [ ] Performance targets documented

## Related Documentation

- [monitoring/README.md](monitoring/README.md) - Complete monitoring setup guide
- [monitoring/PERFORMANCE_QUICK_REFERENCE.md](monitoring/PERFORMANCE_QUICK_REFERENCE.md) - Quick validation commands
- [backend/tests/performance/](backend/tests/performance/) - Performance benchmark suite

---

## Troubleshooting Performance Issues

Comprehensive guide to diagnosing and resolving common performance bottlenecks in the AgentHR platform.

### Overview

Performance issues can manifest in various ways across different components. This section provides a systematic approach to identifying and resolving the most common bottlenecks.

### Quick Diagnostic Flowchart

```
                    ┌─────────────────────┐
                    │  Performance Issue? │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼──────┐              ┌──────▼──────┐
         │ Slow API?   │              │ High Memory?│
         └──────┬──────┘              └──────┬──────┘
                │                             │
         ┌──────▼──────┐              ┌──────▼──────┐
         │ Queue Backup?│             │ ML Model?   │
         └──────┬──────┘              └──────┬──────┘
                │                             │
                └──────────────┬──────────────┘
                               │
                        ┌──────▼──────┐
                        │  Follow the  │
                        │ sections below│
                        └─────────────┘
```

---

## 1. Slow API Performance

### Symptoms

- API responses take > 500ms (p95)
- Frontend pages load slowly
- Users experience lag or timeouts
- Grafana shows high API latency

### Diagnosis

#### Step 1: Identify the Bottleneck

```bash
# Check API response times
curl -w "@-" -o /dev/null -s 'http://localhost:8000/api/v1/candidates' <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF

# Check Prometheus metrics
curl -s 'http://localhost:9090/api/v1/query?query=http_request_duration_seconds_bucket{le="0.5"}' | jq '.data.result[0].value[1]'

# View slow queries in PostgreSQL
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

#### Step 2: Check Database Performance

```bash
# Check active connections
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;"

# Check for blocking queries
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;"

# Check table sizes (large tables slow down queries)
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;"
```

#### Step 3: Check Connection Pool

```bash
# Check pool statistics
docker-compose logs backend | grep -i "connection pool"

# Verify pool size in .env
grep POOL .env
```

### Solutions

#### Solution 1: Optimize Database Queries

**Problem:** N+1 queries or missing indexes

**Fix:**

```bash
# Add missing indexes
docker-compose exec -T db psql -U agenthr -d agenthr -c "
CREATE INDEX CONCURRENTLY idx_candidates_email ON candidates(email);
CREATE INDEX CONCURRENTLY idx_vacancies_status ON vacancies(status);
CREATE INDEX CONCURRENTLY idx_analysis_tasks_created ON analysis_tasks(created_at);"

# Update query statistics
docker-compose exec -T db psql -U agenthr -d agenthr -c "SELECT pg_stat_statements_reset();"
```

**Backend Code Changes:**

```python
# BAD: N+1 query problem
candidates = db.query(Candidate).all()
for candidate in candidates:
    print(candidate.skills)  # N+1 query!

# GOOD: Use eager loading
candidates = db.query(Candidate).options(
    joinedload(Candidate.skills),
    joinedload(Candidate.experience)
).all()
```

#### Solution 2: Increase Connection Pool Size

**Problem:** Connection pool exhausted

**Fix:**

```bash
# Update .env
echo "DB_POOL_SIZE=20" >> .env
echo "DB_MAX_OVERFLOW=10" >> .env

# Restart backend
docker-compose restart backend
```

#### Solution 3: Enable Response Caching

**Problem:** Repeated expensive queries

**Fix:**

```python
# Add caching to API endpoints
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.get("/api/v1/vacancies")
@cache(expire=60)  # Cache for 60 seconds
async def get_vacancies():
    return await vacancy_service.list_vacancies()
```

#### Solution 4: Optimize Serialization

**Problem:** Slow JSON serialization

**Fix:**

```python
# Use Pydantic for efficient serialization
from pydantic import BaseModel

class CandidateResponse(BaseModel):
    id: int
    email: str
    # Only include necessary fields

class Config:
    orm_mode = True

# Use list comprehension instead of .dict()
@app.get("/api/v1/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).limit(100).all()
    return [CandidateResponse.from_orm(c) for c in candidates]
```

### Verification

```bash
# Re-measure API performance
curl -w "Total: %{time_total}s\n" -o /dev/null -s 'http://localhost:8000/api/v1/candidates'

# Check Prometheus for improvement
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])' | jq '.data.result[0]'

# Verify database query time
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT mean_exec_time < 0.1 AS queries_fast
FROM pg_stat_statements
WHERE query LIKE '%SELECT%';"
```

---

## 2. High Memory Usage

### Symptoms

- Containers restart with exit code 137 (OOM killed)
- Docker stats show memory usage > 85%
- System becomes sluggish under load
- `docker events` shows OOM kills

### Diagnosis

```bash
# Check current memory usage
docker stats --no-stream $(docker-compose ps -q)

# Check for OOM kills
docker events --filter 'type=oom' --since 24h

# Check per-container memory
docker-compose ps
docker inspect $(docker-compose ps -q backend) | jq '.[0].HostConfig.Memory'

# Check Redis memory usage
docker-compose exec -T redis redis-cli INFO memory | grep used_memory

# Check PostgreSQL memory
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT name, setting, unit
FROM pg_settings
WHERE name LIKE '%memory%';"
```

### Solutions

#### Solution 1: ML Model Memory Optimization

**Problem:** ML models consume too much memory

**Fix:**

```python
# Reduce batch size
# In .env:
ML_BATCH_SIZE=4  # Reduce from 8

# Use model quantization (if supported)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
model.quantize=True  # Reduce memory by ~40%

# Clear unused models
import gc
gc.collect()
```

#### Solution 2: Optimize Model Caching

**Problem:** Too many models loaded simultaneously

**Fix:**

```python
# Limit cache size in .env
MODEL_CACHE_SIZE=3  # Keep only 3 models in memory

# Implement model unloading
class ModelManager:
    def __init__(self, max_models=3):
        self.max_models = max_models
        self.loaded_models = {}

    def load_model(self, model_name):
        if len(self.loaded_models) >= self.max_models:
            # Unload least recently used
            lru_model = min(self.loaded_models.items(), key=lambda x: x[1]['last_used'])
            del self.loaded_models[lru_model[0]]
            gc.collect()

        self.loaded_models[model_name] = {
            'model': load_model(model_name),
            'last_used': time.time()
        }
        return self.loaded_models[model_name]['model']
```

#### Solution 3: Configure Celery Worker Memory Limits

**Problem:** Workers consume too much memory

**Fix:**

```yaml
# In docker-compose.yml
services:
  celery_worker:
    deploy:
      resources:
        limits:
          memory: 12G  # Increase from 8G
        reservations:
          memory: 6G
    environment:
      - CELERYD_CONCURRENCY=2  # Reduce from 4
      - CELERYD_PREFETCH_MULTIPLIER=1  # Reduce from 4
```

#### Solution 4: Optimize Redis Memory

**Problem:** Redis memory usage too high

**Fix:**

```bash
# Set maxmemory policy
docker-compose exec -T redis redis-cli CONFIG SET maxmemory 1gb
docker-compose exec -T redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Check memory usage by key
docker-compose exec -T redis redis-cli --scan --pattern 'analysis:*' | head -10 |
  xargs -I {} docker-compose exec -T redis redis-cli MEMORY USAGE {}

# Clear old cached results
docker-compose exec -T redis redis-cli --scan --pattern 'result:*' |
  head -1000 | xargs -I {} docker-compose exec -T redis redis-cli DEL {}
```

#### Solution 5: Database Memory Tuning

**Problem:** PostgreSQL consuming too much memory

**Fix:**

```bash
# Add to docker-compose.yml
services:
  db:
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=512MB"  # 25% of available RAM
      - "-c"
      - "effective_cache_size=2GB"  # 50-75% of RAM
      - "-c"
      - "maintenance_work_mem=128MB"
      - "-c"
      - "work_mem=16MB"
      - "-c"
      - "max_connections=100"
```

### Verification

```bash
# Monitor memory after changes
watch -n 5 'docker stats --no-stream $(docker-compose ps -q)'

# Check for OOM kills (should be none)
docker events --filter 'type=oom' --since 1h | wc -l

# Verify Redis memory under limit
docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human

# Check container restarts
docker inspect $(docker-compose ps -q) | jq '.[] | {name: .Name, restart_count: .RestartCount}'
```

---

## 3. Celery Queue Backup

### Symptoms

- Tasks take too long to process
- Flower dashboard shows queue depth > 100
- Tasks pile up during peak load
- Users wait long for analysis results

### Diagnosis

```bash
# Check queue depth
curl -s http://localhost:5555/api/tasks | jq '.length'

# Check worker status
curl -s http://localhost:5555/api/workers | jq '.'

# Check task processing rate
docker-compose logs celery_worker | grep "Task.*succeeded" | tail -100 |
  awk '{print $1, $2}' | uniq -c

# Check for failed tasks
curl -s http://localhost:5555/api/tasks?state=FAILURE | jq 'length'

# Monitor task duration
docker-compose logs celery_worker --tail 100 | grep "runtime" |
  awk -F'retval=' '{print $2}' | awk '{print $1}' | sort -n | tail -10
```

### Solutions

#### Solution 1: Increase Worker Concurrency

**Problem:** Not enough workers to handle load

**Fix:**

```yaml
# In docker-compose.yml, scale workers
docker-compose up -d --scale celery_worker=4

# Or increase concurrency per worker
services:
  celery_worker:
    command: celery -A celery_app.celery_app worker --concurrency=8  # Increase from 4
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G  # Increase memory for more concurrency
```

#### Solution 2: Optimize Task Batching

**Problem:** Tasks processed inefficiently

**Fix:**

```python
# Batch similar tasks together
@app.task(bind=True, max_retries=3)
def process_resumes_batch(self, resume_ids: List[int]):
    batch_size = 10
    results = []

    for i in range(0, len(resume_ids), batch_size):
        batch = resume_ids[i:i + batch_size]
        # Process batch in parallel
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            batch_results = list(executor.map(analyze_resume, batch))
        results.extend(batch_results)

    return results
```

#### Solution 3: Implement Task Priorities

**Problem:** Urgent tasks stuck behind slow tasks

**Fix:**

```python
# Define priority queues
from kombu import Queue

app.conf.task_queues = [
    Queue('high_priority', routing_key='high'),
    Queue('default', routing_key='default'),
    Queue('low_priority', routing_key='low'),
]

# Assign priorities
@app.task(queue='high_priority')
def urgent_analysis_task(resume_id: int):
    # Time-sensitive analysis
    pass

@app.task(queue='low_priority')
def background_cleanup_task():
    # Non-urgent cleanup
    pass

# Configure workers for priority queues
# celery_worker_high: celery worker -Q high_priority,default -c 4
# celery_worker_low: celery worker -Q low_priority,default -c 2
```

#### Solution 4: Add Auto-Scaling

**Problem:** Static worker count can't handle variable load

**Fix:**

```bash
# Install celery autoscaling tools
pip install celery[redis,sqs]

# Configure autoscaling in docker-compose.yml
services:
  celery_worker:
    command: >
      celery -A celery_app.celery_app worker
      --autoscale=10,2  # Max 10, min 2
      --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
```

#### Solution 5: Optimize Task Timeouts and Retries

**Problem:** Failed tasks clog the queue

**Fix:**

```python
# Configure task timeouts
@app.task(
    bind=True,
    max_retries=3,
    time_limit=300,      # Hard limit: 5 minutes
    soft_time_limit=240, # Soft limit: 4 minutes
    acks_late=True,      # Only acknowledge after completion
)
def analyze_resume(self, resume_id: int):
    try:
        # Analysis logic
        pass
    except SoftTimeLimitExceeded:
        # Gracefully handle timeout
        logger.warning(f"Task {resume_id} timed out, will retry")
        self.retry(countdown=60)
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(exc=exc, countdown=60)
```

#### Solution 6: Implement Result Expiration

**Problem:** Old results clog the backend

**Fix:**

```python
# Set result expiration
app.conf.task_result_expires = 3600  # 1 hour
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Clean up old results periodically
@app.task
def cleanup_old_results():
    from celery.result import AsyncResult
    # Remove results older than 24 hours
    pass

# Schedule cleanup
app.conf.beat_schedule = {
    'cleanup-old-results': {
        'task': 'cleanup_old_results',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

### Verification

```bash
# Monitor queue depth (should be < 10)
watch -n 5 'curl -s http://localhost:5555/api/tasks | jq ".length"'

# Check worker processing rate
docker-compose logs celery_worker --since 5m | grep "succeeded" | wc -l

# Verify tasks complete within SLA
curl -s http://localhost:5555/api/tasks | jq '.[] | select(.state=="SUCCESS") | .runtime' |
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "s"}'

# Test with load test
# This should complete without queue backup
for i in {1..50}; do
  curl -X POST http://localhost:8000/api/v1/analyze -F "file=@test_resume.pdf" &
done
wait
```

---

## 4. Slow ML Model Inference

### Symptoms

- Resume analysis takes > 30 seconds
- ML inference latency spikes in Grafana
- Model loading time is excessive
- High GPU/CPU usage during inference

### Diagnosis

```bash
# Check model loading time
docker-compose logs celery_worker | grep "Loading model" | tail -10

# Check inference time per model
docker-compose logs celery_worker | grep "inference" | tail -20

# Check which models are loaded
docker-compose exec celery_worker python -c "
from backend.services.model_manager import get_model_manager
mm = get_model_manager()
print('Loaded models:', list(mm.loaded_models.keys()))
"

# Profile model inference
docker-compose exec celery_worker python -m cProfile -s cumulative \
  -o profile.stats backend/analyzers/skill_matcher.py
```

### Solutions

#### Solution 1: Use Smaller/Faster Models

**Problem:** Models too large for use case

**Fix:**

```python
# Use smaller models
# Instead of:
model = SentenceTransformer('all-mpnet-base-v2')  # 420MB, 1.2s inference

# Use:
model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, 0.3s inference

# Or use quantized models
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    'model-name',
    load_in_8bit=True  # Reduce memory by ~50%
)
```

#### Solution 2: Implement Model Caching

**Problem:** Models reloaded on every task

**Fix:**

```python
# Cache models in memory
from functools import lru_cache

@lru_cache(maxsize=5)
def get_model(model_name: str):
    """Load and cache models"""
    return SentenceTransformer(model_name)

# Use in tasks
@app.task
def analyze_skills(text: str):
    model = get_model('all-MiniLM-L6-v2')  # Cached after first load
    embeddings = model.encode(text)
    return embeddings
```

#### Solution 3: Batch Processing

**Problem:** Processing one resume at a time

**Fix:**

```python
# Batch multiple resumes
@app.task
def analyze_resume_batch(resume_ids: List[int]):
    model = get_model('all-MiniLM-L6-v2')

    # Load all resumes
    resumes = [load_resume(id) for id in resume_ids]
    texts = [r['text'] for r in resumes]

    # Encode in batch (much faster)
    embeddings = model.encode(texts, batch_size=16, show_progress_bar=False)

    # Process results
    results = process_embeddings(embeddings, resumes)
    return results
```

#### Solution 4: Model Preloading

**Problem:** First request slow due to model loading

**Fix:**

```python
# Preload models on worker startup
# In celery_app.py:
from celery.signals import worker_ready

@worker_ready.connect
def preload_models(**kwargs):
    """Preload models when worker starts"""
    logger.info("Preloading ML models...")
    get_model('all-MiniLM-L6-v2')
    get_model('en_core_web_sm')
    logger.info("Models preloaded successfully")
```

#### Solution 5: Use GPU Acceleration

**Problem:** CPU inference too slow

**Fix:**

```yaml
# Enable GPU in docker-compose.yml
services:
  celery_worker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0

# In Python, use GPU
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = model.to(device)
```

### Verification

```bash
# Test inference time
time docker-compose exec celery_worker python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.encode(['test text'] * 10)
"

# Check model caching works
docker-compose logs celery_worker | grep "Preloading ML models"

# Monitor batch processing performance
docker-compose logs celery_worker | grep "Batch processing" | tail -10
```

---

## 5. Frontend Performance Issues

### Symptoms

- Page load time > 3 seconds
- Janky scrolling or interactions
- High bundle size
- Slow initial render

### Diagnosis

```bash
# Analyze bundle size
npm run build
ls -lh dist/assets/*.js | sort -k5 -h

# Check with Lighthouse
npx lighthouse http://localhost:5173 --view

# Monitor with browser DevTools
# Open Chrome DevTools > Performance > Record
# Interact with the application
# Stop recording and analyze

# Check for large dependencies
npm run build -- --report
# Open dist/report.html to see bundle analysis
```

### Solutions

#### Solution 1: Code Splitting

**Problem:** Large bundle blocks initial render

**Fix:**

```typescript
// Route-based splitting
import { lazy, Suspense } from 'react'

const UploadPage = lazy(() => import('./pages/UploadPage'))
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'))

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/analysis" element={<AnalysisPage />} />
      </Routes>
    </Suspense>
  )
}
```

#### Solution 2: Virtualization for Large Lists

**Problem:** Rendering large lists causes lag

**Fix:**

```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function CandidateList({ candidates }: { candidates: Candidate[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: candidates.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated row height
    overscan: 5, // Render 5 extra items above/below
  })

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <CandidateCard candidate={candidates[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### Solution 3: Optimize API Calls

**Problem:** Too many API calls or redundant requests

**Fix:**

```typescript
// Implement request debouncing
import { useDebouncedCallback } from 'use-debounce'

function SearchBar() {
  const debouncedSearch = useDebouncedCallback((query: string) => {
    searchCandidates(query)
  }, 500) // Wait 500ms after typing stops

  return <input onChange={(e) => debouncedSearch(e.target.value)} />
}

// Implement request caching
import { useQuery } from '@tanstack/react-query'

function useVacancies() {
  return useQuery({
    queryKey: ['vacancies'],
    queryFn: fetchVacancies,
    staleTime: 60000, // Cache for 1 minute
    cacheTime: 300000, // Keep in cache for 5 minutes
  })
}
```

#### Solution 4: Image Optimization

**Problem:** Large images slow down loading

**Fix:**

```typescript
// Lazy load images
import { LazyLoadImage } from 'react-lazy-load-image-component'

function CandidateProfile({ avatar }: { avatar: string }) {
  return (
    <LazyLoadImage
      src={avatar}
      alt="Candidate avatar"
      effect="blur" // Blur effect while loading
      threshold={200} // Load 200px before entering viewport
    />
  )
}

// Use modern formats
// Convert images to WebP/AVIF for 30-50% size reduction
```

### Verification

```bash
# Check bundle size after optimizations
npm run build
du -sh dist/assets/

# Run Lighthouse audit
npx lighthouse http://localhost:5173 --json --output json > lighthouse-report.json
cat lighthouse-report.json | jq '.categories.performance.score'

# Test on slow 3G connection
# Chrome DevTools > Network > Throttling > Slow 3G
# Reload page and measure load time
```

---

## 6. Database Performance Issues

### Symptoms

- Slow queries (> 100ms average)
- High database CPU usage
- Connection pool exhaustion
- Database locks blocking queries

### Diagnosis

```bash
# Identify slow queries
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT query, calls, mean_exec_time, max_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;"

# Check for missing indexes
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;"

# Check table bloat
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
       pg_total_relation_size(schemaname||'.'||tablename) * 100.0 /
         (SELECT sum(pg_total_relation_size(schemaname||'.'||tablename))
          FROM pg_tables WHERE schemaname = 'public') AS percentage
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check for locks
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT pid, usename, pg_blocking_pids(pid) AS blocked_by,
       query as blocked_query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;"
```

### Solutions

#### Solution 1: Add Missing Indexes

**Problem:** Queries perform full table scans

**Fix:**

```sql
-- Create indexes on frequently filtered columns
CREATE INDEX CONCURRENTLY idx_candidates_status ON candidates(status);
CREATE INDEX CONCURRENTLY idx_candidates_created_at ON candidates(created_at DESC);

-- Create composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_vacancies_status_created ON vacancies(status, created_at DESC);

-- Create indexes for foreign keys
CREATE INDEX CONCURRENTLY idx_analysis_tasks_candidate_id ON analysis_tasks(candidate_id);

-- Create partial indexes for specific conditions
CREATE INDEX CONCURRENTLY idx_active_candidates ON candidates(id) WHERE status = 'active';

-- Analyze index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

#### Solution 2: Optimize Query Performance

**Problem:** Inefficient query structure

**Fix:**

```python
# BAD: Multiple queries
def get_candidate_with_skills(candidate_id: int):
    candidate = db.query(Candidate).filter_by(id=candidate_id).first()
    skills = db.query(Skill).filter_by(candidate_id=candidate_id).all()
    return {"candidate": candidate, "skills": skills}

# GOOD: Single query with join
def get_candidate_with_skills(candidate_id: int):
    return db.query(Candidate).options(
        joinedload(Candidate.skills)
    ).filter_by(id=candidate_id).first()

# Use pagination for large result sets
def get_candidates(page: int = 1, per_page: int = 50):
    return db.query(Candidate).limit(per_page).offset((page - 1) * per_page).all()
```

#### Solution 3: Connection Pool Optimization

**Problem:** Pool exhausted or too small

**Fix:**

```bash
# Update .env
DB_POOL_SIZE=20  # Increase from default 5
DB_MAX_OVERFLOW=10  # Allow 10 extra connections
DB_POOL_TIMEOUT=30  # Wait 30s for connection
DB_POOL_RECYCLE=3600  # Recycle connections after 1 hour

# Monitor pool usage
docker-compose logs backend | grep "connection pool"
```

#### Solution 4: Database Vacuum and Analyze

**Problem:** Table bloat and outdated statistics

**Fix:**

```bash
# Run vacuum and analyze
docker-compose exec -T db psql -U agenthr -d agenthr -c "VACUUM ANALYZE;"

# Schedule automatic vacuum
# In docker-compose.yml:
services:
  db:
    command:
      - "postgres"
      - "-c"
      - "autovacuum=on"
      - "-c"
      - "autovacuum_vacuum_scale_factor=0.1"  # Vacuum when 10% of rows change
      - "-c"
      - "autovacuum_analyze_scale_factor=0.05"  # Analyze when 5% change

# Monitor bloat
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Verification

```bash
# Re-check slow queries
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT mean_exec_time < 0.1 AS queries_optimized
FROM pg_stat_statements
WHERE query LIKE '%SELECT%'
LIMIT 1;"

# Verify indexes are being used
docker-compose exec -T db psql -U agenthr -d agentagenthr -c "
EXPLAIN ANALYZE SELECT * FROM candidates WHERE status = 'active';"
# Should show "Index Scan" not "Seq Scan"

# Monitor connection pool
docker-compose logs backend --tail 100 | grep "pool" | tail -10
```

---

## Performance Tuning Checklist

Use this checklist to systematically identify and resolve performance issues.

### Quick Health Check (Run First)

```bash
#!/bin/bash
echo "=== AgentHR Performance Health Check ==="
echo ""

# 1. Container Status
echo "1. Container Status:"
docker-compose ps
echo ""

# 2. Resource Usage
echo "2. Resource Usage:"
docker stats --no-stream $(docker-compose ps -q)
echo ""

# 3. API Response Time
echo "3. API Response Time:"
curl -w "Total: %{time_total}s\n" -o /dev/null -s http://localhost:8000/health
echo ""

# 4. Queue Depth
echo "4. Celery Queue Depth:"
curl -s http://localhost:5555/api/tasks | jq '.length'
echo ""

# 5. Database Connections
echo "5. Database Connections:"
docker-compose exec -T db psql -U agenthr -d agenthr -c "SELECT count(*) FROM pg_stat_activity;"
echo ""

# 6. Slow Queries
echo "6. Slow Queries (avg > 100ms):"
docker-compose exec -T db psql -U agenthr -d agenthr -c "
SELECT count(*) FROM pg_stat_statements WHERE mean_exec_time > 0.1;"
echo ""

# 7. Redis Memory
echo "7. Redis Memory:"
docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human
echo ""

# 8. OOM Kills (last 24h)
echo "8. OOM Kills (last 24h):"
docker events --filter 'type=oom' --since 24h | wc -l
echo ""

echo "=== Health Check Complete ==="
```

### Component-Specific Checks

#### ML Models
- [ ] Models cached in memory
- [ ] Batch size optimized (4-8)
- [ ] Model loading time < 5 seconds
- [ ] Inference time < 10 seconds per resume
- [ ] Memory usage < 80% of limit

#### Celery Workers
- [ ] Queue depth < 10 tasks
- [ ] Worker concurrency appropriate (2-8 per worker)
- [ ] Task failure rate < 5%
- [ ] Average task duration < 30 seconds
- [ ] No task retries exceeding limit

#### Redis Cache
- [ ] Memory usage < 80% of max
- [ ] Cache hit rate > 70%
- [ ] Eviction policy configured (allkeys-lru)
- [ ] Old results expire automatically
- [ ] Model cache size limited

#### PostgreSQL
- [ ] All foreign keys indexed
- [ ] No sequential scans on large tables
- [ ] Connection pool size appropriate (10-20)
- [ ] Average query time < 100ms
- [ ] No long-running locks

#### Frontend
- [ ] Initial load time < 3 seconds
- [ ] Bundle size < 500KB (gzipped)
- [ ] Large lists use virtualization
- [ ] Images lazy-loaded
- [ ] API calls debounced/cached

### Diagnostic Commands Reference

```bash
# API Performance
curl -w "@-" -o /dev/null -s 'http://localhost:8000/api/v1/candidates' <<'EOF'
time_total: %{time_total}\n
EOF

# Database
docker-compose exec -T db psql -U agenthr -d agenthr -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Celery
curl -s http://localhost:5555/api/workers | jq '.'
docker-compose logs celery_worker --tail 100 | grep "succeeded\|failed"

# Redis
docker-compose exec -T redis redis-cli INFO stats
docker-compose exec -T redis redis-cli --scan --pattern 'analysis:*' | head -10 | xargs -I {} redis-cli MEMORY USAGE {}

# Memory/Docker
docker stats --no-stream $(docker-compose ps -q)
docker events --filter 'type=oom' --since 1h

# Monitoring
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])' | jq '.data.result'
```

### Common Bottleneck Patterns

| Symptom | Likely Cause | First Check |
|---------|-------------|-------------|
| **Slow API** | Database queries | Check `pg_stat_statements` |
| **High memory** | ML models | Check loaded models |
| **Queue backup** | Insufficient workers | Check worker concurrency |
| **Frontend slow** | Large bundle | Check bundle size |
| **DB CPU high** | Missing indexes | Check query plan |
| **Redis full** | No expiration | Check `maxmemory-policy` |

### Performance Tuning Priority Matrix

```
High Impact, Low Effort (Do First):
├── Add database indexes
├── Enable Redis cache expiration
├── Implement frontend code splitting
└── Configure connection pooling

High Impact, High Effort (Plan Carefully):
├── Implement model quantization
├── Add GPU acceleration
├── Redesign database schema
└── Implement microservices architecture

Low Impact, Low Effort (Quick Wins):
├── Tune worker concurrency
├── Optimize batch sizes
├── Enable compression
└── Clean up old data

Low Impact, High Effort (Avoid):
├── Premature optimization
├── Rewriting working code
└── Over-engineering solutions
```

### When to Escalate

Escalate to senior engineers or infrastructure team if:

- Performance degrades after optimization
- Unable to identify bottleneck with available tools
- Changes require database downtime
- Optimization affects multiple services
- Resource limits reached on current infrastructure

---

## Related Documentation

- [ML_PIPELINE.md](ML_PIPELINE.md) - Detailed ML/NLP pipeline documentation
- [backend/analyzers/MATCHERS_GUIDE.md](backend/analyzers/MATCHERS_GUIDE.md) - Skill matching methods
- [backend/docs/BACKGROUND_TASKS.md](backend/docs/BACKGROUND_TASKS.md) - Complete Celery task documentation
- [SETUP.md](SETUP.md) - Initial setup and configuration
- [monitoring/README.md](monitoring/README.md) - Monitoring setup and metrics
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) - Complete configuration reference

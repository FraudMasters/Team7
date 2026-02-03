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

## Related Documentation

- [ML_PIPELINE.md](ML_PIPELINE.md) - Detailed ML/NLP pipeline documentation
- [backend/analyzers/MATCHERS_GUIDE.md](backend/analyzers/MATCHERS_GUIDE.md) - Skill matching methods
- [SETUP.md](SETUP.md) - Initial setup and configuration
- [monitoring/README.md](monitoring/README.md) - Monitoring setup and metrics
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) - Complete configuration reference

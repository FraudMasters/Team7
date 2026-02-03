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

## Related Documentation

- [ML_PIPELINE.md](ML_PIPELINE.md) - Detailed ML/NLP pipeline documentation
- [SETUP.md](SETUP.md) - Initial setup and configuration
- [monitoring/README.md](monitoring/README.md) - Monitoring setup and metrics
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) - Complete configuration reference

# Performance Tracking

This document describes the performance monitoring system integrated into the frontend API client.

## Overview

The performance tracking system automatically monitors all API calls made through the `apiClient`, collecting metrics on:
- Request duration (milliseconds)
- HTTP status codes
- Success/failure rates
- Response sizes (when available)
- Endpoint usage patterns

## Usage

### Automatic Tracking

Performance metrics are automatically tracked for all API calls. No code changes are needed in your components.

```tsx
import { apiClient } from '@/api/client';

// All API calls are automatically tracked
const candidates = await apiClient.listCandidates();
const metrics = apiClient.getPerformanceStats();

console.log(`Average duration: ${metrics.averageDuration}ms`);
console.log(`Total calls: ${metrics.totalCalls}`);
console.log(`Success rate: ${(metrics.successfulCalls / metrics.totalCalls * 100).toFixed(1)}%`);
```

### Viewing Metrics

#### Get Performance Statistics

```tsx
const stats = apiClient.getPerformanceStats();

// stats contains:
// - totalCalls: number
// - successfulCalls: number
// - failedCalls: number
// - averageDuration: number
// - minDuration: number
// - maxDuration: number
// - p95Duration: number
// - slowestEndpoint: { endpoint, averageDuration, callCount }
// - mostCalledEndpoint: { endpoint, callCount, averageDuration }
```

#### Log Summary to Console

```tsx
// In development mode, logs a formatted summary
apiClient.logPerformanceSummary();

// Output:
// [API Performance Summary]
// Total calls: 45
// Successful: 42 (93.3%)
// Failed: 3 (6.7%)
// Average duration: 245ms
// Min duration: 120ms
// Max duration: 850ms
// P95 duration: 612ms
// Slowest endpoint: /api/resumes/analyze (425ms avg, 5 calls)
// Most called: /api/candidates (15 calls, 180ms avg)
```

#### Advanced Metrics

```ts
import {
  getMetrics,
  getMetricsByEndpoint,
  getMetricsBySuccess,
  getMetricsByMethod,
  logMetricsByEndpoint,
  exportMetricsAsJson,
  getRecentMetrics,
} from '@/utils/performanceTracker';

// Get all metrics
const allMetrics = getMetrics();

// Filter by endpoint
const candidateMetrics = getMetricsByEndpoint('/api/candidates');

// Filter by success/failure
const failedMetrics = getMetricsBySuccess(false);

// Filter by method
const postMetrics = getMetricsByMethod('POST');

// Log detailed breakdown by endpoint
logMetricsByEndpoint();

// Export as JSON for analysis
const json = exportMetricsAsJson();

// Get recent metrics (last 5 minutes)
const recent = getRecentMetrics();
const lastMinute = getRecentMetrics(60000); // Last 1 minute
```

## Console Output

In development mode, API calls are logged in real-time:

```
[API Performance] ✓ GET /api/candidates - 180ms (200)
[API Performance] ✓ POST /api/resumes/upload - 2450ms (201)
[API Performance] ✗ POST /api/resumes/analyze - 12050ms (500)
```

Colors indicate performance:
- 🟢 Green: Fast (< 500ms)
- 🟡 Yellow: Medium (500-1000ms)
- 🔴 Red: Slow (> 1000ms)

## Configuration

### Enable/Disable Logging

Set environment variable in `.env`:

```bash
# Enable performance logging (default: true in dev)
VITE_ENABLE_PERFORMANCE_LOGGING=true

# Disable in production
VITE_ENABLE_PERFORMANCE_LOGGING=false
```

### Storage Limits

- Stores up to 1,000 most recent API calls
- Older metrics are automatically discarded
- Prevents memory issues in long-running sessions

## Performance Considerations

- **Non-blocking**: Tracking uses async operations and doesn't block API responses
- **Lightweight**: Minimal overhead (~1-2ms per request)
- **Memory-safe**: Automatic cleanup of old metrics
- **Development-friendly**: Detailed logging in dev mode only

## Use Cases

### 1. Monitor API Performance

```tsx
useEffect(() => {
  const interval = setInterval(() => {
    const stats = apiClient.getPerformanceStats();
    if (stats.averageDuration > 1000) {
      console.warn('API performance degrading:', stats);
    }
  }, 30000); // Check every 30 seconds

  return () => clearInterval(interval);
}, []);
```

### 2. Track Slow Endpoints

```tsx
const stats = apiClient.getPerformanceStats();
if (stats.slowestEndpoint?.averageDuration > 2000) {
  console.warn(`Slow endpoint detected: ${stats.slowestEndpoint.endpoint}`);
  // Consider caching or optimizing this endpoint
}
```

### 3. Debug API Issues

```tsx
try {
  await apiClient.analyzeResume({ resume_id: 'abc-123' });
} catch (error) {
  apiClient.logPerformanceSummary();
  // Review metrics to identify patterns in failures
}
```

### 4. Performance Analytics

```tsx
import { exportMetricsAsJson } from '@/utils/performanceTracker';

const sendMetricsToAnalytics = () => {
  const metrics = exportMetricsAsJson();
  // Send to your analytics service
  analytics.track('api_performance', { metrics });
};
```

## Types

### ApiMetric

```ts
interface ApiMetric {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  success: boolean;
  timestamp: number;
  error?: string;
  responseSize?: number;
}
```

### PerformanceStats

```ts
interface PerformanceStats {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  averageDuration: number;
  minDuration: number;
  maxDuration: number;
  p95Duration: number;
  slowestEndpoint: {
    endpoint: string;
    averageDuration: number;
    callCount: number;
  } | null;
  mostCalledEndpoint: {
    endpoint: string;
    callCount: number;
    averageDuration: number;
  } | null;
}
```

## Best Practices

1. **Monitor in Development**: Use `logPerformanceSummary()` during development to catch performance issues early
2. **Set Alerts**: Monitor `p95Duration` and `averageDuration` for performance regression
3. **Track Slow Endpoints**: Use `slowestEndpoint` data to prioritize optimization efforts
4. **Clean Data**: Call `clearMetrics()` between test runs to get accurate measurements
5. **Export for Analysis**: Use `exportMetricsAsJson()` for deeper analysis or reporting

## Examples

### React DevTools Integration

```tsx
import { apiClient } from '@/api/client';

if (import.meta.env.DEV) {
  // Expose to window for debugging
  (window as any).apiMetrics = {
    getStats: () => apiClient.getPerformanceStats(),
    logSummary: () => apiClient.logPerformanceSummary(),
  };
}

// Use in browser console:
// apiMetrics.logSummary()
```

### Performance Monitoring Component

```tsx
function PerformanceMonitor() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const updateStats = () => {
      setStats(apiClient.getPerformanceStats());
    };

    updateStats();
    const interval = setInterval(updateStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!stats || !import.meta.env.DEV) return null;

  return (
    <div className="performance-monitor">
      <div>Avg: {stats.averageDuration}ms</div>
      <div>P95: {stats.p95Duration}ms</div>
      <div>Success: {((stats.successfulCalls / stats.totalCalls) * 100).toFixed(1)}%</div>
    </div>
  );
}
```

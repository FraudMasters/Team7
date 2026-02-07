# Frontend Health Dashboard Verification Guide

## Subtask: subtask-6-6
**Description:** Verify frontend dashboard shows correct status for all services

## Prerequisites

Before running verification, ensure the following services are running:

1. **Backend Server** (FastAPI):
   ```bash
   cd backend
   python main.py
   ```
   Expected: Running on http://localhost:8000

2. **Frontend Dev Server** (Vite):
   ```bash
   cd frontend
   npm run dev
   ```
   Expected: Running on http://localhost:5173

## Automated Verification

### Shell Script
Run the automated verification script:
```bash
bash frontend/tests/verification/test_frontend_health_dashboard.sh
```

This script checks:
- ✅ Backend health endpoint returns 200
- ✅ All expected services are present in response
- ✅ Status values (healthy/degraded/unhealthy) are correct
- ✅ Dependency graph endpoint returns valid data
- ✅ Frontend route is accessible
- ✅ Response structure matches expected format

## Manual Verification Steps

### 1. Navigate to Health Dashboard
**URL:** http://localhost:5173/recruiter/health

**Expected Result:**
- Page loads without errors
- "System Health Dashboard" heading is visible
- No console errors (check browser DevTools)

### 2. Verify All Services Show Correct Status Colors

**Expected Services:**
- Database (should show green/yellow/red status)
- Redis Cache (should show green/yellow/red status)
- Celery Workers (should show green/yellow/red status)
- NER Model (should show green/yellow/red status)
- Zero-Shot Model (should show green/yellow/red status)
- Language Tools (should show green/yellow/red status)
- External APIs (should show green/yellow/red status)

**Status Color Legend:**
- 🟢 **Green (Healthy)**: Component is fully operational
- 🟡 **Yellow (Degraded)**: Component is working but with issues
- 🔴 **Red (Unhealthy)**: Component is down or failing

**Verification:**
- Each service card has a colored left border indicating status
- Status chip shows "HEALTHY", "DEGRADED", or "UNHEALTHY"
- Status icon matches the status (checkcircle/warning/error)
- Color is consistent across all UI elements

### 3. Click on a Service to See Detailed Health Information

**Instructions:**
1. Click on any service card (e.g., "Database")
2. View the detailed information displayed

**Expected Result:**
For each service card, verify display shows:
- **Category:** Infrastructure, Messaging, ML, or External Services
- **Response Time:** in milliseconds (e.g., "45ms")
- **Essential:** Yes/No indicator
- **Error Message:** (if unhealthy, shows error details)

### 4. Verify Dependency Graph Displays Correctly

**Instructions:**
1. Scroll to "Service Dependency Graph" section
2. Hover over each service node

**Expected Result:**
- All service nodes are visible with labels
- Color-coded status indicators on each node
- Essential services have a blue dot indicator
- Connection lines show dependencies between services
- Legend shows: Healthy count, Degraded count, Unhealthy count, Essential Service marker

**Hover Interaction:**
- Hovering highlights related connections
- Service details panel appears with:
  - Service name and category
  - Essential/Optional chip
  - Status chip
  - Dependencies list ("DEPENDS ON")
  - Dependents list ("USED BY")
  - Service description

**Critical Path:**
- "Critical Dependency Path" section shows the longest essential chain
- Services are connected with arrow separators (→)

### 5. Trigger a Service Failure and Verify Status Updates

**Method 1: Stop a Non-Essential Service (Recommended)**
1. Stop ML model loading or disable external API
2. Wait for auto-refresh (30 seconds) or click "Refresh" button
3. Verify service status changes to "DEGRADED" (yellow)
4. Verify overall system status remains "HEALTHY" or changes to "DEGRADED"
5. Restart the service
6. Verify status updates back to "HEALTHY" (green)

**Method 2: Stop an Essential Service (Advanced)**
1. Stop Redis or database temporarily
2. Wait for health check to detect failure
3. Verify service status changes to "UNHEALTHY" (red)
4. Verify overall system status changes to "UNHEALTHY"
5. Restart the service
6. Verify status recovers to "HEALTHY" (green)

**Auto-Refresh Verification:**
1. Note the "Last updated" timestamp
2. Wait 30 seconds
3. Verify timestamp updates automatically
4. Verify service statuses refresh if changed

**Manual Refresh Verification:**
1. Click the "Refresh" button
2. Verify circular progress indicator appears
3. Verify "Last updated" timestamp changes
4. Verify service data updates

## Expected Component Behavior

### HealthDashboard Component

**State Management:**
- `healthData`: Stores detailed health check results
- `dependencyData`: Stores dependency graph information
- `loading`: Shows loading spinner on initial load
- `error`: Displays error message if API calls fail
- `lastRefresh`: Shows timestamp of last data refresh
- `refreshing`: Disables refresh button during refresh

**Auto-Refresh:**
- Triggers every 30 seconds via `setInterval`
- Cleans up interval on component unmount
- Updates both health and dependency data

### DependencyGraph Component

**Visual Features:**
- Hierarchical layout based on dependency depth
- SVG-based rendering with service nodes and connection lines
- Color-coded health status (green/yellow/red)
- Essential service markers (blue dot)
- Interactive hover states with highlight effects

**Interactions:**
- Hover highlights related services and connections
- Service details panel shows on hover
- Legend displays status counts
- Critical path visualization

## Acceptance Criteria Verification

- ✅ Each service shows green/yellow/red status indicator
- ✅ Service status cards display detailed information (category, response time, essential flag)
- ✅ Dependency graph renders with all services
- ✅ Dependency graph shows service relationships (dependencies and dependents)
- ✅ Hover interactions display detailed service information
- ✅ Auto-refresh updates status every 30 seconds
- ✅ Manual refresh button works correctly
- ✅ Overall system health status displays correctly
- ✅ Critical issues and warnings display when present
- ✅ Health percentage score is displayed

## Troubleshooting

### Issue: Health dashboard shows "Failed to fetch health data"
**Solution:** Verify backend server is running on port 8000

### Issue: Services all show "unknown" status
**Solution:** Check browser console for API errors, verify CORS settings

### Issue: Dependency graph doesn't render
**Solution:** Verify dependency graph API endpoint returns data

### Issue: Status colors don't match actual service state
**Solution:** Check backend health check service for correct status mapping

### Issue: Auto-refresh not working
**Solution:** Check browser console for JavaScript errors

## Test Data Examples

### Healthy Response Example
```json
{
  "status": "healthy",
  "overall_health_percentage": 100,
  "checks": {
    "database": {
      "status": "healthy",
      "essential": true,
      "category": "infrastructure",
      "response_time_ms": 15
    },
    "redis": {
      "status": "healthy",
      "essential": true,
      "category": "messaging",
      "response_time_ms": 5
    }
  },
  "critical_issues": [],
  "warnings": []
}
```

### Degraded Response Example
```json
{
  "status": "degraded",
  "overall_health_percentage": 85,
  "checks": {
    "ml_ner_model": {
      "status": "degraded",
      "essential": false,
      "category": "ml",
      "response_time_ms": null
    }
  },
  "critical_issues": [],
  "warnings": ["NER Model is not loaded"]
}
```

### Unhealthy Response Example
```json
{
  "status": "unhealthy",
  "overall_health_percentage": 33,
  "checks": {
    "redis": {
      "status": "unhealthy",
      "essential": true,
      "category": "messaging",
      "error": "Connection refused"
    }
  },
  "critical_issues": ["Redis is unavailable"],
  "warnings": []
}
```

## Completion Checklist

- [ ] Automated verification script passes all tests
- [ ] Manual verification completed for all steps
- [ ] All service status indicators display correctly
- [ ] Dependency graph renders and shows relationships
- [ ] Service details appear on hover/click
- [ ] Auto-refresh functionality works
- [ ] Manual refresh button works
- [ ] Status colors are accurate (green/yellow/red)
- [ ] Essential service markers display correctly
- [ ] Response times are shown for healthy services
- [ ] Critical issues and warnings display when present
- [ ] No console errors on page load or refresh

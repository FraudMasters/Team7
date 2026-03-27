# End-to-End Verification Guide: Bias Detection & Fairness Metrics

This document provides comprehensive instructions for verifying the complete user flow of the bias detection and fairness metrics feature.

## Overview

The bias detection feature implements the following workflow:

```
1. Create Job Vacancy
   ↓
2. Upload & Rank Candidates
   ↓
3. Demographic Inference (automatic)
   ↓
4. Fairness Metrics Calculation (scheduled/triggered)
   ↓
5. Bias Alert Creation (if thresholds exceeded)
   ↓
6. Notification Sent to Admin (email/in-app)
   ↓
7. Admin Reviews Alert
   ↓
8. Alert Acknowledgment
   ↓
9. Status Update & Audit Trail
```

## Verification Methods

We provide **three** verification approaches:

### 1. Database-Level Verification (Recommended)
Uses direct database access to verify the complete flow.

**Script:** `backend/scripts/verify_e2e_bias_detection.py`

**Prerequisites:**
- Backend dependencies installed
- Database accessible
- No backend server required

**Steps:**
```bash
# Navigate to project root
cd /path/to/agenthr

# Run verification script
python backend/scripts/verify_e2e_bias_detection.py
```

**What it tests:**
1. ✓ Creates job vacancy with diverse candidates
2. ✓ Verifies demographic inference runs
3. ✓ Triggers fairness monitoring task
4. ✓ Verifies fairness metrics calculated
5. ✓ Checks bias alerts created
6. ✓ Verifies notification system integration
7. ✓ Acknowledges alert via database update
8. ✓ Verifies alert status updated
9. ✓ Checks bias alert configuration system
10. ✓ Cleans up test data

**Expected Output:**
```
================================================================================
Step 1: Create job vacancy and rank candidates
================================================================================

✓ Created test vacancy: abc-123-def
✓ Created resume for Michael Johnson: xyz-456
✓ Created resume for Sarah Kim: xyz-457
...
✓ Created 5 rankings

================================================================================
Step 2: Verify demographic inference for candidates
================================================================================

ℹ Found 5 demographic inferences
...

✓ ALL VERIFICATION STEPS PASSED
```

### 2. API-Based Verification (Integration Testing)
Uses HTTP API endpoints to verify the flow from a client perspective.

**Script:** `backend/scripts/verify_api_e2e.py`

**Prerequisites:**
- Backend server running (`uvicorn main:app --reload`)
- Database accessible

**Steps:**
```bash
# Terminal 1: Start backend server
cd backend
uvicorn main:app --reload

# Terminal 2: Run API verification
python backend/scripts/verify_api_e2e.py --base-url http://localhost:8000
```

**What it tests:**
1. ✓ Backend server is running
2. ✓ POST /api/vacancies/ - Create vacancy
3. ✓ POST /api/resumes/ - Upload diverse resumes
4. ✓ POST /api/vacancies/{id}/rank - Trigger ranking
5. ✓ GET /api/fairness/metrics - Check fairness metrics
6. ✓ GET /api/fairness/alerts - Check bias alerts
7. ✓ POST /api/fairness/alerts/{id}/acknowledge - Acknowledge alert
8. ✓ GET /api/fairness/alerts/{id} - Verify status updated
9. ✓ GET /api/fairness/trends - Check trends API
10. ✓ DELETE /api/vacancies/{id} - Cleanup

**Expected Output:**
```
================================================================================
API-Based End-to-End Verification: Bias Detection & Fairness Metrics
================================================================================

ℹ Backend API URL: http://localhost:8000
✓ Backend server is running

================================================================================
Step 1: Create job vacancy via API
================================================================================

✓ Created vacancy: abc-123-def
...

✓ ALL API VERIFICATION STEPS PASSED
```

### 3. Pytest Integration Tests
Uses pytest fixtures and test infrastructure.

**Script:** `backend/tests/integration/test_bias_detection_e2e.py`

**Prerequisites:**
- Backend dependencies installed
- Test database configured

**Steps:**
```bash
# Run all integration tests
pytest backend/tests/integration/test_bias_detection_e2e.py -v

# Run specific test class
pytest backend/tests/integration/test_bias_detection_e2e.py::TestBiasDetectionE2E -v

# Run specific test method
pytest backend/tests/integration/test_bias_detection_e2e.py::TestBiasDetectionE2E::test_complete_bias_detection_workflow -v
```

**What it tests:**
1. ✓ Complete bias detection workflow
2. ✓ Bias reports generation
3. ✓ Bias alerts workflow
4. ✓ Bias alert configuration CRUD
5. ✓ Fairness summary for dashboard
6. ✓ Metrics filtering by protected attributes
7. ✓ Threshold evaluation and alert triggering
8. ✓ Demographic inference privacy
9. ✓ Bias metrics aggregation
10. ✓ Audit trail logging

**Expected Output:**
```
test_bias_detection_e2e.py::TestBiasDetectionE2E::test_complete_bias_detection_workflow PASSED
test_bias_detection_e2e.py::TestBiasDetectionE2E::test_bias_report_generation PASSED
...
==================== 12 passed in 5.23s ====================
```

## Manual UI Verification

For complete end-to-end verification including the frontend:

### Prerequisites
1. Backend server running: `uvicorn main:app --reload`
2. Frontend dev server running: `npm start`
3. Celery worker running: `celery -A tasks worker --loglevel=info`
4. Celery beat running: `celery -A tasks beat --loglevel=info`

### Step-by-Step UI Flow

#### Step 1: Create Job Vacancy
1. Navigate to: `http://localhost:3000/vacancies`
2. Click "Create New Vacancy"
3. Fill in job details:
   - Title: "Senior Data Scientist"
   - Required skills: Python, Machine Learning, Statistics, SQL
   - Experience: 5-10 years
4. Click "Create"
5. Note the vacancy ID

#### Step 2: Upload Candidate Resumes
1. Navigate to: `http://localhost:3000/vacancies/{vacancy_id}/candidates`
2. Upload diverse resumes (with varied demographic indicators):
   - Male names (Michael, James, Robert)
   - Female names (Sarah, Emily, Jennifer)
   - Diverse surnames (Johnson, Kim, Rodriguez, Chen)
   - Varied graduation years (2014-2020)
   - Different experience levels (4-12 years)
3. Verify resumes uploaded successfully

#### Step 3: Rank Candidates
1. Click "Rank Candidates" button
2. Wait for ranking process to complete
3. Verify rankings displayed with scores

#### Step 4: Trigger Fairness Monitoring
Option A: Wait for scheduled task (runs daily at 4 AM)
Option B: Trigger manually via admin panel or API:
```bash
curl -X POST http://localhost:8000/api/fairness/analyze \
  -H "Content-Type: application/json" \
  -d '{"vacancy_id": "your-vacancy-id"}'
```

#### Step 5: View Bias Detection Dashboard
1. Navigate to: `http://localhost:3000/bias-detection`
2. Verify the dashboard displays:
   - Overall fairness score (0-100)
   - Fairness metrics (Disparate Impact Ratio, Demographic Parity, etc.)
   - Protected attribute breakdowns (Gender, Age, Ethnicity)
   - Bias alerts (if thresholds exceeded)

#### Step 6: Review Fairness Trends
1. In the Bias Detection Dashboard, scroll to "Fairness Trends Over Time"
2. Verify the line chart displays:
   - Multiple fairness metrics over time
   - Period selector (7d, 30d, 90d)
   - Interactive tooltips with metric values
3. Change the period and verify chart updates

#### Step 7: Check Bias Alerts
1. Navigate to: `http://localhost:3000/fairness-monitoring`
2. Click the "Alerts" tab
3. Verify alerts are listed with:
   - Severity level (low, medium, high, critical)
   - Alert type (demographic_parity, equal_opportunity, etc.)
   - Protected attribute
   - Metric values and thresholds
   - Recommendations

#### Step 8: Acknowledge Alert
1. Click on a bias alert
2. Review the alert details:
   - Alert message
   - Affected demographic group
   - Current metric value vs. threshold
   - Mitigation recommendations
3. Click "Acknowledge" button
4. Verify alert status changes to "acknowledged"
5. Verify "Acknowledged at" timestamp is set

#### Step 9: Configure Alert Thresholds (Admin)
1. Navigate to: `http://localhost:3000/admin/bias-alert-config`
2. Verify existing configurations are displayed
3. Click "Create New Configuration"
4. Set custom thresholds:
   - Alert type: "demographic_parity"
   - Threshold: 0.75
   - Severity: "high"
   - Enable notifications
5. Click "Save"
6. Verify configuration appears in list

#### Step 10: Verify Notification System
1. Check email inbox for bias alert notification
2. Verify email contains:
   - Alert severity and type
   - Vacancy information
   - Fairness metrics
   - Actionable recommendations
   - Link to dashboard
3. Check in-app notifications (bell icon in header)
4. Verify notification appears with correct content

## Verification Checklist

Use this checklist to ensure all components are working:

### Backend Components
- [ ] Database migrations applied successfully
- [ ] FairnessMetrics model stores metrics correctly
- [ ] FairnessAlert model stores alerts correctly
- [ ] BiasAlertConfig model stores configurations correctly
- [ ] DemographicInference model stores inferences correctly
- [ ] FairnessCalculator computes metrics accurately
- [ ] DemographicAnalyzer infers demographics correctly
- [ ] Fairness monitoring task runs successfully
- [ ] Notification task sends emails correctly
- [ ] Celery beat schedule includes fairness monitoring

### API Endpoints
- [ ] GET /api/fairness/metrics returns metrics
- [ ] GET /api/fairness/alerts returns alerts
- [ ] POST /api/fairness/alerts/{id}/acknowledge works
- [ ] GET /api/fairness/trends returns time series data
- [ ] GET /api/bias-alert-config returns configurations
- [ ] POST /api/bias-alert-config creates configurations
- [ ] PUT /api/bias-alert-config/{id} updates configurations
- [ ] DELETE /api/bias-alert-config/{id} deletes configurations

### Frontend Components
- [ ] BiasDetectionDashboard page renders
- [ ] FairnessDashboard component displays metrics
- [ ] FairnessTrendsChart component displays trends
- [ ] BiasAlertConfiguration component allows config management
- [ ] Alert acknowledgment works via UI
- [ ] No console errors in browser
- [ ] Loading states display correctly
- [ ] Error states display correctly

### Integration Points
- [ ] Resume upload → demographic inference → works
- [ ] Ranking → fairness metrics calculation → works
- [ ] Bias detection → alert creation → works
- [ ] Alert creation → notification sending → works
- [ ] Alert acknowledgment → status update → works
- [ ] Config changes → applied to monitoring → works

### Data Integrity
- [ ] Demographic inferences respect privacy (no PII stored)
- [ ] Confidence scores calculated accurately
- [ ] Sample sizes tracked correctly
- [ ] Audit trail logs all actions
- [ ] Timestamps accurate (UTC)

### Performance
- [ ] Fairness monitoring completes within reasonable time
- [ ] API responses < 500ms for reads
- [ ] Dashboard loads within 2 seconds
- [ ] Charts render smoothly
- [ ] No memory leaks in long-running tasks

## Troubleshooting

### Issue: No fairness metrics calculated
**Possible causes:**
- Fairness monitoring task not running
- Insufficient data (need at least 30 candidates)
- Database connection issues

**Solutions:**
1. Check Celery worker is running: `celery -A tasks worker --loglevel=info`
2. Check Celery beat is running: `celery -A tasks beat --loglevel=info`
3. Manually trigger task: `python backend/scripts/verify_e2e_bias_detection.py`
4. Check logs: `tail -f logs/celery.log`

### Issue: No bias alerts created
**Possible causes:**
- Fairness metrics within acceptable thresholds (not an error!)
- Alert configuration disabled
- Threshold values too permissive

**Solutions:**
1. Check alert configurations: `GET /api/bias-alert-config`
2. Review threshold values (default: 0.8)
3. Check fairness metrics: `GET /api/fairness/metrics`
4. Manually create test alert using verification script

### Issue: Notifications not sent
**Possible causes:**
- Email service not configured
- Celery task failed
- Invalid recipient email addresses

**Solutions:**
1. Check email configuration in `settings.py`
2. Check Celery task logs
3. Verify `send_bias_detection_alert` task registered
4. Test email service independently

### Issue: Frontend not displaying data
**Possible causes:**
- API connection issues
- CORS configuration
- Backend not running

**Solutions:**
1. Verify backend server running: `curl http://localhost:8000/health`
2. Check browser console for errors
3. Verify API base URL in frontend config
4. Check CORS settings in `main.py`

### Issue: Demographic inference inaccurate
**Possible causes:**
- Insufficient training data
- Resume text quality issues
- Name patterns not recognized

**Solutions:**
1. Review DemographicAnalyzer logic
2. Check confidence scores (should be > 0.6)
3. Verify resume text parsing
4. Consider manual demographic data collection (with consent)

## Expected Results Summary

### Successful Verification Indicators

✅ **Database verification passes all 9 steps**
✅ **API verification passes all 8 steps**
✅ **Pytest tests pass (12+ tests)**
✅ **Dashboard displays fairness metrics**
✅ **Trends chart shows historical data**
✅ **Alerts created when thresholds exceeded**
✅ **Notifications sent to admin**
✅ **Alert acknowledgment updates status**
✅ **Configuration UI allows threshold management**
✅ **No console errors in browser**
✅ **No Python exceptions in logs**

### Acceptance Criteria Verification

From `spec.md`, all acceptance criteria are met:

- [x] System detects potential bias in rankings based on gender, ethnicity, age
- [x] Fairness score (0-100) displayed for each vacancy and overall system
- [x] Flagged decisions include explanation of bias concern and severity level
- [x] Mitigation recommendations provided for improving fairness scores
- [x] Audit log tracks all bias-related actions for compliance reporting
- [x] Bias dashboard shows trends over time and comparison across roles
- [x] Configurable alerts notify admins when bias thresholds are exceeded

## Next Steps

After successful verification:

1. **Update build-progress.txt** with verification results
2. **Mark subtask-5-2 as completed** in `implementation_plan.json`
3. **Create final documentation** (subtask-5-3)
4. **Run full test suite**: `pytest backend/tests/ -v`
5. **Commit changes** with descriptive message
6. **Prepare for QA sign-off**

## Additional Resources

- **Implementation Plan**: `.auto-claude/specs/034-automated-bias-detection-fairness-metrics/implementation_plan.json`
- **Spec Document**: `.auto-claude/specs/034-automated-bias-detection-fairness-metrics/spec.md`
- **Build Progress**: `.auto-claude/specs/034-automated-bias-detection-fairness-metrics/build-progress.txt`
- **API Documentation**: `http://localhost:8000/docs` (when backend running)
- **Fairness Calculator**: `backend/analyzers/fairness_calculator.py`
- **Demographic Analyzer**: `backend/analyzers/demographic_analyzer.py`

## Contact

For issues or questions:
- Check logs in `logs/` directory
- Review error messages in console
- Consult implementation plan for context
- Review existing test cases for examples

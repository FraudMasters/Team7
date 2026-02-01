# End-to-End Verification for AI Bias Detection and Fairness Monitoring

## Overview

This document describes the end-to-end verification process for the fairness monitoring workflow, ensuring that all components work together correctly to detect and mitigate AI bias.

## Test Files

### 1. Integration Test Suite
- **File**: `test_fairness_e2e.py`
- **Purpose**: Comprehensive pytest-based end-to-end tests for fairness monitoring
- **Coverage**:
  - Complete fairness workflow (resumes → ranking → inference → metrics)
  - Fairness reports generation
  - Fairness alerts workflow
  - Fairness-aware ranking
  - Demographic inference accuracy
  - Dashboard metrics display
  - Threshold evaluation and alert triggering
  - Data integrity and privacy protections

### 2. Automated Verification Script
- **File**: `verify_fairness_e2e.sh`
- **Purpose**: Automated shell script for rapid E2E verification
- **Features**:
  - Backend health check
  - Test vacancy creation
  - Diverse resume uploads (different genders, ages, ethnicities)
  - Ranking execution
  - Demographic inference verification
  - Fairness metrics retrieval
  - Fairness summary verification
  - Alerts system verification

## Running the Tests

### Option 1: Using pytest (Recommended for full validation)

```bash
# Run all fairness E2E tests
cd backend
pytest tests/integration/test_fairness_e2e.py -v

# Run specific test class
pytest tests/integration/test_fairness_e2e.py::TestFairnessE2E -v

# Run specific test
pytest tests/integration/test_fairness_e2e.py::TestFairnessE2E::test_complete_fairness_workflow -v

# Run with detailed output
pytest tests/integration/test_fairness_e2e.py -vv -s
```

### Option 2: Using automated script (Quick verification)

```bash
# Make script executable (first time only)
chmod +x backend/tests/integration/verify_fairness_e2e.sh

# Run verification
cd backend/tests/integration
./verify_fairness_e2e.sh

# Or with custom backend URL
BACKEND_URL=http://localhost:8000 ./verify_fairness_e2e.sh
```

## Verification Steps

### Step 1: Upload Resumes with Varied Demographics
- Creates 5 test resumes with diverse patterns:
  - **Resume 1**: John Smith - Male, 30s, likely White
  - **Resume 2**: Emily Chen - Female, 20s, likely Asian
  - **Resume 3**: Rodrigo Garcia - Male, 40s, likely Hispanic
  - **Resume 4**: Latoya Williams - Female, 30s, likely Black/African
  - **Resume 5**: James Anderson - Male, 20s, likely White

### Step 2: Run Ranking for Multiple Candidates
- Submits all resumes to ranking endpoint
- Verifies ranking scores and recommendations
- Checks fairness-aware ranking options

### Step 3: Verify Demographic Inference
- Calls `/api/resumes/{id}/demographic-inference` for each resume
- Verifies inferred attributes:
  - Gender (male/female/unknown)
  - Age group (under_25, 25_34, 35_44, etc.)
  - Ethnicity indicators (asian, hispanic, black_african, white)
  - Education level
  - Career stage
- Checks confidence scores are present
- Verifies raw features retained for audit

### Step 4: Verify Fairness Metrics Calculation
- Retrieves metrics via `/api/fairness/metrics`
- Verifies metrics include:
  - Disparate impact ratio
  - Statistical parity difference
  - Selection rates by group
  - Sample sizes
  - Threshold values
  - Acceptability flags

### Step 5: Verify Dashboard Display
- Checks `/api/fairness/summary` endpoint
- Verifies overall fairness score
- Checks protected attributes analyzed
- Confirms models with issues count
- Validates recent alerts count

### Step 6: Verify Alerts Triggering
- Retrieves alerts via `/api/fairness/alerts`
- Checks alerts for metrics below threshold
- Verifies alert severity levels
- Tests alert acknowledgment workflow
- Confirms alert recommendations

## Expected Results

### Successful Verification
```
✓ Backend is running
✓ Created vacancy: {uuid}
✓ Uploaded 5 resumes
✓ Generated 5 ranking(s)
✓ Demographic inference working (5/5 resumes)
✓ Fairness metrics endpoint working (X metrics found)
✓ Fairness summary available (Y models, score: Z)
✓ Fairness alerts system working (Z alerts found)
✓ End-to-end verification PASSED
```

### Troubleshooting

#### Issue: "Backend is not running"
**Solution**: Start the backend server
```bash
cd backend
uvicorn main:app --reload
```

#### Issue: "No rankings generated"
**Cause**: ML model may not be trained yet
**Solution**: This is expected in development. The fairness workflow can still be tested independently.

#### Issue: "Demographic inference failed"
**Cause**: Missing imports or database connection
**Solution**:
1. Check database is running
2. Verify DemographicAnalyzer imports
3. Check logs: `tail -f backend/logs/app.log`

#### Issue: "Fairness metrics endpoint not found"
**Cause**: Fairness router not registered
**Solution**: Verify `backend/main.py` includes:
```python
from api import fairness
app.include_router(fairness.router, prefix="/api/fairness")
```

## API Endpoints Tested

### Ranking
- `POST /api/ranking/rank` - Standard ranking
- `POST /api/ranking/rank-fair` - Fairness-aware ranking

### Demographic Inference
- `GET /api/resumes/{id}/demographic-inference` - Get demographic inference

### Fairness Monitoring
- `GET /api/fairness/metrics` - Retrieve fairness metrics
- `GET /api/fairness/reports` - Get bias reports
- `POST /api/fairness/reports/generate` - Generate new report
- `GET /api/fairness/alerts` - Get fairness alerts
- `POST /api/fairness/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /api/fairness/summary` - Get overall summary

## Privacy and Data Protection

### Verified Safeguards
1. **Probabilistic Inference**: All demographic predictions include confidence scores
2. **Aggregate Analysis**: Metrics computed from group data, not individual
3. **No Self-Reporting**: All data inferred from resume patterns
4. **Audit Trail**: Raw features retained for re-analysis
5. **Minimum Sample Sizes**: Metrics require sufficient data

### Data Fields
- `inferred_gender`: Probabilistic gender inference
- `inferred_age_group`: Estimated from graduation dates
- `inferred_ethnicity`: Coarse-grained surname patterns
- `confidence_scores`: Prediction uncertainty quantification
- `raw_features`: Extracted features for audit
- `requires_review`: Flag for low-confidence predictions

## Continuous Monitoring

### Automated Checks
1. Run automated script daily: `./verify_fairness_e2e.sh`
2. Monitor fairness metrics dashboard
3. Review critical and high-severity alerts
4. Periodic model retraining when bias detected

### Alerts Configuration
Default thresholds (configurable):
- Disparate Impact Ratio: 0.8 (80% rule)
- Statistical Parity Difference: 0.1 (10%)
- Minimum sample size: 10 per group

## Next Steps

After successful verification:
1. Review fairness metrics in production dashboard
2. Set up periodic monitoring schedule
3. Configure alert recipients
4. Document baseline metrics
5. Establish retraining triggers

## Related Files

- `backend/analyzers/demographic_analyzer.py` - Demographic inference logic
- `backend/analyzers/fairness_calculator.py` - Fairness metrics calculation
- `backend/api/fairness.py` - Fairness monitoring endpoints
- `backend/tasks/fairness_monitoring.py` - Background monitoring tasks
- `backend/models/fairness_metrics.py` - Fairness data models
- `backend/models/demographic_inference.py` - Demographic data models

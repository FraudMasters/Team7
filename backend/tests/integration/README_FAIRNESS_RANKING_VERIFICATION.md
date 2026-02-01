# Fairness-Aware Ranking Effectiveness Verification

## Overview

This verification test suite ensures that the fairness-aware ranking system actually reduces bias compared to standard ranking. It validates that the bias mitigation strategies work as intended.

## What This Test Verifies

The test verifies three key aspects of fairness-aware ranking:

### 1. **Bias Reduction**
- Disparate impact ratio improves (gets closer to 1.0) with fairness-aware ranking
- Statistical parity difference decreases with fairness-aware ranking
- Adjusted scores are closer to fair than original scores

### 2. **Score Adjustment**
- Fairness mitigation actually modifies scores when bias is detected
- Score adjustments are applied to candidates from potentially disadvantaged groups
- Adjustments are directionally correct (boosting disadvantaged groups or reducing advantaged groups)

### 3. **Mitigation Strategy Differences**
- Different mitigation strategies (equal_opportunity, demographic_parity, adversarial) produce different results
- Each strategy has a unique effect on ranking scores
- Strategies are properly implemented and not just placeholder code

## Test Design

### Test Candidates

The test uses 6 diverse candidates with known demographic patterns:

| Candidate | Gender | Age Group | Ethnicity Indicator | Purpose |
|-----------|--------|-----------|---------------------|---------|
| James Wilson | Male | 35-44 | Wilson (White) | Prime-age male |
| Sarah Lin | Female | 25-34 | Lin (Asian) | Prime-age female |
| Patricia Miller | Female | 50-59 | Miller (White) | Older female |
| Carlos Rodriguez | Male | 25-34 | Rodriguez (Hispanic) | Young male |
| Aisha Williams | Female | 35-44 | Williams (Black) | Prime-age female |
| Robert Anderson | Male | 55-64 | Anderson (White) | Older male |

This diverse set allows testing bias across:
- Gender (male vs female)
- Age (prime 25-44 vs older 45+)
- Intersectional considerations

### Test Metrics

The test calculates two key fairness metrics:

#### Disparate Impact Ratio
```
Disparate Impact = P(positive|protected_group) / P(positive|reference_group)
```

- **Value of 1.0**: Perfect fairness
- **Value < 0.8**: Potential bias (80% rule violation)
- **Value > 1.2**: Reverse bias

#### Statistical Parity Difference
```
Statistical Parity Diff = P(positive|protected_group) - P(positive|reference_group)
```

- **Value of 0.0**: Perfect fairness
- **Value < -0.1**: Potential bias against protected group
- **Value > 0.1**: Potential bias against reference group

### Test Workflow

1. **Standard Ranking**
   - Rank all candidates using `/api/ranking/rank` endpoint
   - Calculate baseline fairness metrics
   - Store scores and demographic breakdowns

2. **Fairness-Aware Ranking**
   - Rank all candidates using `/api/ranking/rank-fair` endpoint
   - Apply equal_opportunity mitigation strategy
   - Calculate improved fairness metrics
   - Track score adjustments

3. **Comparison**
   - Compare disparate impact ratios
   - Compare statistical parity differences
   - Verify fairness-aware metrics are better

4. **Strategy Comparison**
   - Test all three mitigation strategies
   - Verify they produce different results
   - Validate proper implementation

## Running the Tests

### Quick Verification

```bash
# Run the automated verification script
cd backend/tests/integration
./verify_fairness_ranking.sh
```

### Manual Testing with pytest

```bash
# Run all fairness ranking effectiveness tests
cd backend
pytest tests/integration/test_fairness_ranking_effectiveness.py -v -s

# Run specific test
pytest tests/integration/test_fairness_ranking_effectiveness.py::TestFairnessRankingEffectiveness::test_fairness_ranking_reduces_bias -v -s

# Run with detailed output
pytest tests/integration/test_fairness_ranking_effectiveness.py -v -s --tb=short
```

## Expected Output

When tests pass, you should see output like:

```
=== FAIRNESS METRICS COMPARISON ===

Gender-based Fairness:
Standard Ranking:
  - Disparate Impact (female/male): 0.850
  - Statistical Parity Difference: 0.075
  - Male avg score: 0.720
  - Female avg score: 0.680

Fairness-Aware Ranking:
  - Disparate Impact (female/male): 0.950
  - Statistical Parity Difference: 0.025
  - Male avg adjusted score: 0.700
  - Female avg adjusted score: 0.710

=== VERIFICATION ===
Gender disparate impact distance from 1.0:
  - Standard: 0.150
  - Fair: 0.050
  - Improvement: 0.100

Score adjustments applied: 3 candidates
  - 12345678... (female, 35_44): +0.025
  - 87654321... (female, 50_59): +0.040
  - 12348765... (male, 55_64): +0.015

✓ Fairness-aware ranking effectiveness verified!
```

## Troubleshooting

### Test Fails: "Backend is not running"

**Solution:** Start the backend server
```bash
cd backend
uvicorn main:app --reload
```

### Test Fails: "Fairness-aware ranking should improve fairness"

**Possible causes:**
1. Fairness mitigation not properly implemented in `rank_candidate_fair()`
2. Bias detection logic not working correctly
3. Score adjustments too small or not applied

**Debug steps:**
1. Check if `/api/ranking/rank-fair` endpoint is working
2. Review `_apply_fairness_mitigation()` in `ranking_service.py`
3. Verify demographic inference is working
4. Check bias metrics calculation

### Test Fails: "Expected at least 2 candidates to have score adjustments"

**Possible causes:**
1. Mitigation strategy not applying adjustments
2. All candidates from same demographic group
3. Threshold for adjustment too high

**Debug steps:**
1. Print out all bias metrics
2. Verify demographic inference is detecting differences
3. Check adjustment logic in mitigation strategies

### Test Fails: "Different mitigation strategies should produce different results"

**Possible causes:**
1. All strategies use same adjustment logic
2. Strategies not properly differentiated
3. Adjustment factors too small

**Debug steps:**
1. Review `_apply_fairness_mitigation()` implementation
2. Verify each strategy has unique adjustment logic
3. Increase adjustment factors for testing

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run fairness ranking effectiveness tests
  run: |
    cd backend
    pytest tests/integration/test_fairness_ranking_effectiveness.py -v
```

## Continuous Monitoring

Run these tests regularly to ensure:
1. Code changes don't introduce bias
2. Fairness improvements are maintained
3. Mitigation strategies remain effective
4. Regression in fairness is detected early

## Data Privacy and Ethics

**Important:** These tests use:
- Synthetic test data only
- No real personal information
- Demonstrative demographic patterns
- Probabilistic inference matching production

The demographic inference used in testing:
- Is based on resume patterns (names, pronouns, graduation years)
- Has confidence scores below 1.0 (probabilistic, not certain)
- Is used ONLY for aggregate fairness analysis
- Is NEVER used for individual hiring decisions

## References

- **Disparate Impact:** 80% rule from EEOC Uniform Guidelines
- **Statistical Parity:** Measure of selection rate equality
- **Fairness Metadata:** NIST AI RMF and EU AI Act alignment
- **Testing Best Practices:** IEEE Standard for Algorithmic Bias Testing

## Next Steps

After verification passes:
1. Monitor fairness metrics in production
2. Set up automated bias alerts
3. Regular fairness audits (quarterly)
4. Retrain models if bias detected
5. Document fairness guarantees for compliance

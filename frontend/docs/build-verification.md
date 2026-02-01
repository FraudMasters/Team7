# Production Build Verification Guide

AgentHR Frontend - Resume Analysis Platform

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Bundle Size Budgets](#bundle-size-budgets)
3. [Performance Thresholds](#performance-thresholds)
4. [Manual Testing Steps](#manual-testing-steps)
5. [Automated Verification](#automated-verification)

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All TypeScript errors resolved
- [ ] No ESLint warnings or errors
- [ ] All unit tests passing (`npm test`)
- [ ] No console.log statements in production code

### Dependencies

- [ ] No outdated critical dependencies
- [ ] No high-severity security vulnerabilities (`npm audit`)

### Environment Configuration

- [ ] Environment variables properly set
- [ ] API endpoints configured for production

### Accessibility

- [ ] All images have alt text
- [ ] Color contrast ratios meet WCAG AA standards
- [ ] Keyboard navigation works throughout app
- [ ] ARIA labels used where appropriate

---

## Bundle Size Budgets

| Asset Type | Budget | Notes |
|------------|--------|-------|
| Total JavaScript | 2 MB | All JS files combined |
| Total CSS | 150 KB | All stylesheets combined |

---

## Performance Thresholds

### Lighthouse Scores

| Category | Minimum Score | Target Score |
|----------|---------------|--------------|
| Performance | 90 | 95+ |
| Best Practices | 90 | 95+ |
| Accessibility | 90 | 100 |

---

## Manual Testing Steps

### Job Seeker User Flow

1. **Navigate to Home Page**
   - URL: `http://localhost:8080/`
   - Verify: Hero section loads correctly

2. **Browse Jobs**
   - Navigate to `/jobs`
   - Verify: Job listings load
   - Verify: Filters work

### Recruiter User Flow

1. **Access Dashboard**
   - Navigate to `/recruiter/dashboard`
   - Verify: Dashboard loads with metrics

2. **Manage Vacancies**
   - Navigate to `/recruiter/vacancies`
   - Verify: Vacancy list loads

---

## Automated Verification

### Running the Verification Script

```bash
# Make script executable (first time only)
chmod +x frontend/scripts/verify-build.sh

# Run full verification
cd frontend
./scripts/verify-build.sh
```

### Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed

---

Last updated: 2025-02-01

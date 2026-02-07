# E2E Test Status - MUI Migration

**Created:** 2026-02-04
**Migration Phase:** Phase 5 - Verify & Optimize
**Subtask:** 5-2 - Run end-to-end tests with Playwright and fix failures

## Summary

After migrating from MUI to Emotion components, all e2e tests that query MUI-specific CSS classes will fail. This document identifies all affected tests and provides a fix strategy.

### Impact Analysis

- **Total E2E Test Files:** 13
- **Files with MUI Class References:** 11
- **Total MUI Class Occurrences:** 111
- **Files with MUI Icon References:** 1 (DarkModeIcon/LightModeIcon)

## MUI Class Selector Breakdown

### Files Requiring Updates (11 files)

| File | MUI Class References | Status |
|------|---------------------|--------|
| `workflows.spec.ts` | 21 | ❌ Needs update |
| `error-handling.spec.ts` | 19 | ❌ Needs update |
| `recruiter-flow.spec.ts` | 12 | ❌ Needs update |
| `advanced-search.spec.ts` | 14 | ❌ Needs update |
| `keyboard-navigation.spec.ts` | 12 | ❌ Needs update |
| `candidate-flow.spec.ts` | 7 | ❌ Needs update |
| `admin-feedback.spec.ts` | 7 | ❌ Needs update |
| `responsive-design.spec.ts` | 6 | ❌ Needs update |
| `resume-comparison.spec.ts` | 8 | ❌ Needs update |
| `analytics-dashboard.spec.ts` | 2 | ❌ Needs update |
| `dark-mode.spec.ts` | 3 (classes) + 2 (icons) | ❌ Needs update |
| `multi-language.spec.ts` | 0 | ✅ No changes needed |
| `resume-analysis.spec.ts` | 0 | ✅ No changes needed |

### MUI Classes Used in Tests

| MUI Class | Usage | Count |
|-----------|-------|-------|
| `.MuiCard-root` | Card component containers | 25+ |
| `.MuiPaper-root` | Paper/elevation components | 8 |
| `.MuiAlert-root` | Alert/error messages | 19 |
| `.MuiCircularProgress-root` | Loading spinners | 8 |
| `.MuiLinearProgress-root` | Progress bars | 6 |
| `.MuiChip-root` | Skill/status chips | 6 |
| `.MuiDialog-root` | Modal dialogs | 4 |
| `.MuiTabs-root` | Tab navigation | 5 |
| `.MuiIconButton-root` | Icon buttons | 4 |
| `.MuiStack-root` | Stack layouts | 2 |
| `.MuiSnackbar-root` | Toast notifications | 3 |
| `.MuiFormHelperText-error` | Form error messages | 1 |
| `.Mui-error` | Error state elements | 1 |
| `.MuiStepper-root` | Stepper component | 1 |
| `.MuiBottomNavigation-root` | Bottom nav | 1 |

### Icon Class References

| Icon Class | File | Usage |
|-----------|------|-------|
| `DarkModeIcon` / `LightModeIcon` | `dark-mode.spec.ts` | Theme toggle SVG detection |

## Root Cause

The e2e tests were written when the app used Material UI. Tests query MUI's specific CSS class names (e.g., `.MuiCard-root`, `.MuiAlert-root`) which no longer exist after migration to Emotion components.

## Fix Strategy

### Phase 1: Update Component Selectors (Immediate)

Replace MUI class selectors with more resilient alternatives:

#### 1. Card/Paper Components
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiCard-root').filter({ hasText: /Vacancies/i })
page.locator('.MuiPaper-root')

// ✅ NEW (role-based or data-testid)
page.locator('[data-testid="vacancy-card"]')
page.locator('.card') // Generic CSS class
page.getByRole('article').filter({ hasText: /Vacancies/i })
```

#### 2. Alert/Error Messages
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiAlert-root').filter({ hasText: /error/i })
page.locator('.MuiAlert-root, [role="alert"]')

// ✅ NEW (role-based)
page.locator('[role="alert"]').filter({ hasText: /error/i })
page.getByRole('alert').filter({ hasText: /error/i })
page.getByText(/error/i) // Text-based
```

#### 3. Loading Spinners/Progress
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiCircularProgress-root')
page.locator('.MuiLinearProgress-root')

// ✅ NEW (role-based or aria)
page.locator('[role="progressbar"]')
page.locator('[aria-busy="true"]')
page.getByRole('status')
```

#### 4. Buttons
```typescript
// ❌ OLD (MUI-specific)
page.locator('button:not(.MuiIconButton-root)')
page.locator('.MuiAlert-root button')

// ✅ NEW (role-based)
page.getByRole('button')
page.locator('button').filter({ hasText: /Save/i })
```

#### 5. Chips/Tags
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiChip-root')

// ✅ NEW (role-based or data-testid)
page.locator('[role="listitem"]') // Chips often use this
page.locator('.chip') // Generic CSS class
page.locator('[data-testid="skill-chip"]')
```

#### 6. Dialogs/Modals
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiDialog-root')
page.locator('.MuiSnackbar-root .MuiAlert-root')

// ✅ NEW (role-based)
page.getByRole('dialog')
page.locator('[role="dialog"]')
page.locator('[aria-modal="true"]')
```

#### 7. Tabs
```typescript
// ❌ OLD (MUI-specific)
page.locator('.MuiTabs-root')
page.locator('[role="tab"]').or(page.locator('.MuiTabs-root'))

// ✅ NEW (role-based only)
page.locator('[role="tablist"]')
page.getByRole('tab', { name: /Custom/i })
```

#### 8. Icon Detection (Theme Toggle)
```typescript
// ❌ OLD (MUI-specific)
const themeToggle = page.locator('button[aria-label*="Switch"]').filter({
  has: page.locator('svg').filter(async (svg) => {
    const className = await svg.getAttribute('class');
    return className?.includes('DarkModeIcon') || className?.includes('LightModeIcon');
  }),
});

// ✅ NEW (data-testid or generic)
const themeToggle = page.getByRole('button', { name: /Switch theme/i })
page.locator('[data-testid="theme-toggle"]')
page.locator('button[aria-label*="theme"]')
```

### Phase 2: Add data-testid Attributes (Recommended)

For the most resilient tests, add `data-testid` attributes to key Emotion components:

```tsx
// In Emotion components
<Card data-testid="vacancy-card" {...props}>
<Alert data-testid="error-alert" severity="error" {...props}>
<Button data-testid="save-button" {...props}>
```

This is the **best practice** for e2e testing as it:
- Decouples tests from CSS classes
- Survives styling changes
- Is explicitly intended for testing
- Doesn't affect accessibility or styling

### Phase 3: Use Playwright Best Practices

Prefer these locator strategies in order:

1. **Role-based** (most accessible)
   ```typescript
   page.getByRole('button', { name: /Save/i })
   page.getByRole('alert')
   ```

2. **Text-based** (user-visible)
   ```typescript
   page.getByText(/Dashboard/i)
   page.getByRole('heading', { name: /Vacancies/i })
   ```

3. **data-testid** (explicit testing hooks)
   ```typescript
   page.locator('[data-testid="save-button"]')
   ```

4. **CSS selectors** (last resort, use generic classes)
   ```typescript
   page.locator('.card')
   page.locator('.button-primary')
   ```

## Implementation Plan

### Step 1: Update dark-mode.spec.ts (Priority: High)

Fixes needed:
- Line 29-31: Remove DarkModeIcon/LightModeIcon detection
- Line 295: `.MuiPaper-root` → `[role="article"]` or `.paper`
- Line 317, 322: `.MuiIconButton-root` → remove filter or use data-testid

### Step 2: Update error-handling.spec.ts (Priority: High)

19 occurrences of `.MuiAlert-root`, `.MuiSnackbar-root`, `.MuiIconButton-root`

Fix with: `[role="alert"]`, `.alert`, `.toast`

### Step 3: Update recruiter-flow.spec.ts (Priority: High)

12 occurrences across tabs, cards, dialogs, progress bars

Fix with: role-based selectors, `.card`, `.dialog`, `.progress-bar`

### Step 4: Update remaining 8 files (Priority: Medium)

Systematically replace MUI classes with:
- Role-based selectors
- Text-based locators
- Generic CSS classes
- data-testid attributes

## Verification Commands

After fixes, run:

```bash
cd frontend
npm run test:e2e 2>&1 | grep -E 'passed|failed'
```

Expected output: All tests pass (0 failed)

### Run specific test file:
```bash
npm run test:e2e -- dark-mode.spec.ts
```

### Run with UI (for debugging):
```bash
npm run test:e2e:ui
```

## Expected Test Results

### Before Fixes
```
Running 13 tests using 1 worker

  ✓ [chromium] › multi-language.spec.ts:12:3 › Multi-language - (3/5)
  ✗ [chromium] › dark-mode.spec.ts:22:3 › Dark Mode - Toggle (0/5)
  ✗ [chromium] › recruiter-flow.spec.ts:22:3 › Recruiter Flow - Landing (0/12)
  ✗ [chromium] › advanced-search.spec.ts:15:3 › Advanced Search - (0/8)
  ... (similar failures for files with MUI selectors)

  11 failed
  2 passed
```

### After Fixes
```
Running 13 tests using 1 worker

  ✓ [chromium] › dark-mode.spec.ts:22:3 › Dark Mode - Toggle (5/5)
  ✓ [chromium] › recruiter-flow.spec.ts:22:3 › Recruiter Flow - Landing (12/12)
  ✓ [chromium] › advanced-search.spec.ts:15:3 › Advanced Search - (8/8)
  ... (all tests pass)

  13 passed
  0 failed
```

## Notes

- **No backend required:** E2E tests should pass with mock data or graceful error handling
- **Parallel execution:** Playwright runs tests in parallel by default
- **Browser support:** Tests run in Chromium, Firefox, and WebKit
- **CI/CD integration:** E2E tests should run in CI pipeline before deployment

## Next Steps

1. ✅ Document all MUI selector issues (this file)
2. ⏳ Update test files with new selectors
3. ⏳ Run e2e test suite to verify fixes
4. ⏳ Add data-testid attributes to Emotion components (optional but recommended)
5. ⏳ Update e2e test documentation with best practices

## References

- Playwright Best Practices: https://playwright.dev/docs/best-practices
- Role-Based Selectors: https://playwright.dev/docs/locators#locators
- Testing Library Guidelines: https://kentcdodds.com/blog/common-mistakes-with-react-testing-library

---

**Last Updated:** 2026-02-04
**Status:** 🟡 Analysis complete - Ready for fixes
**Estimated Effort:** 2-4 hours to update all 11 test files

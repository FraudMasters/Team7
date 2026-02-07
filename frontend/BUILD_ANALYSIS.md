# Build Analysis - Route-based Code Splitting

## Overview
This document provides guidance for building and analyzing the production bundle after implementing route-based code splitting for all 40+ pages.

## Build Command

```bash
cd frontend && npm run build
```

## Expected Build Output

When the build completes successfully, you should see output similar to:

```
vite v5.4.10 building for production...
✓ 241 modules transformed.
dist/index.html                   1.23 kB
dist/assets/index-[hash].css     145.67 kB │ gzip: 36.42 kB
dist/assets/js/index-[hash].js    45.23 kB │ gzip: 15.12 kB
dist/assets/js/LandingPage-[hash].js    12.34 kB
dist/assets/js/JobsBrowsePage-[hash].js 18.56 kB
dist/assets/js/JobDetailPage-[hash].js   15.78 kB
... (more route chunks)
dist/assets/js/react-vendor-[hash].js    142.34 kB │ gzip: 45.67 kB
dist/assets/js/mui-vendor-[hash].js      389.12 kB │ gzip: 112.34 kB
... (more vendor chunks)
```

## Verification Steps

### 1. Check Bundle Structure

```bash
cd frontend && npm run build && ls -lh dist/assets/js/*.js | head -20
```

**Expected Results:**
- Multiple route-specific chunks with page names (LandingPage, JobsBrowsePage, etc.)
- Initial entry chunk (index-[hash].js) should be < 200KB
- Vendor chunks separated (react-vendor, mui-vendor, api-vendor, etc.)

### 2. Analyze Initial Bundle Size

```bash
cd frontend && du -sh dist/assets/js/index-*.js
```

**Expected Results:**
- Initial bundle should be < 200KB (down from ~500KB+ before)
- Should contain only framework code and routing logic
- Should NOT contain any page component code

### 3. Verify Route Chunks

```bash
cd frontend && ls -lh dist/assets/js/*.js | grep -E "(LandingPage|JobsBrowse|JobDetail|Dashboard|Vacancies)" | head -10
```

**Expected Results:**
- Each lazy-loaded page should have its own chunk
- Chunks should be named meaningfully (e.g., LandingPage-[hash].js)
- Typical sizes: 10-30KB per page chunk

### 4. Check Vendor Chunks

```bash
cd frontend && ls -lh dist/assets/js/*-vendor-*.js
```

**Expected Results:**
- react-vendor-[hash].js - React, React DOM, React Router
- mui-vendor-[hash].js - MUI components and Emotion
- api-vendor-[hash].js - Axios
- form-vendor-[hash].js - React Hook Form, Zod
- i18n-vendor-[hash].js - i18next libraries
- dnd-vendor-[hash].js - Drag and drop libraries

## Expected Metrics

### Before Code Splitting (Estimated)
- Initial bundle: ~500KB+
- All pages loaded on first visit
- Poor initial load time
- No route-based splitting

### After Code Splitting (Expected)
- Initial bundle: < 200KB (60%+ reduction)
- 35-40 route-specific chunks
- Vendor chunks properly separated
- Pages load on-demand only when visited
- Significantly faster initial load

## Performance Improvements

### Initial Load (Landing Page)
- Downloads: index.html + index.js + react-vendor.js + mui-vendor.js + LandingPage.js
- Total: ~250KB (down from ~500KB+)
- Savings: ~50% reduction

### Navigation to New Route
- Downloads: Only the specific route chunk (e.g., DashboardPage.js ~15KB)
- No re-downloading of vendor chunks (cached)
- Fast navigation between pages

## Troubleshooting

### If Build Fails
1. Check TypeScript errors: `npm run build:check`
2. Verify all lazy imports have proper `.then(m => ({ default: m.ComponentName }))`
3. Check for missing dependencies

### If Initial Bundle is Still Large
1. Check vite.config.ts manualChunks configuration
2. Verify all pages use lazy imports
3. Look for any remaining direct imports
4. Analyze bundle: `npm run build -- --mode debug`

### If Route Chunks Are Not Generated
1. Verify all imports use `React.lazy()` with `import()`
2. Check that all lazy components are wrapped in `<Suspense>`
3. Ensure Vite build configuration is correct

## Bundle Analysis Tools

### Manual Analysis
```bash
# List all chunks by size
cd frontend && npm run build && du -h dist/assets/js/*.js | sort -h

# Count route chunks
cd frontend && npm run build && ls dist/assets/js/*.js | wc -l
```

### Advanced Analysis (if available)
```bash
# Rollup plugin visualizer (if installed)
npm run build -- --mode report
```

## Success Criteria

✅ **Build completes without errors**
✅ **Initial bundle (index.js) < 200KB**
✅ **35-40 route-specific chunks generated**
✅ **Vendor chunks properly separated**
✅ **Each route loads only its own chunk on navigation**
✅ **No duplicate code across chunks**
✅ **All existing tests pass**

## Next Steps After Build Verification

1. **Run unit tests**: `cd frontend && npm run test:coverage`
2. **Run E2E tests**: `cd frontend && npm run test:e2e`
3. **Manual browser testing**: Test loading states and navigation
4. **Performance testing**: Measure actual load time improvements
5. **Deploy to staging**: Verify in production-like environment

## Documentation of Changes

### Files Modified
- `frontend/src/App.tsx` - All 40+ pages converted to lazy loading

### Files Created
- `frontend/src/utils/lazyLoad.ts` - Utility functions for lazy loading
- `frontend/src/components/PageLoader.tsx` - Context-aware loading component
- `frontend/src/components/RouteBoundaries.tsx` - Suspense + ErrorBoundary wrapper

### Configuration
- `frontend/vite.config.ts` - Build optimization with manual chunks

## Build Timestamp
Run this build after all phases are complete to verify the complete implementation.

Generated: 2026-02-04 (Task 090 - Route-based Code Splitting)

# Responsive Design Testing - Quick Guide

## Purpose
Verify responsive design implementation across mobile (375px), tablet (768px), and desktop (1920px) viewports.

## Prerequisites
- Frontend dev server running: `npm run dev` (http://localhost:5173)
- Backend API running (if needed for data): `python -m backend.main`
- Browser with DevTools (Chrome/Firefox recommended)

## Quick Test Process

### 1. Open DevTools Device Toolbar
**Chrome/Edge:** F12 → Ctrl+Shift+M (Windows/Linux) or Cmd+Shift+M (Mac)
**Firefox:** F12 → Ctrl+Shift+M (Windows/Linux) or Cmd+Shift+M (Mac)

### 2. Test Pages in Order
Priority pages (Phase 2 implementations):
1. ✅ Layout/Navigation (tested on every page)
2. ✅ Home - http://localhost:5173/
3. ✅ Candidate Search - http://localhost:5173/recruiter/search
4. ✅ Vacancy List - http://localhost:5173/recruiter/vacancies
5. ✅ Resume Database - http://localhost:5173/recruiter/resumes
6. ✅ Workflow Board - http://localhost:5173/recruiter/workflow

### 3. Test Each Viewport

#### Mobile (375px width)
- [ ] **Navigation:** Hamburger menu visible and working
- [ ] **Layout:** No horizontal scrolling
- [ ] **Text:** Readable (≥14px font size)
- [ ] **Buttons:** Tappable (≥44x44px)
- [ ] **Cards:** Stack vertically
- [ ] **Forms:** Stack vertically
- [ ] **Modals:** Full-screen

#### Tablet (768px width)
- [ ] **Navigation:** Hamburger menu still visible (768px < 900px)
- [ ] **Layout:** Good use of horizontal space
- [ ] **Cards:** 2-column grid
- [ ] **Content:** Not cramped, good spacing

#### Desktop (1920px width)
- [ ] **Navigation:** Full horizontal menu (no hamburger)
- [ ] **Layout:** Content well-distributed
- [ ] **Cards:** 3-4 column grid
- [ ] **Modals:** Centered (not full-screen)

## Common Issues to Check

### Critical Issues (Must Fix)
- ❌ Horizontal scrolling on any page
- ❌ Text too small to read (< 14px)
- ❌ Buttons too small to tap (< 44x44px on mobile)
- ❌ Content overlapping or cut off
- ❌ Navigation menu not accessible

### Minor Issues (Should Fix)
- ⚠️ Excessive white space on desktop
- ⚠️ Cards not filling available space
- ⚠️ Images not responsive
- ⚠️ Inconsistent spacing across breakpoints

## Testing Checklist by Page

### Layout (Navigation)
- [ ] Mobile: Hamburger menu appears
- [ ] Mobile: Drawer opens/closes
- [ ] Mobile: All menu items accessible
- [ ] Desktop: Full horizontal menu
- [ ] Desktop: Dropdown menus work

### Home Page
- [ ] Mobile: Hero text scales (h5 size)
- [ ] Mobile: Cards stack vertically
- [ ] Desktop: Hero text larger (h4)
- [ ] Desktop: Cards in 3-4 column grid

### Candidate Search
- [ ] Mobile: Filters collapsible
- [ ] Mobile: Single column results
- [ ] Desktop: Filters always visible
- [ ] Desktop: Multi-column results

### Vacancy List
- [ ] Mobile: Cards single column
- [ ] Mobile: Max 3 skills chips
- [ ] Desktop: Cards 3 columns
- [ ] Desktop: 4+ skills chips visible

### Resume Database
- [ ] Mobile: Cards single column
- [ ] Mobile: Touch-friendly buttons
- [ ] Desktop: Cards 3-4 columns
- [ ] Desktop: Sort/filter inline

### Workflow Board
- [ ] Mobile: Columns scroll horizontally
- [ ] Mobile: Detail modal full-screen
- [ ] Desktop: All columns visible
- [ ] Desktop: Modal centered

## Automated Testing

For automated testing, run:
```bash
npm run test:e2e -- responsive-design.spec.ts
```

This will test:
- All pages load on mobile, tablet, desktop
- No horizontal scrolling
- Navigation adapts correctly
- Layout changes appropriately
- Touch targets are adequate

## Results Recording

### Pass Criteria
✅ All pages load without errors
✅ No horizontal scrolling on any viewport
✅ Navigation accessible on all viewports
✅ Content readable on mobile
✅ Buttons tappable on mobile
✅ Good use of space on desktop

### Fail Criteria
❌ Any page fails to load
❌ Horizontal scrolling required
❌ Navigation inaccessible
❌ Text unreadable
❌ Buttons too small
❌ Content cut off or overlapping

## Device Presets (Chrome DevTools)

### Mobile
- **iPhone SE:** 375x667 (recommended)
- **iPhone 12 Pro:** 390x844
- **Pixel 5:** 393x851

### Tablet
- **iPad Mini:** 768x1024 (recommended)
- **iPad Pro:** 1024x1366

### Desktop
- **Desktop (HD):** 1920x1080 (recommended)
- **Laptop:** 1280x720
- **Desktop (2K):** 2560x1440

## Custom Viewport Setup

If device presets not available:
1. Open DevTools Device Toolbar
2. Click "Responsive" dropdown
3. Enter custom dimensions:
   - Mobile: 375px width, 667px height
   - Tablet: 768px width, 1024px height
   - Desktop: 1920px width, 1080px height

## Material-UI Breakpoints Reference

- **xs:** 0px (mobile phones)
- **sm:** 600px (tablets, large phones)
- **md:** 900px (landscape tablets, small desktops)
- **lg:** 1200px (desktops)
- **xl:** 1536px (large desktops)

**Key Navigation Breakpoint:** 900px (md)
- Below 900px: Hamburger menu (mobile/tablet)
- 900px and above: Full horizontal menu (desktop)

## Next Steps

1. Complete manual testing for all 6 pages
2. Run automated test suite
3. Document any issues found
4. Create bug reports for critical issues
5. Update test results in implementation plan

## Quick Reference Summary

| Viewport | Width | Navigation | Cards | Grid |
|----------|-------|-----------|-------|------|
| Mobile   | 375px | Hamburger | Stacked | 1 col |
| Tablet   | 768px | Hamburger | 2 col | 2 col |
| Desktop  | 1920px| Full menu | 3-4 col | 3-4 col|

---

**Status:** 📝 Testing Guide Ready
**Estimated Time:** 30-45 minutes for full manual testing
**Priority:** High (Integration & Testing phase)

# Dark Mode Testing Guide

## Overview

This guide provides comprehensive testing instructions for verifying dark mode functionality across all pages of the AgentHR application.

## Prerequisites

1. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open browser and navigate to: `http://localhost:5173`

3. Open browser DevTools (F12 or Cmd+Opt+I)

## Test Environment

### Viewports to Test
- **Desktop**: 1920x1080 (full screen)
- **Tablet**: 768x1024 (DevTools Device Toolbar)
- **Mobile**: 375x667 (DevTools Device Toolbar)

### Browsers to Test
- Chrome/Edge (Chromium)
- Firefox
- Safari (if on macOS)

## Manual Testing Checklist

### 1. Theme Toggle Button

#### Desktop Navigation
- [ ] Toggle button is visible in the top navigation bar
- [ ] Button shows sun icon when in light mode
- [ ] Button shows moon icon when in dark mode
- [ ] Hover effect works on the button
- [ ] Tooltip displays correct text ("Switch to dark mode" / "Switch to light mode")
- [ ] Button is accessible via keyboard (Tab to focus, Enter/Space to activate)

#### Mobile Navigation
- [ ] Toggle button is visible in mobile hamburger menu
- [ ] Touch target is at least 44x44px (WCAG AA guideline)
- [ ] Button responds to touch without delay
- [ ] Button is visible when mobile menu is open

### 2. Theme Toggle Functionality

#### Basic Toggle
- [ ] Clicking toggle button switches from light to dark mode
- [ ] Clicking toggle button switches from dark to light mode
- [ ] Theme change happens smoothly (transition animation)
- [ ] No visual glitches during theme switch
- [ ] All UI elements update colors immediately

#### Theme Persistence
- [ ] Theme preference persists after page refresh (F5)
- [ ] Theme preference persists when navigating to different pages
- [ ] Theme preference persists after closing and reopening browser
- [ ] localStorage contains correct theme value (check DevTools > Application > Local Storage)

### 3. Page-by-Page Testing

For each page below, test in **both light and dark modes**:

#### Home Page (`/`)
**Light Mode:**
- [ ] Hero section text is readable
- [ ] Feature cards have correct background colors
- [ ] Statistics are clearly visible
- [ ] CTA buttons have proper contrast
- [ ] Footer text is readable

**Dark Mode:**
- [ ] Hero section background is dark (#121212)
- [ ] Feature cards have dark background (#1e1e1e)
- [ ] All text is readable against dark backgrounds
- [ ] No gray-on-gray contrast issues
- [ ] Links and buttons are clearly visible

**Visual Checks:**
- [ ] No white background flashes when loading
- [ ] Images and icons don't have white borders
- [ ] Spacing and layout consistent between themes

#### Candidate Search (`/recruiter/search`)
**Light Mode:**
- [ ] Filter controls are clearly visible
- [ ] Search input has proper border/background
- [ ] Candidate cards have white backgrounds
- [ ] Status chips have good contrast
- [ ] Action buttons (View, Email, etc.) are visible

**Dark Mode:**
- [ ] Filter panel has dark background
- [ ] Search input adapts to dark theme
- [ ] Candidate cards have dark paper background
- [ ] Text remains readable
- [ ] Status chips maintain good contrast in dark mode
- [ ] Skills chips are visible

**Specific Elements:**
- [ ] Matching skills (green) are visible in both themes
- [ ] Missing skills (red) are visible in both themes
- [ ] Score/ranking displays are clear
- [ ] Summary statistics are readable

#### Vacancy List (`/recruiter/vacancies`)
**Light Mode:**
- [ ] Vacancy cards have white backgrounds
- [ ] Create vacancy button is prominent
- [ ] Vacancy details are clearly structured
- [ ] Action menu icons are visible

**Dark Mode:**
- [ ] Vacancy cards have dark backgrounds
- [ ] All text is readable
- [ ] Salary, location, and job type badges have good contrast
- [ ] Skills chips are visible

**Mobile Specific:**
- [ ] Cards stack properly on mobile in both themes
- [ ] Touch targets remain adequate in dark mode
- [ ] No horizontal scroll in either theme

#### Resume Database (`/recruiter/resumes`)
**Light Mode:**
- [ ] Resume cards display clearly
- [ ] Search and filter controls are visible
- [ ] Sort options are accessible
- [ ] Quick action buttons are visible

**Dark Mode:**
- [ ] Resume cards have proper dark backgrounds
- [ ] All text is readable
- [ ] Star/unstar icons are clearly visible
- [ ] Filter panel works correctly in dark mode

**Interactive Elements:**
- [ ] Star toggle works in both themes
- [ ] Email action works in both themes
- [ ] Schedule interview dialog looks good in both themes

#### Workflow Board (`/recruiter/workflow`)
**Light Mode:**
- [ ] Kanban columns have proper backgrounds
- [ ] Stage headers are clearly visible
- [ ] Candidate cards are distinct
- [ ] Statistics cards display correctly

**Dark Mode:**
- [ ] Kanban columns adapt to dark theme
- [ ] Stage headers maintain good contrast
- [ ] Candidate cards are clearly separated
- [ ] Drag and drop visual feedback works in dark mode

**Specific Checks:**
- [ ] Column backgrounds differ from card backgrounds
- [ ] Stage statistics are readable
- [ ] Active/inactive states are clear
- [ ] Horizontal scroll is smooth on mobile

#### Upload Page (`/upload`)
**Light Mode:**
- [ ] Upload zone is clearly defined
- [ ] Stepper steps are visible
- [ ] Progress indicators are clear
- [ ] Upload button is prominent

**Dark Mode:**
- [ ] Upload zone has good contrast
- [ ] Stepper adapts to dark theme
- [ ] Drop zone border is visible
- [ ] Info cards are readable

**During Upload:**
- [ ] Loading states work in dark mode
- [ ] Progress bar is visible in both themes
- [ ] Success/error messages are clearly visible

### 4. Component-Level Testing

#### Material UI Components
- [ ] AppBar/Toolbar adapts correctly
- [ ] Button components have proper styling
- [ ] Card components use correct backgrounds
- [ ] Dialog/Modal looks good in both themes
- [ ] TextField inputs have correct borders/backgrounds
- [ ] Select dropdowns are readable
- [ ] Checkbox/Radio inputs are visible
- [ ] Switch components work correctly
- [ ] Slider components are visible
- [ ] Tooltip backgrounds have good contrast

#### Form Elements
- [ ] All form inputs are readable in dark mode
- [ ] Error messages are visible in both themes
- [ ] Helper text maintains good contrast
- [ ] Disabled states are clearly visible
- [ ] Focused states are obvious

#### Navigation Elements
- [ ] Menu items are readable in both themes
- [ ] Dropdown menus have proper backgrounds
- [ ] Breadcrumb links are visible
- [ ] Tabs are clearly differentiated
- [ ] Pagination controls are accessible

### 5. Contrast & Accessibility

#### Color Contrast (WCAG AA Standards)
- [ ] All text has minimum 4.5:1 contrast ratio (normal text)
- [ ] Large text (18pt+) has minimum 3:1 contrast ratio
- [ ] UI components and icons have minimum 3:1 contrast
- [ ] Focus indicators are clearly visible

#### Dark Mode Specific
- [ ] No pure black (#000000) on pure white (#FFFFFF) - too harsh
- [ ] No gray-on-gray combinations with insufficient contrast
- [ ] Links are clearly identifiable (not just by color)
- [ ] Disabled text is distinguishable from enabled text

#### Visual Comfort
- [ ] Dark mode reduces eye strain in low light
- [ ] Text doesn't "bleed" into dark backgrounds
- [ ] No visual vibration between adjacent colors

### 6. Edge Cases & Stress Testing

#### Rapid Theme Switching
- [ ] Rapidly clicking toggle button 5-10 times doesn't cause errors
- [ ] No console errors during rapid theme switching
- [ ] UI remains responsive during rapid toggling

#### Page Transitions
- [ ] No white flash when navigating pages in dark mode
- [ ] Theme applies immediately on page load
- [ ] Scroll position maintains theme correctly

#### Error States
- [ ] Error messages are visible in dark mode
- [ ] Error dialogs have proper styling
- [ ] Validation errors are clearly visible

#### Loading States
- [ ] Loading spinners are visible in both themes
- [ ] Skeleton loaders look good in dark mode
- [ ] Progress bars have good contrast

### 7. Integration with Other Features

#### Language Switching
- [ ] Theme persists when switching languages (EN ↔ RU)
- [ ] All translated text is readable in dark mode

#### Keyboard Navigation
- [ ] Keyboard shortcuts work in both themes
- [ ] Focus indicators are visible in dark mode
- [ ] Tab order is clear in both themes

#### Responsive Design
- [ ] Dark mode works on mobile (375px)
- [ ] Dark mode works on tablet (768px)
- [ ] Dark mode works on desktop (1920px+)
- [ ] Theme toggle button accessible on all viewports

## Automated Testing

Run the automated E2E test suite:

```bash
cd frontend
npm run test:e2e -- dark-mode.spec.ts
```

This will test:
- Theme toggle functionality
- Theme persistence across sessions
- Visual rendering on all pages
- Component integration
- Mobile responsiveness
- Edge cases

## Common Issues to Look For

### Contrast Issues
- Gray text on dark backgrounds (too low contrast)
- Disabled states that look identical to enabled states
- Links that are hard to distinguish from regular text

### Visual Glitches
- White borders around images in dark mode
- Inconsistent background colors
- Flash of unstyled content (FOUC) when switching themes
- Icons not adapting to theme

### Theme Persistence
- Theme not saving to localStorage
- Theme resetting to default on page navigation
- Theme preference not applying on initial load

### Component Issues
- Material UI components not receiving theme
- Custom components not adapting to theme
- Third-party libraries breaking in dark mode

## Test Results Template

### Summary
- **Tester**: [Your Name]
- **Date**: [YYYY-MM-DD]
- **Browser**: [Chrome/Firefox/Safari]
- **Viewport**: [Desktop/Tablet/Mobile]
- **Overall Status**: ✅ Pass / ❌ Fail

### Issues Found

| Page | Issue | Severity | Theme | Screenshot |
|------|-------|----------|-------|------------|
| /recruiter/search | Low contrast on status chips | Medium | Dark | [link] |
| /upload | White border on upload zone | Low | Dark | [link] |

### Pass/Fail by Page
- [ ] Home (/) - ✅ Pass
- [ ] Candidate Search (/recruiter/search) - ✅ Pass
- [ ] Vacancy List (/recruiter/vacancies) - ✅ Pass
- [ ] Resume Database (/recruiter/resumes) - ✅ Pass
- [ ] Workflow Board (/recruiter/workflow) - ✅ Pass
- [ ] Upload (/upload) - ✅ Pass

## Browser DevTools Commands

### Check Current Theme
```javascript
document.documentElement.getAttribute('data-theme')
```

### Force Dark Mode
```javascript
document.documentElement.setAttribute('data-theme', 'dark')
```

### Force Light Mode
```javascript
document.documentElement.setAttribute('data-theme', 'light')
```

### Check Computed Colors
```javascript
// Click on element in DevTools, then run:
window.getComputedStyle($0).backgroundColor
window.getComputedStyle($0).color
```

### Check localStorage
```javascript
localStorage.getItem('app-theme-mode')
```

## Success Criteria

All tests pass when:
1. ✅ Theme toggle button is visible and functional on all pages
2. ✅ All pages render correctly in both light and dark modes
3. ✅ No visual glitches or contrast issues
4. ✅ Theme preference persists across sessions and page navigation
5. ✅ All interactive elements maintain good contrast and visibility
6. ✅ No console errors related to theming
7. ✅ Smooth transitions between themes (no jarring flashes)

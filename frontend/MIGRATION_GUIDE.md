# MUI to Emotion Migration Guide

## Overview

This guide provides comprehensive documentation for migrating from Material UI (MUI) to our custom Emotion-based component library. The migration reduces bundle size by ~450KB gzipped (70% reduction) while maintaining full functionality and visual parity.

**Key Benefits:**
- 📦 **70% smaller UI library** bundle size
- 🎨 **Full visual parity** with existing MUI design
- 🚀 **Better performance** through tree-shaking
- 🔧 **Same API surface** for easy migration
- 🎯 **Type-safe** with full TypeScript support

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Component Mapping](#component-mapping)
3. [Icon Migration](#icon-migration)
4. [Hooks Migration](#hooks-migration)
5. [Theme API Migration](#theme-api-migration)
6. [Before/After Examples](#beforeafter-examples)
7. [Breaking Changes](#breaking-changes)
8. [Automated Migration](#automated-migration)
9. [Step-by-Step Process](#step-by-step-process)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Import Path Changes

**Before (MUI):**
```tsx
import { Box, Typography, Button } from '@mui/material';
import { Search, Menu } from '@mui/icons-material';
```

**After (New Library):**
```tsx
import { Box, Typography, Button } from '@/components/ui';
import Icon from '@/components/ui/primitives/Icon';
```

### 2. Basic Component Migration

Most components have **1:1 API compatibility**. Simply change the import:

```tsx
// Before
import { Container, Typography, Box } from '@mui/material';

// After
import { Container, Typography, Box } from '@/components/ui';
```

The component props remain **identical** for most cases.

---

## Component Mapping

### Layout Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Box` | `Box` | ✅ Yes | Same system props API |
| `Container` | `Container` | ✅ Yes | Identical props |
| `Stack` | `Stack` | ✅ Yes | Same direction/spacing props |
| `Grid` | `Grid` | ✅ Yes | Same breakpoint system |
| `Paper` | `Paper` | ✅ Yes | Same elevation system |
| `Card` | `Card` | ✅ Yes | Same subcomponents |

### Typography Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Typography` | `Typography` | ✅ Yes | All variants supported |
| - `variant="h1"` | `variant="h1"` | ✅ Yes | Identical styling |
| - `variant="body1"` | `variant="body1"` | ✅ Yes | Identical styling |

### Input Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `TextField` | `TextField` | ✅ Yes | react-hook-form compatible |
| `TextArea` | `TextArea` | ✅ Yes | Multiline input |
| `Select` | `Select` | ✅ Yes | Same onChange signature |
| `Checkbox` | `Checkbox` | ✅ Yes | Same checked prop |
| `Radio` | `Radio` | ✅ Yes | Same value/group API |
| `Switch` | `Switch` | ✅ Yes | Same checked/onChange |
| `Slider` | `Slider` | ✅ Yes | Same value/scale |

### Button Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Button` | `Button` | ✅ Yes | Same variants (contained, outlined, text) |
| `IconButton` | `IconButton` | ✅ Yes | Same API |
| `ButtonGroup` | `ButtonGroup` | ✅ Yes | Same orientation |

### Feedback Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Alert` | `Alert` | ✅ Yes | Same severity levels |
| `Snackbar` | `Snackbar` | ✅ Yes | Same open/onClose |
| `CircularProgress` | `CircularProgress` | ✅ Yes | Same size/variant |
| `LinearProgress` | `LinearProgress` | ✅ Yes | Same buffer/value |
| `Skeleton` | `Skeleton` | ✅ Yes | Same animation variants |

### Navigation Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `AppBar` | `AppBar` | ✅ Yes | Same position API |
| `Toolbar` | `Toolbar` | ✅ Yes | Same spacing |
| `Drawer` | `Drawer` | ✅ Yes | Same anchor/variant |
| `Menu` | `Menu` | ✅ Yes | Same anchor position |
| `Breadcrumbs` | `Breadcrumbs` | ✅ Yes | Same separator |
| `Tabs` | `Tabs` | ✅ Yes | Same value/onChange |
| `Tab` | `Tab` | ✅ Yes | Same disabled state |
| `Pagination` | `Pagination` | ✅ Yes | Same count/page |

### Data Display Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Table` | `Table` | ✅ Yes | Same structure |
| `Chip` | `Chip` | ✅ Yes | Same size/delete |
| `Badge` | `Badge` | ✅ Yes | Same badgeContent |
| `Avatar` | `Avatar` | ✅ Yes | Same alt/src |
| `Divider` | `Divider` | ✅ Yes | Same orientation |
| `List` | `List` | ✅ Yes | Same component structure |
| `ListItem` | `ListItem` | ✅ Yes | Same button/dense |
| `Accordion` | `Accordion` | ✅ Yes | Same expanded/disabled |
| `Collapse` | `Collapse` | ✅ Yes | Same in/timeout |

### Overlay Components

| MUI Component | New Component | API Compatible | Notes |
|--------------|---------------|----------------|-------|
| `Dialog` | `Dialog` | ✅ Yes | Same open/onClose |
| `Modal` | `Modal` | ✅ Yes | Same open/close |
| `Popover` | `Popover` | ✅ Yes | Same anchor API |
| `Tooltip` | `Tooltip` | ✅ Yes | Same title/placement |

---

## Icon Migration

### Overview

MUI icons are replaced with **lucide-react** icons, wrapped in our `Icon` component for a consistent API.

### Icon Mapping

Common icon mappings:

| MUI Icon | Lucide Icon | Usage |
|----------|-------------|-------|
| `Search` | `Search` | Search bars |
| `Menu` | `Menu` | Navigation menus |
| `Close` | `X` | Close buttons |
| `ArrowBack` | `ArrowLeft` | Back navigation |
| `ArrowForward` | `ArrowRight` | Forward navigation |
| `ExpandMore` | `ChevronDown` | Expand/collapse |
| `ExpandLess` | `ChevronUp` | Expand/collapse |
| `Add` | `Plus` | Add actions |
| `Delete` | `Trash2` | Delete actions |
| `Edit` | `Pencil` | Edit actions |
| `Check` | `Check` | Success states |
| `ErrorOutline` | `AlertCircle` | Error states |
| `InfoOutlined` | `Info` | Info messages |
| `Warning` | `AlertTriangle` | Warnings |
| `Person` | `User` | User profiles |
| `Work` | `Briefcase` | Jobs/vacancies |
| `Home` | `Home` | Home page |
| `Settings` | `Settings` | Settings |
| `Refresh` | `RefreshCw` | Refresh actions |
| `Download` | `Download` | Downloads |
| `Upload` | `Upload` | Uploads |
| `FilterList` | `Filter` | Filters |
| `Sort` | `ArrowUpDown` | Sorting |
| `Visibility` | `Eye` | Show/visible |
| `VisibilityOff` | `EyeOff` | Hide/hidden |
| `Star` | `Star` | Favorites |
| `StarBorder` | `Star` | Unfavorited |
| `Send` | `Send` | Send actions |
| `Email` | `Mail` | Email |
| `Phone` | `Phone` | Phone |
| `LocationOn` | `MapPin` | Location |
| `CalendarToday` | `Calendar` | Calendar |
| `AccessTime` | `Clock` | Time |

### Icon Migration - Before/After

**Before (MUI):**
```tsx
import { Search, Menu, Close } from '@mui/icons-material';

function SearchBar() {
  return (
    <Box display="flex" gap={1}>
      <Search />
      <Menu />
      <Close />
    </Box>
  );
}
```

**After (New):**
```tsx
import Icon from '@/components/ui/primitives/Icon';

function SearchBar() {
  return (
    <Box display="flex" gap={1}>
      <Icon name="Search" />
      <Icon name="Menu" />
      <Icon name="X" />  // Note: Close -> X in lucide
    </Box>
  );
}
```

### Icon Props

The `Icon` component supports MUI-compatible props:

```tsx
<Icon
  name="Search"
  size="medium"           // 'inherit' | 'small' | 'medium' | 'large' | number
  color="primary"         // 'primary' | 'secondary' | 'error' | 'warning' | 'success' | 'info' | 'action'
  onClick={handleClick}   // Click handler
  disabled={false}        // Disabled state
  className="my-icon"     // Custom class
  style={{ margin: 8 }}   // Inline styles
/>
```

### Icon Color Props

Legacy MUI boolean color props are supported:

```tsx
// MUI style (still works)
<Icon name="Search" colorPrimary />
<Icon name="Close" colorError />
<Icon name="Settings" colorAction />

// Preferred new style
<Icon name="Search" color="primary" />
<Icon name="Close" color="error" />
<Icon name="Settings" color="action" />
```

---

## Hooks Migration

### useBreakpoints → useResponsive

**Before (MUI):**
```tsx
import { useTheme, useMediaQuery } from '@mui/material';

function MyComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  return (
    <Box>
      {isMobile ? <MobileLayout /> : <DesktopLayout />}
    </Box>
  );
}
```

**After (New):**
```tsx
import { useResponsive } from '@/hooks/useResponsive';

function MyComponent() {
  const responsive = useResponsive();

  return (
    <Box>
      {responsive.isMdOnly ? <MobileLayout /> : <DesktopLayout />}
    </Box>
  );
}
```

### useResponsive API

```tsx
interface ResponsiveResult {
  // Boolean flags
  isSmUp: boolean;      // width >= 600px
  isMdUp: boolean;      // width >= 960px
  isLgUp: boolean;      // width >= 1280px
  isXlUp: boolean;      // width >= 1920px
  isXsOnly: boolean;    // width < 600px
  isSmOnly: boolean;    // width < 960px
  isMdOnly: boolean;    // width < 1280px

  // Current state
  currentBreakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  width: number;

  // Utility methods
  up: (breakpoint) => boolean;
  down: (breakpoint) => boolean;
  between: (start, end) => boolean;
  only: (breakpoint) => boolean;
}
```

### Examples

**Check if desktop:**
```tsx
const responsive = useResponsive();
if (responsive.isMdUp) {
  // Render desktop layout
}
```

**Responsive columns:**
```tsx
const responsive = useResponsive();
const columns = responsive.up('xl') ? 4 : responsive.up('lg') ? 3 : 2;
```

**Tablet-only:**
```tsx
const responsive = useResponsive();
if (responsive.between('sm', 'lg')) {
  // Render tablet-only layout
}
```

---

## Theme API Migration

### Theme Context

**Before (MUI):**
```tsx
import { useTheme } from '@mui/material/styles';

function MyComponent() {
  const theme = useTheme();

  return (
    <Box sx={{ color: theme.palette.primary.main }}>
      Colored text
    </Box>
  );
}
```

**After (New):**
```tsx
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';

function MyComponent() {
  const { theme } = useEmotionTheme();

  return (
    <Box style={{ color: theme.primary.main }}>
      Colored text
    </Box>
  );
}
```

### Theme Structure

The new theme maintains the same structure as MUI:

```tsx
interface EmotionTheme {
  // Colors (same as MUI palette)
  primary: { main: string; light: string; dark: string; contrastText: string };
  secondary: { main: string; light: string; dark: string; contrastText: string };
  error: { main: string; light: string; dark: string; contrastText: string };
  warning: { main: string; light: string; dark: string; contrastText: string };
  info: { main: string; light: string; dark: string; contrastText: string };
  success: { main: string; light: string; dark: string; contrastText: string };

  // Text colors
  text: { primary: string; secondary: string; disabled: string; hint: string };

  // Background colors
  background: { default: string; paper: string };

  // Spacing (same 8px grid system)
  spacing: Record<string, string>;

  // Typography
  typography: {
    fontFamily: string;
    fontSize: Record<string, string>;
    fontWeight: Record<string, number>;
    lineHeight: Record<string, number>;
    letterSpacing: Record<string, string>;
  };

  // Breakpoints
  breakpoints: { values: { xs: number; sm: number; md: number; lg: number; xl: number } };

  // Shadows
  shadows: string[];

  // Z-index
  zIndex: Record<string, number>;

  // Transitions
  transitions: {
    duration: Record<string, number>;
    easing: Record<string, string>;
  };
}
```

### Accessing Theme Values

```tsx
const { theme } = useEmotionTheme();

// Colors
theme.primary.main
theme.secondary.light
theme.error.main

// Spacing (use number units, automatically multiplied by 8px)
<Box m={2}>  // 16px margin
<Box p={3}>  // 24px padding

// Typography
theme.typography.fontSize.lg
theme.typography.fontWeight.medium

// Breakpoints
theme.breakpoints.values.md  // 960

// Shadows
<Box boxShadow={theme.shadows[4]}>
```

---

## Before/After Examples

### Example 1: Simple Card

**Before (MUI):**
```tsx
import { Card, CardContent, Typography, Box } from '@mui/material';

function UserCard({ name, email }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {name}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          {email}
        </Typography>
      </CardContent>
    </Card>
  );
}
```

**After (New):**
```tsx
import { Card, CardContent, Typography, Box } from '@/components/ui';

function UserCard({ name, email }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {name}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          {email}
        </Typography>
      </CardContent>
    </Card>
  );
}
```

### Example 2: Form with Inputs

**Before (MUI):**
```tsx
import { TextField, Button, Box, Stack } from '@mui/material';
import { useForm } from 'react-hook-form';

function LoginForm() {
  const { register, handleSubmit } = useForm();

  return (
    <Box maxWidth={400} mx="auto">
      <Stack spacing={2}>
        <TextField
          label="Email"
          {...register('email')}
          fullWidth
        />
        <TextField
          label="Password"
          type="password"
          {...register('password')}
          fullWidth
        />
        <Button variant="contained" fullWidth>
          Login
        </Button>
      </Stack>
    </Box>
  );
}
```

**After (New):**
```tsx
import { TextField, Button, Box, Stack } from '@/components/ui';
import { useForm } from 'react-hook-form';

function LoginForm() {
  const { register, handleSubmit } = useForm();

  return (
    <Box maxWidth={400} mx="auto">
      <Stack spacing={2}>
        <TextField
          label="Email"
          {...register('email')}
          fullWidth
        />
        <TextField
          label="Password"
          type="password"
          {...register('password')}
          fullWidth
        />
        <Button variant="contained" fullWidth>
          Login
        </Button>
      </Stack>
    </Box>
  );
}
```

### Example 3: Responsive Layout

**Before (MUI):**
```tsx
import { Box, Grid, Typography, useMediaQuery, useTheme } from '@mui/material';

function Dashboard() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard label="Users" value={1234} />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard label="Orders" value={567} />
        </Grid>
      </Grid>
      {isMobile ? <MobileTable /> : <DesktopTable />}
    </Box>
  );
}
```

**After (New):**
```tsx
import { Box, Grid, Typography } from '@/components/ui';
import { useResponsive } from '@/hooks/useResponsive';

function Dashboard() {
  const responsive = useResponsive();

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard label="Users" value={1234} />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard label="Orders" value={567} />
        </Grid>
      </Grid>
      {responsive.isMdOnly ? <MobileTable /> : <DesktopTable />}
    </Box>
  );
}
```

### Example 4: Modal Dialog

**Before (MUI):**
```tsx
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';

function ConfirmDialog({ open, onClose, onConfirm }) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Confirm Action</DialogTitle>
      <DialogContent>
        Are you sure you want to proceed?
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} variant="contained" color="primary">
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

**After (New):**
```tsx
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@/components/ui';

function ConfirmDialog({ open, onClose, onConfirm }) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Confirm Action</DialogTitle>
      <DialogContent>
        Are you sure you want to proceed?
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} variant="contained" color="primary">
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

### Example 5: Icons in Buttons

**Before (MUI):**
```tsx
import { Button, IconButton } from '@mui/material';
import { Search, Close, Add } from '@mui/icons-material';

function ButtonExamples() {
  return (
    <>
      <Button startIcon={<Search />}>Search</Button>
      <Button endIcon={<Add />}>Add Item</Button>
      <IconButton aria-label="close">
        <Close />
      </IconButton>
    </>
  );
}
```

**After (New):**
```tsx
import { Button, IconButton } from '@/components/ui';
import Icon from '@/components/ui/primitives/Icon';

function ButtonExamples() {
  return (
    <>
      <Button startIcon={<Icon name="Search" />}>Search</Button>
      <Button endIcon={<Icon name="Plus" />}>Add Item</Button>
      <IconButton aria-label="close">
        <Icon name="X" />
      </IconButton>
    </>
  );
}
```

---

## Breaking Changes

### 1. Icon Import Changes

**Breaking:** Icons are no longer direct imports from `@mui/icons-material`.

**Migration:**
```tsx
// Before
import { Search, Menu } from '@mui/icons-material';

// After
import Icon from '@/components/ui/primitives/Icon';
// Usage: <Icon name="Search" />
```

### 2. sx Prop → style Prop

**Breaking:** The `sx` prop is not supported. Use `style` or system props.

**Migration:**
```tsx
// Before
<Box sx={{ color: 'primary.main', m: 2 }} />

// After - Option 1: System props
<Box color="primary.main" m={2} />

// After - Option 2: style prop
<Box style={{ color: theme.primary.main, margin: '16px' }} />

// After - Option 3: Combined
<Box color="primary.main" m={2} style={{ customProp: 'value' }} />
```

### 3. styled() API Location

**Breaking:** `styled` is imported from `@emotion/styled`, not `@mui/material/styles`.

**Migration:**
```tsx
// Before
import { styled } from '@mui/material/styles';

// After
import styled from '@emotion/styled';
```

### 4. Grid v2 (Grid2) Not Supported

**Breaking:** MUI's `Grid2` component is not implemented. Use standard `Grid`.

**Migration:**
```tsx
// Before
import { Grid2 } from '@mui/material';
<Grid2 container spacing={2}>

// After
import { Grid } from '@/components/ui';
<Grid container spacing={2}>
```

### 5. ThemeProvider Context Change

**Breaking:** If accessing theme directly from context, use `EmotionThemeContext`.

**Migration:**
```tsx
// Before
import { ThemeProvider, useTheme } from '@mui/material/styles';

// After
import { ThemeProvider } from '@/providers/ThemeProvider';
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';
```

### 6. CSS Baseline

**Breaking:** MUI's `CssBaseline` is replaced by custom CSS.

**Migration:**
```tsx
// Before - in main.tsx
import { CssBaseline } from '@mui/material';
<CssBaseline />

// After - already in index.css
// No component needed, CSS resets are in src/index.css
```

### 7. Date/Time Pickers

**Breaking:** If using `@mui/x-date-pickers`, these are not migrated yet.

**Action:** Keep using MUI date pickers until replacement is built.

### 8. Data Grid

**Breaking:** If using `@mui/x-data-grid`, this is not migrated yet.

**Action:** Keep using MUI data grid until replacement is built.

---

## Automated Migration

### Migration Script

A codemod script is provided to automate common migrations:

```bash
# Install jscodeshift if not already installed
npm install -g jscodeshift

# Run the migration script
npx jscodeshift -t scripts/migrate-from-mui.ts src/

# Run with dry run first (no changes made)
npx jscodeshift -d -t scripts/migrate-from-mui.ts src/
```

### What the Script Does

1. **Updates imports:** Replaces `@mui/material` imports with `@/components/ui`
2. **Converts icons:** Replaces icon imports with `<Icon name="..." />`
3. **Updates hooks:** Replaces `useBreakpoints` with `useResponsive`
4. **Converts sx props:** Converts `sx={{ }}` to system props where possible
5. **Updates theme context:** Replaces `useTheme` with `useEmotionTheme`

### Manual Review Required

After running the script, **manually review** these areas:

- Complex `sx` props with nested objects
- Dynamic theme value access
- Custom styled components with theme
- Icon name mappings (verify correct lucide names)
- Test files (snapshot tests may need updates)

---

## Step-by-Step Process

### Phase 1: Preparation

1. **Read this guide** completely
2. **Install dependencies** (lucide-react, @emotion/styled, @emotion/react)
3. **Run tests** to establish baseline
4. **Create a feature branch:** `git checkout -b migrate-to-emotion`

### Phase 2: Run Migration Script

1. **Run codemod:**
   ```bash
   npx jscodeshift -d -t scripts/migrate-from-mui.ts src/
   ```

2. **Review changes:**
   ```bash
   git diff
   ```

3. **Commit script changes:**
   ```bash
   git add .
   git commit -m "Run automated migration script"
   ```

### Phase 3: Manual Fixes

1. **Fix icon names** that don't map 1:1
2. **Convert complex `sx` props** to system props or `style`
3. **Update theme access** using `useEmotionTheme`
4. **Fix any TypeScript errors**

### Phase 4: Test and Verify

1. **Run unit tests:**
   ```bash
   npm test
   ```

2. **Run E2E tests:**
   ```bash
   npm run test:e2e
   ```

3. **Manual testing:**
   - Open application in browser
   - Test common user flows
   - Check responsive behavior
   - Verify dark mode
   - Test forms and inputs

4. **Visual regression:**
   - Compare screenshots with MUI version
   - Check all pages for visual parity

### Phase 5: Performance Verification

1. **Build production bundle:**
   ```bash
   npm run build
   ```

2. **Measure bundle size:**
   ```bash
   du -sh dist/assets/*.js | sort -h
   ```

3. **Expected results:**
   - UI library code reduced by ~70%
   - Total bundle smaller by ~450KB gzipped
   - No runtime performance regression

### Phase 6: Cleanup

1. **Remove MUI dependencies:**
   ```bash
   npm uninstall @mui/material @mui/icons-material
   ```

2. **Remove MUI types:** Delete any `.d.ts` files referencing MUI

3. **Final test run:** Ensure everything still works

4. **Commit and deploy:**
   ```bash
   git add .
   git commit -m "Complete MUI to Emotion migration"
   git push
   ```

---

## Troubleshooting

### Issue: Icon Not Found

**Error:** Icon component shows fallback circle instead of icon.

**Solution:**
1. Check icon name is correct lucide-react name
2. Reference: https://lucide.dev/icons/
3. Common mappings:
   - `Close` → `X`
   - `ExpandMore` → `ChevronDown`
   - `ArrowBack` → `ArrowLeft`

### Issue: TypeScript Errors

**Error:** Type errors after migration.

**Solution:**
1. Clear cache: `rm -rf node_modules/.cache`
2. Restart TypeScript server in VS Code: Cmd+Shift+P → "TypeScript: Restart TS Server"
3. Check import paths are correct
4. Verify `@/components/ui` is mapped in `tsconfig.json`

### Issue: Styles Not Applying

**Error:** Component doesn't look like MUI version.

**Solution:**
1. Check theme provider is wrapping the app
2. Verify design tokens are loaded
3. Check CSS variables are set in index.css
4. Inspect element to see applied styles
5. Check for specificity issues

### Issue: Responsive Layout Broken

**Error:** Layout doesn't respond to breakpoints.

**Solution:**
1. Verify `useResponsive` is being used (not `useBreakpoints`)
2. Check breakpoint values match MUI:
   - xs: 0px
   - sm: 600px
   - md: 960px
   - lg: 1280px
   - xl: 1920px

### Issue: Form Not Working

**Error:** Form inputs not updating with react-hook-form.

**Solution:**
1. Verify `{...register('field')}` is passed to component
2. Check `ref` is forwarded by component
3. Ensure `name` prop is set
4. Check `onChange` is not overridden

### Issue: Performance Regression

**Error:** App is slower after migration.

**Solution:**
1. Check for unnecessary re-renders with React DevTools
2. Verify components are using `React.memo` where appropriate
3. Check for inline functions in render (use `useCallback`)
4. Verify icons are memoized (Icon component is already memoized)
5. Check for large style objects in props

### Issue: Dark Mode Broken

**Error:** Dark mode not working correctly.

**Solution:**
1. Check `[data-theme]` attribute is set on `<html>`
2. Verify theme provider gets theme from context
3. Check CSS variables are defined for both themes in tokens.css
4. Verify theme switching logic updates EmotionThemeContext

### Issue: Build Errors

**Error:** Build fails after migration.

**Solution:**
1. Check all MUI imports are removed: `grep -r '@mui' src/`
2. Verify no MUI types in tsconfig
3. Clear build cache: `rm -rf dist`
4. Check for circular dependencies
5. Verify all components have correct exports

---

## Additional Resources

### Component Documentation

- **Box Component:** `/frontend/src/components/ui/primitives/Box.tsx`
- **Typography Component:** `/frontend/src/components/ui/primitives/Typography.tsx`
- **Icon Component:** `/frontend/src/components/ui/primitives/Icon.tsx`
- **useResponsive Hook:** `/frontend/src/hooks/useResponsive.ts`

### Design System

- **Design Tokens:** `/frontend/src/styles/tokens.ts`
- **Theme Context:** `/frontend/src/contexts/EmotionThemeContext.tsx`
- **Theme Provider:** `/frontend/src/providers/ThemeProvider.tsx`

### External Resources

- **Emotion Documentation:** https://emotion.sh/docs/introduction
- **Lucide Icons:** https://lucide.dev/icons/
- **React Hook Form:** https://react-hook-form.com/

---

## Questions or Issues?

If you encounter issues not covered in this guide:

1. **Check existing issues:** Look in project issue tracker
2. **Create a minimal repro:** Simplify the problem to its core
3. **Include code samples:** Show before/after code
4. **Document error messages:** Include full error stack traces
5. **Share screenshots:** For visual issues

---

## Changelog

### Version 1.0.0 (Current)
- Initial migration guide
- Component mapping for all major MUI components
- Icon migration guide with lucide-react
- Hooks migration (useBreakpoints → useResponsive)
- Theme API migration
- Before/after examples
- Breaking changes documentation
- Automated migration script instructions
- Troubleshooting guide

---

**Last Updated:** 2026-02-04
**Maintained By:** Frontend Team

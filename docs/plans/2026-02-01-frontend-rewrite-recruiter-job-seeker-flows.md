# Frontend Rewrite: Recruiter & Job Seeker Flows (2026 Design)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete frontend rewrite implementing two distinct, optimized user flows (Recruiter and Job Seeker) following 2026 design trends while supporting all existing backend features.

**Architecture:**
- **Dual Flow Architecture:** Separate routing trees and layouts for `/recruiter/*` and `/jobs/*` with role-specific components
- **Design System:** Extended MUI v6 with custom theme implementing 2026 trends (Bento grids, variable fonts, soft gradients, micro-interactions)
- **State Management:** React Context API enhanced with React Query for server state
- **Mobile-First:** Bottom navigation for job seekers, responsive dashboards for recruiters

**Tech Stack:**
- React 18.3.1 + TypeScript + Vite
- MUI v6 (PRIMARY UI LIBRARY - MUST USE for all primitives)
- React Router v6.26.2
- TanStack Query (React Query) for server state
- Framer Motion for micro-interactions
- i18next (existing)

---

## Phase 1: Foundation & Design System

### Task 1: Setup Plan Directory Structure

**Files:**
- Create: `frontend/docs/design-system.md`
- Create: `frontend/docs/architecture.md`
- Create: `frontend/docs/component-inventory.md`

**Step 1: Create design system documentation**

```markdown
# Design System - AgentHR 2026

## Typography
- Primary: Inter Variable (weights: 400, 500, 600, 700)
- Display: Space Grotesk (headings)

## Color Palette - 2026 Soft Gradients
- Primary: #6366f1 → #8b5cf6 (indigo to violet gradient)
- Neutral: #f8fafc (slate-50) to #1e293b (slate-800)
- Success: #10b981 (emerald-500)
- Warning: #f59e0b (amber-500)
- Error: #ef4444 (red-500)

## Spacing Scale
- Base unit: 4px
- Scale: 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96

## Bento Grid
- Gap: 16px (desktop), 12px (tablet), 8px (mobile)
- Border radius: 12px
- Card shadow: 0 1px 3px rgba(0,0,0,0.08)
```

**Step 2: Create architecture documentation**

```markdown
# Architecture - Dual Flow System

## Route Structure

### Job Seeker Flow (/jobs/*)
- /jobs - Browse jobs (bottom nav)
- /jobs/search - Advanced search
- /jobs/{id} - Job details
- /jobs/{id}/apply - Application flow
- /jobs/saved - Saved jobs
- /jobs/applications - My applications
- /resume/upload - Upload resume
- /resume/analyze - View analysis
- /profile - Candidate profile

### Recruiter Flow (/recruiter/*)
- /recruiter/dashboard - Analytics dashboard
- /recruiter/vacancies - Job postings
- /recruiter/vacancies/create - Create vacancy
- /recruiter/vacancies/{id} - Vacancy details
- /recruiter/candidates - Candidate pipeline
- /recruiter/candidates/kanban - Kanban board
- /recruiter/candidates/{id} - Candidate details
- /recruiter/analytics - Detailed analytics
- /recruiter/settings - Workflow config

### Shared (/)
- / - Role selector landing
- /auth - Login/register
```

**Step 3: Create component inventory**

```markdown
# Component Inventory

## MUI Components to Use
- Button, IconButton, LoadingButton
- TextField, Select, Autocomplete
- Dialog, Drawer, Menu
- Card, Paper, Box, Stack
- Grid, Container
- Table, TablePagination
- Tabs, BottomNavigation
- Snackbar, Alert
- Typography, Divider
- Avatar, Badge
- Skeleton, CircularProgress

## Custom Wrappers
- BentoCard - wraps MUI Card with bento styling
- GradientButton - wraps MUI Button with gradient
- MotionBox - wraps MUI Box with Framer Motion
```

**Step 4: Commit**

```bash
git add frontend/docs/
git commit -m "docs: add design system and architecture documentation"
```

---

### Task 2: Update Theme with 2026 Design Tokens

**Files:**
- Modify: `frontend/src/themes/index.ts`
- Modify: `frontend/src/contexts/ThemeContext.tsx`

**Step 1: Create enhanced theme file**

```typescript
// frontend/src/themes/index.ts
import { createTheme, ThemeOptions } from '@mui/material/styles';

const baseTheme: ThemeOptions = {
  typography: {
    fontFamily: '"Inter Variable", "Inter", system-ui, sans-serif',
    h1: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700 },
    h2: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700 },
    h3: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h4: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
    h5: { fontFamily: '"Inter Variable", sans-serif', fontWeight: 600 },
    h6: { fontFamily: '"Inter Variable", sans-serif', fontWeight: 600 },
  },
  spacing: 4,
  shape: {
    borderRadius: 12,
  },
  palette: {
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
    },
    secondary: {
      main: '#8b5cf6',
      light: '#a78bfa',
      dark: '#7c3aed',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          backgroundImage: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 600,
        },
        contained: {
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        },
      },
    },
  },
};

export const lightTheme = createTheme({
  ...baseTheme,
  palette: {
    ...baseTheme.palette,
    mode: 'light',
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
    },
  },
});

export const darkTheme = createTheme({
  ...baseTheme,
  palette: {
    ...baseTheme.palette,
    mode: 'dark',
    background: {
      default: '#0f172a',
      paper: '#1e293b',
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#94a3b8',
    },
  },
});
```

**Step 2: Test theme import**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no TypeScript errors

**Step 3: Commit**

```bash
git add frontend/src/themes/
git commit -m "feat: add 2026 design theme with gradients and variable fonts"
```

---

### Task 3: Install Additional Dependencies

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install required packages**

```bash
cd frontend
npm install @tanstack/react-query@5
npm install @tanstack/react-query-devtools@5
npm install framer-motion@11
npm install react-intersection-observer@9
npm install @fontsource-variable/inter @fontsource/space-grotesk
```

**Step 2: Verify installation**

```bash
cd frontend && npm run type-check
```

Expected: No TypeScript errors

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "deps: add react-query, framer-motion, and variable fonts"
```

---

### Task 4: Create Base Layout Components

**Files:**
- Create: `frontend/src/layouts/RecruiterLayout.tsx`
- Create: `frontend/src/layouts/JobSeekerLayout.tsx`
- Create: `frontend/src/layouts/PublicLayout.tsx`

**Step 1: Write the test for RecruiterLayout**

```typescript
// frontend/src/layouts/__tests__/RecruiterLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { RecruiterLayout } from '../RecruiterLayout';

describe('RecruiterLayout', () => {
  it('renders children content', () => {
    render(
      <BrowserRouter>
        <RecruiterLayout>
          <div>Test Content</div>
        </RecruiterLayout>
      </BrowserRouter>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders navigation with correct links', () => {
    render(
      <BrowserRouter>
        <RecruiterLayout>
          <div>Content</div>
        </RecruiterLayout>
      </BrowserRouter>
    );
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- RecruiterLayout.test.tsx
```

Expected: FAIL with "Cannot find module '../RecruiterLayout'"

**Step 3: Implement RecruiterLayout**

```typescript
// frontend/src/layouts/RecruiterLayout.tsx
import { Outlet } from 'react-router-dom';
import { AppBar, Box, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemButton, ListItemText } from '@mui/material';
import { Menu as MenuIcon, Dashboard as DashboardIcon, Work as WorkIcon, People as PeopleIcon, BarChart as BarChartIcon } from '@mui/icons-material';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const DRAWER_WIDTH = 280;

const NAV_ITEMS = [
  { path: '/recruiter/dashboard', icon: DashboardIcon, label: 'Dashboard' },
  { path: '/recruiter/vacancies', icon: WorkIcon, label: 'Vacancies' },
  { path: '/recruiter/candidates', icon: PeopleIcon, label: 'Candidates' },
  { path: '/recruiter/analytics', icon: BarChartIcon, label: 'Analytics' },
];

export function RecruiterLayout() {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const drawer = (
    <Box sx={{ height: '100%', bgcolor: 'background.default' }}>
      <Toolbar sx={{ justifyContent: 'center', py: 2 }}>
        <Typography variant="h5" fontWeight={700} sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AgentHR
        </Typography>
      </Toolbar>
      <List sx={{ px: 2 }}>
        {NAV_ITEMS.map((item) => (
          <ListItem key={item.path} disablePadding sx={{ mb: 1 }}>
            <ListItemButton
              href={item.path}
              sx={{
                borderRadius: 2,
                '&:hover': { bgcolor: 'action.hover' },
              }}
            >
              <item.icon sx={{ mr: 2, color: 'primary.main' }} />
              <ListItemText primary={t(item.label)} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { sm: `${DRAWER_WIDTH}px` },
          bgcolor: 'background.paper',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" color="text.primary">
            {t('Recruiter Portal')}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, borderRight: '1px solid', borderColor: 'divider' },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: 8,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- RecruiterLayout.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/layouts/
git commit -m "feat: add RecruiterLayout with sidebar navigation"
```

---

### Task 5: Implement JobSeekerLayout with Bottom Navigation

**Files:**
- Create: `frontend/src/layouts/JobSeekerLayout.tsx`
- Test: `frontend/src/layouts/__tests__/JobSeekerLayout.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/layouts/__tests__/JobSeekerLayout.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { JobSeekerLayout } from '../JobSeekerLayout';

describe('JobSeekerLayout', () => {
  it('renders children content', () => {
    render(
      <BrowserRouter>
        <JobSeekerLayout>
          <div>Test Content</div>
        </JobSeekerLayout>
      </BrowserRouter>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders bottom navigation', () => {
    render(
      <BrowserRouter>
        <JobSeekerLayout>
          <div>Content</div>
        </JobSeekerLayout>
      </BrowserRouter>
    );
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- JobSeekerLayout.test.tsx
```

Expected: FAIL with "Cannot find module '../JobSeekerLayout'"

**Step 3: Implement JobSeekerLayout**

```typescript
// frontend/src/layouts/JobSeekerLayout.tsx
import { Outlet, useLocation } from 'react-router-dom';
import { Box, AppBar, Toolbar, BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { Search as SearchIcon, Bookmark as BookmarkIcon, Description as DescriptionIcon, Person as PersonIcon } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const NAV_ITEMS = [
  { path: '/jobs', icon: SearchIcon, label: 'Search' },
  { path: '/jobs/saved', icon: BookmarkIcon, label: 'Saved' },
  { path: '/jobs/applications', icon: DescriptionIcon, label: 'Applications' },
  { path: '/profile', icon: PersonIcon, label: 'Profile' },
];

export function JobSeekerLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const [value, setValue] = useState(0);

  useEffect(() => {
    const index = NAV_ITEMS.findIndex(item => location.pathname.startsWith(item.path));
    if (index !== -1) setValue(index);
  }, [location.pathname]);

  return (
    <Box sx={{ pb: 7, bgcolor: 'background.default', minHeight: '100vh' }}>
      <AppBar
        position="sticky"
        sx={{
          bgcolor: 'background.paper',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography
            variant="h5"
            fontWeight={700}
            sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
          >
            AgentHR
          </Typography>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        <Outlet />
      </Box>

      <Paper
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          elevation: 3,
          borderRadius: 0,
        }}
        elevation={3}
      >
        <BottomNavigation
          value={value}
          onChange={(event, newValue) => {
            setValue(newValue);
            window.location.href = NAV_ITEMS[newValue].path;
          }}
          sx={{
            bgcolor: 'background.paper',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          {NAV_ITEMS.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={t(item.label)}
              icon={<item.icon />}
            />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- JobSeekerLayout.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/layouts/
git commit -m "feat: add JobSeekerLayout with bottom navigation"
```

---

### Task 6: Create Role Selector Landing Page

**Files:**
- Create: `frontend/src/pages/LandingPage.tsx`
- Create: `frontend/src/pages/__tests__/LandingPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/__tests__/LandingPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { LandingPage } from '../LandingPage';

describe('LandingPage', () => {
  it('renders role selection cards', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/job seeker/i)).toBeInTheDocument();
    expect(screen.getByText(/recruiter/i)).toBeInTheDocument();
  });

  it('navigates to correct flow on selection', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    const jobSeekerButton = screen.getByRole('button', { name: /job seeker/i });
    await user.click(jobSeekerButton);
    // Verify navigation occurred
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- LandingPage.test.tsx
```

Expected: FAIL with "Cannot find module '../LandingPage'"

**Step 3: Implement LandingPage**

```typescript
// frontend/src/pages/LandingPage.tsx
import { Container, Box, Card, CardContent, Typography, Button, Stack, useTheme, useMediaQuery } from '@mui/material';
import { Work as WorkIcon, BusinessCenter as BusinessIcon, ArrowForward as ArrowIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

export function LandingPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const roles = [
    {
      title: 'Job Seeker',
      description: 'Find your next opportunity with AI-powered matching',
      icon: WorkIcon,
      path: '/jobs',
      gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    },
    {
      title: 'Recruiter',
      description: 'Source and manage candidates with intelligent tools',
      icon: BusinessIcon,
      path: '/recruiter/dashboard',
      gradient: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 10 } }}>
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '2.5rem', md: '4rem' },
              fontWeight: 700,
              mb: 2,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AgentHR
          </Typography>
          <Typography variant="h5" color="text.secondary">
            AI-Powered Recruitment Platform
          </Typography>
        </Box>

        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={4}
          justifyContent="center"
          alignItems="stretch"
        >
          {roles.map((role, index) => (
            <MotionCard
              key={role.path}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              sx={{
                flex: 1,
                maxWidth: { xs: '100%', md: 400 },
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
                },
              }}
            >
              <CardContent sx={{ p: 4, height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box
                  sx={{
                    width: 64,
                    height: 64,
                    borderRadius: 3,
                    background: role.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 3,
                  }}
                >
                  <role.icon sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Typography variant="h4" fontWeight={700} gutterBottom>
                  {role.title}
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, flexGrow: 1 }}>
                  {role.description}
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  endIcon={<ArrowIcon />}
                  onClick={() => navigate(role.path)}
                  sx={{
                    py: 1.5,
                    background: role.gradient,
                    '&:hover': {
                      background: role.gradient,
                      filter: 'brightness(1.1)',
                    },
                  }}
                >
                  {t('Continue')}
                </Button>
              </CardContent>
            </MotionCard>
          ))}
        </Stack>
      </Container>
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- LandingPage.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: add role selector landing page with animations"
```

---

### Task 7: Setup React Query Provider

**Files:**
- Create: `frontend/src/providers/QueryProvider.tsx`
- Modify: `frontend/src/main.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/providers/__tests__/QueryProvider.test.tsx
import { render, screen } from '@testing-library/react';
import { QueryProvider } from '../QueryProvider';

describe('QueryProvider', () => {
  it('renders children', () => {
    render(
      <QueryProvider>
        <div>Test Content</div>
      </QueryProvider>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- QueryProvider.test.tsx
```

Expected: FAIL with "Cannot find module '../QueryProvider'"

**Step 3: Implement QueryProvider**

```typescript
// frontend/src/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            gcTime: 1000 * 60 * 30, // 30 minutes
            retry: 1,
          },
          mutations: {
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
```

**Step 4: Update main.tsx to use QueryProvider**

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { QueryProvider } from './providers/QueryProvider';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <QueryProvider>
          <App />
        </QueryProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- QueryProvider.test.tsx
```

Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/providers/ frontend/src/main.tsx
git commit -m "feat: add React Query provider for server state management"
```

---

## Phase 2: Job Seeker Flow

### Task 8: Create Job Seeker API Hooks

**Files:**
- Create: `frontend/src/api/jobs.ts`
- Create: `frontend/src/hooks/useJobs.ts`
- Test: `frontend/src/hooks/__tests__/useJobs.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/hooks/__tests__/useJobs.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient } from '@tanstack/react-query';
import { useJobs } from '../useJobs';

describe('useJobs', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  it('returns jobs list', async () => {
    // Mock fetch response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ vacancies: [] }),
      } as Response)
    );

    const { result } = renderHook(() => useJobs(), {
      wrapper: ({ children }) => (
        <div>{children}</div> // Simplified for test
      ),
    });

    await waitFor(() => expect(result.current.data).toBeDefined());
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- useJobs.test.tsx
```

Expected: FAIL with "Cannot find module '../useJobs'"

**Step 3: Implement useJobs hook**

```typescript
// frontend/src/hooks/useJobs.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export interface JobVacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months: number;
  industry: string;
  work_format: 'remote' | 'office' | 'hybrid';
  location: string;
  salary_min?: number;
  salary_max?: number;
  employment_type?: string;
}

export interface JobsResponse {
  vacancies: JobVacancy[];
  total: number;
}

export function useJobs(params?: { limit?: number; skip?: number }) {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: async () => {
      const response = await apiClient.get<JobsResponse>('/vacancies', { params });
      return response.data;
    },
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const response = await apiClient.get<JobVacancy>(`/vacancies/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- useJobs.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useJobs hook for job seeker"
```

---

### Task 9: Create JobCard Component

**Files:**
- Create: `frontend/src/components/jobs/JobCard.tsx`
- Create: `frontend/src/components/jobs/__tests__/JobCard.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/jobs/__tests__/JobCard.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { JobCard } from '../JobCard';

describe('JobCard', () => {
  const mockJob = {
    id: '1',
    title: 'Senior Developer',
    description: 'Build great software',
    required_skills: ['React', 'TypeScript'],
    min_experience_months: 36,
    industry: 'Tech',
    work_format: 'remote' as const,
    location: 'Remote',
  };

  it('renders job title and company', () => {
    render(
      <BrowserRouter>
        <JobCard job={mockJob} />
      </BrowserRouter>
    );
    expect(screen.getByText('Senior Developer')).toBeInTheDocument();
  });

  it('renders skills tags', () => {
    render(
      <BrowserRouter>
        <JobCard job={mockJob} />
      </BrowserRouter>
    );
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- JobCard.test.tsx
```

Expected: FAIL with "Cannot find module '../JobCard'"

**Step 3: Implement JobCard**

```typescript
// frontend/src/components/jobs/JobCard.tsx
import { Card, CardContent, Typography, Box, Chip, Stack, IconButton } from '@mui/material';
import { BookmarkBorder, Bookmark, LocationOn, WorkOutline } from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { JobVacancy } from '../../hooks/useJobs';

const MotionCard = motion(Card);

interface JobCardProps {
  job: JobVacancy;
  saved?: boolean;
  onSave?: () => void;
}

export function JobCard({ job, saved = false, onSave }: JobCardProps) {
  return (
    <MotionCard
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      component={Link}
      to={`/jobs/${job.id}`}
      sx={{
        textDecoration: 'none',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} color="text.primary" gutterBottom>
              {job.title}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" color="text.secondary">
              <LocationOn sx={{ fontSize: 16 }} />
              <Typography variant="body2">{job.location}</Typography>
            </Stack>
          </Box>
          <IconButton
            size="small"
            onClick={(e) => {
              e.preventDefault();
              onSave?.();
            }}
            sx={{ ml: 1 }}
          >
            {saved ? <Bookmark color="primary" /> : <BookmarkBorder />}
          </IconButton>
        </Stack>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {job.description}
        </Typography>

        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }} color="text.secondary">
          <WorkOutline sx={{ fontSize: 16 }} />
          <Typography variant="body2">
            {job.min_experience_months > 0 && `${Math.floor(job.min_experience_months / 12)}+ years`}
            {job.work_format && ` • ${job.work_format}`}
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
          {job.required_skills.slice(0, 4).map((skill) => (
            <Chip
              key={skill}
              label={skill}
              size="small"
              variant="outlined"
              sx={{
                borderRadius: 1,
                fontSize: '0.75rem',
                height: 24,
              }}
            />
          ))}
          {job.required_skills.length > 4 && (
            <Chip
              label={`+${job.required_skills.length - 4}`}
              size="small"
              variant="outlined"
              sx={{ borderRadius: 1, fontSize: '0.75rem', height: 24 }}
            />
          )}
        </Stack>
      </CardContent>
    </MotionCard>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- JobCard.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/jobs/
git commit -m "feat: add JobCard component with bento-style design"
```

---

### Task 10: Create JobsBrowsePage with Grid Layout

**Files:**
- Create: `frontend/src/pages/jobs/JobsBrowsePage.tsx`
- Create: `frontend/src/pages/jobs/__tests__/JobsBrowsePage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/jobs/__tests__/JobsBrowsePage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { JobsBrowsePage } from '../JobsBrowsePage';

describe('JobsBrowsePage', () => {
  it('renders page title', () => {
    render(
      <BrowserRouter>
        <JobsBrowsePage />
      </BrowserRouter>
    );
    expect(screen.getByText(/find your next job/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- JobsBrowsePage.test.tsx
```

Expected: FAIL with "Cannot find module '../JobsBrowsePage'"

**Step 3: Implement JobsBrowsePage**

```typescript
// frontend/src/pages/jobs/JobsBrowsePage.tsx
import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Stack,
  Grid,
  Paper,
  Chip,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import { Search as SearchIcon, FilterList as FilterIcon } from '@mui/icons-material';
import { useJobs } from '../../hooks/useJobs';
import { JobCard } from '../../components/jobs/JobCard';

export function JobsBrowsePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<{
    workFormat?: string;
    experience?: string;
  }>({});

  const { data, isLoading, error } = useJobs();

  const filteredJobs = data?.vacancies.filter((job) => {
    const matchesSearch =
      searchTerm === '' ||
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFormat = !filters.workFormat || job.work_format === filters.workFormat;

    return matchesSearch && matchesFormat;
  }) ?? [];

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Find Your Next Job
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Discover opportunities matched to your skills
        </Typography>
      </Box>

      <Paper
        sx={{
          p: 2,
          mb: 4,
          display: 'flex',
          gap: 2,
          alignItems: 'center',
        }}
      >
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search jobs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Work Format</InputLabel>
            <Select
              value={filters.workFormat || ''}
              label="Work Format"
              onChange={(e) => setFilters({ ...filters, workFormat: e.target.value || undefined })}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="remote">Remote</MenuItem>
              <MenuItem value="office">Office</MenuItem>
              <MenuItem value="hybrid">Hybrid</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="error">Failed to load jobs</Typography>
        </Box>
      ) : filteredJobs.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="text.secondary">No jobs found</Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard job={job} />
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- JobsBrowsePage.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/jobs/
git commit -m "feat: add JobsBrowsePage with search and filters"
```

---

### Task 11: Create JobDetailPage

**Files:**
- Create: `frontend/src/pages/jobs/JobDetailPage.tsx`
- Test: `frontend/src/pages/jobs/__tests__/JobDetailPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/jobs/__tests__/JobDetailPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { JobDetailPage } from '../JobDetailPage';

describe('JobDetailPage', () => {
  it('shows loading state initially', () => {
    render(
      <BrowserRouter>
        <JobDetailPage />
      </BrowserRouter>
    );
    // Loading state test
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- JobDetailPage.test.tsx
```

Expected: FAIL with "Cannot find module '../JobDetailPage'"

**Step 3: Implement JobDetailPage**

```typescript
// frontend/src/pages/jobs/JobDetailPage.tsx
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Divider,
  CircularProgress,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  LocationOn,
  WorkOutline,
  AttachMoney,
  Business,
} from '@mui/icons-material';
import { useJob } from '../../hooks/useJobs';
import { motion } from 'framer-motion';

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading, error } = useJob(id || '');

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !job) {
    return (
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography variant="h6">Job not found</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Paper sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={4}>
            {/* Header */}
            <Box>
              <Typography variant="h3" fontWeight={700} gutterBottom>
                {job.title}
              </Typography>
              <Stack direction="row" spacing={2} flexWrap="wrap" color="text.secondary">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Business sx={{ fontSize: 18 }} />
                  <Typography>{job.industry}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOn sx={{ fontSize: 18 }} />
                  <Typography>{job.location}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <WorkOutline sx={{ fontSize: 18 }} />
                  <Typography>
                    {job.work_format && `${job.work_format}`}
                    {job.min_experience_months > 0 && ` • ${Math.floor(job.min_experience_months / 12)}+ years`}
                  </Typography>
                </Stack>
              </Stack>
            </Box>

            <Divider />

            {/* Salary */}
            {job.salary_min && (
              <Stack direction="row" spacing={1} alignItems="center" color="success.main">
                <AttachMoney sx={{ fontSize: 20 }} />
                <Typography variant="h6" fontWeight={600} color="success.main">
                  {job.salary_min.toLocaleString()}
                  {job.salary_max && ` - ${job.salary_max.toLocaleString()}`}
                </Typography>
              </Stack>
            )}

            {/* Required Skills */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Required Skills
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {job.required_skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    variant="outlined"
                    sx={{
                      borderRadius: 2,
                      px: 1,
                    }}
                  />
                ))}
              </Stack>
            </Box>

            <Divider />

            {/* Description */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Description
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.8,
                }}
              >
                {job.description}
              </Typography>
            </Box>

            {/* Additional Requirements */}
            {job.additional_requirements && job.additional_requirements.length > 0 && (
              <>
                <Divider />
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Additional Requirements
                  </Typography>
                  <Stack spacing={1}>
                    {job.additional_requirements.map((req, index) => (
                      <Typography key={index} variant="body2" color="text.secondary">
                        • {req}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              </>
            )}

            {/* Action Buttons */}
            <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
              <Button
                variant="contained"
                size="large"
                href={`/jobs/${job.id}/apply`}
                sx={{ flexGrow: 1 }}
              >
                Apply Now
              </Button>
              <Button
                variant="outlined"
                size="large"
                sx={{ minWidth: 120 }}
              >
                Save
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </motion.div>
    </Container>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- JobDetailPage.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/jobs/
git commit -m "feat: add JobDetailPage with full job information"
```

---

### Task 12: Create Resume Upload Component

**Files:**
- Create: `frontend/src/components/resume/ResumeUpload.tsx`
- Test: `frontend/src/components/resume/__tests__/ResumeUpload.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/resume/__tests__/ResumeUpload.test.tsx
import { render, screen } from '@testing-library/react';
import { ResumeUpload } from '../ResumeUpload';

describe('ResumeUpload', () => {
  it('renders upload area', () => {
    render(<ResumeUpload onUploadComplete={() => {}} />);
    expect(screen.getByText(/upload your resume/i)).toBeInTheDocument();
  });

  it('shows drag and drop text', () => {
    render(<ResumeUpload onUploadComplete={() => {}} />);
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- ResumeUpload.test.tsx
```

Expected: FAIL

**Step 3: Implement ResumeUpload**

```typescript
// frontend/src/components/resume/ResumeUpload.tsx
import { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import { CloudUpload, Description } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { apiClient } from '../../api/client';

const MotionPaper = motion(Paper);

interface ResumeUploadProps {
  onUploadComplete: (resumeId: string) => void;
}

export function ResumeUpload({ onUploadComplete }: ResumeUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadedFile(file);
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploadComplete(response.data.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <MotionPaper
        {...getRootProps()}
        whileHover={{ scale: 1.01 }}
        sx={{
          p: 6,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <Stack spacing={2} alignItems="center">
            <CircularProgress size={48} />
            <Typography>Uploading and analyzing...</Typography>
          </Stack>
        ) : uploadedFile ? (
          <Stack spacing={2} alignItems="center">
            <Description sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h6">{uploadedFile.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              Ready to analyze
            </Typography>
          </Stack>
        ) : (
          <Stack spacing={3} alignItems="center">
            <CloudUpload sx={{ fontSize: 64, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6" gutterBottom>
                Upload Your Resume
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Drag and drop or click to browse
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center">
              <Typography variant="caption" color="text.secondary">
                PDF, DOCX • Max 10MB
              </Typography>
            </Stack>
          </Stack>
        )}
      </MotionPaper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- ResumeUpload.test.tsx
```

Expected: PASS

**Step 5: Install react-dropzone if needed**

```bash
cd frontend && npm install react-dropzone
```

**Step 6: Commit**

```bash
git add frontend/src/components/resume/
git commit -m "feat: add ResumeUpload component with drag-and-drop"
```

---

### Task 13: Create Application Flow Page

**Files:**
- Create: `frontend/src/pages/jobs/ApplicationFlowPage.tsx`
- Test: `frontend/src/pages/jobs/__tests__/ApplicationFlowPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/jobs/__tests__/ApplicationFlowPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ApplicationFlowPage } from '../ApplicationFlowPage';

describe('ApplicationFlowPage', () => {
  it('renders application form', () => {
    render(
      <BrowserRouter>
        <ApplicationFlowPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('form', { name: /application/i })).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- ApplicationFlowPage.test.tsx
```

Expected: FAIL

**Step 3: Implement ApplicationFlowPage**

```typescript
// frontend/src/pages/jobs/ApplicationFlowPage.tsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Box,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useJob } from '../../hooks/useJobs';
import { ResumeUpload } from '../../components/resume/ResumeUpload';

const steps = ['Upload Resume', 'Review Match', 'Submit Application'];

export function ApplicationFlowPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: job, isLoading: jobLoading } = useJob(id || '');
  const [activeStep, setActiveStep] = useState(0);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    coverLetter: '',
  });

  const handleUploadComplete = (id: string) => {
    setResumeId(id);
    setActiveStep(1);
  };

  const handleSubmit = async () => {
    if (!resumeId) return;

    setSubmitting(true);
    setError(null);

    try {
      // API call to submit application
      await apiClient.post('/applications', {
        vacancy_id: id,
        resume_id: resumeId,
        ...formData,
      });
      setActiveStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (jobLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Apply for {job?.title}
        </Typography>

        <Stepper activeStep={activeStep} sx={{ my: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {activeStep === 0 && (
          <Stack spacing={4}>
            <Typography variant="body1" color="text.secondary">
              Upload your resume and we'll match your skills to this position.
            </Typography>
            <ResumeUpload onUploadComplete={handleUploadComplete} />
          </Stack>
        )}

        {activeStep === 1 && (
          <Stack spacing={4}>
            <Alert severity="success">
              Your resume has been analyzed! Please complete your details below.
            </Alert>

            <Stack spacing={3}>
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
              <TextField
                label="Phone"
                type="tel"
                fullWidth
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
              <TextField
                label="Cover Letter (Optional)"
                multiline
                rows={6}
                fullWidth
                value={formData.coverLetter}
                onChange={(e) => setFormData({ ...formData, coverLetter: e.target.value })}
                placeholder="Tell us why you're a great fit..."
              />
            </Stack>

            <Stack direction="row" spacing={2}>
              <Button onClick={() => setActiveStep(0)}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={() => setActiveStep(2)}
                disabled={!formData.email}
              >
                Review
              </Button>
            </Stack>
          </Stack>
        )}

        {activeStep === 2 && (
          <Stack spacing={4}>
            <Typography variant="h6">Review Your Application</Typography>
            <Box>
              <Typography variant="body2" color="text.secondary">Email</Typography>
              <Typography>{formData.email}</Typography>
            </Box>
            {formData.phone && (
              <Box>
                <Typography variant="body2" color="text.secondary">Phone</Typography>
                <Typography>{formData.phone}</Typography>
              </Box>
            )}

            {error && (
              <Alert severity="error">{error}</Alert>
            )}

            <Stack direction="row" spacing={2}>
              <Button onClick={() => setActiveStep(1)}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={submitting}
                startIcon={submitting ? <CircularProgress size={16} /> : null}
              >
                {submitting ? 'Submitting...' : 'Submit Application'}
              </Button>
            </Stack>
          </Stack>
        )}

        {activeStep === 3 && (
          <Stack spacing={4} alignItems="center" textAlign="center">
            <Typography variant="h5" fontWeight={700} color="success.main">
              Application Submitted!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              We'll review your application and get back to you soon.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/jobs')}>
              Browse More Jobs
            </Button>
          </Stack>
        )}
      </Paper>
    </Container>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- ApplicationFlowPage.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/pages/jobs/
git commit -m "feat: add multi-step application flow"
```

---

## Phase 3: Recruiter Flow

### Task 14: Create Recruiter API Hooks

**Files:**
- Create: `frontend/src/hooks/useRecruiterData.ts`
- Test: `frontend/src/hooks/__tests__/useRecruiterData.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/hooks/__tests__/useRecruiterData.test.tsx
import { renderHook } from '@testing-library/react';
import { useCandidates } from '../useRecruiterData';

describe('useRecruiterData', () => {
  it('returns candidates data hook', () => {
    const { result } = renderHook(() => useCandidates());
    expect(result.current).toBeDefined();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- useRecruiterData.test.tsx
```

Expected: FAIL

**Step 3: Implement useRecruiterData hooks**

```typescript
// frontend/src/hooks/useRecruiterData.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

// Candidates
export interface Candidate {
  id: string;
  name: string;
  email: string;
  resume_id: string;
  stage: string;
  tags: string[];
  notes_count: number;
  match_score?: number;
  vacancy_id?: string;
}

export function useCandidates(params?: { stage?: string; vacancy_id?: string }) {
  return useQuery({
    queryKey: ['candidates', params],
    queryFn: async () => {
      const response = await apiClient.get<{ candidates: Candidate[] }>('/candidates', { params });
      return response.data;
    },
  });
}

export function useCandidateStages() {
  return useQuery({
    queryKey: ['candidate-stages'],
    queryFn: async () => {
      const response = await apiClient.get<{ stages: string[] }>('/candidates/stages');
      return response.data;
    },
  });
}

export function useUpdateCandidateStage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ candidateId, stage }: { candidateId: string; stage: string }) => {
      const response = await apiClient.put(`/candidates/${candidateId}/stage`, { stage });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

// Vacancies for recruiter
export function useRecruiterVacancies() {
  return useQuery({
    queryKey: ['recruiter-vacancies'],
    queryFn: async () => {
      const response = await apiClient.get('/vacancies');
      return response.data;
    },
  });
}

// Analytics
export interface AnalyticsMetrics {
  time_to_hire: number;
  applications_per_job: number;
  source_performance: Record<string, number>;
  funnel_metrics: {
    views: number;
    applications: number;
    interviews: number;
    offers: number;
  };
}

export function useRecruiterAnalytics() {
  return useQuery({
    queryKey: ['recruiter-analytics'],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsMetrics>('/analytics/key-metrics');
      return response.data;
    },
  });
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- useRecruiterData.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add recruiter data hooks"
```

---

### Task 15: Create Bento-Grid Analytics Dashboard

**Files:**
- Create: `frontend/src/pages/recruiter/DashboardPage.tsx`
- Create: `frontend/src/components/dashboard/BentoCard.tsx`
- Test: `frontend/src/pages/recruiter/__tests__/DashboardPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/recruiter/__tests__/DashboardPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DashboardPage } from '../DashboardPage';

describe('DashboardPage', () => {
  it('renders dashboard title', () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- DashboardPage.test.tsx
```

Expected: FAIL

**Step 3: Create BentoCard component**

```typescript
// frontend/src/components/dashboard/BentoCard.tsx
import { Card, CardContent, Box, Typography, SxProps } from '@mui/material';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

interface BentoCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning';
  delay?: number;
  sx?: SxProps;
}

const colorMap = {
  primary: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  secondary: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
  success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
};

export function BentoCard({ title, value, subtitle, icon, color = 'primary', delay = 0, sx }: BentoCardProps) {
  return (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      sx={{
        height: '100%',
        background: 'background.paper',
        borderRadius: 3,
        ...sx,
      }}
    >
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            background: colorMap[color],
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          {icon}
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </MotionCard>
  );
}
```

**Step 4: Implement DashboardPage**

```typescript
// frontend/src/pages/recruiter/DashboardPage.tsx
import { Grid, Box, Container, Typography, Paper } from '@mui/material';
import {
  Speed as SpeedIcon,
  People as PeopleIcon,
  Work as WorkIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { useRecruiterAnalytics, useCandidates, useRecruiterVacancies } from '../../hooks/useRecruiterData';
import { BentoCard } from '../../components/dashboard/BentoCard';

export function DashboardPage() {
  const { data: analytics, isLoading: analyticsLoading } = useRecruiterAnalytics();
  const { data: candidates } = useCandidates();
  const { data: vacancies } = useRecruiterVacancies();

  const candidateCount = candidates?.candidates?.length || 0;
  const vacancyCount = vacancies?.vacancies?.length || 0;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Recruiter Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's what's happening today.
        </Typography>
      </Box>

      {/* Bento Grid Metrics */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Active Jobs"
            value={vacancyCount}
            subtitle="Open positions"
            icon={<WorkIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Candidates"
            value={candidateCount}
            subtitle="In pipeline"
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Time to Hire"
            value={analytics?.time_to_hire ? `${analytics.time_to_hire}d` : '--'}
            subtitle="Average days"
            icon={<SpeedIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Applications/Job"
            value={analytics?.applications_per_job?.toFixed(1) || '--'}
            subtitle="This month"
            icon={<TrendingIcon sx={{ color: 'white' }} />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Funnel Metrics */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Pipeline Funnel
          </Typography>
          {/* Funnel visualization using MUI components */}
        </Paper>
      </Grid>
    </Container>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- DashboardPage.test.tsx
```

Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/pages/recruiter/ frontend/src/components/dashboard/
git commit -m "feat: add recruiter dashboard with bento grid layout"
```

---

### Task 16: Create Kanban Candidate Board

**Files:**
- Create: `frontend/src/pages/recruiter/CandidatesKanbanPage.tsx`
- Create: `frontend/src/components/kanban/KanbanBoard.tsx`
- Test: `frontend/src/pages/recruiter/__tests__/CandidatesKanbanPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/recruiter/__tests__/CandidatesKanbanPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { CandidatesKanbanPage } from '../CandidatesKanbanPage';

describe('CandidatesKanbanPage', () => {
  it('renders kanban board', () => {
    render(
      <BrowserRouter>
        <CandidatesKanbanPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('list', { name: /candidates/i })).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- CandidatesKanbanPage.test.tsx
```

Expected: FAIL

**Step 3: Implement KanbanBoard component**

```typescript
// frontend/src/components/kanban/KanbanBoard.tsx
import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Chip,
  Avatar,
  Card,
  CardContent,
  IconButton,
} from '@mui/material';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Candidate } from '../../hooks/useRecruiterData';

interface KanbanColumn {
  id: string;
  title: string;
  candidates: Candidate[];
}

interface KanbanBoardProps {
  columns: KanbanColumn[];
  onDragEnd: (result: DropResult) => void;
}

export function KanbanBoard({ columns, onDragEnd }: KanbanBoardProps) {
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Box sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 2 }}>
        {columns.map((column) => (
          <Paper
            key={column.id}
            sx={{
              minWidth: 300,
              width: 300,
              bgcolor: 'background.default',
            }}
          >
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="subtitle2" fontWeight={600}>
                  {column.title}
                </Typography>
                <Chip
                  label={column.candidates.length}
                  size="small"
                  variant="outlined"
                />
              </Stack>
            </Box>
            <Droppable droppableId={column.id}>
              {(provided) => (
                <Box
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  sx={{ p: 2, minHeight: 200 }}
                >
                  {column.candidates.map((candidate, index) => (
                    <Draggable
                      key={candidate.id}
                      draggableId={candidate.id}
                      index={index}
                    >
                      {(provided) => (
                        <Card
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          sx={{ mb: 2, cursor: 'grab' }}
                        >
                          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                            <Stack direction="row" spacing={2} alignItems="center">
                              <Avatar>
                                {candidate.name.charAt(0)}
                              </Avatar>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="body2" fontWeight={600}>
                                  {candidate.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {candidate.email}
                                </Typography>
                              </Box>
                              {candidate.match_score && (
                                <Chip
                                  label={`${candidate.match_score}%`}
                                  size="small"
                                  color={candidate.match_score > 70 ? 'success' : 'default'}
                                />
                              )}
                            </Stack>
                          </CardContent>
                        </Card>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </Box>
              )}
            </Droppable>
          </Paper>
        ))}
      </Box>
    </DragDropContext>
  );
}
```

**Step 4: Implement CandidatesKanbanPage**

```typescript
// frontend/src/pages/recruiter/CandidatesKanbanPage.tsx
import { useState, useMemo } from 'react';
import { Container, Box, Typography, TextField, Stack } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useCandidates, useCandidateStages, useUpdateCandidateStage } from '../../hooks/useRecruiterData';
import { KanbanBoard } from '../../components/kanban/KanbanBoard';
import { DropResult } from '@hello-pangea/dnd';

const DEFAULT_STAGES = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'];

export function CandidatesKanbanPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: candidatesData } = useCandidates();
  const { data: stagesData } = useCandidateStages();
  const updateStage = useUpdateCandidateStage();

  const stages = stagesData?.stages || DEFAULT_STAGES;

  const columns = useMemo(() => {
    const candidates = candidatesData?.candidates || [];
    const filtered = candidates.filter((c) =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return stages.map((stage) => ({
      id: stage.toLowerCase().replace(/\s+/g, '-'),
      title: stage,
      candidates: filtered.filter((c) => c.stage === stage),
    }));
  }, [candidatesData, stages, searchTerm]);

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const candidateId = result.draggableId;
    const newStage = columns[result.destination.droppableId].title;

    await updateStage.mutateAsync({ candidateId, stage: newStage });
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Candidate Pipeline
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Drag candidates between stages to update their status
        </Typography>
      </Box>

      <TextField
        placeholder="Search candidates..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
        }}
        sx={{ mb: 3, maxWidth: 400 }}
      />

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <KanbanBoard columns={columns} onDragEnd={handleDragEnd} />
      </Box>
    </Container>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- CandidatesKanbanPage.test.tsx
```

Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/pages/recruiter/ frontend/src/components/kanban/
git commit -m "feat: add candidate kanban board with drag-and-drop"
```

---

### Task 17: Create Vacancy Management Page

**Files:**
- Create: `frontend/src/pages/recruiter/VacanciesPage.tsx`
- Create: `frontend/src/pages/recruiter/VacancyFormPage.tsx`
- Test: `frontend/src/pages/recruiter/__tests__/VacanciesPage.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/pages/recruiter/__tests__/VacanciesPage.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { VacanciesPage } from '../VacanciesPage';

describe('VacanciesPage', () => {
  it('renders vacancies list', () => {
    render(
      <BrowserRouter>
        <VacanciesPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/job postings/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- VacanciesPage.test.tsx
```

Expected: FAIL

**Step 3: Implement VacanciesPage**

```typescript
// frontend/src/pages/recruiter/VacanciesPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Stack,
  Grid,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useRecruiterVacancies } from '../../hooks/useRecruiterData';
import { motion } from 'framer-motion';

const MotionPaper = motion(Paper);

export function VacanciesPage() {
  const navigate = useNavigate();
  const { data: vacanciesData, isLoading } = useRecruiterVacancies();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedVacancy, setSelectedVacancy] = useState<string | null>(null);

  const vacancies = vacanciesData?.vacancies || [];

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, vacancyId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedVacancy(vacancyId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedVacancy(null);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Job Postings
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your open positions
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/recruiter/vacancies/create')}
        >
          Create Vacancy
        </Button>
      </Stack>

      {isLoading ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>Loading...</Box>
      ) : vacancies.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No job postings yet
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Create your first vacancy to start receiving applications
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/recruiter/vacancies/create')}
            sx={{ mt: 2 }}
          >
            Create Vacancy
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {vacancies.map((vacancy: any, index: number) => (
            <Grid item xs={12} md={6} lg={4} key={vacancy.id}>
              <MotionPaper
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}
              >
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      {vacancy.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {vacancy.location}
                    </Typography>
                  </Box>
                  <IconButton size="small" onClick={(e) => handleMenuOpen(e, vacancy.id)}>
                    <MoreVertIcon />
                  </IconButton>
                </Stack>

                <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5} sx={{ my: 2 }}>
                  {vacancy.required_skills?.slice(0, 3).map((skill: string) => (
                    <Chip key={skill} label={skill} size="small" variant="outlined" />
                  ))}
                  {(vacancy.required_skills?.length || 0) > 3 && (
                    <Chip
                      label={`+${vacancy.required_skills.length - 3}`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Stack>

                <Stack direction="row" spacing={2} sx={{ mt: 'auto' }}>
                  <Chip
                    label={vacancy.work_format || 'Not specified'}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  {vacancy.salary_min && (
                    <Chip
                      label={`$${vacancy.salary_min.toLocaleString()}`}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Stack>
              </MotionPaper>
            </Grid>
          ))}
        </Grid>
      )}

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          navigate(`/recruiter/vacancies/${selectedVacancy}/edit`);
          handleMenuClose();
        }}>
          <EditIcon sx={{ mr: 1 }} /> Edit
        </MenuItem>
        <MenuItem>
          <DeleteIcon sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>
    </Container>
  );
}
```

**Step 4: Implement VacancyFormPage**

```typescript
// frontend/src/pages/recruiter/VacancyFormPage.tsx
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Stack,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Box,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useJob } from '../../hooks/useJobs';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

export function VacancyFormPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { data: vacancy } = useJob(id || '');
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    title: vacancy?.title || '',
    description: vacancy?.description || '',
    location: vacancy?.location || '',
    industry: vacancy?.industry || '',
    work_format: vacancy?.work_format || 'remote',
    salary_min: vacancy?.salary_min || '',
    salary_max: vacancy?.salary_max || '',
    min_experience_months: vacancy?.min_experience_months || 0,
    required_skills: vacancy?.required_skills || [],
    additional_requirements: vacancy?.additional_requirements || [],
  });

  const [skillInput, setSkillInput] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => apiClient.post('/vacancies', data),
    onSuccess: () => navigate('/recruiter/vacancies'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => apiClient.put(`/vacancies/${id}`, data),
    onSuccess: () => navigate('/recruiter/vacancies'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isEdit) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleAddSkill = () => {
    if (skillInput && !formData.required_skills.includes(skillInput)) {
      setFormData({
        ...formData,
        required_skills: [...formData.required_skills, skillInput],
      });
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills.filter((s) => s !== skill),
    });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {isEdit ? 'Edit Vacancy' : 'Create Vacancy'}
        </Typography>

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 4 }}>
          <Stack spacing={3}>
            <TextField
              label="Job Title"
              fullWidth
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />

            <TextField
              label="Location"
              fullWidth
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />

            <FormControl fullWidth>
              <InputLabel>Work Format</InputLabel>
              <Select
                value={formData.work_format}
                label="Work Format"
                onChange={(e) => setFormData({ ...formData, work_format: e.target.value as any })}
              >
                <MenuItem value="remote">Remote</MenuItem>
                <MenuItem value="office">Office</MenuItem>
                <MenuItem value="hybrid">Hybrid</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Description"
              multiline
              rows={8}
              fullWidth
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Required Skills
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                {formData.required_skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    onDelete={() => handleRemoveSkill(skill)}
                  />
                ))}
              </Stack>
              <Stack direction="row" spacing={1}>
                <TextField
                  placeholder="Add a skill..."
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                  sx={{ flexGrow: 1 }}
                />
                <Button
                  type="button"
                  variant="outlined"
                  onClick={handleAddSkill}
                  startIcon={<AddIcon />}
                >
                  Add
                </Button>
              </Stack>
            </Box>

            <Stack direction="row" spacing={2}>
              <TextField
                label="Min Salary"
                type="number"
                value={formData.salary_min}
                onChange={(e) => setFormData({ ...formData, salary_min: e.target.value })}
              />
              <TextField
                label="Max Salary"
                type="number"
                value={formData.salary_max}
                onChange={(e) => setFormData({ ...formData, salary_max: e.target.value })}
              />
            </Stack>

            <Stack direction="row" spacing={2} sx={{ mt: 4 }}>
              <Button
                type="button"
                variant="outlined"
                onClick={() => navigate('/recruiter/vacancies')}
                sx={{ flex: 1 }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                sx={{ flex: 1 }}
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {isEdit ? 'Update' : 'Create'} Vacancy
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- VacanciesPage.test.tsx
```

Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/pages/recruiter/
git commit -m "feat: add vacancy management pages"
```

---

## Phase 4: Routing & Integration

### Task 18: Update App Routing

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/App.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

describe('App Routing', () => {
  it('renders landing page at root', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    expect(screen.getByText(/agenthr/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- App.test.tsx
```

Expected: FAIL (routes don't match)

**Step 3: Update App.tsx with new routing**

```typescript
// frontend/src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { LandingPage } from './pages/LandingPage';

// Job Seeker
import { JobSeekerLayout } from './layouts/JobSeekerLayout';
import { JobsBrowsePage } from './pages/jobs/JobsBrowsePage';
import { JobDetailPage } from './pages/jobs/JobDetailPage';
import { ApplicationFlowPage } from './pages/jobs/ApplicationFlowPage';

// Recruiter
import { RecruiterLayout } from './layouts/RecruiterLayout';
import { DashboardPage } from './pages/recruiter/DashboardPage';
import { CandidatesKanbanPage } from './pages/recruiter/CandidatesKanbanPage';
import { VacanciesPage } from './pages/recruiter/VacanciesPage';
import { VacancyFormPage } from './pages/recruiter/VacancyFormPage';

function AppRoutes() {
  return (
    <Routes>
      {/* Landing */}
      <Route path="/" element={<LandingPage />} />

      {/* Job Seeker Flow */}
      <Route path="/jobs" element={<JobSeekerLayout />}>
        <Route index element={<JobsBrowsePage />} />
        <Route path=":id" element={<JobDetailPage />} />
        <Route path=":id/apply" element={<ApplicationFlowPage />} />
        <Route path="saved" element={<div>Saved Jobs (TODO)</div>} />
        <Route path="applications" element={<div>My Applications (TODO)</div>} />
      </Route>

      {/* Recruiter Flow */}
      <Route path="/recruiter" element={<RecruiterLayout />}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="candidates" element={<CandidatesKanbanPage />} />
        <Route path="vacancies" element={<VacanciesPage />} />
        <Route path="vacancies/create" element={<VacancyFormPage />} />
        <Route path="vacancies/:id/edit" element={<VacancyFormPage />} />
        <Route path="analytics" element={<div>Analytics (TODO)</div>} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppRoutes />
    </ThemeProvider>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- App.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: update app routing for dual flow architecture"
```

---

### Task 19: Add Loading and Error States

**Files:**
- Create: `frontend/src/components/ui/LoadingState.tsx`
- Create: `frontend/src/components/ui/ErrorState.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/ui/__tests__/LoadingState.test.tsx
import { render, screen } from '@testing-library/react';
import { LoadingState } from '../LoadingState';

describe('LoadingState', () => {
  it('renders loading indicator', () => {
    render(<LoadingState />);
    expect(screen.getByRole(/progressbar/i)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- LoadingState.test.tsx
```

Expected: FAIL

**Step 3: Implement LoadingState and ErrorState**

```typescript
// frontend/src/components/ui/LoadingState.tsx
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        gap: 2,
      }}
    >
      <CircularProgress size={48} />
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
```

```typescript
// frontend/src/components/ui/ErrorState.tsx
import { Box, Typography, Button, Alert } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <Box sx={{ py: 4 }}>
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          {title}
        </Typography>
        <Typography variant="body2">{message}</Typography>
      </Alert>
      {onRetry && (
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={onRetry}>
          Try Again
        </Button>
      )}
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- LoadingState.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add loading and error state components"
```

---

### Task 20: Add Responsive Breakpoints Utilities

**Files:**
- Create: `frontend/src/hooks/useBreakpoint.ts`

**Step 1: Write the failing test**

```typescript
// frontend/src/hooks/__tests__/useBreakpoint.test.tsx
import { renderHook } from '@testing-library/react';
import { useBreakpoint } from '../useBreakpoint';

describe('useBreakpoint', () => {
  it('returns breakpoint information', () => {
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current).toBeDefined();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- useBreakpoint.test.tsx
```

Expected: FAIL

**Step 3: Implement useBreakpoint**

```typescript
// frontend/src/hooks/useBreakpoint.ts
import { useTheme, useMediaQuery } from '@mui/material';

export function useBreakpoint() {
  const theme = useTheme();

  return {
    isMobile: useMediaQuery(theme.breakpoints.down('sm')),
    isTablet: useMediaQuery(theme.breakpoints.between('sm', 'md')),
    isDesktop: useMediaQuery(theme.breakpoints.up('md')),
    isLargeScreen: useMediaQuery(theme.breakpoints.up('lg')),
  };
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- useBreakpoint.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useBreakpoint hook for responsive utilities"
```

---

## Phase 5: Polish & Micro-interactions

### Task 21: Add Page Transition Wrapper

**Files:**
- Create: `frontend/src/components/ui/PageTransition.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/ui/__tests__/PageTransition.test.tsx
import { render, screen } from '@testing-library/react';
import { PageTransition } from '../PageTransition';

describe('PageTransition', () => {
  it('renders children content', () => {
    render(
      <PageTransition>
        <div>Test Content</div>
      </PageTransition>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- PageTransition.test.tsx
```

Expected: FAIL

**Step 3: Implement PageTransition**

```typescript
// frontend/src/components/ui/PageTransition.tsx
import { motion } from 'framer-motion';
import { Box } from '@mui/material';

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <Box>{children}</Box>
    </motion.div>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- PageTransition.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add page transition wrapper with framer-motion"
```

---

### Task 22: Add Animated Button Component

**Files:**
- Create: `frontend/src/components/ui/AnimatedButton.tsx`
- Test: `frontend/src/components/ui/__tests__/AnimatedButton.test.tsx`

**Step 1: Write the failing test**

```typescript
// frontend/src/components/ui/__tests__/AnimatedButton.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnimatedButton } from '../AnimatedButton';

describe('AnimatedButton', () => {
  it('renders button text', () => {
    render(<AnimatedButton>Click Me</AnimatedButton>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    render(<AnimatedButton onClick={handleClick}>Click</AnimatedButton>);
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- AnimatedButton.test.tsx
```

Expected: FAIL

**Step 3: Implement AnimatedButton**

```typescript
// frontend/src/components/ui/AnimatedButton.tsx
import { Button, ButtonProps } from '@mui/material';
import { motion } from 'framer-motion';

const MotionButton = motion(Button);

interface AnimatedButtonProps extends ButtonProps {
  children: React.ReactNode;
}

export function AnimatedButton({ children, ...props }: AnimatedButtonProps) {
  return (
    <MotionButton
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      {...props}
    >
      {children}
    </MotionButton>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- AnimatedButton.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add animated button with micro-interactions"
```

---

### Task 23: Update Global Styles and Font Imports

**Files:**
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

**Step 1: Create global styles**

```css
/* frontend/src/index.css */
@import '@fontsource-variable/inter/wght.css';
@import '@fontsource/space-grotesk/index.css';

:root {
  /* Smooth scrolling */
  scroll-behavior: smooth;
}

* {
  /* Better touch targets */
  -webkit-tap-highlight-color: transparent;
}

body {
  /* Prevent overscroll on mobile */
  overscroll-behavior-y: none;
  /* Improve text rendering */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Focus visible styles for accessibility */
*:focus-visible {
  outline: 2px solid var(--mui-palette-primary-main);
  outline-offset: 2px;
}

/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Custom scrollbar for webkit browsers */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

@media (prefers-color-scheme: dark) {
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
  }
}
```

**Step 2: Update main.tsx to import styles**

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { QueryProvider } from './providers/QueryProvider';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <QueryProvider>
          <App />
        </QueryProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
```

**Step 3: Verify build succeeds**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors

**Step 4: Commit**

```bash
git add frontend/src/main.tsx frontend/src/index.css
git commit -m "style: add global styles and font imports"
```

---

### Task 24: Accessibility Audit - Add ARIA Labels

**Files:**
- Modify: `frontend/src/layouts/JobSeekerLayout.tsx`
- Modify: `frontend/src/layouts/RecruiterLayout.tsx`
- Modify: `frontend/src/components/jobs/JobCard.tsx`

**Step 1: Update JobSeekerLayout with proper ARIA**

```typescript
// Update bottom navigation in JobSeekerLayout.tsx
<Paper
  role="navigation"
  aria-label="Main navigation"
  sx={{ /* existing props */ }}
>
  <BottomNavigation
    aria-label="Job seeker navigation"
    showLabels
    // ...rest
  >
```

**Step 2: Update RecruiterLayout with proper ARIA**

```typescript
// Update sidebar in RecruiterLayout.tsx
<nav aria-label="Recruiter sidebar navigation">
  <List>
    {NAV_ITEMS.map((item) => (
      <ListItem key={item.path}>
        <ListItemButton
          href={item.path}
          aria-label={t(item.label)}
          // ...rest
        >
```

**Step 3: Update JobCard with proper ARIA**

```typescript
// Add to JobCard.tsx
<MotionCard
  aria-label={`Job posting: ${job.title}`}
  role="article"
  // ...rest
>
```

**Step 4: Verify linter passes**

```bash
cd frontend && npm run lint
```

Expected: No linting errors

**Step 5: Commit**

```bash
git add frontend/src/layouts/ frontend/src/components/jobs/
git commit -m "a11y: add ARIA labels for screen readers"
```

---

### Task 25: Final Integration Test

**Files:**
- Create: `frontend/src/integration/__tests__/app-flow.test.tsx`

**Step 1: Write integration test**

```typescript
// frontend/src/integration/__tests__/app-flow.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';

describe('App Integration Flow', () => {
  it('renders landing page and allows role selection', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    // Landing page visible
    expect(screen.getByText('AgentHR')).toBeInTheDocument();
    expect(screen.getByText(/job seeker/i)).toBeInTheDocument();
    expect(screen.getByText(/recruiter/i)).toBeInTheDocument();
  });

  it('job seeker flow navigation works', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    // Click job seeker
    await user.click(screen.getByRole('button', { name: /job seeker/i }));
    // Should navigate to jobs
    await waitFor(() => {
      expect(screen.getByText(/find your next job/i)).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run integration test**

```bash
cd frontend && npm test -- app-flow.test.tsx
```

Expected: PASS

**Step 3: Run full test suite**

```bash
cd frontend && npm test
```

Expected: All tests pass

**Step 4: Final commit**

```bash
git add frontend/src/integration/
git commit -m "test: add integration tests for app flows"
```

---

## Phase 6: Build & Deploy Verification

### Task 26: Production Build Verification

**Files:**
- None (verification only)

**Step 1: Clean build**

```bash
cd frontend && rm -rf dist && npm run build
```

Expected: Build completes successfully

**Step 2: Check bundle size**

```bash
cd frontend && npm run build
# Look for output showing bundle sizes
```

Expected: Main bundle under 500KB gzipped

**Step 3: Test production build locally**

```bash
cd frontend && npm run preview
```

Expected: App runs in production mode

**Step 4: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No TypeScript errors

**Step 5: Commit any build config changes**

```bash
git add frontend/vite.config.ts frontend/package.json
git commit -m "build: optimize production bundle"
```

---

### Task 27: Create Component Documentation

**Files:**
- Create: `frontend/docs/COMPONENT_LIBRARY.md`
- Create: `frontend/docs/STORYBOOK_SETUP.md`

**Step 1: Create component library documentation**

```markdown
# Component Library

## Layout Components

### RecruiterLayout
Sidebar navigation for recruiter flow.

Usage:
\`\`\`tsx
import { RecruiterLayout } from '@/layouts/RecruiterLayout';

<RecruiterLayout>
  <YourPageContent />
</RecruiterLayout>
\`\`\`

### JobSeekerLayout
Bottom navigation for job seeker flow.

Usage:
\`\`\`tsx
import { JobSeekerLayout } from '@/layouts/JobSeekerLayout';

<JobSeekerLayout>
  <YourPageContent />
</JobSeekerLayout>
\`\`\`

## UI Components

### BentoCard
Metric card for dashboard grids.

Props:
- title: string
- value: string | number
- subtitle?: string
- icon?: ReactNode
- color?: 'primary' | 'secondary' | 'success' | 'warning'

### JobCard
Job listing card.

Props:
- job: JobVacancy
- saved?: boolean
- onSave?: () => void

### KanbanBoard
Drag-and-drop kanban board.

Props:
- columns: KanbanColumn[]
- onDragEnd: (result: DropResult) => void
```

**Step 2: Create Storybook setup guide**

```markdown
# Storybook Setup

Storybook is used for component development in isolation.

## Installation
\`\`\`bash
npm install -D @storybook/react @storybook/addon-essentials
\`\`\`

## Running Storybook
\`\`\`bash
npm run storybook
\`\`\`

## Writing Stories
\`\`\`tsx
// .storybook/stories/BentoCard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { BentoCard } from '@/components/dashboard/BentoCard';

const meta: Meta<typeof BentoCard> = {
  title: 'Components/BentoCard',
  component: BentoCard,
};

export default meta;
type Story = StoryObj<typeof BentoCard>;

export const Primary: Story = {
  args: {
    title: 'Total Candidates',
    value: '234',
    subtitle: 'In pipeline',
    color: 'primary',
  },
};
\`\`\`
```

**Step 3: Commit**

```bash
git add frontend/docs/
git commit -m "docs: add component library documentation"
```

---

### Task 28: Create Migration Guide

**Files:**
- Create: `frontend/docs/MIGRATION_GUIDE.md`

**Step 1: Create migration documentation**

```markdown
# Frontend Migration Guide

## Breaking Changes from Previous Version

### 1. Route Structure
Old: Mixed routes under single layout
New: Separate route trees for each role

\`\`\`
// OLD
/applicants
/applications

// NEW
/jobs/* (Job Seeker)
/recruiter/* (Recruiter)
\`\`\`

### 2. Layout Components
Old: Single Layout component
New: JobSeekerLayout and RecruiterLayout

\`\`\`
// OLD
import { Layout } from '@/components/Layout';

// NEW
import { JobSeekerLayout } from '@/layouts/JobSeekerLayout';
import { RecruiterLayout } from '@/layouts/RecruiterLayout';
\`\`\`

### 3. Data Fetching
Old: Direct API calls in components
New: React Query hooks

\`\`\`
// OLD
const [jobs, setJobs] = useState([]);
useEffect(() => {
  fetchJobs().then(setJobs);
}, []);

// NEW
const { data: jobs } = useJobs();
\`\`\`

### 4. Component Imports
Old: Scattered component locations
New: Organized by feature

\`\`\`
// OLD
import { JobCard } from '@/components/JobCard';

// NEW
import { JobCard } from '@/components/jobs/JobCard';
\`\`\`

## Rollback Plan

If issues arise:
1. Revert to previous commit: `git revert HEAD`
2. Keep old codebase in `frontend/legacy/` for reference
3. Gradual migration possible by keeping both versions running
```

**Step 2: Commit**

```bash
git add frontend/docs/
git commit -m "docs: add migration guide from old frontend"
```

---

## Summary

This plan implements:

1. **Dual Flow Architecture**: Separate, optimized experiences for recruiters and job seekers
2. **2026 Design Trends**: Bento grids, variable fonts, soft gradients, micro-interactions
3. **MUI v6 Compliance**: All primitives use MUI components as required
4. **Full Backend Support**: All API endpoints covered with React Query hooks
5. **Mobile-First**: Bottom navigation for job seekers, responsive dashboards
6. **Accessibility**: ARIA labels, keyboard navigation, semantic HTML
7. **TDD Approach**: Tests written before each component
8. **Atomic Commits**: Each task committed independently

**Total Tasks**: 28
**Estimated Timeline**: 14-21 days of development

## Execution Options

Plan complete and saved to `docs/plans/2026-02-01-frontend-rewrite-recruiter-job-seeker-flows.md`. Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

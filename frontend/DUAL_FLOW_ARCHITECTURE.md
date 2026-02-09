# Dual-Flow Frontend Architecture

**Version:** 1.0
**Last Updated:** 2026-02-09
**Status:** Implemented

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Routing Architecture](#routing-architecture)
- [Layout Components](#layout-components)
- [Authentication & Authorization](#authentication--authorization)
- [State Management](#state-management)
- [Design Patterns](#design-patterns)
- [Implementation Details](#implementation-details)
- [Developer Guide](#developer-guide)
- [Testing Strategy](#testing-strategy)

---

## Overview

The AgentHR frontend implements a **dual-flow architecture** that provides optimized, role-specific user experiences for two distinct user types:

1. **Job Seekers** (`/jobs/*`) - Mobile-first discovery and application experience
2. **Recruiters** (`/recruiter/*`) - Desktop-focused dashboard and management experience

### Key Benefits

- **Separation of Concerns**: Each flow has its own layout, navigation, and components optimized for its users
- **Role-Based Access Control**: Routes are protected based on user roles (JobSeeker, Recruiter, Admin)
- **Responsive Design**: Job seeker flow is mobile-first; recruiter flow is desktop-optimized
- **Shared Authentication**: Both flows share the same authentication system and state management
- **Smooth Transitions**: Loading states and animations provide a polished UX

### Architecture Rationale

The dual-flow design addresses the "poor UI" pain point by providing:
- **Recruiters** with powerful dashboards, data-dense views, and efficient management tools
- **Job Seekers** with a mobile-optimized discovery experience, quick access to saved jobs and applications

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AgentHR Frontend                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Provider Tree                                 │  │
│  │  ErrorBoundary > StrictMode > OidcAuthProvider > AuthProvider >       │  │
│  │  LanguageProvider > EmotionThemeProvider > QueryProvider > App        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           App.tsx (Router)                            │  │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Landing (/) │  │ Auth (/auth/*)   │  │ Protected Routes       │  │  │
│  │  │             │  │                  │  │                        │  │  │
│  │  │ Role-based  │  │ - login          │  │ ┌────────────────────┐ │  │
│  │  │ redirects   │  │ - register       │  │ │ /jobs/* (Seeker)  │ │  │
│  │  │             │  │ - callback       │  │ │ - No auth required│ │  │
│  │  └─────────────┘  └──────────────────┘  │ └────────────────────┘ │  │  │
│  │                                          │                        │  │  │
│  │                                          │ ┌────────────────────┐ │  │
│  │                                          │ │ /recruiter/*       │ │  │
│  │                                          │ │ - ProtectedRoute   │ │  │
│  │                                          │ │ - Recruiter/Admin  │ │  │
│  │                                          │ └────────────────────┘ │  │  │
│  │                                          └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                    ┌─────────────────┴─────────────────┐                     │
│                    ▼                                   ▼                     │
│  ┌───────────────────────────────┐   ┌───────────────────────────────────┐  │
│  │     JobSeekerLayout           │   │      RecruiterLayout               │  │
│  │  ┌─────────────────────────┐  │   │  ┌─────────────────────────────┐  │  │
│  │  │ Mobile-first design     │  │   │  │ Desktop-focused design       │  │  │
│  │  │ - Bottom navigation     │  │   │  │ - Sidebar navigation         │  │  │
│  │  │ - Drawer on desktop     │  │   │  │ - Quick actions in AppBar   │  │  │
│  │  │ - Fade transitions      │  │   │  │ - Collapsible sections      │  │  │
│  │  │ - Loading states        │  │   │  │ - Fade transitions           │  │  │
│  │  └─────────────────────────┘  │   │  │ - Loading states             │  │  │
│  │                               │   │  └─────────────────────────────┘  │  │
│  │  Routes:                      │   │  Routes:                          │  │
│  │  /jobs, /jobs/recommended,    │   │  /recruiter/dashboard,            │  │
│  │  /jobs/saved, /jobs/applications,│   │  /recruiter/vacancies,           │  │
│  │  /jobs/assessment, /profile,   │   │  /recruiter/candidates,           │  │
│  │  etc.                          │   │  /recruiter/search, etc.          │  │
│  └───────────────────────────────┘   └───────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Routing Architecture

### Route Structure

The application uses React Router v6 with nested routes and layout components.

#### Root Routes

```typescript
/                          // Landing page - role-based redirect
/auth/login               // Login page
/auth/register            // Registration page
/auth/callback            // OAuth callback
*                         // Catch-all -> redirect to /
```

#### Job Seeker Routes (`/jobs/*`)

```typescript
/jobs                      // Browse jobs (index)
/jobs/:id                  // Job detail page
/jobs/:id/apply            // Application flow
/jobs/saved                // Saved jobs
/jobs/applications         // My applications
/jobs/recommended          // Recommended jobs
/jobs/assessment           // Skill assessment
/jobs/learning             // Learning resources
/jobs/salary               // Salary calculator
/jobs/tips                 // Interview tips
/jobs/upload               // Resume upload
/jobs/resume-results/:id   // Resume analysis results
/jobs/alerts               // Job alerts
/jobs/settings             // Settings
/profile                   // Candidate profile
```

#### Recruiter Routes (`/recruiter/*`)

All recruiter routes require `Recruiter` or `Admin` role.

```typescript
/recruiter/dashboard        // Dashboard
/recruiter/vacancies        // Vacancy management
/recruiter/vacancies/create // Create vacancy
/recruiter/vacancies/:id    // Vacancy detail
/recruiter/candidates       // Candidates kanban
/recruiter/candidates/:id   // Candidate detail
/recruiter/search           // Candidate search
/recruiter/saved-searches   // Saved searches
/recruiter/applications     // Applications
/recruiter/resumes          // Resume database
/recruiter/upload           // Single upload
/recruiter/batch-upload     // Batch upload
/recruiter/compare          // Compare candidates
/recruiter/skill-gap        // Skill gap analysis
/recruiter/backups          // Backups
/recruiter/workflow         // Workflow board
/recruiter/results/:id      // Analysis results
/recruiter/weights          // Matching weights
/recruiter/analytics        // Analytics dashboard
/recruiter/health           // Health dashboard
```

### Route Protection

Recruiter routes are protected using the `ProtectedRoute` component:

```tsx
// Protected wrapper for recruiter routes
function ProtectedRecruiterLayout() {
  return (
    <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]} redirectTo="/auth/login">
      <RecruiterLayout />
    </ProtectedRoute>
  );
}

// Usage in App.tsx
<Route path="/recruiter" element={<ProtectedRecruiterLayout />}>
  {/* Recruiter routes */}
</Route>
```

---

## Layout Components

### JobSeekerLayout

**File:** `frontend/src/layouts/JobSeekerLayout.tsx`

**Design Philosophy:** Mobile-first, discovery-oriented

**Key Features:**
- **Bottom Navigation** for mobile (4 primary actions: Jobs, Saved, Applications, Profile)
- **Sidebar Navigation** for desktop with collapsible sections
- **Responsive Design** - adapts between mobile and desktop
- **Fade Transitions** - smooth 300ms enter / 200ms exit animations
- **Loading State** - shows spinner during auth initialization

**Navigation Structure:**

```
┌─ Find Jobs (Quick access)
├─ Jobs
│  ├─ Browse
│  ├─ Recommended
│  ├─ Saved
│  └─ Applications
├─ Career
│  ├─ Skill Assessment
│  ├─ Learning
│  ├─ Salary Calculator
│  └─ Interview Tips
└─ Account
   ├─ Profile
   ├─ Resume
   ├─ Job Alerts
   └─ Settings
```

**Mobile Bottom Navigation:**
- Jobs
- Saved
- Applications
- Profile

**Design Highlights:**
- Drawer width: 280px
- Gradient logo branding
- Collapsible navigation sections
- Active state highlighting with `aria-current="page"`
- Skip-to-content link for accessibility

### RecruiterLayout

**File:** `frontend/src/layouts/RecruiterLayout.tsx`

**Design Philosophy:** Dashboard-focused, data-dense

**Key Features:**
- **Sidebar Navigation** with collapsible sections (no bottom nav)
- **Quick Action Buttons** in AppBar (Ctrl+K for quick search)
- **Responsive Design** with mobile drawer support
- **Fade Transitions** - smooth 300ms enter / 200ms exit animations
- **Loading State** - shows spinner during auth initialization

**Navigation Structure:**

```
┌─ Dashboard (Quick access)
├─ Hiring
│  ├─ Vacancies
│  ├─ Candidates
│  ├─ Pipeline
│  └─ Applications
├─ Resumes
│  ├─ Database
│  ├─ Upload
│  └─ Batch Upload
├─ Search
│  ├─ Candidate Search
│  ├─ Saved Searches
│  └─ Compare
├─ Analytics
│  ├─ Overview
│  └─ Skill Gap Analysis
└─ Settings
   ├─ Weights
   ├─ Backups
   └─ Workflow
```

**Design Highlights:**
- Drawer width: 280px
- Quick Search button in AppBar (Ctrl+K)
- Section-based organization with collapse/expand
- Active state highlighting with `aria-current="page"`
- Skip-to-content link for accessibility

---

## Authentication & Authorization

### User Roles

```typescript
export type UserRole = 'JobSeeker' | 'Recruiter' | 'Admin';
```

- **JobSeeker**: Can browse and apply for jobs
- **Recruiter**: Can manage vacancies and candidates
- **Admin**: Has superuser privileges and can access all routes

### AuthContext

**File:** `frontend/src/contexts/AuthContext.tsx`

**Features:**
- JWT-based authentication with access/refresh tokens
- LocalStorage persistence
- Token refresh mechanism
- Role-based access control helpers

**State Interface:**

```typescript
interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;  // True after initial auth check completes
  error: string | null;
}
```

**Key Functions:**

```typescript
// Authentication
login(email, password) => Promise<LoginResponse>
register(email, password, fullName?) => Promise<RegisterResponse>
logout() => Promise<void>
refreshAccessToken() => Promise<void>

// Role-based access control
hasRole(role: UserRole) => boolean
hasAnyRole(roles: UserRole[]) => boolean

// Utility
clearError() => void
```

### ProtectedRoute Component

**File:** `frontend/src/auth/ProtectedRoute.tsx`

**Features:**
- Authentication check before rendering
- Role-based authorization
- Loading state during auth checks
- Customizable redirect paths
- Access denied UI for unauthorized users

**Usage:**

```tsx
// Basic authentication check
<ProtectedRoute>
  <DashboardPage />
</ProtectedRoute>

// Single role requirement
<ProtectedRoute requiredRoles="Admin">
  <AdminPage />
</ProtectedRoute>

// Multiple roles (user needs at least one)
<ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
  <RecruiterPage />
</ProtectedRoute>

// Custom redirect paths
<ProtectedRoute
  requiredRoles="Admin"
  redirectTo="/auth/login"
  unauthorizedTo="/403"
>
  <PremiumPage />
</ProtectedRoute>
```

**Behavior:**

1. **Loading**: Shows spinner while `isLoading` or `!isInitialized`
2. **Not Authenticated**: Redirects to `redirectTo` (default: `/login`)
3. **Wrong Role**: Shows access denied message with required roles
4. **Authorized**: Renders children

### Provider Tree (main.tsx)

```tsx
<ErrorBoundary>
  <React.StrictMode>
    <OidcAuthProvider {...oidcConfig}>      {/* react-oidc-context */}
      <AuthProvider>                         {/* Custom AuthContext */}
        <LanguageProvider>
          <EmotionThemeProvider>
            <QueryProvider>                  {/* React Query */}
              <AppWithTheme />
            </QueryProvider>
          </EmotionThemeProvider>
        </LanguageProvider>
      </AuthProvider>
    </OidcAuthProvider>
  </React.StrictMode>
</ErrorBoundary>
```

### Landing Page Role-Based Redirect

**File:** `frontend/src/pages/LandingPage.tsx`

The landing page automatically redirects authenticated users to their appropriate flow:

```typescript
// Recruiter or Admin -> /recruiter/dashboard
if (hasAnyRole([UserRole.Recruiter, UserRole.Admin])) {
  navigate('/recruiter/dashboard');
}
// Everyone else -> /jobs
else if (isAuthenticated) {
  navigate('/jobs');
}
```

---

## State Management

### React Query Integration

**File:** `frontend/src/providers/QueryProvider.tsx`

**Configuration:**

```typescript
{
  staleTime: 5 * 60 * 1000,      // 5 minutes
  gcTime: 30 * 60 * 1000,        // 30 minutes (formerly cacheTime)
  retry: 1,
  refetchOnWindowFocus: false,
}
```

**Features:**
- React Query DevTools enabled in development
- Sensible defaults for caching
- Automatic refetching on stale data
- Optimistic updates support

### Context Providers

| Context | Purpose | Status |
|---------|---------|--------|
| `AuthContext` | Authentication state | ✅ Integrated |
| `LanguageContext` | i18n support | ✅ Integrated |
| `EmotionThemeContext` | Theme management | ✅ Integrated |
| `NotificationContext` | Toast notifications | ✅ Available |
| `OrganizationContext` | Org-specific data | ✅ Available |
| `UserPreferencesContext` | User settings | ✅ Available |

---

## Design Patterns

### 1. Layout Component Pattern

Each flow has a dedicated layout component that:
- Wraps all pages in that flow
- Provides navigation structure
- Handles common UI elements (header, footer, sidebar)
- Implements loading and transition states

### 2. Protected Route Pattern

Routes requiring authentication/authorization use the `ProtectedRoute` wrapper:

```tsx
<Route path="/recruiter" element={<ProtectedRecruiterLayout />}>
  {/* Protected routes */}
</Route>
```

### 3. Role-Based Access Control Pattern

Components check user roles using `hasRole()` or `hasAnyRole()`:

```tsx
const { hasRole, hasAnyRole } = useAuthContext();

{hasRole(UserRole.Admin) && <AdminPanel />}
{hasAnyRole([UserRole.Recruiter, UserRole.Admin]) && <RecruiterFeatures />}
```

### 4. Responsive Navigation Pattern

- **Mobile**: Bottom navigation for job seekers, drawer menu for recruiters
- **Desktop**: Sidebar navigation for both flows
- **Responsive**: Uses Material-UI's `useMediaQuery` breakpoint system

### 5. Loading State Pattern

Components show loading states during:
- Initial authentication check (`!isInitialized`)
- Authentication operations (`isLoading`)
- Route transitions (fade animations)

---

## Implementation Details

### File Structure

```
frontend/src/
├── App.tsx                          # Main routing configuration
├── main.tsx                         # Provider tree setup
├── layouts/
│   ├── JobSeekerLayout.tsx          # Job seeker layout (mobile-first)
│   ├── RecruiterLayout.tsx          # Recruiter layout (dashboard-focused)
│   ├── AdminLayout.tsx              # Admin layout (not currently wired)
│   └── DeveloperLayout.tsx          # Developer layout (not currently wired)
├── auth/
│   ├── LoginPage.tsx                # Login page
│   ├── RegisterPage.tsx             # Registration page
│   ├── CallbackPage.tsx             # OAuth callback
│   ├── ProtectedRoute.tsx           # Route protection wrapper
│   └── oidcConfig.ts                # OIDC configuration
├── contexts/
│   ├── AuthContext.tsx              # Custom auth context
│   ├── LanguageContext.tsx          # i18n context
│   └── EmotionThemeContext.tsx      # Theme context
├── providers/
│   └── QueryProvider.tsx            # React Query provider
├── pages/
│   ├── LandingPage.tsx              # Landing page with role redirects
│   ├── jobs/                        # Job seeker pages
│   └── recruiter/                   # Recruiter pages
└── hooks/
    └── useRoles.ts                  # Role type definitions
```

### Key Constants

```typescript
// Drawer width for both layouts
const DRAWER_WIDTH = 280;

// Transition timing (ms)
const FADE_ENTER_TIMEOUT = 300;
const FADE_EXIT_TIMEOUT = 200;

// Auth initialization delay (ms)
const AUTH_INIT_DELAY = 100;
```

### Active Route Detection

Both layouts use intelligent active route detection:

```typescript
// JobSeekerLayout - exact match or child routes
const isActive = location.pathname === item.path ||
  (item.path !== '/jobs' && location.pathname.startsWith(item.path + '/'));

// RecruiterLayout - exact match or child routes (except dashboard)
const isActive = location.pathname === item.path ||
  (item.path !== '/recruiter/dashboard' && location.pathname.startsWith(item.path + '/'));
```

---

## Developer Guide

### Adding a New Job Seeker Page

1. Create the page component in `frontend/src/pages/jobs/`:

```tsx
// frontend/src/pages/jobs/NewFeaturePage.tsx
export const NewFeaturePage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h1">New Feature</Typography>
      {/* Your content */}
    </Box>
  );
};
```

2. Add the route in `App.tsx`:

```tsx
import { NewFeaturePage } from './pages/jobs/NewFeaturePage';

// Inside /jobs route
<Route path="/jobs" element={<JobSeekerLayout />}>
  {/* ...existing routes */}
  <Route path="new-feature" element={<NewFeaturePage />} />
</Route>
```

3. Add navigation item in `JobSeekerLayout.tsx`:

```typescript
const navSections: NavSection[] = [
  // ...existing sections
  {
    title: 'Account',
    items: [
      // ...existing items
      { label: 'New Feature', path: '/jobs/new-feature', icon: <NewIcon /> },
    ],
  },
];
```

### Adding a New Recruiter Page

1. Create the page component in `frontend/src/pages/recruiter/`:

```tsx
// frontend/src/pages/recruiter/NewManagementPage.tsx
export const NewManagementPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h1">New Management Feature</Typography>
      {/* Your content */}
    </Box>
  );
};
```

2. Add the route in `App.tsx`:

```tsx
import { NewManagementPage } from './pages/recruiter/NewManagementPage';

// Inside /recruiter route
<Route path="/recruiter" element={<ProtectedRecruiterLayout />}>
  {/* ...existing routes */}
  <Route path="new-management" element={<NewManagementPage />} />
</Route>
```

3. Add navigation item in `RecruiterLayout.tsx`:

```typescript
const navSections: NavSection[] = [
  // ...existing sections
  {
    title: 'Settings',
    items: [
      // ...existing items
      { label: 'New Management', path: '/recruiter/new-management', icon: <ManageIcon /> },
    ],
  },
];
```

### Protecting a Route with a Specific Role

Use `ProtectedRoute` for fine-grained control:

```tsx
// Admin-only route
<Route
  path="/admin/settings"
  element={
    <ProtectedRoute requiredRoles={UserRole.Admin}>
      <AdminSettingsPage />
    </ProtectedRoute>
  }
/>

// Multiple allowed roles
<Route
  path="/recruiter/analytics"
  element={
    <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
      <AnalyticsPage />
    </ProtectedRoute>
  }
/>
```

### Checking User Roles in Components

```tsx
import { useAuthContext, UserRole } from '@/contexts/AuthContext';

const MyComponent: React.FC = () => {
  const { user, hasRole, hasAnyRole, isAuthenticated } = useAuthContext();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  if (hasRole(UserRole.Admin)) {
    return <AdminDashboard />;
  }

  if (hasAnyRole([UserRole.Recruiter, UserRole.Admin])) {
    return <RecruiterDashboard />;
  }

  return <JobSeekerDashboard />;
};
```

### Customizing Redirects

```tsx
// Custom login redirect
<ProtectedRoute
  requiredRoles={UserRole.Recruiter}
  redirectTo="/auth/login?redirect=/recruiter/dashboard"
>
  <RecruiterOnlyPage />
</ProtectedRoute>

// Custom unauthorized page
<ProtectedRoute
  requiredRoles={UserRole.Admin}
  unauthorizedTo="/access-denied"
>
  <AdminOnlyPage />
</ProtectedRoute>
```

---

## Testing Strategy

### Integration Tests

**Location:** `frontend/src/__tests__/integration/`

**Test Files:**

1. **`recruiter-flow.test.tsx`** - Tests recruiter flow navigation
   - Navigation transitions between pages
   - Active state highlighting
   - Section collapse/expand behavior
   - Mobile navigation drawer
   - Quick action buttons
   - Accessibility features

2. **`jobseeker-flow.test.tsx`** - Tests job seeker flow navigation
   - Landing page to flow entry
   - All navigation sections (Jobs, Career, Account)
   - Bottom navigation (mobile)
   - Sidebar navigation (desktop)
   - Route configuration verification
   - Active route highlighting
   - Accessibility features

3. **`role-routing.test.tsx`** - Tests role-based routing protection
   - Unauthenticated user redirects
   - Role-based access (JobSeeker, Recruiter, Admin)
   - Multi-role users
   - Protected layout integration
   - Custom redirect paths
   - Edge cases

4. **`auth-persistence.test.tsx`** - Tests authentication state persistence
   - Auth state across route changes
   - Token persistence
   - Role checks across navigation
   - Error handling

### Manual Verification Checklist

- [ ] Landing page redirects correctly based on user role
- [ ] Job seeker routes work without authentication
- [ ] Recruiter routes require proper authentication and role
- [ ] Navigation highlights active route correctly
- [ ] Mobile bottom navigation works on job seeker flow
- [ ] Desktop sidebar navigation works on both flows
- [ ] Loading states appear during authentication checks
- [ ] Fade transitions work between routes
- [ ] ProtectedRoute shows access denied for wrong roles
- [ ] Logout clears auth state and redirects properly

### Browser Testing URLs

| Page | URL | Verification |
|------|-----|--------------|
| Landing | `http://localhost:5173/` | Loads without console errors |
| Job Seeker | `http://localhost:5173/jobs` | Bottom nav visible on mobile |
| Recruiter Dashboard | `http://localhost:5173/recruiter/dashboard` | Sidebar visible, auth redirect works |
| Login | `http://localhost:5173/auth/login` | Login form renders |
| Register | `http://localhost:5173/auth/register` | Registration form renders |

---

## Future Enhancements

### Potential Additions

1. **Admin Layout Integration** - Wire up `AdminLayout` routes for admin-specific workflows
2. **Developer Layout Integration** - Wire up `DeveloperLayout` routes for developer tools
3. **Unauthorized Page** - Create dedicated `/unauthorized` page with helpful links
4. **Route-Based Code Splitting** - Lazy load route components for better performance
5. **Skeleton Loading** - Add skeleton screens during route transitions
6. **Analytics Integration** - Track user flow transitions for insights
7. **A/B Testing** - Test different navigation structures and layouts
8. **Accessibility Improvements** - Enhanced keyboard navigation and screen reader support

### Performance Optimizations

1. **Route Prefetching** - Prefetch likely-next routes on hover/idle
2. **Image Optimization** - Lazy load images in job cards and candidate lists
3. **Virtual Scrolling** - For long lists (jobs, candidates, applications)
4. **Memoization** - Optimize re-renders in navigation components
5. **Bundle Analysis** - Regular bundle size audits and optimization

---

## Related Documentation

- [Assessment Document](../.auto-claude/specs/006-dual-flow-frontend-architecture/ASSESSMENT.md) - Detailed gap analysis
- [React Router v6 Documentation](https://reactrouter.com/)
- [Material-UI Documentation](https://mui.com/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Application Specification](../.auto-claude/specs/006-dual-flow-frontend-architecture/spec.md)

---

## Changelog

### Version 1.0 (2026-02-09)
- Initial dual-flow architecture documentation
- Complete routing structure and layout components
- Authentication and authorization implementation
- State management with React Context and React Query
- Developer guide and testing strategy

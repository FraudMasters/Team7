# Customer Journey Documentation

## Overview

This document provides a comprehensive mapping of customer journeys for all three user roles in the AgentHR application: **JobSeeker**, **Recruiter**, and **Admin**. It details page access, navigation flows, authentication requirements, and the microservices that support each feature.

---

## Role Hierarchy

```
Admin (Level 3)
├── Full access to Admin routes
├── Full access to Recruiter routes
└── Read-only access to JobSeeker routes

Recruiter (Level 2)
├── Full access to Recruiter routes
└── No access to Admin routes

JobSeeker (Level 1)
├── Full access to JobSeeker routes
└── No access to Admin or Recruiter routes
```

---

## Page-to-Role Mapping Matrix

| Page/Section | Route | JobSeeker | Recruiter | Admin | Auth Required | Microservice |
|--------------|-------|-----------|-----------|-------|---------------|--------------|
| **Landing Page** | `/` | ✓ | ✓ | ✓ | No | - |
| **JobSeeker Flow** | | | | | | |
| Browse Jobs | `/jobs` | ✓ | - | ✓ (RO) | No | vacancy |
| Job Detail | `/jobs/:id` | ✓ | - | ✓ (RO) | No | vacancy |
| Apply for Job | `/jobs/:id/apply` | ✓ | - | - | Yes* | vacancy, candidate |
| Saved Jobs | `/jobs/saved` | ✓ | - | ✓ (RO) | Yes | candidate |
| My Applications | `/jobs/applications` | ✓ | - | ✓ (RO) | Yes | candidate |
| Candidate Profile | `/profile` | ✓ | - | ✓ (RO) | Yes | candidate |
| Resume Upload | `/jobs/upload` | ✓ | - | - | Yes | candidate |
| Resume Results | `/jobs/resume-results/:id` | ✓ | - | ✓ (RO) | Yes | candidate |
| Recommended Jobs | `/jobs/recommended` | ✓ | - | ✓ (RO) | Yes | vacancy, analytics |
| Skill Assessment | `/jobs/assessment` | ✓ | - | ✓ (RO) | Yes | analytics |
| Learning Resources | `/jobs/learning` | ✓ | - | ✓ (RO) | No | - |
| Salary Calculator | `/jobs/salary` | ✓ | - | ✓ (RO) | No | - |
| Interview Tips | `/jobs/tips` | ✓ | - | ✓ (RO) | No | - |
| Job Alerts | `/jobs/alerts` | ✓ | - | ✓ (RO) | Yes | candidate |
| Settings | `/jobs/settings` | ✓ | - | ✓ (RO) | Yes | candidate |
| **Recruiter Flow** | | | | | | |
| Dashboard | `/recruiter/dashboard` | - | ✓ | ✓ | Yes | analytics |
| Vacancies List | `/recruiter/vacancies` | - | ✓ | ✓ | Yes | vacancy |
| Create Vacancy | `/recruiter/vacancies/create` | - | ✓ | ✓ | Yes | vacancy |
| Vacancy Detail | `/recruiter/vacancies/:id` | - | ✓ | ✓ | Yes | vacancy |
| Edit Vacancy | `/recruiter/vacancies/:id/edit` | - | ✓ | ✓ | Yes | vacancy |
| Candidates Kanban | `/recruiter/candidates` | - | ✓ | ✓ | Yes | candidate |
| Candidate Detail | `/recruiter/candidates/:id` | - | ✓ | ✓ | Yes | candidate |
| Candidate Search | `/recruiter/search` | - | ✓ | ✓ | Yes | candidate |
| Saved Searches | `/recruiter/saved-searches` | - | ✓ | ✓ | Yes | candidate |
| Applications | `/recruiter/applications` | - | ✓ | ✓ | Yes | candidate, vacancy |
| Resume Database | `/recruiter/resumes` | - | ✓ | ✓ | Yes | candidate |
| Upload Resume | `/recruiter/upload` | - | ✓ | ✓ | Yes | candidate |
| Batch Upload | `/recruiter/batch-upload` | - | ✓ | ✓ | Yes | candidate |
| Compare | `/recruiter/compare` | - | ✓ | ✓ | Yes | candidate |
| Skill Gap Analysis | `/recruiter/skill-gap` | - | ✓ | ✓ | Yes | analytics |
| Backups | `/recruiter/backups` | - | ✓ | ✓ | Yes | vacancy |
| Workflow Board | `/recruiter/workflow` | - | ✓ | ✓ | Yes | candidate |
| Results | `/recruiter/results/:id` | - | ✓ | ✓ | Yes | analytics |
| Weights | `/recruiter/weights` | - | ✓ | ✓ | Yes | analytics |
| Analytics | `/recruiter/analytics` | - | ✓ | ✓ | Yes | analytics |
| **Admin Flow** | | | | | | |
| Admin Dashboard | `/admin/dashboard` | - | - | ✓ | Yes | analytics |
| User Management | `/admin/users` | - | - | ✓ | Yes | integration |
| System Settings | `/admin/settings` | - | - | ✓ | Yes | integration |
| Audit Logs | `/admin/audit-logs` | - | - | ✓ | Yes | analytics |

**Legend:**
- ✓ = Full access
- ✓ (RO) = Read-only access for Admin
- - = No access
- \* = Authentication can be bypassed when `VITE_AUTH_ENABLED=false`

---

## JobSeeker Journey

### Overview

JobSeekers can browse jobs, apply to positions, manage their profile, and track applications. Most pages are accessible without authentication, but actions like applying and viewing personal data require login.

### Navigation Structure

```
JobSeekerLayout (/jobs, /profile)
├── Find Jobs (Quick Action)
├── Jobs Section
│   ├── Browse Jobs
│   ├── Recommended Jobs
│   ├── Saved Jobs
│   └── Applications
├── Career Section
│   ├── Skill Assessment
│   ├── Learning Resources
│   ├── Salary Calculator
│   └── Interview Tips
└── Account Section
    ├── Profile
    ├── Resume
    ├── Job Alerts
    └── Settings
```

### Complete User Flow

```
1. Landing Page (/)
   ↓ [Select "Find Jobs"]
2. Browse Jobs (/jobs)
   ↓ [Select Job]
3. Job Detail (/jobs/:id)
   ↓ [Click "Apply"]
4. Application Flow (/jobs/:id/apply) ← AUTH REQUIRED
   ↓ [Complete Application]
5. My Applications (/jobs/applications)
```

### Key Features

| Feature | Route | Description | Service |
|---------|-------|-------------|---------|
| **Job Discovery** | `/jobs` | Search and filter vacancies | vacancy |
| **Job Details** | `/jobs/:id` | View full job description | vacancy |
| **Apply** | `/jobs/:id/apply` | Submit application | vacancy, candidate |
| **Saved Jobs** | `/jobs/saved` | Bookmark interesting positions | candidate |
| **Applications** | `/jobs/applications` | Track application status | candidate |
| **Profile** | `/profile` | Manage candidate profile | candidate |
| **Resume** | `/jobs/upload` | Upload resume/CV | candidate |
| **Recommendations** | `/jobs/recommended` | AI-matched jobs | vacancy, analytics |
| **Assessment** | `/jobs/assessment` | Skill evaluation | analytics |
| **Learning** | `/jobs/learning` | Training resources | - |
| **Salary Calculator** | `/jobs/salary` | Compensation estimation | - |
| **Interview Tips** | `/jobs/tips` | Interview preparation | - |
| **Job Alerts** | `/jobs/alerts` | Email notifications | candidate |

### Error Handling

- **Microservice Down**: ServiceErrorFallback component with retry option
- **Network Timeout**: Loading indicator with timeout message
- **Invalid Route**: Redirect to `/jobs`
- **Auth Token Expired**: Silent refresh, continue to destination

---

## Recruiter Journey

### Overview

Recruiters manage job postings, review candidates, and make hiring decisions. All Recruiter routes require authentication (Recruiter or Admin role).

### Navigation Structure

```
RecruiterLayout (/recruiter/*)
├── Dashboard
├── Hiring Section
│   ├── Vacancies
│   ├── Candidates
│   ├── Pipeline (Kanban)
│   └── Applications
├── Resumes Section
│   ├── Database
│   ├── Upload
│   └── Batch Upload
├── Search Section
│   ├── Candidate Search
│   ├── Saved Searches
│   └── Compare
├── Analytics Section
│   ├── Overview
│   └── Skill Gap Analysis
└── Settings Section
    ├── Weights
    ├── Backups
    └── Workflow
```

### Complete User Flow

```
1. Login (KeyCloak) ← AUTH REQUIRED
   ↓ [Authenticated as Recruiter]
2. Dashboard (/recruiter/dashboard)
   ↓ [Select "Create Vacancy"]
3. Create Vacancy (/recruiter/vacancies/create)
   ↓ [Publish]
4. Vacancies List (/recruiter/vacancies)
   ↓ [View Applications]
5. Candidates Kanban (/recruiter/candidates)
   ↓ [Review Candidate]
6. Candidate Detail (/recruiter/candidates/:id)
   ↓ [Compare]
7. Compare Candidates (/recruiter/compare)
```

### Key Features

| Feature | Route | Description | Service |
|---------|-------|-------------|---------|
| **Dashboard** | `/recruiter/dashboard` | Overview of hiring metrics | analytics |
| **Vacancies** | `/recruiter/vacancies` | Manage job postings | vacancy |
| **Create Vacancy** | `/recruiter/vacancies/create` | Post new job | vacancy |
| **Edit Vacancy** | `/recruiter/vacancies/:id/edit` | Update job details | vacancy |
| **Candidates Kanban** | `/recruiter/candidates` | Pipeline visualization | candidate |
| **Candidate Detail** | `/recruiter/candidates/:id` | Full candidate profile | candidate |
| **Search** | `/recruiter/search` | Find candidates | candidate |
| **Saved Searches** | `/recruiter/saved-searches` | Reuse search queries | candidate |
| **Compare** | `/recruiter/compare` | Compare candidates | candidate |
| **Applications** | `/recruiter/applications` | All applications | candidate, vacancy |
| **Resume Database** | `/recruiter/resumes` | Resume repository | candidate |
| **Upload** | `/recruiter/upload` | Single resume upload | candidate |
| **Batch Upload** | `/recruiter/batch-upload` | Bulk resume upload | candidate |
| **Skill Gap** | `/recruiter/skill-gap` | Analysis tool | analytics |
| **Backups** | `/recruiter/backups` | Data backups | vacancy |
| **Workflow** | `/recruiter/workflow` | Pipeline configuration | candidate |
| **Weights** | `/recruiter/weights` | Matching weights | analytics |
| **Analytics** | `/recruiter/analytics` | Hiring analytics | analytics |

### Error Handling

- **Microservice Down**: ServiceErrorFallback component with retry option
- **Network Timeout**: Loading indicator with timeout message
- **Invalid Route**: Redirect to `/recruiter/dashboard`
- **Auth Token Expired**: Silent refresh, continue to destination
- **Permission Denied**: Redirect to authorized section, show message

---

## Admin Journey

### Overview

Administrators have superuser privileges with access to all routes. They can manage users, configure system settings, and view audit logs. All Admin routes require Admin role.

### Navigation Structure

```
AdminLayout (/admin/*)
├── Dashboard
├── System Section
│   ├── System Health
│   └── Active Sessions
├── User Management Section
│   ├── Users
│   └── Roles
├── Content Section
│   ├── Vacancies
│   ├── Resumes
│   └── Skills
├── Reports Section
│   └── Analytics
└── Configuration Section
    ├── General Settings
    ├── AI/ML Settings
    ├── Notifications
    └── Security
```

### Complete User Flow

```
1. Login (KeyCloak) ← AUTH REQUIRED (Admin)
   ↓ [Authenticated as Admin]
2. Admin Dashboard (/admin/dashboard)
   ↓ [Select "Users"]
3. User Management (/admin/users)
   ↓ [Edit User]
4. User Detail
   ↓ [Access Recruiter Routes]
5. Recruiter Dashboard (/recruiter/dashboard)
   ↓ [View JobSeeker Data]
6. Browse Jobs (/jobs) - Read-only
```

### Key Features

| Feature | Route | Description | Service |
|---------|-------|-------------|---------|
| **Dashboard** | `/admin/dashboard` | System overview | analytics |
| **Users** | `/admin/users` | User management | integration |
| **Settings** | `/admin/settings` | System configuration | integration |
| **Audit Logs** | `/admin/audit-logs` | System audit trail | analytics |

### Elevated Access

As an Admin, you have:

1. **Full Admin Access**: All `/admin/*` routes
2. **Recruiter Access**: All `/recruiter/*` routes with full permissions
3. **JobSeeker Read-Only**: All `/jobs/*` and `/profile` routes in read-only mode

### Error Handling

- **Microservice Down**: ServiceErrorFallback component with retry option
- **Network Timeout**: Loading indicator with timeout message
- **Invalid Route**: Redirect to `/admin/dashboard`
- **Auth Token Expired**: Silent refresh, continue to destination
- **Permission Denied**: Redirect to `/admin/dashboard`, show message

---

## Authentication & Authorization

### Auth Toggle System

The application supports a feature flag to enable/disable authentication:

```bash
# Disable Auth (Development Mode)
VITE_AUTH_ENABLED=false
VITE_MOCK_ROLE=Admin  # Mock role for testing

# Enable Auth (Production Mode)
VITE_AUTH_ENABLED=true
```

### Role-Based Access Control

Roles are checked using the `useRoles` hook:

```typescript
import { useRoles } from '@/hooks/useRoles';

function MyComponent() {
  const { hasRole, hasAnyRole } = useRoles();

  if (hasRole('Admin')) {
    return <AdminOnlyContent />;
  }

  if (hasAnyRole(['Recruiter', 'Admin'])) {
    return <RecruiterContent />;
  }

  return <PublicContent />;
}
```

### Protected Routes

Routes are protected using the `ProtectedRoute` component:

```tsx
<Route
  path="/admin/dashboard"
  element={
    <ProtectedRoute requiredRoles={['Admin']}>
      <AdminDashboard />
    </ProtectedRoute>
  }
/>
```

### Role Hierarchy

```
Admin (Level 3)
  ├─ Can access all Admin routes
  ├─ Can access all Recruiter routes
  └─ Can read JobSeeker routes

Recruiter (Level 2)
  ├─ Can access all Recruiter routes
  └─ Cannot access Admin routes

JobSeeker (Level 1)
  ├─ Can access all JobSeeker routes
  └─ Cannot access Recruiter or Admin routes
```

---

## Error Handling & Resilience

### Error Boundaries

Each user flow has its own ErrorBoundary:

```
App.tsx
├── ErrorBoundary (JobSeeker Flow)
├── ErrorBoundary (Recruiter Flow)
└── ErrorBoundary (Admin Flow)
```

This ensures that errors in one flow don't affect other flows.

### Service Degradation

When a microservice is unavailable:

1. **Detection**: API client detects timeout/error
2. **Fallback**: ServiceErrorFallback component displays
3. **Retry**: User can retry the request
4. **Isolation**: Other routes remain functional

### Navigation Failure Handling

| Scenario | Behavior |
|----------|----------|
| Microservice down | Error UI with retry option |
| Network timeout | Loading → timeout message → retry |
| Invalid route | Redirect to role-appropriate landing |
| Token expired | Silent refresh → continue |
| Permission denied | Redirect + message |

---

## Microservices Integration

### API Gateway

All microservices are accessed via the API gateway:

```
Frontend → API Gateway (Port 5888) → Microservices
```

### Service Endpoints

| Service | Purpose | Endpoints |
|---------|---------|-----------|
| **candidate** | Candidate profile and applications | `/candidates/*` |
| **vacancy** | Job postings and vacancies | `/vacancies/*` |
| **analytics** | Analytics and reporting | `/analytics/*` |
| **integration** | API gateway | `/api/*` |

### API Client

The application uses a centralized API client (`frontend/src/api/client.ts`) with:

- Automatic retry on failure
- Timeout handling (120s default)
- Error categorization (network, timeout, server)
- Request/response logging (debug mode)

---

## Development Testing

### Mock Mode (Auth Disabled)

When `VITE_AUTH_ENABLED=false`:

1. No login required
2. Mock role from `VITE_MOCK_ROLE` is used
3. All routes accessible based on mock role
4. Useful for UI testing without KeyCloak

### Testing Different Roles

```bash
# Test as JobSeeker
VITE_AUTH_ENABLED=false
VITE_MOCK_ROLE=JobSeeker

# Test as Recruiter
VITE_AUTH_ENABLED=false
VITE_MOCK_ROLE=Recruiter

# Test as Admin
VITE_AUTH_ENABLED=false
VITE_MOCK_ROLE=Admin
```

---

## Route Summary

### Public Routes (No Auth Required)

- `/` - Landing Page
- `/jobs` - Browse Jobs
- `/jobs/:id` - Job Detail
- `/jobs/learning` - Learning Resources
- `/jobs/salary` - Salary Calculator
- `/jobs/tips` - Interview Tips

### Protected Routes (Auth Required)

**JobSeeker:**
- `/jobs/:id/apply` - Apply for Job
- `/jobs/saved` - Saved Jobs
- `/jobs/applications` - My Applications
- `/profile` - Candidate Profile
- `/jobs/upload` - Resume Upload
- `/jobs/resume-results/:id` - Resume Results
- `/jobs/recommended` - Recommended Jobs
- `/jobs/assessment` - Skill Assessment
- `/jobs/alerts` - Job Alerts
- `/jobs/settings` - Settings

**Recruiter (Recruiter or Admin role):**
- `/recruiter/*` - All Recruiter routes

**Admin (Admin role only):**
- `/admin/dashboard` - Admin Dashboard
- `/admin/users` - User Management
- `/admin/settings` - System Settings
- `/admin/audit-logs` - Audit Logs

---

## Accessibility

### Keyboard Navigation

- **Skip Links**: Each layout has a "Skip to main content" link
- **Focus Indicators**: Visible focus states on all interactive elements
- **ARIA Labels**: Proper ARIA attributes on navigation and controls
- **Keyboard Shortcuts**: All features accessible via keyboard

### Screen Reader Support

- Semantic HTML (`<nav>`, `<main>`, `<header>`)
- ARIA roles (`menubar`, `menuitem`, `navigation`)
- aria-current for active routes
- aria-expanded for collapsible sections

---

## Mobile Responsiveness

### JobSeeker Layout

- Desktop: 280px sidebar + main content
- Mobile: Bottom navigation bar + hamburger menu

### Recruiter Layout

- Desktop: 280px sidebar + main content
- Mobile: Temporary drawer + hamburger menu

### Admin Layout

- Desktop: 280px sidebar + main content
- Mobile: Temporary drawer + hamburger menu

---

## Future Enhancements

### Planned Features

1. **Admin Role Impersonation**: Admins can view as other roles
2. **Organization Management**: Multi-tenant support
3. **Advanced Analytics**: More reporting options
4. **Notifications**: Real-time alerts
5. **Offline Support**: PWA capabilities

### Routes Not Yet Implemented

The following routes appear in the AdminLayout navigation but don't have pages yet:

- `/admin/system-health` - System Health
- `/admin/sessions` - Active Sessions
- `/admin/roles` - Role Management
- `/admin/vacancies` - Admin Vacancy Management
- `/admin/resumes` - Admin Resume Management
- `/admin/skills` - Skills Database
- `/admin/analytics` - Admin Analytics
- `/admin/ai-settings` - AI/ML Configuration
- `/admin/notifications` - Notification Settings
- `/admin/security` - Security Settings

---

## Related Documentation

- [Feature Flags Configuration](../frontend/src/config/features.ts)
- [useRoles Hook Documentation](../frontend/src/hooks/useRoles.ts)
- [ProtectedRoute Component](../frontend/src/components/ProtectedRoute.tsx)
- [API Client](../frontend/src/api/client.ts)
- [Specification](../.auto-claude/specs/113-1-customer-journey/spec.md)

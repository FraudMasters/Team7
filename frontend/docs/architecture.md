# Frontend Architecture - AgentHR Dual Flow System

## Overview

The AgentHR frontend application uses React with TypeScript, Material-UI (MUI) as the component library, and React Router for navigation. The application follows a dual-flow architecture serving both job seekers and recruiters with distinct user journeys.

## Tech Stack

- **Framework**: React 18.3.1 with TypeScript 5.6.3
- **Build Tool**: Vite 5.4.10
- **UI Library**: Material-UI (MUI) 6.1.6
- **Routing**: React Router DOM 6.26.2
- **State Management**: React Context API
- **Styling**: Emotion (included with MUI)
- **HTTP Client**: Axios 1.7.7
- **Internationalization**: i18next + react-i18next
- **Testing**: Vitest + Playwright

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   ├── components/       # Reusable UI components
│   │   └── analytics/    # Analytics-specific components
│   ├── contexts/         # React context providers
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components (routes)
│   ├── utils/            # Utility functions
│   ├── data/             # Static data and constants
│   ├── i18n/             # Internationalization configuration
│   ├── types/            # TypeScript type definitions
│   ├── tests/            # Test setup and utilities
│   ├── App.tsx           # Root application component
│   └── main.tsx          # Application entry point
├── docs/                 # Documentation
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Routing Architecture - Dual Flow System

### 1. Shared Routes (`/`)

**Purpose**: Public-facing pages accessible to all users

**Routes**:
- `/` - Role selector landing page (`LandingPage`)
- Role selection between job seeker and recruiter flows
- Authentication pages (login, register, password reset)

**Features**:
- Clear role selection with visual distinction
- Brief explanation of each flow's purpose
- Quick access to public job listings

### 2. Job Seeker Flow (`/jobs/*`)

**Purpose**: Candidates searching and applying for jobs

**Base Path**: `/jobs`

**Routes**:

| Route | Component | Purpose |
|-------|-----------|---------|
| `/jobs` | `JobsBrowsePage` | Browse all job listings |
| `/jobs/search` | `JobsSearchPage` | Advanced job search with filters |
| `/jobs/:id` | `JobDetailPage` | Job detail page |
| `/jobs/:id/apply` | `ApplicationFlowPage` | Application form |
| `/jobs/saved` | `SavedJobsPage` | Saved/bookmarked jobs |
| `/jobs/applications` | `MyApplicationsPage` | My applications tracker |
| `/jobs/upload` | `ResumeUploadPage` | Single resume upload |
| `/jobs/results/:id` | `ResumeResultsPage` | Resume analysis results |
| `/jobs/profile` | `CandidateProfilePage` | Candidate profile management |

**User Journey**:
1. Browse jobs → View job details → Upload/attach resume → Apply → Track applications
2. Upload resume → Get AI analysis → View matched jobs → Apply to opportunities

**Key Features**:
- Resume upload with AI-powered analysis
- Job search with filters (location, salary, skills)
- Application status tracking
- Skill gap analysis and learning recommendations

### 3. Recruiter Flow (`/recruiter/*`)

**Purpose**: Employers managing vacancies and candidates

**Base Path**: `/recruiter`

**Routes**:

| Route | Component | Purpose |
|-------|-----------|---------|
| `/recruiter` | `RecruiterDashboardPage` | Main dashboard overview |
| `/recruiter/vacancies` | `VacanciesPage` | Manage job postings |
| `/recruiter/vacancies/create` | `VacancyFormPage` | Create new vacancy |
| `/recruiter/vacancies/:id` | `VacancyDetailPage` | View vacancy details |
| `/recruiter/candidates` | `CandidatesKanbanPage` | Kanban workflow board |
| `/recruiter/candidates/:id` | `CandidateDetailPage` | Candidate details |
| `/recruiter/analytics` | `AnalyticsPage` | Analytics dashboard |
| `/recruiter/weights` | `WeightsPage` | Customize matching weights |

**User Journey**:
1. Create vacancy → Define requirements → Receive applications → Review candidates → Hire
2. Search resume database → Filter candidates → Compare applicants → Manage pipeline

**Key Features**:
- Vacancy creation with smart suggestions
- AI-powered candidate matching
- Kanban-style workflow management
- Advanced analytics and reporting
- Skill gap analysis

### 4. Admin Routes (`/admin/*`)

**Purpose**: System administration and configuration

**Routes**:

| Route | Component | Purpose |
|-------|-----------|---------|
| `/admin` | Redirect to `/admin/synonyms` | Default admin page |
| `/admin/synonyms` | `AdminSynonymsPage` | Manage skill synonyms |
| `/admin/analytics` | `AdminAnalyticsPage` | System analytics |
| `/admin/taxonomies` | `TaxonomyManagerPage` | Industry taxonomy management |
| `/admin/taxonomy-analytics` | `TaxonomyAnalyticsPage` | Taxonomy analytics |
| `/admin/public-taxonomies` | `PublicTaxonomyBrowser` | Browse public taxonomies |
| `/admin/backups` | `BackupsPage` | System backups |

## Layout Architecture

### JobSeekerLayout

**Purpose**: Mobile-first layout with bottom navigation for job seekers

**Features**:
- Sticky top AppBar with AgentHR logo
- Bottom navigation with 4 items: Search, Saved, Applications, Profile
- Outlet for child routes
- Responsive design optimized for mobile

**Navigation Items**:
- `/jobs` - Search (SearchIcon)
- `/jobs/saved` - Saved (BookmarkIcon)
- `/jobs/applications` - Applications (DescriptionIcon)
- `/profile` - Profile (PersonIcon)

### RecruiterLayout

**Purpose**: Desktop-optimized sidebar layout for recruiters

**Features**:
- Sidebar with 280px width containing AgentHR logo
- Navigation items: Dashboard, Vacancies, Candidates, Analytics
- Top AppBar with hamburger menu on mobile
- Outlet for child routes
- Responsive: collapses to drawer on mobile

**Navigation Items**:
- `/recruiter/dashboard` - Dashboard (DashboardIcon)
- `/recruiter/vacancies` - Vacancies (WorkIcon)
- `/recruiter/candidates` - Candidates (PeopleIcon)
- `/recruiter/analytics` - Analytics (BarChartIcon)

## State Management

### Context Providers

The application uses React Context for global state:

1. **ThemeProvider** (`/Users/fraud/Projects/agenthr/frontend/src/contexts/ThemeContext.tsx`)
   - Theme mode (light/dark)
   - Theme persistence
   - Theme switching functions

2. **LanguageProvider** (`/Users/fraud/Projects/agenthr/frontend/src/contexts/LanguageContext.tsx`)
   - Current language (en/ru)
   - Language switching
   - Locale-aware formatting

### Local State
- Component-level state with `useState`
- Derived state with `useMemo`
- Side effects with `useEffect`

### Server State (Planned)
- React Query for API caching and synchronization
- Automatic refetching and invalidation
- Optimistic updates

## API Integration

### API Client Configuration

**Base Configuration** (`vite.config.ts`):
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

### API Structure

**Directory**: `/Users/fraud/Projects/agenthr/frontend/src/api/`

Key API modules:
- `client.ts` - Axios client configuration
- `preferences.ts` - User preferences
- `skillGap.ts` - Skill gap analysis
- `taxonomies.ts` - Industry taxonomies
- `workflowStages.ts` - Workflow stage management

## Internationalization

### Supported Languages
- English (`en`)
- Russian (`ru`)

### i18n Configuration

**Directory**: `/Users/fraud/Projects/agenthr/frontend/src/i18n/`

**Usage**:
```tsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();
<t>{'nav.browseJobs'}</t>
```

## Performance Optimization

### Code Splitting

**Vite Configuration** (`vite.config.ts`):
```typescript
manualChunks: (id) => {
  if (id.includes('react')) return 'react-vendor';
  if (id.includes('@mui')) return 'mui-vendor';
  if (id.includes('axios')) return 'api-vendor';
}
```

**Chunks**:
- `react-vendor` - React core
- `mui-vendor` - Material UI
- `api-vendor` - API clients

### Lazy Loading

Routes can be lazy-loaded for better initial load time:
```tsx
const JobDetailPage = lazy(() => import('./pages/jobs/JobDetailPage'));
```

## Accessibility

### Keyboard Navigation

**Custom Hook**: `/Users/fraud/Projects/agenthr/frontend/src/hooks/useKeyboardNavigation.ts`

**Shortcuts**:
- Documented in `keyboardShortcuts.ts`
- Help dialog with `KeyboardShortcutsHelp` component

### Screen Reader Support
- Semantic HTML
- ARIA labels where needed
- Focus management
- Error announcements

## Build and Deployment

### Build Process

**Command**: `npm run build`
**Output**: `dist/` directory

## Related Files

- `/Users/fraud/Projects/agenthr/frontend/src/App.tsx` - Route definitions
- `/Users/fraud/Projects/agenthr/frontend/src/main.tsx` - App initialization
- `/Users/fraud/Projects/agenthr/frontend/src/components/Layout.tsx` - Layout component
- `/Users/fraud/Projects/agenthr/frontend/vite.config.ts` - Build configuration
- `/Users/fraud/Projects/agenthr/frontend/package.json` - Dependencies

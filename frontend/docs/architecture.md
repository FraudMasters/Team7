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
- **Backend Integration**: API Gateway (port 8888) → 10 Microservices

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

## Page Documentation

### Job Seeker Pages

#### SavedJobsPage

**Route**: `/jobs/saved`

**Purpose**: Allows candidates to bookmark and manage jobs they're interested in

**Key Features**:
- Save/unsave jobs with bookmark icon
- List view of all saved jobs
- Quick access to job details
- Filter and sort saved jobs
- Persistent storage across sessions

**Components**:
- Job card grid/list
- Bookmark toggle buttons
- Empty state with call-to-action
- Filter controls (by date, company, location)

**State Management**:
- Local storage for persistence
- API integration to sync saved jobs
- Real-time bookmark updates

#### MyApplicationsPage

**Route**: `/jobs/applications`

**Purpose**: Track all job applications and their status

**Key Features**:
- View all submitted applications
- Track application status (submitted, under review, rejected, offered)
- Application timeline and history
- Quick access to application details
- Filter by status, date, or company

**Components**:
- Application list with status badges
- Status filter chips
- Application detail cards
- Empty state for no applications
- Timeline view for each application

**State Management**:
- API integration for application data
- Real-time status updates
- Local caching for performance

#### CandidateProfilePage

**Route**: `/jobs/profile`

**Purpose**: Manage candidate profile and resume information

**Key Features**:
- Edit personal information
- Upload and manage resumes
- View profile completion status
- Skills and experience management
- Preferences and settings

**Components**:
- Profile form with validation
- Resume upload section
- Skills tags input
- Experience timeline
- Education history
- Profile completeness indicator

**State Management**:
- Form state management
- API integration for profile updates
- Optimistic updates for better UX

### Recruiter Pages

#### VacancyDetailPage

**Route**: `/recruiter/vacancies/:id`

**Purpose**: View detailed information about a specific vacancy

**Key Features**:
- Complete vacancy information display
- Application statistics
- Candidate list for this vacancy
- Edit vacancy details
- View matching candidates
- Application management actions

**Components**:
- Vacancy header with actions
- Job description section
- Requirements display
- Application metrics cards
- Candidates list (filtered for this vacancy)
- Edit/delete actions
- Status management

**State Management**:
- Route parameter for vacancy ID
- API integration for vacancy data
- Real-time candidate list updates

#### CandidateDetailPage

**Route**: `/recruiter/candidates/:id`

**Purpose**: View detailed candidate profile and application information

**Key Features**:
- Complete candidate profile
- Resume viewer
- Application history
- Skill assessment
- Match scores for vacancies
- Notes and comments
- Status change actions

**Components**:
- Candidate header with profile picture
- Contact information
- Resume preview/download
- Skills and experience sections
- Application history timeline
- Match score indicators
- Notes section
- Status change buttons
- Activity log

**State Management**:
- Route parameter for candidate ID
- API integration for candidate data
- Real-time status updates
- Notes persistence

#### WeightsPage

**Route**: `/recruiter/weights`

**Purpose**: Customize matching algorithm weights for candidate-vacancy matching

**Key Features**:
- Adjust importance weights for different criteria
- Preview impact of weight changes
- Save custom weight profiles
- Reset to defaults
- Real-time matching score preview

**Components**:
- Weight sliders for each criterion:
  - Skills match
  - Experience relevance
  - Education level
  - Location proximity
  - Salary expectations
  - Industry fit
- Weight profile selector
- Preview section with sample matches
- Save/Reset buttons
- Validation indicators

**State Management**:
- Form state for weight values
- API integration for saving profiles
- Local storage for drafts
- Real-time preview calculations

**Weight Categories**:
1. **Skills Match** (0-100): Importance of skill alignment
2. **Experience** (0-100): Relevance of work experience
3. **Education** (0-100): Importance of educational background
4. **Location** (0-100): Preference for local candidates
5. **Salary** (0-100): Alignment on salary expectations
6. **Industry** (0-100): Industry experience importance

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

### Microservices Architecture

The frontend communicates with the backend through a unified **API Gateway** that routes requests to 10 specialized microservices:

| Service | Internal Port | Purpose |
|---------|---------------|---------|
| API Gateway | 8888 | Single entry point, routing, authentication |
| Resume Processing | 8001 | Resume upload, parsing, analysis |
| Matching | 8002 | Skill matching, candidate ranking |
| Candidate | 8003 | Candidate CRUD, notes, tags, activities |
| Vacancy | 8004 | Job vacancy management |
| Taxonomy | 8005 | Skill taxonomies, synonyms |
| Analytics | 8006 | Dashboards, reports, metrics |
| ATS Simulation | 8007 | ATS scoring, screening |
| Notification | 8008 | Email, SMS, webhook notifications |
| Integration | 8009 | Third-party integrations |

**Important:** The frontend only needs to know the API Gateway URL (`http://localhost:8888`). Individual service URLs are abstracted away.

### API Client Configuration

**Base Configuration** (`vite.config.ts`):
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8888',  // API Gateway
    changeOrigin: true,
  }
}
```

**Environment Variables:**
```bash
# .env
VITE_API_URL=http://localhost:8888
VITE_API_TIMEOUT=120000  # 2 minutes for long-running analysis
```

### API Structure

**Directory**: `/Users/fraud/Projects/agenthr/frontend/src/api/`

Key API modules:
- `client.ts` - Main Axios client with typed methods for all endpoints
- `candidateActivities.ts` - Candidate activity tracking
- `candidateNotes.ts` - Candidate notes management
- `candidateTags.ts` - Candidate tagging
- `fairness.ts` - Fairness metrics and bias detection
- `industryClassifier.ts` - Industry classification
- `preferences.ts` - User preferences
- `savedSearches.ts` - Saved search management
- `search.ts` - Advanced search functionality
- `searchHistory.ts` - Search history tracking
- `skillGap.ts` - Skill gap analysis
- `skillSuggestions.ts` - AI-powered skill suggestions
- `taxonomies.ts` - Industry taxonomies
- `workflowStages.ts` - Workflow stage management

**Note:** For complete API integration documentation including error handling, authentication, and usage examples, see [api-integration.md](api-integration.md).

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

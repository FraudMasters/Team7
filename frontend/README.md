# AgentHR Frontend

AI-powered recruitment platform frontend built with React 18, Vite, TypeScript, and a lightweight custom component library.

> **Current Status:** ~40% of backend API implemented. See [BACKLOG.md](BACKLOG.md) for missing features and [docs/ROADMAP.md](docs/ROADMAP.md) for implementation plan.
>
> **Recent Migration:** Successfully migrated from Material-UI to custom Emotion CSS-in-JS components, reducing bundle size by ~47%. See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details.

## Tech Stack

- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **UI Library**: Custom components with Emotion CSS-in-JS
- **Icons**: lucide-react (lightweight, tree-shakeable)
- **Routing**: React Router v6
- **State Management**: TanStack React Query v5
- **Animations**: Framer Motion v11
- **HTTP Client**: Axios
- **Drag & Drop**: @hello-pangea/dnd
- **i18n**: react-i18next
- **Testing**: Vitest + React Testing Library + Playwright (E2E)
- **Code Quality**: ESLint, Prettier

## Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0
- Docker & Docker Compose (for full stack)

## Quick Start

### Development (Docker - Recommended)

```bash
# Start backend and frontend together
docker-compose up

# Frontend available at http://localhost:3000
# Backend API available at http://localhost:8000
```

### Development (Local)

```bash
cd frontend
npm install
npm run dev

# Application at http://localhost:5173
# API proxy to http://localhost:8000
```

## Available Scripts

### Development
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

### Unit Tests
- `npm run test` - Run unit tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage report

### E2E Tests
- `npm run test:e2e` - Run end-to-end tests
- `npm run test:e2e:ui` - Run E2E tests in UI mode
- `npm run test:e2e:debug` - Debug E2E tests
- `npm run test:e2e:install` - Install Playwright browsers

### Code Quality
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoint methods
│   ├── components/       # React components
│   │   ├── analytics/    # Analytics dashboard components
│   │   ├── dashboard/    # Dashboard bento cards
│   │   ├── jobs/         # Job seeker components
│   │   ├── kanban/       # Drag-and-drop kanban board
│   │   ├── resume/       # Resume upload and display
│   │   └── ui/           # Custom UI component library
│   │       ├── primitives/   # Box, Typography, Container, Icon
│   │       ├── interactive/ # Button, IconButton, ButtonGroup
│   │       ├── forms/        # TextField, Select, Checkbox, etc.
│   │       ├── layout/       # Grid, Stack, Container
│   │       ├── navigation/   # AppBar, Drawer, Menu, Tabs
│   │       ├── feedback/     # Alert, Snackbar, Progress
│   │       ├── overlays/     # Dialog, Modal, Popover, Tooltip
│   │       └── data-display/ # Table, Chip, Badge, Avatar, List
│   ├── contexts/         # React contexts (EmotionTheme)
│   ├── hooks/            # Custom React hooks
│   ├── layouts/          # Page layouts
│   ├── pages/            # Route pages
│   │   ├── jobs/         # Job seeker pages
│   │   └── recruiter/    # Recruiter pages
│   ├── providers/        # React providers (ThemeProvider)
│   ├── styles/           # Design tokens and global styles
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Root application component
│   └── main.tsx          # Application entry point
├── docs/                 # Documentation
│   ├── ROADMAP.md        # Development roadmap
│   ├── TASKS.md          # Task breakdown for Kanban
│   ├── components.md     # Component documentation
│   ├── architecture.md   # Architecture documentation
│   ├── design-system.md  # Design tokens and guidelines
│   └── build-verification.md # Production checklist
├── e2e/                  # End-to-end tests
├── BACKLOG.md            # Missing frontend features
├── MIGRATION_GUIDE.md    # MUI → Emotion migration guide
├── public/               # Static assets
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Application Title
VITE_APP_TITLE=AgentHR
```

### API Proxy (Development)

The Vite dev server proxies API requests:
- `/api/*` → `http://localhost:8000/api/*`
- `/health` → `http://localhost:8000/health`

## Features

### Implemented ✅

**Job Seeker:**
- Browse and search vacancies
- View job details
- Apply with resume upload
- Track application status

**Recruiter:**
- Dashboard with key metrics
- Kanban board for candidates
- Vacancy management (CRUD)
- Resume analysis with AI
- Matching candidates to vacancies
- Analytics (key metrics, skill demand)
- Dark mode support

**General:**
- Responsive design (mobile + desktop)
- Accessible (WCAG 2.1 AA)
- Internationalization (EN, RU)
- Smooth animations (Framer Motion)

### Not Implemented ❌

See [BACKLOG.md](BACKLOG.md) for full list:
- Search module
- Saved searches
- Candidate tags
- Candidate notes
- Reports download
- Ranking comparison
- Skill gap analysis
- And 10+ more modules

## Documentation

| Document | Description |
|----------|-------------|
| [BACKLOG.md](BACKLOG.md) | Missing features by priority |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Complete guide for MUI → Emotion migration |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phased implementation plan |
| [docs/TASKS.md](docs/TASKS.md) | Task breakdown for Kanban import |
| [docs/components.md](docs/components.md) | Component documentation |
| [docs/architecture.md](docs/architecture.md) | Architecture documentation |
| [docs/design-system.md](docs/design-system.md) | Design tokens and guidelines |
| [docs/build-verification.md](docs/build-verification.md) | Production checklist |
| [ACCESSIBILITY_AUDIT.md](ACCESSIBILITY_AUDIT.md) | WCAG 2.1 AA compliance audit |
| [PERFORMANCE_MEASUREMENT.md](PERFORMANCE_MEASUREMENT.md) | Performance metrics and improvements |
| [TEST_STATUS.md](TEST_STATUS.md) | Test suite status and migration notes |
| [E2E_TEST_STATUS.md](E2E_TEST_STATUS.md) | E2E test status and fixes |

## Architecture

### Dual Flow Design

```
┌─────────────────────────────────────────────────────────────┐
│                          App.tsx                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   JobSeekerLayout       │     │   RecruiterLayout       │
│   (Bottom Navigation)   │     │   (Sidebar)             │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
    ┌─────────┴─────────┐           ┌─────────┴─────────┐
    ▼                   ▼           ▼                   ▼
/Landing            /jobs/*    /recruiter/*        /admin/*
```

### Role-Based Routing

The AgentHR frontend implements a **dual-flow architecture** with role-based routing that provides optimized experiences for different user types:

#### User Roles

```typescript
type UserRole = 'JobSeeker' | 'Recruiter' | 'Admin';
```

- **JobSeeker**: Can browse and apply for jobs without authentication
- **Recruiter**: Can manage vacancies and candidates (requires authentication + role)
- **Admin**: Has full access to all recruiter and admin features

#### Route Protection

**Job Seeker Routes** (`/jobs/*`):
- No authentication required
- Mobile-first design with bottom navigation
- Focus on job discovery and application flow

**Recruiter Routes** (`/recruiter/*`):
- Require `Recruiter` or `Admin` role
- Protected by `ProtectedRoute` component
- Desktop-focused dashboard with sidebar navigation
- Role-based access control using `AuthContext`

**Authentication Routes** (`/auth/*`):
- Shared between both flows
- Login, registration, and OAuth callback

#### ProtectedRoute Component

Recruiter routes are wrapped with `ProtectedRoute` for role-based access control:

```tsx
// Example: Protecting recruiter routes
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

#### Role-Based Redirects

The landing page automatically redirects authenticated users based on their role:

```typescript
// Recruiter or Admin → /recruiter/dashboard
if (hasAnyRole([UserRole.Recruiter, UserRole.Admin])) {
  navigate('/recruiter/dashboard');
}
// Everyone else → /jobs
else if (isAuthenticated) {
  navigate('/jobs');
}
```

#### Checking User Roles in Components

```tsx
import { useAuthContext, UserRole } from '@/contexts/AuthContext';

const MyComponent = () => {
  const { user, hasRole, hasAnyRole, isAuthenticated } = useAuthContext();

  // Check if user has specific role
  if (hasRole(UserRole.Admin)) {
    return <AdminPanel />;
  }

  // Check if user has any of the specified roles
  if (hasAnyRole([UserRole.Recruiter, UserRole.Admin])) {
    return <RecruiterFeatures />;
  }

  return <JobSeekerView />;
};
```

#### Layout Differences

| Feature | JobSeekerLayout | RecruiterLayout |
|---------|----------------|-----------------|
| **Primary Navigation** | Bottom nav (mobile) + Sidebar (desktop) | Sidebar only |
| **Design Focus** | Mobile-first, discovery | Desktop-first, dashboard |
| **Target Device** | Responsive, mobile-optimized | Desktop-optimized |
| **Sections** | Jobs, Career, Account | Hiring, Resumes, Search, Analytics, Settings |
| **Authentication** | Optional | Required |
| **Protected** | No | Yes (Recruiter/Admin roles) |

For detailed architecture documentation, see [DUAL_FLOW_ARCHITECTURE.md](DUAL_FLOW_ARCHITECTURE.md).

### Data Fetching Pattern

All components use TanStack React Query for server state:

```tsx
import { useQuery } from '@tanstack/react-query';

function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['resource'],
    queryFn: async () => {
      const response = await apiClient.get('/resource');
      return response.data;
    },
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  return <div>{data}</div>;
}
```

## Component Library

The application uses a custom component library built with Emotion CSS-in-JS, replacing Material-UI for better performance and smaller bundle size.

### Key Features

- **Lightweight**: ~35 KB vs MUI's 450 KB (92% reduction)
- **Type-safe**: Full TypeScript support with comprehensive interfaces
- **Accessible**: WCAG 2.1 AA compliant with ARIA attributes and keyboard navigation
- **Themeable**: Design tokens with light/dark mode support
- **58 Components**: Complete UI component coverage across 8 categories

### Component Categories

| Category | Components | Examples |
|----------|-----------|----------|
| **Primitives** | 4 | Box, Typography, Container, Icon |
| **Interactive** | 3 | Button, IconButton, ButtonGroup |
| **Forms** | 8 | TextField, Select, Checkbox, Radio, Switch, Slider, TextArea, Autocomplete |
| **Layout** | 2 | Grid, Stack |
| **Navigation** | 7 | AppBar, Toolbar, Drawer, Menu, Breadcrumbs, Tabs, Pagination |
| **Feedback** | 5 | Alert, Snackbar, CircularProgress, LinearProgress, Skeleton |
| **Overlays** | 4 | Dialog, Modal, Popover, Tooltip |
| **Data Display** | 8 | Table, Chip, Badge, Avatar, Divider, List, Accordion, Collapse |

### Using Components

```tsx
import { Button, TextField, Card, CardContent } from '@/components/ui';

function MyForm() {
  return (
    <Card>
      <CardContent>
        <TextField label="Name" fullWidth />
        <Button variant="contained" color="primary">
          Submit
        </Button>
      </CardContent>
    </Card>
  );
}
```

### Theme Customization

```tsx
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';

function MyComponent() {
  const theme = useEmotionTheme();
  return <div style={{ color: theme.colors.primary }}>Themed content</div>;
}
```

### Migration from MUI

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for:
- Complete component mapping (MUI → Emotion)
- Icon migration guide (@mui/icons-material → lucide-react)
- Before/after code examples
- Breaking changes and solutions
- Automated migration script

## Routes

### Job Seeker Routes
| Route | Component | Description |
|-------|-----------|-------------|
| `/` | LandingPage | Landing page with CTA |
| `/jobs` | JobsBrowsePage | Browse and filter jobs |
| `/jobs/:id` | JobDetailPage | View job details |
| `/jobs/:id/apply` | ApplicationFlowPage | Apply with resume |
| `/upload` | ResumeUploadPage | Upload resume |

### Recruiter Routes
| Route | Component | Description |
|-------|-----------|-------------|
| `/recruiter/dashboard` | DashboardPage | Key metrics and bento cards |
| `/recruiter/candidates` | CandidatesKanbanPage | Kanban board for candidates |
| `/recruiter/vacancies` | VacanciesPage | List and manage vacancies |
| `/recruiter/vacancies/create` | VacancyFormPage | Create new vacancy |
| `/recruiter/vacancies/:id/edit` | VacancyFormPage | Edit vacancy |
| `/recruiter/analytics` | AnalyticsDashboardPage | Metrics and charts |
| `/recruiter/matching` | MatchingPage | Candidate-vacancy matching |
| `/recruiter/settings` | SettingsPage | User settings |

## Building for Production

```bash
npm run build
```

Output in `dist/` directory. For Docker deployment:

```bash
docker-compose build frontend
docker-compose up -d frontend
```

## Known Issues

1. **Analytics endpoints**: Funnel, recruiter performance, and source tracking are disabled due to missing PostgreSQL Enum types in backend database. See backend migration required in [BACKLOG.md](BACKLOG.md#database-considerations).

2. **Test suite updates**: Some test files still reference MUI class names and need updates. See [TEST_STATUS.md](TEST_STATUS.md) for details and [E2E_TEST_STATUS.md](E2E_TEST_STATUS.md) for E2E test updates needed.

3. **Bundle verification**: Manual browser testing and Lighthouse audits needed to verify performance improvements. See [PERFORMANCE_MEASUREMENT.md](PERFORMANCE_MEASUREMENT.md) for testing checklist.

## Contributing

1. Check [docs/TASKS.md](docs/TASKS.md) for available tasks
2. Use existing components from `@/components/ui` instead of creating new ones
3. Follow the [design system](docs/design-system.md) for styling consistency
4. Add TypeScript types to `src/types/api.ts`
5. Create custom hooks in `src/hooks/`
6. Write tests for new features (Vitest for unit, Playwright for E2E)
7. Ensure accessibility (ARIA labels, keyboard nav) - see [ACCESSIBILITY_AUDIT.md](ACCESSIBILITY_AUDIT.md)
8. Use `useEmotionTheme()` hook for theme access instead of direct values

### Adding New Components

When adding new UI components:
1. Place in appropriate `src/components/ui/` category
2. Use Emotion's `styled` API with `useEmotionTheme` hook
3. Follow TypeScript best practices with comprehensive interfaces
4. Add comprehensive JSDoc with examples
5. Create test file with `*.test.tsx` suffix
6. Export from `src/components/ui/index.ts`
7. Update [docs/components.md](docs/components.md)

## License

MIT

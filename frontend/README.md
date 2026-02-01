# AgentHR Frontend

AI-powered recruitment platform frontend built with React 18, Vite, TypeScript, and Material-UI.

> **Current Status:** ~40% of backend API implemented. See [BACKLOG.md](BACKLOG.md) for missing features and [docs/ROADMAP.md](docs/ROADMAP.md) for implementation plan.

## Tech Stack

- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **UI Library**: Material-UI (MUI) v6.1 with Emotion
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
│   │   └── ui/           # Reusable UI components
│   ├── contexts/         # React contexts (theme, etc.)
│   ├── hooks/            # Custom React hooks
│   ├── layouts/          # Page layouts
│   ├── pages/            # Route pages
│   │   ├── jobs/         # Job seeker pages
│   │   └── recruiter/    # Recruiter pages
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Root application component
│   └── main.tsx          # Application entry point
├── docs/                 # Documentation
│   ├── ROADMAP.md        # Development roadmap
│   ├── TASKS.md          # Task breakdown for Kanban
│   ├── components.md     # Component documentation
│   ├── migration-guide.md # Old → New architecture guide
│   └── build-verification.md # Production checklist
├── e2e/                  # End-to-end tests
├── BACKLOG.md            # Missing frontend features
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
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phased implementation plan |
| [docs/TASKS.md](docs/TASKS.md) | Task breakdown for Kanban import |
| [docs/components.md](docs/components.md) | Component documentation |
| [docs/migration-guide.md](docs/migration-guide.md) | Old → New architecture |
| [docs/build-verification.md](docs/build-verification.md) | Production checklist |

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

2. **Circular dependencies**: Fixed by using object-based manualChunks in vite.config.ts (framer-motion bundled with MUI).

## Contributing

1. Check [docs/TASKS.md](docs/TASKS.md) for available tasks
2. Follow existing component patterns in `src/components/`
3. Add TypeScript types to `src/types/api.ts`
4. Create custom hooks in `src/hooks/`
5. Write tests for new features
6. Ensure accessibility (ARIA labels, keyboard nav)

## License

MIT

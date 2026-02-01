# Migration Guide: Old Frontend → New Dual-Flow Architecture

AgentHR Frontend - Resume Analysis Platform

---

## Table of Contents

1. [Overview of Changes](#overview-of-changes)
2. [New Directory Structure](#new-directory-structure)
3. [Migrating Pages](#migrating-pages)
4. [Using New Hooks](#using-new-hooks)
5. [Component Migration](#component-migration)
6. [Breaking Changes](#breaking-changes)

---

## Overview of Changes

### Architecture Changes

| Old Approach | New Approach |
|--------------|--------------|
| Single layout for all users | Dual flow: JobSeekerLayout + RecruiterLayout |
| Class components | Functional components with hooks |
| Custom fetch logic | TanStack React Query for data fetching |
| Inline styles | MUI theme + sx props |
| No animations | Framer Motion for transitions |

### Key New Features

- **Dual Flow Architecture**: Separate layouts and navigation for job seekers and recruiters
- **Responsive Design**: Mobile-first approach with breakpoint hooks
- **Accessibility**: WCAG 2.1 AA compliance with ARIA labels, skip links
- **2026 Design Trends**: Bento grids, variable fonts, soft gradients

---

## New Directory Structure

```
src/
├── components/
│   ├── dashboard/       # Dashboard-specific components
│   │   └── BentoCard.tsx
│   ├── jobs/            # Job seeker components
│   │   └── JobCard.tsx
│   ├── kanban/          # Drag-and-drop components
│   │   └── KanbanBoard.tsx
│   ├── resume/          # Resume-related components
│   │   └── ResumeUpload.tsx
│   └── ui/              # Reusable UI components
│       ├── AnimatedButton.tsx
│       ├── ErrorState.tsx
│       ├── LoadingState.tsx
│       └── PageTransition.tsx
├── hooks/
│   ├── useBreakpoint.ts
│   ├── useJobs.ts
│   └── useRecruiterData.ts
├── layouts/
│   ├── JobSeekerLayout.tsx   # Bottom nav layout
│   └── RecruiterLayout.tsx   # Sidebar layout
├── pages/
│   ├── LandingPage.tsx
│   ├── jobs/            # Job seeker pages
│   │   ├── JobsBrowsePage.tsx
│   │   ├── JobDetailPage.tsx
│   │   └── ApplicationFlowPage.tsx
│   └── recruiter/       # Recruiter pages
│       ├── DashboardPage.tsx
│       ├── CandidatesKanbanPage.tsx
│       └── VacanciesPage.tsx
```

---

## Migrating Pages

### Old Page (Class Component)

```tsx
// Old approach
import React from 'react';

export default class DashboardPage extends React.Component {
  state = {
    data: null,
    loading: false,
    error: null,
  };

  componentDidMount() {
    this.fetchData();
  }

  fetchData = async () => {
    this.setState({ loading: true });
    try {
      const response = await fetch('/api/data');
      const data = await response.json();
      this.setState({ data });
    } catch (error) {
      this.setState({ error });
    } finally {
      this.setState({ loading: false });
    }
  };

  render() {
    // ...
  }
}
```

### New Page (Functional Component + React Query)

```tsx
// New approach
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-data'],
    queryFn: async () => {
      const response = await fetch('/api/data');
      return response.json();
    },
  });

  if (isLoading) return <LoadingState message="Loading dashboard..." />;
  if (error) return <ErrorState message="Failed to load dashboard" onRetry={() => refetch()} />;

  return <div>{/* Render data */}</div>;
}
```

---

## Using New Hooks

### Data Fetching with `useJobs`

```tsx
import { useJobs, useJob } from '@/hooks/useJobs';

// List jobs
function JobsPage() {
  const { data, isLoading, error } = useJobs({ limit: 20 });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={error.message} />;

  return (
    <div>
      {data.vacancies.map(job => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}

// Single job
function JobDetail({ id }) {
  const { data: job, isLoading } = useJob(id);

  if (isLoading) return <LoadingState />;

  return <div>{job.title}</div>;
}
```

### Recruiter Data with `useRecruiterData`

```tsx
import { useCandidates, useUpdateCandidateStage } from '@/hooks/useRecruiterData';

function CandidatesPage() {
  const { data: candidatesData } = useCandidates();
  const updateStage = useUpdateCandidateStage();

  const handleStageChange = (candidateId, newStage) => {
    updateStage.mutate({ candidateId, stage: newStage });
  };

  return (
    <div>
      {candidatesData.candidates.map(candidate => (
        <CandidateCard
          key={candidate.id}
          candidate={candidate}
          onStageChange={handleStageChange}
        />
      ))}
    </div>
  );
}
```

### Responsive Design with `useBreakpoint`

```tsx
import { useBreakpoint } from '@/hooks/useBreakpoint';

function MyComponent() {
  const { isMobile, isDesktop } = useBreakpoint();

  return (
    <Box sx={{
      flexDirection: isMobile ? 'column' : 'row',
      padding: isMobile ? 2 : 4,
    }}>
      {isMobile ? <MobileNav /> : <DesktopNav />}
    </Box>
  );
}
```

---

## Component Migration

### Button → AnimatedButton

```tsx
// Old
import { Button } from '@mui/material';
<Button variant="contained">Click</Button>

// New (with micro-interactions)
import { AnimatedButton } from '@/components/ui/AnimatedButton';
<AnimatedButton variant="contained">Click</AnimatedButton>

// New (with gradient)
<AnimatedButton gradient="primary">Get Started</AnimatedButton>
```

### Custom Loading → LoadingState

```tsx
// Old
{loading && <div>Loading...</div>}

// New
import { LoadingState } from '@/components/ui/LoadingState';
{loading && <LoadingState message="Loading..." />}
```

### Custom Error → ErrorState

```tsx
// Old
{error && <div>Error: {error.message}</div>}

// New
import { ErrorState } from '@/components/ui/ErrorState';
{error && (
  <ErrorState
    title="Failed to load"
    message={error.message}
    onRetry={() => refetch()}
  />
)}
```

---

## Breaking Changes

### 1. Layout Components

**Old**: Single `Layout` component for all pages

**New**: Separate layouts for each user flow
```tsx
// Job seeker routes
<Route path="/jobs" element={<JobSeekerLayout />}>

// Recruiter routes
<Route path="/recruiter" element={<RecruiterLayout()}>
```

### 2. Default Exports

Most new components use **named exports** instead of default exports:
```tsx
// Import named components
import { AnimatedButton } from '@/components/ui/AnimatedButton';
import { useBreakpoint } from '@/hooks/useBreakpoint';
```

Exceptions (default exports):
- `JobSeekerLayout`
- `RecruiterLayout`
- `LandingPage`
- `PageTransition`

### 3. Route Structure

Nested routes are now explicit:
```tsx
// Old
<Route path="/job/:id" element={<JobDetail />} />

// New (nested under layout)
<Route path="/jobs" element={<JobSeekerLayout />}>
  <Route path=":id" element={<JobDetailPage />} />
  <Route path=":id/apply" element={<ApplicationFlowPage />} />
</Route>
```

### 4. Theme Usage

**Old**: Inline styles or style objects

**New**: MUI `sx` prop with theme tokens
```tsx
// Old
<div style={{ padding: '16px', color: '#6366f1' }}>

// New
<Box sx={{ p: 2, color: 'primary.main' }}>
```

---

## Quick Reference

### Common Imports

```tsx
// Components
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { AnimatedButton } from '@/components/ui/AnimatedButton';
import PageTransition from '@/components/ui/PageTransition';

// Layouts
import JobSeekerLayout from '@/layouts/JobSeekerLayout';
import RecruiterLayout from '@/layouts/RecruiterLayout';

// Hooks
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useJobs, useJob } from '@/hooks/useJobs';
import { useCandidates, useRecruiterAnalytics } from '@/hooks/useRecruiterData';

// MUI
import { Box, Container, Stack, Typography } from '@mui/material';
```

---

Last updated: 2025-02-01

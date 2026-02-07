# Component Library Documentation

AgentHR Frontend - Resume Analysis Platform

---

## Table of Contents

1. [Design System](#design-system)
2. [UI Components](#ui-components)
3. [Layout Components](#layout-components)
4. [Custom Hooks](#custom-hooks)
5. [Animation Components](#animation-components)

---

## Design System

### Typography

- **Primary Font**: Inter Variable (body text)
- **Heading Font**: Space Grotesk (headings)
- **Code Font**: source-code-pro (monospace)

### Color Palette

| Color Token | Value | Usage |
|-------------|-------|-------|
| `--gradient-primary` | `linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)` | Primary actions, branding |
| `--gradient-secondary` | `linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)` | Secondary actions |

### Spacing Scale

Base unit: 4px. Uses MUI's spacing system (1 = 4px, 2 = 8px, etc.).

---

## UI Components

### LoadingState

Loading spinner with optional message.

```tsx
import { LoadingState } from '@/components/ui/LoadingState';

<LoadingState message="Loading jobs..." />
<LoadingState size={60} color="primary" />
```

**Props:**
- `message?: string` - Optional loading message
- `size?: number | string` - Spinner size (default: 48)
- `color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'`
- `sx?: SxProps<Theme>` - MUI sx prop

---

### ErrorState

Error display with optional retry button.

```tsx
import { ErrorState } from '@/components/ui/ErrorState';

<ErrorState
  title="Failed to load"
  message="Please check your connection"
  onRetry={() => refetch()}
/>
```

**Props:**
- `title?: string` - Error title (default: "Error")
- `message: string` - Error message
- `onRetry?: () => void` - Optional retry callback
- `sx?: SxProps<Theme>` - MUI sx prop

---

### AnimatedButton

MUI Button with micro-interactions and gradient support.

```tsx
import { AnimatedButton } from '@/components/ui/AnimatedButton';

// Standard button
<AnimatedButton variant="contained" color="primary">
  Click Me
</AnimatedButton>

// Gradient button
<AnimatedButton gradient="primary">
  Get Started
</AnimatedButton>

<AnimatedButton gradient="secondary" size="large">
  Learn More
</AnimatedButton>
```

**Props:**
- Extends MUI `ButtonProps`
- `gradient?: 'primary' | 'secondary' | 'success' | 'warning'`

**Features:**
- Hover lift effect (y: -2px)
- Press scale effect (scale: 0.98)
- Smooth transitions (0.1s duration)

---

### PageTransition

Wrapper for smooth route transitions.

```tsx
import PageTransition from '@/components/ui/PageTransition';

<PageTransition duration={350}>
  <YourPageContent />
</PageTransition>

// With AnimatePresence for route transitions
<AnimatePresence mode="wait">
  <PageTransition key={location.pathname}>
    <Outlet />
  </PageTransition>
</AnimatePresence>
```

**Props:**
- `children: ReactNode` - Content to animate
- `duration?: number` - Duration in ms (default: 350)
- `delay?: number` - Delay in ms (default: 0)
- `exit?: boolean` - Enable exit animation (default: true)
- `className?: string` - Optional className

---

## Layout Components

### JobSeekerLayout

Mobile-first layout with bottom navigation for job seekers.

```tsx
import JobSeekerLayout from '@/layouts/JobSeekerLayout';

<Route path="/jobs" element={<JobSeekerLayout()}>
  <Route index element={<JobsBrowsePage />} />
  <Route path=":id" element={<JobDetailPage />} />
</Route>
```

**Features:**
- Sticky top app bar with branding
- Bottom navigation (Search, Saved, Applications, Profile)
- Skip link for accessibility
- Active route highlighting

---

### RecruiterLayout

Desktop-first layout with sidebar navigation for recruiters.

```tsx
import RecruiterLayout from '@/layouts/RecruiterLayout';

<Route path="/recruiter" element={<RecruiterLayout />}>
  <Route path="dashboard" element={<DashboardPage />} />
  <Route path="vacancies" element={<VacanciesPage />} />
</Route>
```

**Features:**
- 280px sidebar with navigation
- Mobile hamburger menu
- Skip link for accessibility
- Active route highlighting with `aria-current="page"`

---

## Dashboard Components

### BentoCard

Animated metric card for dashboard widgets.

```tsx
import { BentoCard } from '@/components/dashboard/BentoCard';

<BentoCard
  title="Active Jobs"
  value="12"
  subtitle="+2 this week"
  icon={<WorkIcon />}
  color="primary"
  delay={0.1}
/>
```

**Props:**
- `title: string` - Card title
- `value: string | number` - Main value to display
- `subtitle?: string` - Optional subtitle
- `icon?: React.ReactNode` - Optional icon
- `color?: 'primary' | 'secondary' | 'success' | 'warning'` - Gradient color
- `delay?: number` - Animation delay in seconds
- `sx?: SxProps<Theme>` - MUI sx prop

**Colors:**
- `primary`: Indigo to purple gradient
- `secondary`: Sky to cyan gradient
- `success`: Emerald to green gradient
- `warning`: Amber to orange gradient

---

## Kanban Components

### KanbanBoard

Drag-and-drop kanban board for candidate pipeline.

```tsx
import { KanbanBoard } from '@/components/kanban/KanbanBoard';

const columns = [
  { id: 'applied', title: 'Applied', candidates: [...] },
  { id: 'screening', title: 'Screening', candidates: [...] },
];

<KanbanBoard
  columns={columns}
  onDragEnd={(result) => {
    // Handle drop
  }}
/>
```

**Props:**
- `columns: KanbanColumn[]` - Array of column data
- `onDragEnd: (result: DropResult) => void` - Drop handler

**Column Interface:**
```tsx
interface KanbanColumn {
  id: string;
  title: string;
  candidates: Candidate[];
}
```

---

## Custom Hooks

### useBreakpoint

MUI-integrated responsive breakpoint detection.

```tsx
import { useBreakpoint } from '@/hooks/useBreakpoint';

const { breakpoint, isMobile, isTablet, isDesktop } = useBreakpoint();

if (isMobile) {
  // Show mobile navigation
}
```

**Returns:**
- `breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl'`
- `isXs, isSm, isMd, isLg, isXl: boolean`
- `isMobile: boolean` - true for xs (< 600px)
- `isTablet: boolean` - true for sm (600-899px)
- `isDesktop: boolean` - true for md+ (≥ 900px)

---

### useJobs

TanStack Query hook for job data.

```tsx
import { useJobs, useJob } from '@/hooks/useJobs';

// List jobs
const { data, isLoading, error } = useJobs({ limit: 10 });

// Single job
const { data: job } = useJob(jobId);
```

**Job Interface:**
```tsx
interface JobVacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months?: number;
  work_format?: 'remote' | 'office' | 'hybrid';
  location?: string;
  salary_min?: number;
  salary_max?: number;
}
```

---

### useRecruiterData

TanStack Query hooks for recruiter data.

```tsx
import {
  useCandidates,
  useCandidateStages,
  useUpdateCandidateStage,
  useRecruiterVacancies,
  useRecruiterAnalytics,
} from '@/hooks/useRecruiterData';

// Candidates
const { data: candidatesData } = useCandidates();
const updateStage = useUpdateCandidateStage();

// Analytics
const { data: analytics } = useRecruiterAnalytics();
```

**Candidate Interface:**
```tsx
interface Candidate {
  id: string;
  name: string;
  email: string;
  stage: string;
  tags: string[];
  match_score?: number;
}
```

---

## New API Integration Hooks

### useApiMetrics

Track API performance metrics across all requests.

```tsx
import { useApiMetrics } from '@/hooks/useApiMetrics';

function ApiStats() {
  const { stats, reset } = useApiMetrics();

  return (
    <Box>
      <Typography>Total Calls: {stats.totalCalls}</Typography>
      <Typography>Average Duration: {stats.averageDuration}ms</Typography>
      <Typography>Success Rate: {stats.successRate}%</Typography>
      <Button onClick={reset}>Reset Metrics</Button>
    </Box>
  );
}
```

### useCandidateWorkflow

Manage candidate workflow stages with optimistic updates.

```tsx
import { useCandidateWorkflow } from '@/hooks/useCandidateWorkflow';

function CandidateStage({ candidateId }: { candidateId: string }) {
  const { candidate, moveStage, isLoading } = useCandidateWorkflow(candidateId);

  const handleMove = async (newStage: string) => {
    await moveStage(newStage, { vacancy_id: 'vac-123' });
  };

  return (
    <Select
      value={candidate?.current_stage}
      onChange={(e) => handleMove(e.target.value)}
      disabled={isLoading}
    >
      <MenuItem value="applied">Applied</MenuItem>
      <MenuItem value="screening">Screening</MenuItem>
      <MenuItem value="interview">Interview</MenuItem>
    </Select>
  );
}
```

### useATSAnalysis

ATS simulation for resume evaluation.

```tsx
import { useATSAnalysis } from '@/hooks/useATSAnalysis';

function ATSEvaluation({ resumeId, vacancyId }: { resumeId: string; vacancyId: string }) {
  const { evaluate, result, isEvaluating } = useATSAnalysis();

  const handleEvaluate = async () => {
    await evaluate({ resume_id: resumeId, vacancy_id: vacancyId, use_llm: true });
  };

  return (
    <Box>
      <Button onClick={handleEvaluate} disabled={isEvaluating}>
        Evaluate ATS Score
      </Button>
      {result && (
        <Alert severity={result.passed ? 'success' : 'warning'}>
          Score: {Math.round(result.overall_score * 100)}%
          {result.passed ? ' - Passed' : ' - Failed'}
        </Alert>
      )}
    </Box>
  );
}
```

### useMatchingWeights

Customize matching algorithm weights per vacancy.

```tsx
import { useMatchingWeights } from '@/hooks/useMatchingWeights';

function WeightSelector({ vacancyId }: { vacancyId: string }) {
  const { profiles, activeProfile, applyProfile, createProfile } = useMatchingWeights();

  return (
    <Box>
      <FormControl>
        <InputLabel>Matching Profile</InputLabel>
        <Select
          value={activeProfile?.id || ''}
          onChange={(e) => applyProfile(vacancyId, e.target.value)}
        >
          {profiles?.map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
```

---

Last updated: 2026-02-05

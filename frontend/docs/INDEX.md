# Frontend Documentation Index

> **AgentHR Frontend Documentation**
> **Last updated:** 2026-02-05

---

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Project overview, setup, quick start | Everyone |
| [BACKLOG.md](../BACKLOG.md) | Missing features by priority | Developers |
| [ROADMAP.md](ROADMAP.md) | Phased implementation plan | Tech Leads, PMs |
| [TASKS.md](TASKS.md) | Task breakdown for Kanban | Developers, PMs |

---

## Developer Guides

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | Frontend architecture, routing, state management |
| [api-integration.md](api-integration.md) | **NEW:** API Gateway integration guide with microservices |
| [components.md](components.md) | Component catalog and patterns |
| [migration-guide.md](migration-guide.md) | Old → New architecture migration |
| [build-verification.md](build-verification.md) | Pre-deployment checklist |

---

## Quick Reference

### Current Coverage

- **Backend API**: 100% migrated to microservices architecture
- **Test Coverage**: ~30% (needs improvement)
- **Accessibility**: WCAG 2.1 AA compliant

### Tech Stack Summary

```
React 18.3 + TypeScript
├── UI: MUI v6.1 + Emotion
├── State: TanStack React Query v5
├── Routing: React Router v6
├── Build: Vite 5.4
├── Testing: Vitest + Playwright
└── API: API Gateway (port 8888) → 10 Microservices
```

### File Locations

| What You Need | Where to Find It |
|---------------|------------------|
| Components | `src/components/` |
| Pages | `src/pages/` |
| Hooks | `src/hooks/` |
| API Types | `src/types/api.ts` |
| API Client | `src/api/client.ts` |
| API Integration Guide | [docs/api-integration.md](api-integration.md) |
| Routes | `src/App.tsx` |
| Theme | `src/contexts/ThemeContext.tsx` |

---

## Getting Started

### For New Developers

1. Read [README.md](../README.md) for setup
2. Review [architecture.md](architecture.md) for frontend architecture
3. Read [api-integration.md](api-integration.md) for API Gateway and microservices
4. Browse [components.md](components.md) for patterns
5. Check [TASKS.md](TASKS.md) for available work

### For Project Managers

1. Review [BACKLOG.md](../BACKLOG.md) for missing features
2. See [ROADMAP.md](ROADMAP.md) for timeline
3. Use [TASKS.md](TASKS.md) to create tickets

### For Technical Leads

1. Review [ROADMAP.md](ROADMAP.md) for technical approach
2. Check [build-verification.md](build-verification.md) for standards
3. Monitor progress via [TASKS.md](TASKS.md) completion

---

## Module Status

| Module | Status | Priority | Tasks |
|--------|--------|----------|-------|
| Search | Not Started | HIGH | 12 tasks |
| Saved Searches | Not Started | HIGH | 10 tasks |
| Candidate Tags | Not Started | HIGH | 10 tasks |
| Candidate Notes | Not Started | HIGH | 10 tasks |
| Reports | Partial | HIGH | 8 tasks |
| Ranking | Not Started | MEDIUM | 7 tasks |
| Skill Gap | Not Started | MEDIUM | 7 tasks |
| Interview Prep | Not Started | MEDIUM | 5 tasks |
| Batch Operations | Partial | MEDIUM | 6 tasks |
| Comparison | Not Started | MEDIUM | 3 tasks |
| Taxonomy | Not Started | LOW | 6 tasks |
| Weights | Not Started | LOW | 4 tasks |
| Performance | Not Started | LOW | 4 tasks |
| Backups | Not Started | LOW | 5 tasks |
| Fairness | Not Started | LOW | 4 tasks |
| Work Experience | Not Started | LOW | 4 tasks |
| Workflow Stages | Partial | MEDIUM | 4 tasks |

---

## Conventions

### Component Naming

- Use PascalCase for components: `MyComponent.tsx`
- Group by feature: `components/analytics/`, `components/jobs/`
- Reusable UI in `components/ui/`

### File Structure

```tsx
// MyComponent.tsx
import React from 'react';

interface MyComponentProps {
  // Props interface
}

export function MyComponent({ prop }: MyComponentProps) {
  // Component logic
  return <div>{/* JSX */}</div>;
}
```

### API Integration

The frontend communicates with backend microservices via a unified API Gateway:

```tsx
// All requests go through API Gateway (port 8888)
// Environment: VITE_API_URL=http://localhost:8888

// Using the typed API client
import { apiClient } from '@/api/client';

const result = await apiClient.uploadResume(file);
const analysis = await apiClient.analyzeResume({ resume_id: id });
const match = await apiClient.compareWithVacancy(resumeId, vacancy);

// With React Query for caching
import { useQuery } from '@tanstack/react-query';

export function useCandidates(stageId?: string) {
  return useQuery({
    queryKey: ['candidates', stageId],
    queryFn: () => apiClient.listCandidates(stageId),
  });
}
```

**Key Points:**
- All API calls go through the API Gateway (port 8888)
- Individual microservice URLs are abstracted
- See [api-integration.md](api-integration.md) for complete guide

---

## Support

- **API Integration Issues**: Check [api-integration.md](api-integration.md) troubleshooting section
- **Component Questions**: Check [components.md](components.md) first
- **Architecture Questions**: Review [architecture.md](architecture.md)
- **Build Errors**: See [build-verification.md](build-verification.md)
- **Issues**: Create via TASKS.md breakdown

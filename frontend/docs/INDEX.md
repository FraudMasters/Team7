# Frontend Documentation Index

> **AgentHR Frontend Documentation**
> **Last updated:** 2026-02-01

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
| [components.md](components.md) | Component catalog and patterns |
| [migration-guide.md](migration-guide.md) | Old → New architecture migration |
| [build-verification.md](build-verification.md) | Pre-deployment checklist |

---

## Quick Reference

### Current Coverage

- **Backend API**: ~40% implemented
- **Test Coverage**: ~30% (needs improvement)
- **Accessibility**: WCAG 2.1 AA compliant

### Tech Stack Summary

```
React 18.3 + TypeScript
├── UI: MUI v6.1 + Emotion
├── State: TanStack React Query v5
├── Routing: React Router v6
├── Build: Vite 5.4
└── Testing: Vitest + Playwright
```

### File Locations

| What You Need | Where to Find It |
|---------------|------------------|
| Components | `src/components/` |
| Pages | `src/pages/` |
| Hooks | `src/hooks/` |
| API Types | `src/types/api.ts` |
| API Client | `src/api/client.ts` |
| Routes | `src/App.tsx` |
| Theme | `src/contexts/ThemeContext.tsx` |

---

## Getting Started

### For New Developers

1. Read [README.md](../README.md) for setup
2. Review [migration-guide.md](migration-guide.md) for architecture
3. Browse [components.md](components.md) for patterns
4. Check [TASKS.md](TASKS.md) for available work

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

```tsx
// hooks/useMyFeature.ts
import { useQuery } from '@tanstack/react-query';

export function useMyFeature() {
  return useQuery({
    queryKey: ['my-feature'],
    queryFn: async () => {
      const response = await apiClient.get('/api/my-feature');
      return response.data;
    },
  });
}
```

---

## Support

- **Issues**: Create via TASKS.md breakdown
- **Questions**: Check components.md first
- **Build errors**: See build-verification.md

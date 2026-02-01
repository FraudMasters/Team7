# Component Inventory

## Overview

This document provides a comprehensive inventory of Material-UI components used in the AgentHR frontend application and custom wrapper components that need to be created for the design system implementation.

## Material-UI Components to Use

### Layout Components

#### Box
- **Import**: `@mui/material/Box`
- **Usage**: Extensive use throughout the application for layout, spacing, and styling
- **Common Props**: `sx`, `display`, `flexDirection`, `gap`, `p`, `m`

#### Container
- **Import**: `@mui/material/Container`
- **Usage**: Page-level content containers
- **Max Width**: `lg` (1280px)

#### Stack
- **Import**: `@mui/material/Stack`
- **Usage**: Vertical/horizontal stacking with automatic spacing
- **Common Props**: `spacing`, `direction`

#### Grid
- **Import**: `@mui/material/Grid`
- **Usage**: Responsive grid layouts
- **Examples**: Dashboard layouts, card grids

### Navigation Components

#### AppBar
- **Import**: `@mui/material/AppBar`
- **Usage**: Top navigation bar
- **Position**: Static or Sticky

#### Toolbar
- **Import**: `@mui/material/Toolbar`
- **Usage**: Container for AppBar content

#### BottomNavigation
- **Import**: `@mui/material/BottomNavigation`
- **Usage**: Bottom navigation for job seeker flow

#### BottomNavigationAction
- **Import**: `@mui/material/BottomNavigationAction`
- **Usage**: Individual bottom nav items

#### Button
- **Import**: `@mui/material/Button`
- **Usage**: Primary action buttons throughout app
- **Variants**: `contained`, `outlined`, `text`

#### IconButton
- **Import**: `@mui/material/IconButton`
- **Usage**: Icon-only buttons

#### Menu & MenuItem
- **Import**: `@mui/material/Menu`, `@mui/material/MenuItem`
- **Usage**: Dropdown menus

### Data Display Components

#### Card & CardContent
- **Import**: `@mui/material/Card`, `@mui/material/CardContent`
- **Usage**: Content containers, dashboard cards

#### Paper
- **Import**: `@mui/material/Paper`
- **Usage**: Elevated surface containers

#### Chip
- **Import**: `@mui/material/Chip`
- **Usage**: Tags, status indicators, labels

#### Avatar
- **Import**: `@mui/material/Avatar`
- **Usage**: User profile images, initials

#### Badge
- **Import**: `@mui/material/Badge`
- **Usage**: Notification counts, status indicators

#### Divider
- **Import**: `@mui/material/Divider`
- **Usage**: Visual separators

### Input Components

#### TextField
- **Import**: `@mui/material/TextField`
- **Usage**: Text input forms
- **Variants**: `outlined`

#### Select
- **Import**: `@mui/material/Select`
- **Usage**: Dropdown selection inputs

#### FormControl & InputLabel
- **Import**: `@mui/material/FormControl`, `@mui/material/InputLabel`
- **Usage**: Form control wrappers

#### Checkbox & FormControlLabel
- **Import**: `@mui/material/Checkbox`, `@mui/material/FormControlLabel`
- **Usage**: Boolean input, multi-select

#### Switch
- **Import**: `@mui/material/Switch`
- **Usage**: Toggle settings

### Feedback Components

#### Alert
- **Import**: `@mui/material/Alert`
- **Usage**: Error messages, warnings, info, success
- **Severities**: `error`, `warning`, `info`, `success`

#### Snackbar
- **Import**: `@mui/material/Snackbar`
- **Usage**: Temporary notifications

#### CircularProgress
- **Import**: `@mui/material/CircularProgress`
- **Usage**: Loading indicators

#### LinearProgress
- **Import**: `@mui/material/LinearProgress`
- **Usage**: Progress bars

#### Backdrop
- **Import**: `@mui/material/Backdrop`
- **Usage**: Full-screen loading overlay

### Surface Components

#### Dialog
- **Import**: `@mui/material/Dialog`
- **Usage**: Modal dialogs

#### DialogTitle, DialogContent, DialogActions
- **Import**: `@mui/material/DialogTitle` (etc.)
- **Usage**: Dialog content structure

#### Drawer
- **Import**: `@mui/material/Drawer`
- **Usage**: Side panels

#### Popover
- **Import**: `@mui/material/Popover`
- **Usage**: Floating content containers

### Typography Components

#### Typography
- **Import**: `@mui/material/Typography`
- **Usage**: All text rendering
- **Variants**: `h1`-`h6`, `body1`, `body2`, `caption`, `button`

### Utility Components

#### Tooltip
- **Import**: `@mui/material/Tooltip`
- **Usage**: Hover information

#### Collapse
- **Import**: `@mui/material/Collapse`
- **Usage**: Expandable content

#### Stepper, Step, StepLabel
- **Import**: `@mui/material/Stepper` (etc.)
- **Usage**: Multi-step processes

#### Skeleton
- **Import**: `@mui/material/Skeleton`
- **Usage**: Loading placeholders

### Icons

**Package**: `@mui/icons-material`

**Common Icons**:
- Navigation: `Menu`, `Home`, `ArrowBack`, `ArrowForward`
- Job Seeker: `Search`, `Bookmark`, `Description`, `Person`, `Work`
- Recruiter: `Dashboard`, `Business`, `People`, `BarChart`, `TrendingUp`
- Actions: `Add`, `Edit`, `Delete`, `Refresh`, `Download`, `Upload`
- Status: `CheckCircle`, `Error`, `Warning`, `Info`, `Cancel`
- Locations: `LocationOn`, `Business`
- Files: `CloudUpload`, `FolderOpen`, `InsertDriveFile`

## Custom Wrapper Components

### BentoCard

**Purpose**: Standardized card component for Bento Grid layouts

**Props**:
```tsx
interface BentoCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning';
  delay?: number;
  sx?: SxProps<Theme>;
}
```

**Features**:
- Predefined sizes matching grid column spans
- Gradient icon box (48x48)
- Consistent padding and border radius (12px)
- Motion animation with delay

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/dashboard/BentoCard.tsx`

### GradientButton

**Purpose**: Primary action button with brand gradient

**Props**:
```tsx
interface GradientButtonProps extends ButtonProps {
  gradient?: 'primary' | 'secondary';
}
```

**Features**:
- Default gradient background (#6366f1 → #8b5cf6)
- Hover state with increased brightness
- All MUI Button props supported

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/ui/GradientButton.tsx`

### MotionBox

**Purpose**: Animated container for motion effects

**Props**:
```tsx
interface MotionBoxProps extends BoxProps {
  animate?: boolean;
  animation?: 'fadeIn' | 'slideIn' | 'scaleIn';
  delay?: number;
}
```

**Features**:
- Predefined animations
- Configurable delay
- All Box props supported
- Framer Motion integration

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/ui/MotionBox.tsx`

### KanbanBoard

**Purpose**: Drag-and-drop kanban board for candidate pipeline

**Props**:
```tsx
interface KanbanBoardProps {
  columns: KanbanColumn[];
  onDragEnd: (result: DropResult) => void;
}

interface KanbanColumn {
  id: string;
  title: string;
  candidates: Candidate[];
}
```

**Features**:
- Uses @hello-pangea/dnd
- Draggable candidate cards
- Column headers with counts
- Responsive layout

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/kanban/KanbanBoard.tsx`

### PageTransition

**Purpose**: Wrapper for page transition animations

**Props**:
```tsx
interface PageTransitionProps {
  children: ReactNode;
}
```

**Features**:
- Fade-in and slide-up animation
- 200ms duration
- Works with React Router

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/ui/PageTransition.tsx`

### LoadingState

**Purpose**: Consistent loading displays

**Props**:
```tsx
interface LoadingStateProps {
  message?: string;
}
```

**Features**:
- CircularProgress with optional message
- Centered flex column layout

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/ui/LoadingState.tsx`

### ErrorState

**Purpose**: Consistent error displays

**Props**:
```tsx
interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}
```

**Features**:
- Alert with error styling
- Optional retry button

**Implementation Location**: `/Users/fraud/Projects/agenthr/frontend/src/components/ui/ErrorState.tsx`

## Component Dependencies

### External Libraries

#### @hello-pangea/dnd
- **Purpose**: Drag and drop functionality
- **Usage**: Kanban board, candidate sorting

#### react-window
- **Purpose**: Virtual scrolling for large lists
- **Usage**: Resume database, candidate lists

#### framer-motion
- **Purpose**: Production-ready animation library
- **Usage**: Page transitions, micro-interactions

#### @tanstack/react-query
- **Purpose**: Server state management
- **Usage**: API caching, synchronization

## Component Best Practices

### When to Use Custom Wrappers

1. **Repeated Patterns**: When the same component structure appears 3+ times
2. **Design System Elements**: For brand-specific components (gradients, typography)
3. **Complex Interactions**: For components with multiple related behaviors
4. **Business Logic**: For domain-specific UI patterns

### When to Use MUI Components Directly

1. **Simple Use Cases**: Standard buttons, inputs without special styling
2. **One-Off Components**: Components used only once
3. **Rapid Prototyping**: During development phase

## Component Testing

### Test Coverage Goals

- Custom wrappers: 100% coverage
- Complex components: >90% coverage
- Simple components: >80% coverage

### Testing Strategy

1. **Unit Tests**: Component behavior and props
2. **Integration Tests**: Component interactions
3. **Visual Tests**: Screenshot testing with Playwright
4. **Accessibility Tests**: ARIA attributes, keyboard navigation

## Related Files

- `/Users/fraud/Projects/agenthr/frontend/docs/design-system.md` - Design specifications
- `/Users/fraud/Projects/agenthr/frontend/docs/architecture.md` - Architecture overview
- `/Users/fraud/Projects/agenthr/frontend/src/components/` - Existing components
- `/Users/fraud/Projects/agenthr/frontend/package.json` - Dependencies

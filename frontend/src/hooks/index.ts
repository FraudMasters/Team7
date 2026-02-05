/**
 * Custom React Hooks
 *
 * This module exports all custom hooks used throughout the application.
 */

export {
  useKeyboardNavigation,
  getAllKeyboardShortcuts,
  clearKeyboardShortcuts,
  type KeyboardShortcut,
  type UseKeyboardNavigationOptions,
} from './useKeyboardNavigation';

// useResponsive is now the primary hook for breakpoints
// useBreakpoints is an alias for backward compatibility
export {
  useResponsive as useBreakpoints,
  type ResponsiveResult as BreakpointsResult,
} from './useResponsive';

// Export breakpoint types and values directly from utils to avoid re-export issues
export type { Breakpoint } from './useResponsive';
export { BREAKPOINT_VALUES } from '../utils/responsive';

export {
  useGlobalKeyboardShortcuts,
  createGlobalShortcut,
  COMMON_SHORTCUTS,
  type GlobalShortcutConfig,
} from './useGlobalKeyboardShortcuts';

export {
  useAuth,
  type AuthContextValue,
} from './useAuth';

export {
  useMediaQuery,
} from './useMediaQuery';

// Role management hooks
export {
  getUserRoles,
  useUserRoles,
  hasRole,
  hasAnyRole,
  isAdmin,
  isRecruiter,
  isJobSeeker,
  useHasRole,
  useHasAnyRole,
  useIsAdmin,
  useIsRecruiter,
  useIsJobSeeker,
} from './useRoles';
export type { UserRole } from './useRoles';

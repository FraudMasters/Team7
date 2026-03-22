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

export {
  useBreakpoints,
  type BreakpointsResult,
  type Breakpoint,
  BREAKPOINT_VALUES,
} from './useBreakpoints';

export {
  useGlobalKeyboardShortcuts,
  createGlobalShortcut,
  COMMON_SHORTCUTS,
  type GlobalShortcutConfig,
} from './useGlobalKeyboardShortcuts';

export {
  useRoles,
  isValidRole,
  normalizeRole,
  getRoleLevel,
  compareRoles,
  type UserRole,
  type RolesResult,
  type UserInfo,
} from './useRoles';

export { useJobSearch, useJobSearchGet } from './useJobSearch';

export {
  useJobApplications,
  useJobApplication,
  useSubmitJobApplication,
} from './useJobApplications';

export {
  useSavedJobs,
  useCheckJobSaved,
  useSaveJob,
  useUnsaveJob,
} from './useSavedJobs';

export {
  useWebSocketProgress,
  type UseWebSocketProgressOptions,
  type UseWebSocketProgressReturn,
} from './useWebSocketProgress';

export {
  useAnalyticsRealTime,
  type UseAnalyticsRealTimeOptions,
  type UseAnalyticsRealTimeReturn,
} from './useAnalyticsRealTime';

export {
  useSkillFeedback,
  type FeedbackEntry,
  type FeedbackListResponse,
  type FeedbackEntryCreate,
  type FeedbackCreateRequest,
  type FeedbackFilters,
  type UseSkillFeedbackResult,
} from './useSkillFeedback';

export {
  useTransparencyRealTime,
  type UseTransparencyRealTimeOptions,
  type UseTransparencyRealTimeReturn,
} from './useTransparencyRealTime';

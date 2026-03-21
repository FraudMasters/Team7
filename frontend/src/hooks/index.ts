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
  useKeyMetrics,
  useQualityMetrics,
  useFunnelMetrics,
  useStageDuration,
  useSourceTracking,
  useRecruiterPerformance,
  useSkillDemand,
  useRankingAccuracy,
  useTaxonomyUsage,
  useAIConfidence,
  useFeatureImportance,
  useRankingRationale,
  usePerformanceTrends,
  type AnalyticsDateParams,
  type SourceTrackingParams,
  type RecruiterPerformanceParams,
  type StageDurationParams,
  type RankingAccuracyParams,
} from './useAnalytics';

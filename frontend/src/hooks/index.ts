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
  useWebSocket,
  type UseWebSocketOptions,
  type UseWebSocketReturn,
} from './useWebSocket';
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

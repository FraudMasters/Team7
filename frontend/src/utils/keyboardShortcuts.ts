/**
 * Keyboard Shortcuts Utility
 *
 * Provides helper functions and utilities for working with keyboard shortcuts
 * in the application. This module complements the KeyboardShortcutsHelp component
 * and useKeyboardNavigation hook with formatting and validation utilities.
 *
 * @module utils/keyboardShortcuts
 */

import type { KeyboardShortcut, ShortcutCategory } from '@/components/KeyboardShortcutsHelp';

/**
 * Modifier key names
 */
export type ModifierKey = 'Ctrl' | 'Shift' | 'Alt' | 'Meta' | 'Cmd';

/**
 * Key combination format
 */
export interface KeyCombination {
  /**
   * Modifier keys (Ctrl, Shift, Alt, Meta/Cmd)
   */
  modifiers?: ModifierKey[];

  /**
   * Primary key (e.g., 'S', 'Enter', 'Escape')
   */
  key: string;

  /**
   * Whether to prevent default browser behavior
   * @default true
   */
  preventDefault?: boolean;
}

/**
 * Platform-specific key mappings
 */
const PLATFORM_KEYS: Record<string, Record<string, string>> = {
  // macOS uses Cmd instead of Ctrl for some shortcuts
  macos: {
    Ctrl: 'Cmd',
    Meta: 'Cmd',
  },
  // Windows, Linux, and others use Ctrl
  default: {
    Meta: 'Win',
  },
};

/**
 * Detect the current platform
 *
 * @returns 'macos' if running on macOS, 'default' otherwise
 *
 * @example
 * ```ts
 * const platform = getPlatform();
 * if (platform === 'macos') {
 *   // Show Cmd symbols instead of Ctrl
 * }
 * ```
 */
export function getPlatform(): 'macos' | 'default' {
  if (typeof window === 'undefined') return 'default';

  return navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'macos' : 'default';
}

/**
 * Format a key combination for display
 *
 * Formats a key combination array into a human-readable string with
 * platform-specific key names and symbols.
 *
 * @param keys - Array of key names (e.g., ['Ctrl', 'S'])
 * @param platform - Target platform ('macos' or 'default')
 * @returns Formatted key combination string
 *
 * @example
 * ```ts
 * formatKeyCombination(['Ctrl', 'S'], 'default')  // "Ctrl+S"
 * formatKeyCombination(['Ctrl', 'S'], 'macos')     // "⌘+S"
 * formatKeyCombination(['Shift', 'Enter'])         // "Shift+Enter"
 * ```
 */
export function formatKeyCombination(
  keys: string[],
  platform: 'macos' | 'default' = getPlatform()
): string {
  return keys
    .map((key) => {
      // Apply platform-specific mappings
      const platformMap = platform === 'macos' ? PLATFORM_KEYS.macos : PLATFORM_KEYS.default;
      const mappedKey = platformMap[key] || key;

      // Convert special keys to symbols for macOS
      if (platform === 'macos') {
        const symbolMap: Record<string, string> = {
          Cmd: '⌘',
          Ctrl: '⌃',
          Shift: '⇧',
          Alt: '⌥',
          Meta: '⌘',
        };
        return symbolMap[mappedKey] || mappedKey;
      }

      return mappedKey;
    })
    .join('+');
}

/**
 * Format key combination as JSX elements for UI rendering
 *
 * Returns an array of strings and/or elements that can be rendered
 * in React components with proper styling.
 *
 * @param keys - Array of key names
 * @param platform - Target platform
 * @returns Array of key strings ready for rendering
 *
 * @example
 * ```tsx
 * const keys = formatKeysForDisplay(['Ctrl', 'S']);
 * // ['Ctrl', 'S'] - render with <Chip /> components
 *
 * {keys.map((key, i) => (
 *   <React.Fragment key={i}>
 *     {i > 0 && <span>+</span>}
 *     <Chip label={key} />
 *   </React.Fragment>
 * ))}
 * ```
 */
export function formatKeysForDisplay(
  keys: string[],
  platform: 'macos' | 'default' = getPlatform()
): string[] {
  return keys.map((key) => {
    const platformMap = platform === 'macos' ? PLATFORM_KEYS.macos : PLATFORM_KEYS.default;
    return platformMap[key] || key;
  });
}

/**
 * Parse a keyboard event into key combination
 *
 * Extracts modifier keys and primary key from a KeyboardEvent
 * into a standardized KeyCombination format.
 *
 * @param event - Keyboard event to parse
 * @returns Parsed key combination
 *
 * @example
 * ```ts
 * useEffect(() => {
 *   const handleKeyDown = (e: KeyboardEvent) => {
 *     const combo = parseKeyCombination(e);
 *     // combo: { modifiers: ['Ctrl'], key: 'S', preventDefault: true }
 *   };
 *   window.addEventListener('keydown', handleKeyDown);
 * }, []);
 * ```
 */
export function parseKeyCombination(event: KeyboardEvent): KeyCombination {
  const modifiers: ModifierKey[] = [];

  if (event.ctrlKey) modifiers.push('Ctrl');
  if (event.shiftKey) modifiers.push('Shift');
  if (event.altKey) modifiers.push('Alt');
  if (event.metaKey) modifiers.push('Meta');

  return {
    modifiers,
    key: event.key,
    preventDefault: true,
  };
}

/**
 * Check if a keyboard event matches a key combination
 *
 * Tests whether a KeyboardEvent matches the expected combination
 * of modifier keys and primary key.
 *
 * @param event - Keyboard event to test
 * @param expected - Expected key combination
 * @returns true if event matches the combination
 *
 * @example
 * ```ts
 * const isCtrlS = matchesKeyCombination(event, {
 *   modifiers: ['Ctrl'],
 *   key: 'S'
 * });
 *
 * if (isCtrlS) {
 *   // Handle Ctrl+S shortcut
 * }
 * ```
 */
export function matchesKeyCombination(
  event: KeyboardEvent,
  expected: KeyCombination
): boolean {
  // Check primary key
  if (event.key.toLowerCase() !== expected.key.toLowerCase()) {
    return false;
  }

  // Check modifiers
  const expectedModifiers = expected.modifiers || [];
  const hasCtrl = expectedModifiers.includes('Ctrl');
  const hasShift = expectedModifiers.includes('Shift');
  const hasAlt = expectedModifiers.includes('Alt');
  const hasMeta = expectedModifiers.includes('Meta') || expectedModifiers.includes('Cmd');

  // All specified modifiers must be present
  if (hasCtrl && !event.ctrlKey) return false;
  if (hasShift && !event.shiftKey) return false;
  if (hasAlt && !event.altKey) return false;
  if (hasMeta && !event.metaKey) return false;

  // No unspecified modifiers should be present
  if (!hasCtrl && event.ctrlKey) return false;
  if (!hasShift && event.shiftKey) return false;
  if (!hasAlt && event.altKey) return false;
  if (!hasMeta && event.metaKey) return false;

  return true;
}

/**
 * Format keyboard shortcut description for help text
 *
 * Creates a human-readable description of a keyboard shortcut
 * with proper key formatting.
 *
 * @param shortcut - Keyboard shortcut object
 * @param platform - Target platform
 * @returns Formatted description with keys
 *
 * @example
 * ```ts
 * const shortcut = {
 *   id: 'save',
 *   keys: ['Ctrl', 'S'],
 *   description: 'Save document',
 *   category: 'forms'
 * };
 *
 * formatShortcutHelp(shortcut);
 * // "Ctrl+S - Save document" (on Windows/Linux)
 * // "⌘+S - Save document" (on macOS)
 * ```
 */
export function formatShortcutHelp(
  shortcut: KeyboardShortcut,
  platform: 'macos' | 'default' = getPlatform()
): string {
  const keys = formatKeyCombination(shortcut.keys, platform);
  return `${keys} - ${shortcut.description}`;
}

/**
 * Group shortcuts by category
 *
 * Organizes an array of shortcuts into groups based on their category.
 * Useful for rendering organized shortcut lists.
 *
 * @param shortcuts - Array of keyboard shortcuts
 * @returns Object with shortcuts grouped by category
 *
 * @example
 * ```ts
 * const shortcuts = getAllKeyboardShortcuts();
 * const grouped = groupShortcutsByCategory(shortcuts);
 * // {
 * //   global: [{ id: 'global.search', ... }],
 * //   upload: [{ id: 'upload.focusZone', ... }],
 * //   vacancy: [{ id: 'vacancy.new', ... }],
 * //   ...
 * // }
 * ```
 */
export function groupShortcutsByCategory(
  shortcuts: KeyboardShortcut[]
): Record<ShortcutCategory, KeyboardShortcut[]> {
  return shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<ShortcutCategory, KeyboardShortcut[]>);
}

/**
 * Filter shortcuts by search query
 *
 * Filters shortcuts array by matching search query against
 * shortcut ID, description, or keys.
 *
 * @param shortcuts - Array of keyboard shortcuts
 * @param query - Search query string
 * @returns Filtered array of shortcuts
 *
 * @example
 * ```ts
 * const shortcuts = getAllKeyboardShortcuts();
 * const results = filterShortcuts(shortcuts, 'save');
 * // Returns all shortcuts matching 'save' in description or keys
 * ```
 */
export function filterShortcuts(shortcuts: KeyboardShortcut[], query: string): KeyboardShortcut[] {
  if (!query.trim()) return shortcuts;

  const lowerQuery = query.toLowerCase();

  return shortcuts.filter((shortcut) => {
    // Search in description
    if (shortcut.description.toLowerCase().includes(lowerQuery)) {
      return true;
    }

    // Search in keys
    if (shortcut.keys.some((key) => key.toLowerCase().includes(lowerQuery))) {
      return true;
    }

    // Search in ID
    if (shortcut.id.toLowerCase().includes(lowerQuery)) {
      return true;
    }

    return false;
  });
}

/**
 * Validate a key combination array
 *
 * Checks if a key combination array is valid and properly formatted.
 *
 * @param keys - Array of key names to validate
 * @returns true if the key combination is valid
 *
 * @example
 * ```ts
 * validateKeyCombination(['Ctrl', 'S']);    // true
 * validateKeyCombination(['Ctrl', 'Shift', 'Enter']); // true
 * validateKeyCombination([]);               // false
 * validateKeyCombination(['Invalid']);      // true (no strict validation)
 * ```
 */
export function validateKeyCombination(keys: string[]): boolean {
  if (!Array.isArray(keys) || keys.length === 0) {
    return false;
  }

  // Valid modifier keys
  const validModifiers = ['Ctrl', 'Shift', 'Alt', 'Meta', 'Cmd'];

  // Must have at least one primary key (non-modifier)
  const hasPrimaryKey = keys.some((key) => !validModifiers.includes(key));

  return hasPrimaryKey;
}

/**
 * Get keyboard shortcut accessibility label
 *
 * Generates an ARIA-friendly label for a keyboard shortcut
 * for use with accessibility attributes.
 *
 * @param shortcut - Keyboard shortcut object
 * @returns Accessible label string
 *
 * @example
 * ```tsx
 * <button
 *   aria-label={getShortcutAriaLabel(shortcut)}
 *   onClick={handleAction}
 * >
 *   Save
 * </button>
 * ```
 */
export function getShortcutAriaLabel(shortcut: KeyboardShortcut): string {
  const keys = shortcut.keys.join(' plus ');
  return `Keyboard shortcut: ${keys}. ${shortcut.description}`;
}

/**
 * Convert keyboard shortcut to useKeyboardNavigation format
 *
 * Transforms a KeyboardShortcut object into the format expected
 * by the useKeyboardNavigation hook.
 *
 * @param shortcut - Keyboard shortcut from KeyboardShortcutsHelp
 * @returns Shortcut config for useKeyboardNavigation
 *
 * @example
 * ```ts
 * const shortcut = {
 *   id: 'save',
 *   keys: ['Ctrl', 'S'],
 *   description: 'Save',
 *   category: 'forms'
 * };
 *
 * const config = toUseKeyboardNavigationFormat(shortcut);
 * // {
 * //   id: 'save',
 * //   key: 'S',
 * //   modifiers: { Ctrl: true },
 * //   handler: () => {},
 * //   description: 'Save'
 * // }
 * ```
 */
export function toUseKeyboardNavigationFormat(
  shortcut: KeyboardShortcut
): {
  id: string;
  key: string;
  modifiers: { Ctrl?: boolean; Shift?: boolean; Alt?: boolean; Meta?: boolean };
  description: string;
} {
  const modifiers: { Ctrl?: boolean; Shift?: boolean; Alt?: boolean; Meta?: boolean } = {};

  shortcut.keys.forEach((key) => {
    switch (key) {
      case 'Ctrl':
        modifiers.Ctrl = true;
        break;
      case 'Shift':
        modifiers.Shift = true;
        break;
      case 'Alt':
        modifiers.Alt = true;
        break;
      case 'Meta':
      case 'Cmd':
        modifiers.Meta = true;
        break;
    }
  });

  // Last key is typically the primary key
  const primaryKey = shortcut.keys[shortcut.keys.length - 1];

  return {
    id: shortcut.id,
    key: primaryKey,
    modifiers,
    description: shortcut.description,
  };
}

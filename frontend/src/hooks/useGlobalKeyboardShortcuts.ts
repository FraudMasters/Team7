/**
 * Global Keyboard Shortcuts Hook
 *
 * Manages application-wide keyboard shortcuts that work across all pages.
 * This hook provides a centralized way to handle global shortcuts like
 * closing modals, opening help, and navigation.
 *
 * @module hooks/useGlobalKeyboardShortcuts
 */

import { useEffect, useCallback } from 'react';
import { matchesKeyCombination } from '@/utils/keyboardShortcuts';

/**
 * Global keyboard shortcut configuration
 */
export interface GlobalShortcutConfig {
  /**
   * Unique identifier for the shortcut
   */
  id: string;

  /**
   * Key combination to trigger the shortcut
   */
  keyCombination: {
    key: string;
    modifiers?: Array<'Ctrl' | 'Shift' | 'Alt' | 'Meta'>;
  };

  /**
   * Handler function to execute when shortcut is triggered
   */
  handler: (event: KeyboardEvent) => void;

  /**
   * Condition that must be true for shortcut to be active
   * Useful for context-sensitive shortcuts
   */
  condition?: () => boolean;

  /**
   * Whether to prevent default browser behavior
   * @default true
   */
  preventDefault?: boolean;
}

/**
 * Global Keyboard Shortcuts Hook
 *
 * Registers and manages global keyboard shortcuts that work across
 * the entire application. Automatically cleans up event listeners
 * on unmount.
 *
 * @param shortcuts - Array of shortcut configurations
 *
 * @example
 * ```tsx
 * const [modalOpen, setModalOpen] = useState(false);
 * const [menuOpen, setMenuOpen] = useState(false);
 *
 * useGlobalKeyboardShortcuts([
 *   {
 *     id: 'close-modal',
 *     keyCombination: { key: 'Escape' },
 *     handler: () => setModalOpen(false),
 *     condition: () => modalOpen,
 *   },
 *   {
 *     id: 'close-menu',
 *     keyCombination: { key: 'Escape' },
 *     handler: () => setMenuOpen(false),
 *     condition: () => menuOpen,
 *   },
 *   {
 *     id: 'show-help',
 *     keyCombination: { key: '/', modifiers: ['Ctrl'] },
 *     handler: () => setHelpOpen(true),
 *   },
 * ]);
 * ```
 */
export function useGlobalKeyboardShortcuts(shortcuts: GlobalShortcutConfig[]): void {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Find matching shortcuts
      const matchedShortcuts = shortcuts.filter((shortcut) => {
        // Check condition first
        if (shortcut.condition && !shortcut.condition()) {
          return false;
        }

        // Check if key combination matches
        return matchesKeyCombination(event, shortcut.keyCombination);
      });

      // Execute all matched shortcuts (in case of multiple handlers for same key)
      matchedShortcuts.forEach((shortcut) => {
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        shortcut.handler(event);
      });
    };

    // Add event listener with capture phase for early handling
    window.addEventListener('keydown', handleKeyDown, true);

    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [shortcuts]);
}

/**
 * Create a global shortcut configuration object
 *
 * Helper function to create properly typed shortcut configurations.
 *
 * @param config - Shortcut configuration
 * @returns GlobalShortcutConfig object
 *
 * @example
 * ```ts
 * const closeShortcut = createGlobalShortcut({
 *   id: 'close-dialog',
 *   keyCombination: { key: 'Escape' },
 *   handler: () => setDialogOpen(false),
 *   condition: () => dialogOpen,
 * });
 * ```
 */
export function createGlobalShortcut(
  config: Omit<GlobalShortcutConfig, 'preventDefault'>
): GlobalShortcutConfig {
  return {
    ...config,
    preventDefault: config.preventDefault ?? true,
  };
}

/**
 * Common global shortcut combinations
 *
 * Pre-defined key combinations for frequently used shortcuts.
 */
export const COMMON_SHORTCUTS = {
  /**
   * Escape key - typically used to close modals, dialogs, menus
   */
  ESCAPE: { key: 'Escape' },

  /**
   * Ctrl+/ or Cmd+/ - typically used to open keyboard shortcuts help
   */
  SHOW_SHORTCUTS: { key: '/', modifiers: ['Ctrl'] },

  /**
   * Ctrl+K or Cmd+K - typically used for global search
   */
  GLOBAL_SEARCH: { key: 'K', modifiers: ['Ctrl'] },

  /**
   * Ctrl+N or Cmd+N - typically used to create new items
   */
  NEW_ITEM: { key: 'N', modifiers: ['Ctrl'] },

  /**
   * Ctrl+F or Cmd+F - typically used for search within a page
   */
  FIND: { key: 'F', modifiers: ['Ctrl'] },

  /**
   * Ctrl+S or Cmd+S - typically used to save
   */
  SAVE: { key: 'S', modifiers: ['Ctrl'] },

  /**
   * Enter key - typically used to submit forms or open selected items
   */
  ENTER: { key: 'Enter' },

  /**
   * Space key - typically used to toggle selection or play/pause
   */
  SPACE: { key: ' ' },
} as const;

export default useGlobalKeyboardShortcuts;

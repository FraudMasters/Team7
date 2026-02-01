import { useEffect, useCallback, useRef } from 'react';
import {
  type KeyboardShortcut,
  type ParsedShortcut,
  matchesShortcut,
  preventShortcutDefaults,
  normalizeKey,
} from '@/utils/keyboardShortcuts';

/**
 * Keyboard navigation options
 */
export interface UseKeyboardNavigationOptions {
  /** Array of keyboard shortcuts to register */
  shortcuts: KeyboardShortcut[];
  /** Whether to prevent default browser behavior for matching shortcuts */
  preventDefault?: boolean;
  /** Event target to attach listeners to (default: window) */
  target?: EventTarget;
  /** Whether the hook is enabled (default: true) */
  enabled?: boolean;
  /** Priority level (higher = more priority, default: 0) */
  priority?: number;
  /** Callback when a shortcut is triggered */
  onShortcutTriggered?: (shortcutId: string, event: KeyboardEvent) => void;
}

/**
 * Keyboard navigation state
 */
export interface KeyboardNavigationState {
  /** Register a new shortcut */
  registerShortcut: (shortcut: KeyboardShortcut) => void;
  /** Unregister a shortcut by ID */
  unregisterShortcut: (shortcutId: string) => void;
  /** Enable all shortcuts */
  enable: () => void;
  /** Disable all shortcuts */
  disable: () => void;
  /** Check if shortcuts are enabled */
  isEnabled: () => boolean;
}

/**
 * Global registry of keyboard shortcuts across all hook instances
 *
 * This allows multiple components to register shortcuts and handles
 * priority-based conflict resolution.
 */
interface ShortcutRegistry {
  shortcuts: Map<string, { shortcut: KeyboardShortcut; priority: number }>;
  listeners: Set<(event: KeyboardEvent) => void>;
  isEnabled: boolean;
}

const globalRegistry: ShortcutRegistry = {
  shortcuts: new Map(),
  listeners: new Set(),
  isEnabled: true,
};

/**
 * Process keyboard event through the global registry
 *
 * @private
 * @param event - Keyboard event
 */
function _processKeyboardEvent(event: KeyboardEvent): void {
  if (!globalRegistry.isEnabled) {
    return;
  }

  // Convert event to a comparable format
  const eventKey = normalizeKey(event.key);
  const eventModifiers = {
    ctrl: event.ctrlKey,
    alt: event.altKey,
    shift: event.shiftKey,
    meta: event.metaKey,
  };

  // Find matching shortcuts, sorted by priority
  const matches = Array.from(globalRegistry.shortcuts.entries())
    .filter(([_, { shortcut }]) => {
      // Check if shortcut is enabled
      if (shortcut.enabled === false) {
        return false;
      }

      // Check if event matches the shortcut
      const shortcutKey = normalizeKey(shortcut.key);
      if (eventKey !== shortcutKey) {
        return false;
      }

      const modifiers = shortcut.modifiers || [];
      const requiredCtrl = modifiers.includes('Ctrl') || modifiers.includes('Control');
      const requiredAlt = modifiers.includes('Alt');
      const requiredShift = modifiers.includes('Shift');
      const requiredMeta = modifiers.includes('Meta') || modifiers.includes('Cmd');

      return (
        eventModifiers.ctrl === requiredCtrl &&
        eventModifiers.alt === requiredAlt &&
        eventModifiers.shift === requiredShift &&
        eventModifiers.meta === requiredMeta
      );
    })
    .sort((a, b) => (b[1].priority || 0) - (a[1].priority || 0));

  // Execute the highest priority matching shortcut
  if (matches.length > 0) {
    const [shortcutId, { shortcut }] = matches[0];

    try {
      shortcut.handler(event);
    } catch (error) {
      console.error(`Error executing keyboard shortcut "${shortcutId}":`, error);
    }
  }
}

/**
 * Setup global event listener (only once)
 *
 * @private
 */
let globalListenerSetup = false;

function _setupGlobalListener(): void {
  if (globalListenerSetup || typeof window === 'undefined') {
    return;
  }

  window.addEventListener('keydown', _processKeyboardEvent, { passive: false });
  globalListenerSetup = true;
}

/**
 * Teardown global event listener
 *
 * @private
 */
function _teardownGlobalListener(): void {
  if (!globalListenerSetup || typeof window === 'undefined') {
    return;
  }

  window.removeEventListener('keydown', _processKeyboardEvent);
  globalListenerSetup = false;
}

/**
 * useKeyboardNavigation Hook
 *
 * Provides keyboard navigation and shortcut management for React components.
 * Automatically registers shortcuts on mount and unregisters on unmount.
 *
 * This hook uses a global registry to manage shortcuts across all components,
 * with priority-based conflict resolution.
 *
 * @param options - Keyboard navigation options
 * @returns Keyboard navigation state and control functions
 *
 * @example
 * ```tsx
 * // Basic usage with shortcuts array
 * const { enable, disable } = useKeyboardNavigation({
 *   shortcuts: [
 *     {
 *       id: 'save',
 *       key: 's',
 *       modifiers: ['Ctrl'],
 *       handler: () => console.log('Save triggered'),
 *       description: 'Save document',
 *     },
 *     {
 *       id: 'close',
 *       key: 'Escape',
 *       handler: () => console.log('Close modal'),
 *       description: 'Close modal dialog',
 *     },
 *   ],
 * });
 *
 * // With prevent default for browser shortcuts
 * useKeyboardNavigation({
 *   shortcuts: [
 *     {
 *       id: 'search',
 *       key: 'k',
 *       modifiers: ['Ctrl'],
 *       handler: (event) => {
 *         focusSearchInput();
 *       },
 *     },
 *   ],
 *   preventDefault: true,
 * });
 *
 * // With custom target and priority
 * useKeyboardNavigation({
 *   shortcuts: [
 *     {
 *       id: 'navigate',
 *       key: 'ArrowDown',
 *       handler: () => selectNextItem(),
 *     },
 *   ],
 *   target: myRef.current,
 *   priority: 10, // Higher priority than global shortcuts
 * });
 *
 * // Conditional shortcuts
 * const [isEditing, setIsEditing] = useState(false);
 * useKeyboardNavigation({
 *   shortcuts: [
 *     {
 *       id: 'save',
 *       key: 's',
 *       modifiers: ['Ctrl'],
 *       handler: () => saveChanges(),
 *       enabled: isEditing, // Only active when editing
 *     },
 *   ],
 * });
 *
 * // Dynamic shortcuts (register/unregister)
 * const { registerShortcut, unregisterShortcut } = useKeyboardNavigation({
 *   shortcuts: [], // Start with no shortcuts
 * });
 *
 * useEffect(() => {
 *   registerShortcut({
 *     id: 'custom',
 *     key: 'x',
 *     handler: () => console.log('Custom shortcut'),
 *   });
 *
 *   return () => unregisterShortcut('custom');
 * }, []);
 * ```
 */
export const useKeyboardNavigation = (
  options: UseKeyboardNavigationOptions
): KeyboardNavigationState => {
  const {
    shortcuts,
    preventDefault = true,
    target,
    enabled = true,
    priority = 0,
    onShortcutTriggered,
  } = options;

  const shortcutsRef = useRef<Map<string, KeyboardShortcut>>(new Map());
  const isEnabledRef = useRef<boolean>(enabled);

  // Register shortcuts on mount
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    _setupGlobalListener();

    // Register all shortcuts
    shortcuts.forEach((shortcut) => {
      globalRegistry.shortcuts.set(shortcut.id, { shortcut, priority });
      shortcutsRef.current.set(shortcut.id, shortcut);
    });

    return () => {
      // Unregister all shortcuts
      shortcuts.forEach((shortcut) => {
        globalRegistry.shortcuts.delete(shortcut.id);
        shortcutsRef.current.delete(shortcut.id);
      });

      // Teardown global listener if no shortcuts remain
      if (globalRegistry.shortcuts.size === 0) {
        _teardownGlobalListener();
      }
    };
  }, [shortcuts, priority]);

  // Update shortcut enabled states when dependencies change
  useEffect(() => {
    shortcuts.forEach((shortcut) => {
      const registered = globalRegistry.shortcuts.get(shortcut.id);
      if (registered) {
        registered.shortcut = { ...registered.shortcut, enabled: shortcut.enabled };
      }
    });
  }, [shortcuts]);

  // Register a new shortcut dynamically
  const registerShortcut = useCallback((shortcut: KeyboardShortcut): void => {
    if (typeof window === 'undefined') {
      return;
    }

    _setupGlobalListener();

    globalRegistry.shortcuts.set(shortcut.id, { shortcut, priority });
    shortcutsRef.current.set(shortcut.id, shortcut);
  }, [priority]);

  // Unregister a shortcut by ID
  const unregisterShortcut = useCallback((shortcutId: string): void => {
    globalRegistry.shortcuts.delete(shortcutId);
    shortcutsRef.current.delete(shortcutId);

    if (globalRegistry.shortcuts.size === 0) {
      _teardownGlobalListener();
    }
  }, []);

  // Enable all shortcuts
  const enable = useCallback((): void => {
    isEnabledRef.current = true;
    shortcutsRef.current.forEach((shortcut) => {
      const registered = globalRegistry.shortcuts.get(shortcut.id);
      if (registered) {
        registered.shortcut.enabled = true;
      }
    });
  }, []);

  // Disable all shortcuts
  const disable = useCallback((): void => {
    isEnabledRef.current = false;
    shortcutsRef.current.forEach((shortcut) => {
      const registered = globalRegistry.shortcuts.get(shortcut.id);
      if (registered) {
        registered.shortcut.enabled = false;
      }
    });
  }, []);

  // Check if shortcuts are enabled
  const isEnabled = useCallback((): boolean => {
    return isEnabledRef.current;
  }, []);

  return {
    registerShortcut,
    unregisterShortcut,
    enable,
    disable,
    isEnabled,
  };
};

/**
 * useKeyboardShortcut Hook (convenience wrapper)
 *
 * Simplified hook for registering a single keyboard shortcut.
 *
 * @param shortcut - Keyboard shortcut configuration
 * @param enabled - Whether the shortcut is enabled (default: true)
 * @param preventDefault - Whether to prevent default behavior (default: true)
 *
 * @example
 * ```tsx
 * // Single shortcut for closing a modal
 * useKeyboardShortcut({
 *   id: 'closeModal',
 *   key: 'Escape',
 *   handler: () => onClose(),
 *   description: 'Close modal',
 * });
 *
 * // Conditional shortcut
 * const [isFormValid, setIsFormValid] = useState(false);
 * useKeyboardShortcut({
 *   id: 'submit',
 *   key: 'Enter',
 *   modifiers: ['Ctrl'],
 *   handler: () => handleSubmit(),
 *   enabled: isFormValid, // Only active when form is valid
 * });
 * ```
 */
export const useKeyboardShortcut = (
  shortcut: KeyboardShortcut,
  enabled: boolean = true,
  preventDefault: boolean = true
): void => {
  useKeyboardNavigation({
    shortcuts: [{ ...shortcut, enabled }],
    preventDefault,
  });
};

export default useKeyboardNavigation;

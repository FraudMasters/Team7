import { useEffect, useRef, useCallback } from 'react';

/**
 * Keyboard shortcut definition
 */
export interface KeyboardShortcut {
  /** Unique identifier for this shortcut */
  id: string;
  /** Key code (e.g., 'k', 'Escape', 'ArrowDown') */
  key: string;
  /** Modifier keys (Ctrl, Shift, Alt, Meta) */
  modifiers?: ('Ctrl' | 'Shift' | 'Alt' | 'Meta')[];
  /** Handler function when shortcut is triggered */
  handler: (event: KeyboardEvent) => void;
  /** Human-readable description */
  description?: string;
  /** Whether to prevent default browser behavior */
  preventDefault?: boolean;
  /** Priority for conflict resolution (higher wins) */
  priority?: number;
  /** When disabled, shortcut won't trigger */
  disabled?: boolean;
  /** Condition check before activating shortcut */
  when?: () => boolean;
}

/**
 * Hook options
 */
export interface UseKeyboardNavigationOptions {
  /** Array of keyboard shortcuts to register */
  shortcuts: KeyboardShortcut[];
  /** Default priority for shortcuts without explicit priority */
  priority?: number;
  /** Whether to prevent default behavior by default */
  preventDefault?: boolean;
  /** Whether all shortcuts in this hook are disabled */
  disabled?: boolean;
  /** Global condition check for all shortcuts */
  when?: () => boolean;
}

/**
 * Registry entry for tracking registered shortcuts
 */
interface RegistryEntry {
  shortcut: KeyboardShortcut;
  hookId: string;
  createdAt: number;
}

/**
 * Global registry for keyboard shortcuts
 * Supports priority-based conflict resolution
 */
class KeyboardShortcutRegistry {
  private entries: RegistryEntry[] = [];
  private listeners: Set<(event: KeyboardEvent) => void> = new Set();
  private globalHandler: ((event: KeyboardEvent) => void) | null = null;

  /**
   * Register shortcuts for a hook instance
   */
  register(shortcuts: KeyboardShortcut[], hookId: string): void {
    // Remove existing entries for this hook
    this.unregister(hookId);

    // Add new entries
    const now = Date.now();
    shortcuts.forEach((shortcut) => {
      this.entries.push({
        shortcut,
        hookId,
        createdAt: now,
      });
    });

    // Update global handler if needed
    this.updateGlobalHandler();
  }

  /**
   * Unregister all shortcuts for a hook instance
   */
  unregister(hookId: string): void {
    this.entries = this.entries.filter((entry) => entry.hookId !== hookId);
    this.updateGlobalHandler();
  }

  /**
   * Update the global window event handler
   */
  private updateGlobalHandler(): void {
    // Remove existing handler if present
    if (this.globalHandler) {
      window.removeEventListener('keydown', this.globalHandler);
      this.globalHandler = null;
    }

    // Add new handler if there are entries
    if (this.entries.length > 0) {
      this.globalHandler = this.handleKeyDown.bind(this);
      window.addEventListener('keydown', this.globalHandler);
    }
  }

  /**
   * Handle keyboard events with priority-based resolution
   */
  private handleKeyDown(event: KeyboardEvent): void {
    // Find all matching shortcuts
    const matchingEntries = this.entries.filter((entry) => {
      const { shortcut } = entry;

      // Check if disabled
      if (shortcut.disabled) return false;

      // Check condition
      if (shortcut.when && !shortcut.when()) return false;

      // Check key match
      if (shortcut.key.toLowerCase() !== event.key.toLowerCase()) {
        return false;
      }

      // Check modifiers
      if (shortcut.modifiers) {
        const hasCtrl = shortcut.modifiers.includes('Ctrl');
        const hasShift = shortcut.modifiers.includes('Shift');
        const hasAlt = shortcut.modifiers.includes('Alt');
        const hasMeta = shortcut.modifiers.includes('Meta');

        if (hasCtrl && !event.ctrlKey) return false;
        if (hasShift && !event.shiftKey) return false;
        if (hasAlt && !event.altKey) return false;
        if (hasMeta && !event.metaKey) return false;

        // Ensure no extra modifiers are pressed unless explicitly allowed
        const allowedModifiers = shortcut.modifiers.length;
        const actualModifiers =
          (event.ctrlKey ? 1 : 0) +
          (event.shiftKey ? 1 : 0) +
          (event.altKey ? 1 : 0) +
          (event.metaKey ? 1 : 0);

        // Allow if actual modifiers match or are fewer (e.g., Ctrl with no Shift)
        // but not if extra modifiers are pressed
        if (actualModifiers > allowedModifiers) return false;
      } else {
        // No modifiers specified - ensure none are pressed
        if (event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) {
          return false;
        }
      }

      return true;
    });

    if (matchingEntries.length === 0) return;

    // Sort by priority (higher first), then by creation time (newer first)
    matchingEntries.sort((a, b) => {
      const priorityDiff = (b.shortcut.priority || 0) - (a.shortcut.priority || 0);
      if (priorityDiff !== 0) return priorityDiff;
      return b.createdAt - a.createdAt;
    });

    // Execute highest priority shortcut
    const winner = matchingEntries[0];
    const preventDefault = winner.shortcut.preventDefault ?? true;

    if (preventDefault) {
      event.preventDefault();
      event.stopPropagation();
    }

    winner.shortcut.handler(event);
  }

  /**
   * Get all registered shortcuts for documentation
   */
  getAllShortcuts(): KeyboardShortcut[] {
    return this.entries.map((entry) => entry.shortcut);
  }

  /**
   * Clear all entries (for testing)
   */
  clear(): void {
    this.entries = [];
    this.updateGlobalHandler();
  }
}

// Global registry instance
const globalRegistry = new KeyboardShortcutRegistry();

/**
 * React hook for keyboard navigation with global registry
 * and priority-based conflict resolution
 *
 * @example
 * ```tsx
 * useKeyboardNavigation({
 *   shortcuts: [
 *     {
 *       id: 'save',
 *       key: 's',
 *       modifiers: ['Ctrl'],
 *       handler: () => saveForm(),
 *       description: 'Save current form',
 *       priority: 10,
 *     },
 *     {
 *       id: 'closeModal',
 *       key: 'Escape',
 *       handler: () => closeModal(),
 *       description: 'Close modal dialog',
 *     },
 *   ],
 *   priority: 5,
 * });
 * ```
 */
export const useKeyboardNavigation = (options: UseKeyboardNavigationOptions): void => {
  const { shortcuts, priority: defaultPriority, preventDefault, disabled, when } = options;

  // Generate unique hook ID for this component instance
  const hookIdRef = useRef(`hook-${Date.now()}-${Math.random()}`);

  // Normalize shortcuts with defaults
  const normalizedShortcuts: KeyboardShortcut[] = shortcuts.map((shortcut) => ({
    ...shortcut,
    priority: shortcut.priority ?? defaultPriority ?? 0,
    preventDefault: shortcut.preventDefault ?? preventDefault ?? true,
    disabled: shortcut.disabled ?? disabled ?? false,
    when: shortcut.when ?? when,
  }));

  // Register shortcuts on mount
  useEffect(() => {
    globalRegistry.register(normalizedShortcuts, hookIdRef.current);

    // Cleanup on unmount
    return () => {
      globalRegistry.unregister(hookIdRef.current);
    };
  }, [normalizedShortcuts]); // Re-register when shortcuts change
};

/**
 * Get all registered keyboard shortcuts (for documentation/help)
 */
export const getAllKeyboardShortcuts = (): KeyboardShortcut[] => {
  return globalRegistry.getAllShortcuts();
};

/**
 * Clear all keyboard shortcuts (for testing)
 */
export const clearKeyboardShortcuts = (): void => {
  globalRegistry.clear();
};

export default useKeyboardNavigation;

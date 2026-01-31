/**
 * Keyboard Shortcuts Utilities
 *
 * Provides utilities for managing keyboard shortcuts in the application.
 * Handles key combination parsing, validation, and formatting.
 *
 * @module utils/keyboardShortcuts
 */

/**
 * Keyboard key codes
 */
export type KeyCode =
  | 'a'
  | 'b'
  | 'c'
  | 'd'
  | 'e'
  | 'f'
  | 'g'
  | 'h'
  | 'i'
  | 'j'
  | 'k'
  | 'l'
  | 'm'
  | 'n'
  | 'o'
  | 'p'
  | 'q'
  | 'r'
  | 's'
  | 't'
  | 'u'
  | 'v'
  | 'w'
  | 'x'
  | 'y'
  | 'z'
  | '0'
  | '1'
  | '2'
  | '3'
  | '4'
  | '5'
  | '6'
  | '7'
  | '8'
  | '9'
  | 'Enter'
  | 'Escape'
  | 'Esc'
  | 'Space'
  | 'ArrowUp'
  | 'ArrowDown'
  | 'ArrowLeft'
  | 'ArrowRight'
  | 'Tab'
  | 'Home'
  | 'End'
  | 'PageUp'
  | 'PageDown'
  | 'Delete'
  | 'Backspace'
  | 'Insert'
  | 'F1'
  | 'F2'
  | 'F3'
  | 'F4'
  | 'F5'
  | 'F6'
  | 'F7'
  | 'F8'
  | 'F9'
  | 'F10'
  | 'F11'
  | 'F12';

/**
 * Modifier keys
 */
export type ModifierKey = 'Ctrl' | 'Control' | 'Alt' | 'Shift' | 'Meta' | 'Cmd';

/**
 * Keyboard shortcut configuration
 */
export interface KeyboardShortcut {
  /** Unique identifier for the shortcut */
  id: string;
  /** Key code */
  key: KeyCode;
  /** Modifier keys (Ctrl, Alt, Shift, Meta/Cmd) */
  modifiers?: ModifierKey[];
  /** Callback function when shortcut is triggered */
  handler: (event: KeyboardEvent) => void;
  /** Human-readable description */
  description?: string;
  /** Whether the shortcut is currently enabled */
  enabled?: boolean;
}

/**
 * Parsed keyboard shortcut
 */
export interface ParsedShortcut {
  /** Key code */
  key: string;
  /** Ctrl modifier */
  ctrl: boolean;
  /** Alt modifier */
  alt: boolean;
  /** Shift modifier */
  shift: boolean;
  /** Meta/Cmd modifier */
  meta: boolean;
}

/**
 * Standard keyboard shortcuts for the application
 */
export const STANDARD_SHORTCUTS: Record<string, Omit<KeyboardShortcut, 'handler'>> = {
  globalSearch: {
    id: 'globalSearch',
    key: 'k',
    modifiers: ['Ctrl'],
    description: 'Focus search input',
  },
  showHelp: {
    id: 'showHelp',
    key: '/',
    modifiers: ['Ctrl'],
    description: 'Show keyboard shortcuts help',
  },
  navigateHome: {
    id: 'navigateHome',
    key: 'Home',
    modifiers: ['Alt'],
    description: 'Navigate to home page',
  },
  navigateUp: {
    id: 'navigateUp',
    key: 'ArrowUp',
    description: 'Navigate up in lists',
  },
  navigateDown: {
    id: 'navigateDown',
    key: 'ArrowDown',
    description: 'Navigate down in lists',
  },
  selectItem: {
    id: 'selectItem',
    key: 'Enter',
    description: 'Select focused item',
  },
  closeModal: {
    id: 'closeModal',
    key: 'Escape',
    description: 'Close modal or dropdown',
  },
  saveForm: {
    id: 'saveForm',
    key: 's',
    modifiers: ['Ctrl'],
    description: 'Save current form',
  },
  toggleDarkMode: {
    id: 'toggleDarkMode',
    key: 'd',
    modifiers: ['Ctrl', 'Shift'],
    description: 'Toggle dark mode',
  },
} as const;

/**
 * Parse a keyboard shortcut string into key and modifiers
 *
 * @param shortcut - Shortcut string (e.g., "Ctrl+K", "Alt+Home", "Ctrl+Shift+S")
 * @returns Parsed shortcut object
 *
 * @throws {Error} If shortcut string is invalid
 *
 * @example
 * ```ts
 * parseShortcutString("Ctrl+K")  // { key: 'k', ctrl: true, alt: false, shift: false, meta: false }
 * parseShortcutString("Alt+Home")  // { key: 'Home', ctrl: false, alt: true, shift: false, meta: false }
 * parseShortcutString("Ctrl+Shift+S")  // { key: 's', ctrl: true, alt: false, shift: true, meta: false }
 * ```
 */
export function parseShortcutString(shortcut: string): ParsedShortcut {
  const parts = shortcut.split('+').map((p) => p.trim().toLowerCase());
  const key = parts.pop() || '';

  const modifiers = {
    ctrl: false,
    alt: false,
    shift: false,
    meta: false,
  };

  for (const part of parts) {
    switch (part) {
      case 'ctrl':
      case 'control':
        modifiers.ctrl = true;
        break;
      case 'alt':
        modifiers.alt = true;
        break;
      case 'shift':
        modifiers.shift = true;
        break;
      case 'meta':
      case 'cmd':
        modifiers.meta = true;
        break;
      default:
        throw new Error(`Invalid modifier: ${part}`);
    }
  }

  if (!key) {
    throw new Error(`Shortcut must have a key: ${shortcut}`);
  }

  return {
    key,
    ...modifiers,
  };
}

/**
 * Format a keyboard shortcut object into a human-readable string
 *
 * @param shortcut - Shortcut object or parsed shortcut
 * @returns Formatted shortcut string (e.g., "Ctrl+K", "Alt+Home")
 *
 * @example
 * ```ts
 * formatShortcut({ key: 'k', ctrl: true, alt: false, shift: false, meta: false })  // "Ctrl+K"
 * formatShortcut({ key: 'Home', ctrl: false, alt: true, shift: false, meta: false })  // "Alt+Home"
 * formatShortcut({ key: 's', ctrl: true, alt: false, shift: true, meta: false })  // "Ctrl+Shift+S"
 * ```
 */
export function formatShortcut(shortcut: ParsedShortcut | KeyboardShortcut): string {
  const parsed = 'key' in shortcut && typeof shortcut.key === 'string'
    ? shortcut as ParsedShortcut
    : _shortcutToParsed(shortcut as KeyboardShortcut);

  const parts: string[] = [];

  if (parsed.ctrl) parts.push('Ctrl');
  if (parsed.alt) parts.push('Alt');
  if (parsed.shift) parts.push('Shift');
  if (parsed.meta) parts.push(isMac() ? 'Cmd' : 'Meta');

  parts.push(_formatKey(parsed.key));

  return parts.join('+');
}

/**
 * Check if a keyboard event matches a shortcut
 *
 * @param event - Keyboard event
 * @param shortcut - Shortcut to match against
 * @returns True if event matches the shortcut
 *
 * @example
 * ```ts
 * const shortcut = { key: 'k', ctrl: true, alt: false, shift: false, meta: false };
 * const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true });
 * matchesShortcut(event, shortcut)  // true
 * ```
 */
export function matchesShortcut(
  event: KeyboardEvent,
  shortcut: ParsedShortcut | KeyboardShortcut
): boolean {
  const parsed = 'key' in shortcut && typeof shortcut.key === 'string'
    ? shortcut as ParsedShortcut
    : _shortcutToParsed(shortcut as KeyboardShortcut);

  // Normalize event key
  const eventKey = event.key.toLowerCase();

  // Check key match
  if (eventKey !== parsed.key.toLowerCase()) {
    return false;
  }

  // Check modifiers
  if (parsed.ctrl !== event.ctrlKey) return false;
  if (parsed.alt !== event.altKey) return false;
  if (parsed.shift !== event.shiftKey) return false;
  if (parsed.meta !== event.metaKey) return false;

  return true;
}

/**
 * Check if the current platform is Mac
 *
 * @returns True if running on macOS
 *
 * @example
 * ```ts
 * isMac()  // true on macOS, false on Windows/Linux
 * ```
 */
export function isMac(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  return navigator.platform.toUpperCase().indexOf('MAC') >= 0;
}

/**
 * Get the platform-specific modifier key name
 *
 * @param modifier - Modifier key
 * @returns Platform-specific modifier name (Cmd on Mac, Ctrl on others)
 *
 * @example
 * ```ts
 * getModifierKeyName('Ctrl')  // "Cmd" on Mac, "Ctrl" on Windows/Linux
 * getModifierKeyName('Meta')  // "Cmd" on Mac, "Win" on Windows
 * ```
 */
export function getModifierKeyName(modifier: ModifierKey): string {
  if (modifier === 'Ctrl' || modifier === 'Control') {
    return isMac() ? 'Cmd' : 'Ctrl';
  }
  if (modifier === 'Meta' || modifier === 'Cmd') {
    return isMac() ? 'Cmd' : 'Win';
  }
  return modifier;
}

/**
 * Format a key for display (capitalize first letter, handle special keys)
 *
 * @private
 * @param key - Key code
 * @returns Formatted key name
 */
function _formatKey(key: string): string {
  const specialKeys: Record<string, string> = {
    'arrowup': '↑',
    'arrowdown': '↓',
    'arrowleft': '←',
    'arrowright': '→',
    'enter': 'Enter',
    'escape': 'Esc',
    'esc': 'Esc',
    ' ': 'Space',
    'tab': 'Tab',
    'home': 'Home',
    'end': 'End',
    'pageup': 'Page Up',
    'pagedown': 'Page Down',
    'delete': 'Delete',
    'backspace': 'Backspace',
    'insert': 'Insert',
  };

  const lowerKey = key.toLowerCase();

  if (specialKeys[lowerKey]) {
    return specialKeys[lowerKey];
  }

  // Capitalize single letter keys
  return key.length === 1 ? key.toUpperCase() : key;
}

/**
 * Convert a KeyboardShortcut to ParsedShortcut
 *
 * @private
 * @param shortcut - Keyboard shortcut object
 * @returns Parsed shortcut object
 */
function _shortcutToParsed(shortcut: KeyboardShortcut): ParsedShortcut {
  const key = shortcut.key.toLowerCase();
  const modifiers = shortcut.modifiers || [];

  return {
    key,
    ctrl: modifiers.includes('Ctrl') || modifiers.includes('Control'),
    alt: modifiers.includes('Alt'),
    shift: modifiers.includes('Shift'),
    meta: modifiers.includes('Meta') || modifiers.includes('Cmd'),
  };
}

/**
 * Normalize a key code for comparison
 *
 * Handles case-insensitivity and special key aliases.
 *
 * @param key - Key code to normalize
 * @returns Normalized key code
 *
 * @example
 * ```ts
 * normalizeKey('Enter')  // 'enter'
 * normalizeKey('K')  // 'k'
 * normalizeKey('Escape')  // 'escape'
 * normalizeKey('Esc')  // 'escape'
 * ```
 */
export function normalizeKey(key: string): string {
  const aliases: Record<string, string> = {
    'esc': 'escape',
    'ctrl': 'control',
    'cmd': 'meta',
    'del': 'delete',
    'ins': 'insert',
    'return': 'enter',
  };

  const normalized = key.toLowerCase();
  return aliases[normalized] || normalized;
}

/**
 * Check if a key is a printable character
 *
 * @param key - Key code to check
 * @returns True if key is printable
 *
 * @example
 * ```ts
 * isPrintableKey('a')  // true
 * isPrintableKey('Enter')  // false
 * isPrintableKey(' ')  // true
 * ```
 */
export function isPrintableKey(key: string): boolean {
  const nonPrintableKeys = [
    'enter', 'escape', 'esc', 'tab', 'arrowup', 'arrowdown',
    'arrowleft', 'arrowright', 'home', 'end', 'pageup', 'pagedown',
    'delete', 'backspace', 'insert', 'f1', 'f2', 'f3', 'f4', 'f5',
    'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
  ];

  const normalized = normalizeKey(key);
  return !nonPrintableKeys.includes(normalized);
}

/**
 * Prevent default behavior for keyboard shortcuts that conflict with browser defaults
 *
 * Some shortcuts like Ctrl+S (save), Ctrl+P (print), etc. have browser defaults
 * that should be prevented when used in the application.
 *
 * @param event - Keyboard event
 * @returns True if default was prevented
 *
 * @example
 * ```ts
 * const handleKeyDown = (event: KeyboardEvent) => {
 *   preventShortcutDefaults(event);
 *   // Handle shortcut...
 * };
 * ```
 */
export function preventShortcutDefaults(event: KeyboardEvent): boolean {
  const key = event.key.toLowerCase();
  const ctrl = event.ctrlKey || event.metaKey;

  // Prevent browser defaults for common shortcuts
  const preventableShortcuts = [
    { key: 's', ctrl: true }, // Save
    { key: 'p', ctrl: true }, // Print
    { key: 'f', ctrl: true }, // Find
    { key: 'g', ctrl: true }, // Find again
    { key: 'k', ctrl: true }, // Focus search (DevTools)
    { key: 'o', ctrl: true }, // Open
  ];

  for (const shortcut of preventableShortcuts) {
    if (key === shortcut.key && ctrl === shortcut.ctrl) {
      event.preventDefault();
      return true;
    }
  }

  return false;
}

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, cleanup } from '@testing-library/react';
import { useKeyboardNavigation, getAllKeyboardShortcuts, clearKeyboardShortcuts } from './useKeyboardNavigation';

describe('useKeyboardNavigation', () => {
  beforeEach(() => {
    // Clear registry before each test
    clearKeyboardShortcuts();
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  describe('hook registration', () => {
    it('should register keyboard shortcuts on mount', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test-shortcut',
              key: 'k',
              modifiers: ['Ctrl'],
              handler,
              description: 'Test shortcut',
            },
          ],
        })
      );

      const allShortcuts = getAllKeyboardShortcuts();
      expect(allShortcuts).toHaveLength(1);
      expect(allShortcuts[0].id).toBe('test-shortcut');
    });

    it('should unregister shortcuts on unmount', () => {
      const handler = vi.fn();

      const { unmount } = renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test-shortcut',
              key: 'k',
              handler,
            },
          ],
        })
      );

      expect(getAllKeyboardShortcuts()).toHaveLength(1);

      unmount();

      expect(getAllKeyboardShortcuts()).toHaveLength(0);
    });

    it('should handle multiple shortcuts from one hook', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'shortcut-1',
              key: 'k',
              handler: handler1,
            },
            {
              id: 'shortcut-2',
              key: 'Escape',
              handler: handler2,
            },
          ],
        })
      );

      const allShortcuts = getAllKeyboardShortcuts();
      expect(allShortcuts).toHaveLength(2);
    });

    it('should handle multiple hooks with different shortcuts', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'shortcut-1',
              key: 'k',
              handler: handler1,
            },
          ],
        })
      );

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'shortcut-2',
              key: 'Escape',
              handler: handler2,
            },
          ],
        })
      );

      const allShortcuts = getAllKeyboardShortcuts();
      expect(allShortcuts).toHaveLength(2);
    });
  });

  describe('priority-based conflict resolution', () => {
    it('should execute higher priority shortcut when conflicts exist', () => {
      const lowPriorityHandler = vi.fn();
      const highPriorityHandler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'low-priority',
              key: 'k',
              modifiers: ['Ctrl'],
              handler: lowPriorityHandler,
              priority: 1,
            },
          ],
        })
      );

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'high-priority',
              key: 'k',
              modifiers: ['Ctrl'],
              handler: highPriorityHandler,
              priority: 10,
            },
          ],
        })
      );

      // Simulate Ctrl+K keypress
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        ctrlKey: true,
        bubbles: true,
      });
      window.dispatchEvent(event);

      expect(highPriorityHandler).toHaveBeenCalledTimes(1);
      expect(lowPriorityHandler).not.toHaveBeenCalled();
    });

    it('should use default priority when not specified', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'default-priority',
              key: 'k',
              handler,
            },
          ],
          priority: 5,
        })
      );

      const allShortcuts = getAllKeyboardShortcuts();
      expect(allShortcuts[0].priority).toBe(5);
    });

    it('should prefer newer shortcuts when priorities are equal', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'first',
              key: 'k',
              handler: handler1,
              priority: 5,
            },
          ],
        })
      );

      // Small delay to ensure different timestamps
      setTimeout(() => {
        renderHook(() =>
          useKeyboardNavigation({
            shortcuts: [
              {
                id: 'second',
                key: 'k',
                handler: handler2,
                priority: 5,
              },
            ],
          })
        );

        const event = new KeyboardEvent('keydown', {
          key: 'k',
          bubbles: true,
        });
        window.dispatchEvent(event);

        expect(handler2).toHaveBeenCalledTimes(1);
        expect(handler1).not.toHaveBeenCalled();
      }, 10);
    });
  });

  describe('cleanup and lifecycle', () => {
    it('should clean up event listeners on unmount', () => {
      const handler = vi.fn();
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 'k',
              handler,
            },
          ],
        })
      );

      unmount();

      // Verify cleanup happened
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );
    });

    it('should update shortcuts when dependencies change', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      const { rerender } = renderHook(
        ({ shortcuts }) =>
          useKeyboardNavigation({
            shortcuts,
          }),
        {
          initialProps: {
            shortcuts: [
              {
                id: 'shortcut-1',
                key: 'k',
                handler: handler1,
              },
            ],
          },
        }
      );

      expect(getAllKeyboardShortcuts()).toHaveLength(1);

      rerender({
        shortcuts: [
          {
            id: 'shortcut-2',
            key: 'Escape',
            handler: handler2,
          },
        ],
      });

      const allShortcuts = getAllKeyboardShortcuts();
      expect(allShortcuts).toHaveLength(1);
      expect(allShortcuts[0].id).toBe('shortcut-2');
    });
  });

  describe('keyboard event handling', () => {
    it('should prevent default when preventDefault is true', () => {
      const handler = vi.fn();
      const preventDefaultSpy = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 's',
              modifiers: ['Ctrl'],
              handler,
              preventDefault: true,
            },
          ],
        })
      );

      const event = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        bubbles: true,
      });
      Object.defineProperty(event, 'preventDefault', {
        value: preventDefaultSpy,
        writable: true,
      });

      window.dispatchEvent(event);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('should not prevent default when preventDefault is false', () => {
      const handler = vi.fn();
      const preventDefaultSpy = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 's',
              modifiers: ['Ctrl'],
              handler,
              preventDefault: false,
            },
          ],
        })
      );

      const event = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        bubbles: true,
      });
      Object.defineProperty(event, 'preventDefault', {
        value: preventDefaultSpy,
        writable: true,
      });

      window.dispatchEvent(event);

      expect(preventDefaultSpy).not.toHaveBeenCalled();
    });

    it('should match modifiers correctly', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 's',
              modifiers: ['Ctrl', 'Shift'],
              handler,
            },
          ],
        })
      );

      // Should not trigger without Shift
      const event1 = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      window.dispatchEvent(event1);
      expect(handler).not.toHaveBeenCalled();

      // Should trigger with both Ctrl and Shift
      const event2 = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
      });
      window.dispatchEvent(event2);
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('conditional shortcuts', () => {
    it('should not trigger when disabled is true', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 'k',
              handler,
              disabled: true,
            },
          ],
        })
      );

      const event = new KeyboardEvent('keydown', {
        key: 'k',
        bubbles: true,
      });
      window.dispatchEvent(event);

      expect(handler).not.toHaveBeenCalled();
    });

    it('should not trigger when when condition returns false', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 'k',
              handler,
              when: () => false,
            },
          ],
        })
      );

      const event = new KeyboardEvent('keydown', {
        key: 'k',
        bubbles: true,
      });
      window.dispatchEvent(event);

      expect(handler).not.toHaveBeenCalled();
    });

    it('should trigger when when condition returns true', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 'k',
              handler,
              when: () => true,
            },
          ],
        })
      );

      const event = new KeyboardEvent('keydown', {
        key: 'k',
        bubbles: true,
      });
      window.dispatchEvent(event);

      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('utility functions', () => {
    it('getAllKeyboardShortcuts should return all registered shortcuts', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'shortcut-1',
              key: 'k',
              handler,
              description: 'First shortcut',
            },
          ],
        })
      );

      const shortcuts = getAllKeyboardShortcuts();
      expect(shortcuts).toHaveLength(1);
      expect(shortcuts[0].id).toBe('shortcut-1');
      expect(shortcuts[0].description).toBe('First shortcut');
    });

    it('clearKeyboardShortcuts should remove all shortcuts', () => {
      const handler = vi.fn();

      renderHook(() =>
        useKeyboardNavigation({
          shortcuts: [
            {
              id: 'test',
              key: 'k',
              handler,
            },
          ],
        })
      );

      expect(getAllKeyboardShortcuts()).toHaveLength(1);

      clearKeyboardShortcuts();

      expect(getAllKeyboardShortcuts()).toHaveLength(0);
    });
  });
});

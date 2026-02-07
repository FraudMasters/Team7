import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, cleanup, act } from '@testing-library/react';
import { useOffline } from './useOffline';

// Add afterEach for cleanup
afterEach(() => {
  cleanup();
});

describe('useOffline', () => {
  // Save original navigator and window properties
  let originalNavigator: typeof navigator;
  let originalWindow: typeof window;

  beforeEach(() => {
    // Store original values
    originalNavigator = global.navigator;
    originalWindow = global.window as any;

    // Reset to default online state before each test
    vi.stubGlobal('navigator', {
      onLine: true,
    });
  });

  afterEach(() => {
    // Restore original values
    vi.restoreAllMocks();
  });

  describe('initial state', () => {
    it('should initialize with online status from navigator', () => {
      vi.stubGlobal('navigator', {
        onLine: true,
      });

      const { result } = renderHook(() => useOffline());

      expect(result.current.online).toBe(true);
      expect(result.current.offline).toBe(false);
      expect(result.current.since).toBeInstanceOf(Date);
    });

    it('should initialize with offline status from navigator', () => {
      vi.stubGlobal('navigator', {
        onLine: false,
      });

      const { result } = renderHook(() => useOffline());

      expect(result.current.online).toBe(false);
      expect(result.current.offline).toBe(true);
      expect(result.current.since).toBeInstanceOf(Date);
    });

    it('should set initial "since" timestamp to current time', () => {
      const beforeTime = new Date();
      const { result } = renderHook(() => useOffline());
      const afterTime = new Date();

      expect(result.current.since.getTime()).toBeGreaterThanOrEqual(
        beforeTime.getTime()
      );
      expect(result.current.since.getTime()).toBeLessThanOrEqual(
        afterTime.getTime()
      );
    });
  });

  describe('online/offline events', () => {
    it('should update to offline when offline event is triggered', () => {
      const { result } = renderHook(() => useOffline());

      expect(result.current.online).toBe(true);

      act(() => {
        // Simulate going offline
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      expect(result.current.online).toBe(false);
      expect(result.current.offline).toBe(true);
    });

    it('should update to online when online event is triggered', () => {
      // Start offline
      vi.stubGlobal('navigator', {
        onLine: false,
      });

      const { result } = renderHook(() => useOffline());

      expect(result.current.online).toBe(false);
      expect(result.current.offline).toBe(true);

      act(() => {
        // Simulate coming online
        const event = new Event('online');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: true });
      });

      expect(result.current.online).toBe(true);
      expect(result.current.offline).toBe(false);
    });

    it('should update "since" timestamp when status changes', () => {
      const { result } = renderHook(() => useOffline());

      const initialSince = result.current.since;

      // Wait a bit to ensure timestamp difference
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          act(() => {
            const event = new Event('offline');
            window.dispatchEvent(event);
            vi.stubGlobal('navigator', { onLine: false });
          });

          expect(result.current.since.getTime()).toBeGreaterThan(
            initialSince.getTime()
          );
          resolve();
        }, 10);
      });
    });

    it('should handle multiple online/offline transitions', () => {
      const { result } = renderHook(() => useOffline());

      expect(result.current.online).toBe(true);

      // Go offline
      act(() => {
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      expect(result.current.online).toBe(false);

      // Come back online
      act(() => {
        const event = new Event('online');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: true });
      });

      expect(result.current.online).toBe(true);

      // Go offline again
      act(() => {
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      expect(result.current.online).toBe(false);
    });
  });

  describe('event listener cleanup', () => {
    it('should remove event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useOffline());

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'online',
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'offline',
        expect.any(Function)
      );
    });

    it('should not update after unmount', () => {
      const { result, unmount } = renderHook(() => useOffline());

      const statusBeforeUnmount = result.current.online;

      unmount();

      act(() => {
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      // Status should not have changed after unmount
      expect(result.current.online).toBe(statusBeforeUnmount);
    });
  });

  describe('offline property', () => {
    it('should return inverse of online property', () => {
      vi.stubGlobal('navigator', {
        onLine: true,
      });

      const { result } = renderHook(() => useOffline());

      expect(result.current.offline).toBe(!result.current.online);

      act(() => {
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      expect(result.current.offline).toBe(!result.current.online);
    });
  });

  describe('SSR compatibility', () => {
    it('should handle missing navigator gracefully', () => {
      // Simulate SSR environment
      vi.stubGlobal('navigator', undefined as any);

      const { result } = renderHook(() => useOffline());

      // Should default to online when navigator is unavailable
      expect(result.current.online).toBe(true);
      expect(result.current.offline).toBe(false);
      expect(result.current.since).toBeInstanceOf(Date);
    });

    it('should not throw errors in SSR environment', () => {
      vi.stubGlobal('navigator', undefined as any);
      vi.stubGlobal('window', undefined as any);

      expect(() => {
        renderHook(() => useOffline());
      }).not.toThrow();
    });
  });

  describe('integration with online status checks', () => {
    it('should provide consistent status across multiple hook instances', () => {
      const { result: result1 } = renderHook(() => useOffline());
      const { result: result2 } = renderHook(() => useOffline());

      expect(result1.current.online).toBe(result2.current.online);
      expect(result1.current.offline).toBe(result2.current.offline);

      act(() => {
        const event = new Event('offline');
        window.dispatchEvent(event);
        vi.stubGlobal('navigator', { onLine: false });
      });

      expect(result1.current.online).toBe(result2.current.online);
      expect(result1.current.offline).toBe(result2.current.offline);
    });
  });

  describe('type safety', () => {
    it('should return OfflineResult with correct shape', () => {
      const { result } = renderHook(() => useOffline());

      expect(result.current).toHaveProperty('online');
      expect(result.current).toHaveProperty('offline');
      expect(result.current).toHaveProperty('since');

      expect(typeof result.current.online).toBe('boolean');
      expect(typeof result.current.offline).toBe('boolean');
      expect(result.current.since).toBeInstanceOf(Date);
    });
  });

  describe('real-world usage scenarios', () => {
    it('should work in a component that uses the status', () => {
      const { result } = renderHook(() => useOffline());

      // Simulate checking status for UI decisions
      const message = result.current.online
        ? 'Connected'
        : `Offline since ${result.current.since.toLocaleTimeString()}`;

      expect(typeof message).toBe('string');
    });

    it('should handle rapid status changes', () => {
      const { result } = renderHook(() => useOffline());

      // Simulate rapid connection changes
      for (let i = 0; i < 5; i++) {
        act(() => {
          const event = new Event(i % 2 === 0 ? 'offline' : 'online');
          window.dispatchEvent(event);
          vi.stubGlobal('navigator', { onLine: i % 2 !== 0 });
        });
      }

      // Final state should be offline (last toggle)
      expect(result.current.online).toBe(false);
      expect(result.current.offline).toBe(true);
    });
  });
});

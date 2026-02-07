import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, cleanup } from '@testing-library/react';
import { useResponsive, BREAKPOINT_VALUES, type Breakpoint } from './useResponsive';

// Add afterEach for cleanup
afterEach(() => {
  cleanup();
});

/**
 * Mock window.matchMedia and window.innerWidth for testing
 */
function mockWindowWidth(width: number) {
  // Mock window.innerWidth
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });

  // Mock matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => {
      // Parse query like "(min-width:600px)" to extract width
      const minWidthMatch = query.match(/min-width:\s*(\d+)px/);
      const maxWidthMatch = query.match(/max-width:\s*(\d+)px/);

      let matches = false;

      if (minWidthMatch) {
        const minWidth = parseInt(minWidthMatch[1], 10);
        matches = width >= minWidth;
      } else if (maxWidthMatch) {
        const maxWidth = parseInt(maxWidthMatch[1], 10);
        matches = width < maxWidth;
      }

      return {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };
    }),
  });
}

/**
 * Mock resize event
 */
function triggerResize(width: number) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });

  window.dispatchEvent(new Event('resize'));
}

describe('useResponsive', () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  describe('BREAKPOINT_VALUES constant', () => {
    it('should have correct breakpoint values', () => {
      expect(BREAKPOINT_VALUES.xs).toBe(0);
      expect(BREAKPOINT_VALUES.sm).toBe(600);
      expect(BREAKPOINT_VALUES.md).toBe(900);
      expect(BREAKPOINT_VALUES.lg).toBe(1200);
      expect(BREAKPOINT_VALUES.xl).toBe(1536);
    });

    it('should have all 5 breakpoints', () => {
      const breakpoints: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
      breakpoints.forEach((bp) => {
        expect(BREAKPOINT_VALUES[bp]).toBeDefined();
        expect(typeof BREAKPOINT_VALUES[bp]).toBe('number');
      });
    });
  });

  describe('mobile viewport (xs: 320px)', () => {
    beforeEach(() => {
      mockWindowWidth(320);
    });

    it('should return correct breakpoint flags', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isXsOnly).toBe(true);
      expect(result.current.isSmOnly).toBe(true);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(false);
      expect(result.current.isMdUp).toBe(false);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as xs', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('xs');
    });

    it('should return correct width', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.width).toBe(320);
    });

    it('up() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(false);
      expect(result.current.up('md')).toBe(false);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('down() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(true);
      expect(result.current.down('md')).toBe(true);
      expect(result.current.down('lg')).toBe(true);
      expect(result.current.down('xl')).toBe(true);
    });

    it('only() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.only('xs')).toBe(true);
      expect(result.current.only('sm')).toBe(false);
      expect(result.current.only('md')).toBe(false);
      expect(result.current.only('lg')).toBe(false);
      expect(result.current.only('xl')).toBe(false);
    });

    it('between() should work correctly', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.between('xs', 'sm')).toBe(true);
      expect(result.current.between('xs', 'md')).toBe(true);
      expect(result.current.between('sm', 'md')).toBe(false);
      expect(result.current.between('sm', 'lg')).toBe(false);
    });
  });

  describe('small viewport (sm: 700px)', () => {
    beforeEach(() => {
      mockWindowWidth(700);
    });

    it('should return correct breakpoint flags', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(true);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(false);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as sm', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('sm');
    });

    it('up() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(false);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('down() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(false);
      expect(result.current.down('md')).toBe(true);
      expect(result.current.down('lg')).toBe(true);
      expect(result.current.down('xl')).toBe(true);
    });

    it('only() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.only('xs')).toBe(false);
      expect(result.current.only('sm')).toBe(true);
      expect(result.current.only('md')).toBe(false);
      expect(result.current.only('lg')).toBe(false);
      expect(result.current.only('xl')).toBe(false);
    });

    it('between() should work correctly', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.between('xs', 'sm')).toBe(false);
      expect(result.current.between('sm', 'md')).toBe(true);
      expect(result.current.between('sm', 'lg')).toBe(true);
      expect(result.current.between('md', 'lg')).toBe(false);
    });
  });

  describe('medium viewport (md: 1000px)', () => {
    beforeEach(() => {
      mockWindowWidth(1000);
    });

    it('should return correct breakpoint flags', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as md', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('md');
    });

    it('up() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('down() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(false);
      expect(result.current.down('md')).toBe(false);
      expect(result.current.down('lg')).toBe(true);
      expect(result.current.down('xl')).toBe(true);
    });

    it('only() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.only('xs')).toBe(false);
      expect(result.current.only('sm')).toBe(false);
      expect(result.current.only('md')).toBe(true);
      expect(result.current.only('lg')).toBe(false);
      expect(result.current.only('xl')).toBe(false);
    });

    it('between() should work correctly', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.between('sm', 'lg')).toBe(true);
      expect(result.current.between('md', 'lg')).toBe(true);
      expect(result.current.between('lg', 'xl')).toBe(false);
    });
  });

  describe('large viewport (lg: 1300px)', () => {
    beforeEach(() => {
      mockWindowWidth(1300);
    });

    it('should return correct breakpoint flags', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(false);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(true);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as lg', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('lg');
    });

    it('up() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(true);
      expect(result.current.up('xl')).toBe(false);
    });

    it('down() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(false);
      expect(result.current.down('md')).toBe(false);
      expect(result.current.down('lg')).toBe(false);
      expect(result.current.down('xl')).toBe(true);
    });

    it('only() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.only('xs')).toBe(false);
      expect(result.current.only('sm')).toBe(false);
      expect(result.current.only('md')).toBe(false);
      expect(result.current.only('lg')).toBe(true);
      expect(result.current.only('xl')).toBe(false);
    });
  });

  describe('extra large viewport (xl: 1600px)', () => {
    beforeEach(() => {
      mockWindowWidth(1600);
    });

    it('should return correct breakpoint flags', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(false);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(true);
      expect(result.current.isXlUp).toBe(true);
    });

    it('should detect current breakpoint as xl', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('xl');
    });

    it('up() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(true);
      expect(result.current.up('xl')).toBe(true);
    });

    it('down() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(false);
      expect(result.current.down('md')).toBe(false);
      expect(result.current.down('lg')).toBe(false);
      expect(result.current.down('xl')).toBe(false);
    });

    it('only() should return correct values', () => {
      const { result } = renderHook(() => useResponsive());

      expect(result.current.only('xs')).toBe(false);
      expect(result.current.only('sm')).toBe(false);
      expect(result.current.only('md')).toBe(false);
      expect(result.current.only('lg')).toBe(false);
      expect(result.current.only('xl')).toBe(true);
    });
  });

  describe('window resize handling', () => {
    it('should update width on resize', () => {
      mockWindowWidth(500);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.width).toBe(500);
      expect(result.current.currentBreakpoint).toBe('xs');

      triggerResize(800);

      expect(result.current.width).toBe(800);
      expect(result.current.currentBreakpoint).toBe('sm');
    });

    it('should update breakpoint flags on resize', () => {
      mockWindowWidth(500);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.isMdUp).toBe(false);

      triggerResize(1000);

      expect(result.current.isMdUp).toBe(true);
    });

    it('should update utility methods on resize', () => {
      mockWindowWidth(500);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.up('md')).toBe(false);

      triggerResize(1000);

      expect(result.current.up('md')).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('should handle exact breakpoint boundaries', () => {
      mockWindowWidth(600);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('sm');
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.only('sm')).toBe(true);
    });

    it('should handle xl breakpoint with no upper limit', () => {
      mockWindowWidth(2000);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.currentBreakpoint).toBe('xl');
      expect(result.current.up('xl')).toBe(true);
      expect(result.current.only('xl')).toBe(true);
    });

    it('should warn on invalid between() range', () => {
      mockWindowWidth(1000);
      const { result } = renderHook(() => useResponsive());

      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});

      // Invalid: lg is after md
      result.current.between('lg', 'md');

      expect(consoleWarn).toHaveBeenCalled();
      consoleWarn.mockRestore();
    });

    it('should handle zero width (SSR)', () => {
      mockWindowWidth(0);
      const { result } = renderHook(() => useResponsive());

      expect(result.current.width).toBe(0);
      expect(result.current.currentBreakpoint).toBe('xs');
    });
  });

  describe('utility functions stability', () => {
    it('should maintain stable function references across re-renders', () => {
      mockWindowWidth(1000);
      const { result, rerender } = renderHook(() => useResponsive());

      const upFn = result.current.up;
      const downFn = result.current.down;
      const onlyFn = result.current.only;
      const betweenFn = result.current.between;

      rerender();

      expect(result.current.up).toBe(upFn);
      expect(result.current.down).toBe(downFn);
      expect(result.current.only).toBe(onlyFn);
      expect(result.current.between).toBe(betweenFn);
    });
  });

  describe('integration with React', () => {
    it('should work with useMemo', () => {
      mockWindowWidth(1000);
      const { result } = renderHook(() => useResponsive());

      const columns = result.current.up('xl') ? 4 : result.current.up('lg') ? 3 : result.current.up('md') ? 2 : 1;

      expect(columns).toBe(2);
    });

    it('should trigger re-renders on breakpoint change', () => {
      mockWindowWidth(500);
      let renderCount = 0;

      const { result } = renderHook(() => {
        renderCount++;
        return useResponsive();
      });

      const initialRenders = renderCount;
      triggerResize(1000);

      expect(renderCount).toBeGreaterThan(initialRenders);
    });
  });

  describe('SSR compatibility', () => {
    it('should handle undefined window (SSR)', () => {
      // Save original window
      const originalWindow = global.window;

      // @ts-ignore - Remove window for SSR test
      delete global.window;

      const { result } = renderHook(() => useResponsive());

      // Should provide default width to prevent errors
      expect(result.current.width).toBeDefined();

      // Restore window
      global.window = originalWindow;
    });
  });
});

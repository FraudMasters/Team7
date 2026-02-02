import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, cleanup } from '@testing-library/react';
import { useBreakpoints, BREAKPOINT_VALUES, type Breakpoint } from './useBreakpoints';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// Add afterEach for cleanup
afterEach(() => {
  cleanup();
});

/**
 * Mock window.matchMedia for breakpoint testing
 */
function mockMatchMedia(width: number) {
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

describe('useBreakpoints', () => {
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
      mockMatchMedia(320);
    });

    it('should return correct breakpoint flags', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.isXsOnly).toBe(true);
      expect(result.current.isSmOnly).toBe(true);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(false);
      expect(result.current.isMdUp).toBe(false);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as xs', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.currentBreakpoint).toBe('xs');
    });

    it('up() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(false);
      expect(result.current.up('md')).toBe(false);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('down() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.down('xs')).toBe(false);
      expect(result.current.down('sm')).toBe(true);
      expect(result.current.down('md')).toBe(true);
      expect(result.current.down('lg')).toBe(true);
    });

    it('between() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.between('xs', 'sm')).toBe(true);
      expect(result.current.between('xs', 'md')).toBe(true);
      expect(result.current.between('sm', 'md')).toBe(false);
      expect(result.current.between('md', 'lg')).toBe(false);
    });

    it('only() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.only('xs')).toBe(true);
      expect(result.current.only('sm')).toBe(false);
      expect(result.current.only('md')).toBe(false);
      expect(result.current.only('lg')).toBe(false);
      expect(result.current.only('xl')).toBe(false);
    });
  });

  describe('tablet viewport (sm: 768px)', () => {
    beforeEach(() => {
      mockMatchMedia(768);
    });

    it('should return correct breakpoint flags', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(true);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(false);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as sm', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.currentBreakpoint).toBe('sm');
    });

    it('up() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(false);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('between() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.between('xs', 'sm')).toBe(false);
      expect(result.current.between('sm', 'md')).toBe(true);
      expect(result.current.between('sm', 'lg')).toBe(true);
      expect(result.current.between('xs', 'md')).toBe(true);
    });
  });

  describe('desktop viewport (md: 1024px)', () => {
    beforeEach(() => {
      mockMatchMedia(1024);
    });

    it('should return correct breakpoint flags', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(true);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(false);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as md', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.currentBreakpoint).toBe('md');
    });

    it('up() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(false);
      expect(result.current.up('xl')).toBe(false);
    });

    it('between() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.between('md', 'lg')).toBe(true);
      expect(result.current.between('md', 'xl')).toBe(true);
      expect(result.current.between('sm', 'md')).toBe(false);
    });
  });

  describe('large desktop viewport (lg: 1400px)', () => {
    beforeEach(() => {
      mockMatchMedia(1400);
    });

    it('should return correct breakpoint flags', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(false);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(true);
      expect(result.current.isXlUp).toBe(false);
    });

    it('should detect current breakpoint as lg', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.currentBreakpoint).toBe('lg');
    });

    it('up() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(true);
      expect(result.current.up('xl')).toBe(false);
    });
  });

  describe('extra large viewport (xl: 1920px)', () => {
    beforeEach(() => {
      mockMatchMedia(1920);
    });

    it('should return correct breakpoint flags', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.isXsOnly).toBe(false);
      expect(result.current.isSmOnly).toBe(false);
      expect(result.current.isMdOnly).toBe(false);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isLgUp).toBe(true);
      expect(result.current.isXlUp).toBe(true);
    });

    it('should detect current breakpoint as xl', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.currentBreakpoint).toBe('xl');
    });

    it('up() should return true for all breakpoints', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.up('xs')).toBe(true);
      expect(result.current.up('sm')).toBe(true);
      expect(result.current.up('md')).toBe(true);
      expect(result.current.up('lg')).toBe(true);
      expect(result.current.up('xl')).toBe(true);
    });

    it('between() should work correctly', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      expect(result.current.between('lg', 'xl')).toBe(true);
      expect(result.current.between('xl', 'xs')).toBe(false); // Invalid range
    });
  });

  describe('edge cases and error handling', () => {
    beforeEach(() => {
      mockMatchMedia(1024);
    });

    it('between() should warn for invalid ranges', () => {
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      // Invalid: start >= end
      expect(result.current.between('md', 'sm')).toBe(false);

      expect(consoleWarn).toHaveBeenCalledWith(
        expect.stringContaining('Invalid between')
      );

      consoleWarn.mockRestore();
    });

    it('between() should handle non-existent breakpoints gracefully', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const theme = createTheme();
        return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      // This should not throw, just return false
      expect(() => result.current.between('xs' as Breakpoint, 'xl')).not.toThrow();
    });
  });

  describe('integration with MUI breakpoints', () => {
    it('should use MUI theme breakpoints correctly', () => {
      mockMatchMedia(900);

      const customTheme = createTheme({
        breakpoints: {
          values: {
            xs: 0,
            sm: 600,
            md: 900,
            lg: 1200,
            xl: 1536,
          },
        },
      });

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        return <ThemeProvider theme={customTheme}>{children}</ThemeProvider>;
      };

      const { result } = renderHook(() => useBreakpoints(), { wrapper });

      // At exactly 900px (md breakpoint)
      expect(result.current.isMdUp).toBe(true);
      expect(result.current.isSmUp).toBe(true);
      expect(result.current.currentBreakpoint).toBe('md');
    });
  });
});

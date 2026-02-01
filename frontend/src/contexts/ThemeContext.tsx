import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { createTheme, Theme } from '@mui/material/styles';

/**
 * Supported theme modes for the application
 */
export type ThemeMode = 'light' | 'dark';

/**
 * Theme display configuration
 */
export interface ThemeConfig {
  /** Theme mode code */
  mode: ThemeMode;
  /** Display name */
  name: string;
  /** Icon name (for UI) */
  icon: string;
}

/**
 * Supported themes configuration
 */
export const SUPPORTED_THEMES: Record<ThemeMode, ThemeConfig> = {
  light: {
    mode: 'light',
    name: 'Light',
    icon: 'light_mode',
  },
  dark: {
    mode: 'dark',
    name: 'Dark',
    icon: 'dark_mode',
  },
} as const;

/**
 * Local storage key for theme persistence
 */
const THEME_STORAGE_KEY = 'app-theme-mode';

/**
 * Theme Context State Interface
 */
interface ThemeState {
  /** Current theme mode */
  themeMode: ThemeMode;
  /** Current MUI theme object */
  theme: Theme;
  /** Toggle between light and dark mode */
  toggleTheme: () => void;
  /** Set theme mode */
  setThemeMode: (mode: ThemeMode) => void;
  /** Get theme configuration */
  getThemeConfig: (mode: ThemeMode) => ThemeConfig;
  /** Check if theme mode is supported */
  isThemeModeSupported: (mode: string) => mode is ThemeMode;
}

/**
 * Theme Context Props
 */
interface ThemeProviderProps {
  /** Children components */
  children: ReactNode;
  /** Initial theme mode (optional, defaults to localStorage or system preference) */
  initialThemeMode?: ThemeMode;
}

/**
 * Get initial theme mode from localStorage or system preference
 */
const getInitialThemeMode = (): ThemeMode => {
  // Check localStorage first
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (storedTheme && (storedTheme === 'light' || storedTheme === 'dark')) {
    return storedTheme as ThemeMode;
  }

  // Fall back to system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
};

/**
 * Create Material-UI theme based on mode
 */
const createAppTheme = (mode: ThemeMode): Theme => {
  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
      success: {
        main: '#2e7d32', // Green for matched skills
      },
      error: {
        main: '#d32f2f', // Red for missing skills
      },
      background: {
        default: mode === 'dark' ? '#121212' : '#f5f5f5',
        paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
      },
      grey: {
        200: '#eeeeee',
        800: '#424242',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none', // Keep button text in normal case
          },
        },
      },
    },
  });
};

/**
 * Theme Context
 *
 * Provides theme state and management for the application.
 * Handles theme toggling between light and dark modes.
 *
 * @example
 * ```tsx
 * // Wrap your app with ThemeProvider
 * <ThemeProvider>
 *   <App />
 * </ThemeProvider>
 *
 * // Use in components
 * const { themeMode, toggleTheme } = useThemeContext();
 *
 * // Toggle theme
 * toggleTheme();
 * ```
 */
const ThemeContext = createContext<ThemeState | undefined>(undefined);

/**
 * Theme Provider Component
 *
 * Manages application theme state and provides theme toggling functionality.
 * Handles theme changes and persists theme preference to localStorage.
 *
 * @param props - Provider props
 * @returns Theme context provider
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  initialThemeMode,
}) => {
  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    // Use initialThemeMode if provided, otherwise get from storage/system
    if (initialThemeMode) {
      return initialThemeMode;
    }
    return getInitialThemeMode();
  });

  const [theme, setTheme] = useState<Theme>(() => createAppTheme(themeMode));

  /**
   * Update HTML data-theme attribute when theme changes
   * This ensures CSS custom properties and other theme-dependent styles work correctly
   */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', themeMode);
  }, [themeMode]);

  /**
   * Toggle between light and dark mode
   */
  const toggleTheme = useCallback(() => {
    const newMode: ThemeMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
  }, [themeMode]);

  /**
   * Set theme mode
   *
   * Updates the theme mode and triggers re-render of all themed components.
   * Theme change is persisted to localStorage.
   *
   * @param newMode - Theme mode to switch to
   */
  const setThemeMode = useCallback((newMode: ThemeMode) => {
    if (!SUPPORTED_THEMES[newMode]) {
      console.warn(`Unsupported theme mode: ${newMode}. Falling back to 'light'.`);
      newMode = 'light';
    }

    // Update state
    setThemeModeState(newMode);
    setTheme(createAppTheme(newMode));

    // Persist to localStorage
    try {
      localStorage.setItem(THEME_STORAGE_KEY, newMode);
    } catch (error) {
      // Log error but don't throw - UI already updated
      console.warn('Failed to persist theme preference to localStorage:', error);
    }
  }, []);

  /**
   * Get theme configuration object
   *
   * @param mode - Theme mode
   * @returns Theme configuration object
   */
  const getThemeConfig = useCallback(
    (mode: ThemeMode): ThemeConfig => {
      return SUPPORTED_THEMES[mode] || SUPPORTED_THEMES.light;
    },
    []
  );

  /**
   * Check if a theme mode is supported
   *
   * @param mode - Theme mode to check
   * @returns True if theme mode is supported
   */
  const isThemeModeSupported = useCallback(
    (mode: string): mode is ThemeMode => {
      return mode in SUPPORTED_THEMES;
    },
    []
  );

  const contextValue: ThemeState = {
    themeMode,
    theme,
    toggleTheme,
    setThemeMode,
    getThemeConfig,
    isThemeModeSupported,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * useThemeContext Hook
 *
 * Access theme context state and functions.
 * Must be used within a ThemeProvider.
 *
 * @throws Error if used outside of ThemeProvider
 * @returns Theme context state
 *
 * @example
 * ```tsx
 * const { themeMode, toggleTheme, theme } = useThemeContext();
 *
 * // Display current theme
 * <p>Current theme: {themeMode}</p>
 *
 * // Toggle theme on button click
 * <button onClick={toggleTheme}>
 *   Toggle Theme
 * </button>
 * ```
 */
export const useThemeContext = (): ThemeState => {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error(
      'useThemeContext must be used within a ThemeProvider. ' +
        'Wrap your component tree with <ThemeProvider>.'
    );
  }

  return context;
};

export default ThemeContext;

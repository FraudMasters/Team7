import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

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
 * Emotion Theme Interface
 * Provides theme values for Emotion components
 */
export interface EmotionTheme {
  /** Current theme mode */
  mode: ThemeMode;
  /** Primary colors */
  primary: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Secondary colors */
  secondary: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Success state colors */
  success: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Error state colors */
  error: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Warning state colors */
  warning: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Info state colors */
  info: {
    main: string;
    light: string;
    dark: string;
    contrastText: string;
  };
  /** Background colors */
  background: {
    default: string;
    paper: string;
  };
  /** Grey scale colors */
  grey: {
    50: string;
    100: string;
    200: string;
    300: string;
    400: string;
    500: string;
    600: string;
    700: string;
    800: string;
    900: string;
  };
  /** Text colors */
  text: {
    primary: string;
    secondary: string;
    disabled: string;
    hint: string;
  };
  /** Divider color */
  divider: string;
  /** Spacing scale */
  spacing: {
    none: number;
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
    xxxl: string;
  };
  /** Typography settings */
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
      '5xl': string;
      '6xl': string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
    letterSpacing: {
      tight: string;
      normal: string;
      wide: string;
    };
  };
  /** Breakpoint values */
  breakpoints: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  /** Border radius values */
  borderRadius: {
    none: string;
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
    pill: string;
  };
  /** Action states */
  action: {
    disabledBackground: string;
    hover: string;
    active: string;
    focus: string;
  };
  /** Shadow values */
  shadows: {
    none: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  /** Z-index scale */
  zIndex: {
    dropdown: number;
    sticky: number;
    fixed: number;
    modalBackdrop: number;
    modal: number;
    popover: number;
    tooltip: number;
  };
  /** Transition settings */
  transitions: {
    duration: {
      shortest: number;
      shorter: number;
      short: number;
      standard: number;
      complex: number;
      enteringScreen: number;
      leavingScreen: number;
    };
    easing: {
      easeInOut: string;
      easeOut: string;
      easeIn: string;
      sharp: string;
    };
  };
}

/**
 * Emotion Theme Context State Interface
 */
interface EmotionThemeState {
  /** Current theme mode */
  themeMode: ThemeMode;
  /** Current Emotion theme object */
  theme: EmotionTheme;
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
 * Emotion Theme Context Props
 */
interface EmotionThemeProviderProps {
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
 * Create Emotion theme based on mode
 * Returns theme object compatible with Emotion's ThemeProvider
 */
const createEmotionTheme = (mode: ThemeMode): EmotionTheme => {
  const isDark = mode === 'dark';

  return {
    mode,
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#dc004e',
      light: '#f50057',
      dark: '#c51162',
      contrastText: '#ffffff',
    },
    success: {
      main: '#2e7d32',
      light: '#4caf50',
      dark: '#1b5e20',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d32f2f',
      light: '#f44336',
      dark: '#c62828',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#ed6c02',
      light: '#ff9800',
      dark: '#e65100',
      contrastText: '#ffffff',
    },
    info: {
      main: '#0288d1',
      light: '#03a9f4',
      dark: '#01579b',
      contrastText: '#ffffff',
    },
    background: {
      default: isDark ? '#121212' : '#f5f5f5',
      paper: isDark ? '#1e1e1e' : '#ffffff',
    },
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    text: {
      primary: isDark ? 'rgba(255, 255, 255, 0.87)' : 'rgba(0, 0, 0, 0.87)',
      secondary: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
      disabled: isDark ? 'rgba(255, 255, 255, 0.38)' : 'rgba(0, 0, 0, 0.38)',
      hint: isDark ? 'rgba(255, 255, 255, 0.38)' : 'rgba(0, 0, 0, 0.38)',
    },
    divider: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
    spacing: {
      none: 0,
      xs: '4px',
      sm: '8px',
      md: '16px',
      lg: '24px',
      xl: '32px',
      xxl: '40px',
      xxxl: '48px',
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        base: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
        '5xl': '3rem',
        '6xl': '3.75rem',
      },
      fontWeight: {
        light: 300,
        normal: 400,
        medium: 500,
        semibold: 600,
        bold: 700,
      },
      lineHeight: {
        tight: 1.25,
        normal: 1.5,
        relaxed: 1.75,
      },
      letterSpacing: {
        tight: '-0.025em',
        normal: '0',
        wide: '0.025em',
      },
    },
    breakpoints: {
      xs: '0px',
      sm: '600px',
      md: '960px',
      lg: '1280px',
      xl: '1920px',
    },
    borderRadius: {
      none: '0',
      xs: '2px',
      sm: '4px',
      md: '8px',
      lg: '12px',
      xl: '16px',
      full: '9999px',
      pill: '9999px',
    },
    action: {
      disabledBackground: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
      hover: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
      active: isDark ? 'rgba(255, 255, 255, 0.16)' : 'rgba(0, 0, 0, 0.12)',
      focus: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
    },
    shadows: {
      none: 'none',
      sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    },
    zIndex: {
      dropdown: 1000,
      sticky: 1020,
      fixed: 1030,
      modalBackdrop: 1040,
      modal: 1050,
      popover: 1060,
      tooltip: 1070,
    },
    transitions: {
      duration: {
        shortest: 150,
        shorter: 200,
        short: 250,
        standard: 300,
        complex: 375,
        enteringScreen: 225,
        leavingScreen: 195,
      },
      easing: {
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
      },
    },
  };
};

/**
 * Emotion Theme Context
 *
 * Provides Emotion theme state and management for the application.
 * Handles theme toggling between light and dark modes.
 *
 * @example
 * ```tsx
 * // Wrap your app with EmotionThemeProvider
 * <EmotionThemeProvider>
 *   <App />
 * </EmotionThemeProvider>
 *
 * // Use in components
 * const { themeMode, toggleTheme, theme } = useEmotionTheme();
 *
 * // Toggle theme
 * toggleTheme();
 *
 * // Access theme values in styled components
 * const StyledDiv = styled.div(({ theme }) => ({
 *   color: theme.text.primary,
 *   backgroundColor: theme.background.paper,
 * }));
 * ```
 */
const EmotionThemeContext = createContext<EmotionThemeState | undefined>(undefined);

/**
 * Emotion Theme Provider Component
 *
 * Manages application Emotion theme state and provides theme toggling functionality.
 * Handles theme changes and persists theme preference to localStorage.
 *
 * @param props - Provider props
 * @returns Emotion theme context provider
 */
export const EmotionThemeProvider: React.FC<EmotionThemeProviderProps> = ({
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

  const [theme, setTheme] = useState<EmotionTheme>(() => createEmotionTheme(themeMode));

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
    setTheme(createEmotionTheme(newMode));

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

  const contextValue: EmotionThemeState = {
    themeMode,
    theme,
    toggleTheme,
    setThemeMode,
    getThemeConfig,
    isThemeModeSupported,
  };

  return (
    <EmotionThemeContext.Provider value={contextValue}>
      {children}
    </EmotionThemeContext.Provider>
  );
};

/**
 * useEmotionTheme Hook
 *
 * Access Emotion theme context state and functions.
 * Must be used within an EmotionThemeProvider.
 *
 * @throws Error if used outside of EmotionThemeProvider
 * @returns Emotion theme context state
 *
 * @example
 * ```tsx
 * const { themeMode, toggleTheme, theme } = useEmotionTheme();
 *
 * // Display current theme
 * <p>Current theme: {themeMode}</p>
 *
 * // Toggle theme on button click
 * <button onClick={toggleTheme}>
 *   Toggle Theme
 * </button>
 *
 * // Access theme in styled components
 * const StyledBox = styled.div(({ theme }) => ({
 *   padding: theme.spacing.md,
 *   color: theme.primary.main,
 * }));
 * ```
 */
export const useEmotionTheme = (): EmotionThemeState => {
  const context = useContext(EmotionThemeContext);

  if (context === undefined) {
    throw new Error(
      'useEmotionTheme must be used within an EmotionThemeProvider. ' +
        'Wrap your component tree with <EmotionThemeProvider>.'
    );
  }

  return context;
};

export default EmotionThemeContext;

/**
 * Design Tokens
 *
 * Centralized design system tokens for the application.
 * These tokens provide a single source of truth for colors, spacing, typography, and breakpoints.
 * Use these tokens in CSS-in-JS solutions to maintain consistency across the application.
 *
 * @example
 * ```tsx
 * import { colors, spacing, typography } from './styles/tokens';
 *
 * const styles = {
 *   color: colors.primary.main,
 *   padding: spacing.md,
 *   fontSize: typography.fontSize.md,
 * };
 * ```
 */

/**
 * Color tokens
 * Matches the Material-UI palette from EmotionThemeContext
 */
export const colors = {
  /**
   * Primary brand color
   */
  primary: {
    main: '#1976d2',
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff',
  },

  /**
   * Secondary accent color
   */
  secondary: {
    main: '#dc004e',
    light: '#f50057',
    dark: '#c51162',
    contrastText: '#ffffff',
  },

  /**
   * Success state color (e.g., for matched skills)
   */
  success: {
    main: '#2e7d32',
    light: '#4caf50',
    dark: '#1b5e20',
    contrastText: '#ffffff',
  },

  /**
   * Error state color (e.g., for missing skills)
   */
  error: {
    main: '#d32f2f',
    light: '#f44336',
    dark: '#c62828',
    contrastText: '#ffffff',
  },

  /**
   * Warning state color
   */
  warning: {
    main: '#ed6c02',
    light: '#ff9800',
    dark: '#e65100',
    contrastText: '#ffffff',
  },

  /**
   * Info state color
   */
  info: {
    main: '#0288d1',
    light: '#03a9f4',
    dark: '#01579b',
    contrastText: '#ffffff',
  },

  /**
   * Background colors for light and dark themes
   */
  background: {
    /** Light theme background */
    light: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    /** Dark theme background */
    dark: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },

  /**
   * Grey scale colors
   */
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

  /**
   * Text colors
   */
  text: {
    /** Primary text - highest emphasis */
    primary: '#000000',
    /** Secondary text - medium emphasis */
    secondary: 'rgba(0, 0, 0, 0.6)',
    /** Disabled text - low emphasis */
    disabled: 'rgba(0, 0, 0, 0.38)',
    /** Hint text - lowest emphasis */
    hint: 'rgba(0, 0, 0, 0.38)',
  },

  /**
   * Divider color
   */
  divider: 'rgba(0, 0, 0, 0.12)',
} as const;

/**
 * Spacing tokens
 * Consistent spacing scale based on 8px grid system
 */
export const spacing = {
  /** 0px */
  none: 0,
  /** 4px */
  xs: '4px',
  /** 8px */
  sm: '8px',
  /** 16px */
  md: '16px',
  /** 24px */
  lg: '24px',
  /** 32px */
  xl: '32px',
  /** 40px */
  xxl: '40px',
  /** 48px */
  xxxl: '48px',
} as const;

/**
 * Typography tokens
 * Font sizes, weights, and line heights
 */
export const typography = {
  /**
   * Font family
   */
  fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',

  /**
   * Font sizes
   */
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
  },

  /**
   * Font weights
   */
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  /**
   * Line heights
   */
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },

  /**
   * Letter spacing
   */
  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
  },
} as const;

/**
 * Breakpoint tokens
 * Responsive design breakpoints
 */
export const breakpoints = {
  /** Extra small devices (phones, less than 600px) */
  xs: '0px',
  /** Small devices (landscape phones, 600px and up) */
  sm: '600px',
  /** Medium devices (tablets, 960px and up) */
  md: '960px',
  /** Large devices (desktops, 1280px and up) */
  lg: '1280px',
  /** Extra large devices (large desktops, 1920px and up) */
  xl: '1920px',
} as const;

/**
 * Border radius tokens
 */
export const borderRadius = {
  none: '0',
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
} as const;

/**
 * Shadow tokens
 * Box shadows for elevation
 */
export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
} as const;

/**
 * Z-index tokens
 * Layering hierarchy
 */
export const zIndex = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
} as const;

/**
 * Transition tokens
 * Standard transition durations and easing functions
 */
export const transitions = {
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
} as const;

/**
 * All design tokens combined
 */
export const tokens = {
  colors,
  spacing,
  typography,
  breakpoints,
  borderRadius,
  shadows,
  zIndex,
  transitions,
} as const;

export default tokens;

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
 * Includes variable font support for 2026 Design System
 */
export const typography = {
  /**
   * Variable font families - 2026 Design System
   * Inter Variable: Supports weight 100-900, width 25-151%, slant -10-0
   * Space Grotesk Variable: Supports weight 300-700, optical sizing 9-144
   */
  fontFamily: 'var(--font-family-base, "Inter Variable", "Inter", "Roboto", "Helvetica", "Arial", sans-serif)',
  fontFamilyDisplay: 'var(--font-family-display, "Space Grotesk Variable", "Space Grotesk", "Roboto", "Helvetica", "Arial", sans-serif)',
  fontFamilyMono: 'var(--font-family-mono, "SF Mono", "Monaco", "Inconsolata", "Fira Mono", monospace)',

  /**
   * Font sizes - optimized for variable fonts
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
   * Font weights - Variable font axes (wght)
   * Inter Variable supports 100-900
   * Space Grotesk Variable supports 300-700
   */
  fontWeight: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },

  /**
   * Variable font axes - for font-variation-settings
   * Use these for fine-grained control over variable fonts
   */
  fontVariation: {
    // Weight axis (wght)
    wght: {
      thin: 100,
      extralight: 200,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    // Width axis (wdth) - Inter Variable only (25-151)
    wdth: {
      compressed: 50,
      condensed: 75,
      normal: 100,
      expanded: 125,
      extraExpanded: 150,
    },
    // Optical size axis (opsz) - Space Grotesk only (9-144)
    opsz: {
      text: 12,
      subheading: 18,
      heading: 24,
      display: 36,
      poster: 72,
    },
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
 * Gradient tokens
 * CSS gradient definitions for backgrounds and effects
 */
export const gradients = {
  /**
   * Primary gradients
   */
  primary: {
    main: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
    reverse: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
    subtle: 'linear-gradient(135deg, rgba(25, 118, 210, 0.08) 0%, rgba(21, 101, 192, 0.08) 100%)',
    light: 'linear-gradient(135deg, #42a5f5 0%, #1976d2 100%)',
    lightSubtle: 'linear-gradient(135deg, rgba(66, 165, 245, 0.08) 0%, rgba(25, 118, 210, 0.08) 100%)',
  },

  /**
   * Secondary gradients
   */
  secondary: {
    main: 'linear-gradient(135deg, #dc004e 0%, #c51162 100%)',
    reverse: 'linear-gradient(135deg, #c51162 0%, #dc004e 100%)',
    subtle: 'linear-gradient(135deg, rgba(220, 0, 78, 0.08) 0%, rgba(197, 17, 98, 0.08) 100%)',
    light: 'linear-gradient(135deg, #f50057 0%, #dc004e 100%)',
    lightSubtle: 'linear-gradient(135deg, rgba(245, 0, 87, 0.08) 0%, rgba(220, 0, 78, 0.08) 100%)',
  },

  /**
   * Success gradients
   */
  success: {
    main: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
    reverse: 'linear-gradient(135deg, #2e7d32 0%, #4caf50 100%)',
    subtle: 'linear-gradient(135deg, rgba(76, 175, 80, 0.08) 0%, rgba(46, 125, 50, 0.08) 100%)',
  },

  /**
   * Error gradients
   */
  error: {
    main: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
    reverse: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
    subtle: 'linear-gradient(135deg, rgba(244, 67, 54, 0.08) 0%, rgba(211, 47, 47, 0.08) 100%)',
  },

  /**
   * Warning gradients
   */
  warning: {
    main: 'linear-gradient(135deg, #ff9800 0%, #ed6c02 100%)',
    reverse: 'linear-gradient(135deg, #ed6c02 0%, #ff9800 100%)',
    subtle: 'linear-gradient(135deg, rgba(255, 152, 0, 0.08) 0%, rgba(237, 108, 2, 0.08) 100%)',
  },

  /**
   * Info gradients
   */
  info: {
    main: 'linear-gradient(135deg, #03a9f4 0%, #0288d1 100%)',
    reverse: 'linear-gradient(135deg, #0288d1 0%, #03a9f4 100%)',
    subtle: 'linear-gradient(135deg, rgba(3, 169, 244, 0.08) 0%, rgba(2, 136, 209, 0.08) 100%)',
  },

  /**
   * Neutral gradients
   */
  neutral: {
    grey: 'linear-gradient(135deg, #9e9e9e 0%, #616161 100%)',
    greyLight: 'linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%)',
    greySubtle: 'linear-gradient(135deg, rgba(158, 158, 158, 0.08) 0%, rgba(97, 97, 97, 0.08) 100%)',
    light: 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)',
    dark: 'linear-gradient(135deg, #1e1e1e 0%, #121212 100%)',
  },

  /**
   * Rainbow gradients
   */
  rainbow: {
    main: 'linear-gradient(90deg, #f44336 0%, #ff9800 16.66%, #4caf50 33.33%, #2196f3 50%, #9c27b0 66.66%, #e91e63 83.33%, #f44336 100%)',
    subtle: 'linear-gradient(90deg, rgba(244, 67, 54, 0.3) 0%, rgba(255, 152, 0, 0.3) 16.66%, rgba(76, 175, 80, 0.3) 33.33%, rgba(33, 150, 243, 0.3) 50%, rgba(156, 39, 176, 0.3) 66.66%, rgba(233, 30, 99, 0.3) 83.33%, rgba(244, 67, 54, 0.3) 100%)',
    horizontal: 'linear-gradient(90deg, #1976d2 0%, #dc004e 50%, #2e7d32 100%)',
  },

  /**
   * Special effect gradients
   */
  effects: {
    glossy: 'linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.05) 100%)',
    glass: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
    glassDark: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%)',
    shine: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%)',
    shineDark: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%)',
  },

  /**
   * Radial gradients
   */
  radial: {
    primary: 'radial-gradient(circle, #42a5f5 0%, #1976d2 100%)',
    secondary: 'radial-gradient(circle, #f50057 0%, #dc004e 100%)',
    glow: 'radial-gradient(circle, rgba(25, 118, 210, 0.3) 0%, transparent 70%)',
    glowSuccess: 'radial-gradient(circle, rgba(76, 175, 80, 0.3) 0%, transparent 70%)',
    glowError: 'radial-gradient(circle, rgba(244, 67, 54, 0.3) 0%, transparent 70%)',
    glowWarning: 'radial-gradient(circle, rgba(255, 152, 0, 0.3) 0%, transparent 70%)',
  },

  /**
   * Overlay gradients
   */
  overlay: {
    top: 'linear-gradient(180deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%)',
    bottom: 'linear-gradient(0deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%)',
    full: 'linear-gradient(180deg, rgba(0, 0, 0, 0.6) 0%, transparent 30%, transparent 70%, rgba(0, 0, 0, 0.6) 100%)',
    subtle: 'linear-gradient(180deg, rgba(0, 0, 0, 0.05) 0%, transparent 100%)',
    subtleDark: 'linear-gradient(180deg, rgba(0, 0, 0, 0.2) 0%, transparent 100%)',
  },

  /**
   * Mesh gradients
   */
  mesh: {
    primary: 'radial-gradient(at 40% 20%, #42a5f5 0px, transparent 50%), radial-gradient(at 80% 0%, #1976d2 0px, transparent 50%), radial-gradient(at 0% 50%, #1565c0 0px, transparent 50%), radial-gradient(at 80% 50%, #42a5f5 0px, transparent 50%), radial-gradient(at 0% 100%, #1976d2 0px, transparent 50%), radial-gradient(at 80% 100%, #1565c0 0px, transparent 50%)',
    secondary: 'radial-gradient(at 40% 20%, #f50057 0px, transparent 50%), radial-gradient(at 80% 0%, #dc004e 0px, transparent 50%), radial-gradient(at 0% 50%, #c51162 0px, transparent 50%), radial-gradient(at 80% 50%, #f50057 0px, transparent 50%), radial-gradient(at 0% 100%, #dc004e 0px, transparent 50%), radial-gradient(at 80% 100%, #c51162 0px, transparent 50%)',
    colorful: 'radial-gradient(at 40% 20%, #f44336 0px, transparent 50%), radial-gradient(at 80% 0%, #ff9800 0px, transparent 50%), radial-gradient(at 0% 50%, #4caf50 0px, transparent 50%), radial-gradient(at 80% 50%, #2196f3 0px, transparent 50%), radial-gradient(at 0% 100%, #9c27b0 0px, transparent 50%), radial-gradient(at 80% 100%, #e91e63 0px, transparent 50%)',
  },

  /**
   * Utility gradients
   */
  utility: {
    fadeRight: 'linear-gradient(90deg, transparent 0%, currentColor 100%)',
    fadeLeft: 'linear-gradient(270deg, transparent 0%, currentColor 100%)',
    fadeUp: 'linear-gradient(0deg, transparent 0%, currentColor 100%)',
    fadeDown: 'linear-gradient(180deg, transparent 0%, currentColor 100%)',
    fadeIn: 'linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.05) 50%, rgba(0, 0, 0, 0.1) 100%)',
    fadeInLight: 'linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.03) 50%, rgba(0, 0, 0, 0.06) 100%)',
    fadeInDark: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.03) 50%, rgba(255, 255, 255, 0.06) 100%)',
  },
} as const;

/**
 * Animation tokens
 * Animation name definitions for use with CSS animation property
 */
export const animations = {
  /**
   * Fade animations
   */
  fade: {
    in: 'fadeIn',
    out: 'fadeOut',
    inUp: 'fadeInUp',
    inDown: 'fadeInDown',
    inLeft: 'fadeInLeft',
    inRight: 'fadeInRight',
  },

  /**
   * Slide animations
   */
  slide: {
    inUp: 'slideInUp',
    inDown: 'slideInDown',
    inLeft: 'slideInLeft',
    inRight: 'slideInRight',
    outUp: 'slideOutUp',
    outDown: 'slideOutDown',
    outLeft: 'slideOutLeft',
    outRight: 'slideOutRight',
  },

  /**
   * Zoom animations
   */
  zoom: {
    in: 'zoomIn',
    out: 'zoomOut',
    inUp: 'zoomInUp',
    inDown: 'zoomInDown',
  },

  /**
   * Bounce animations
   */
  bounce: {
    infinite: 'bounce',
    in: 'bounceIn',
    out: 'bounceOut',
  },

  /**
   * Pulse animations
   */
  pulse: {
    scale: 'pulse',
    glow: 'pulseGlow',
  },

  /**
   * Spin animations
   */
  spin: {
    normal: 'spin',
    reverse: 'spinReverse',
  },

  /**
   * Shake and wobble animations
   */
  shake: 'shake',
  wobble: 'wobble',

  /**
   * Special effect animations
   */
  effects: {
    heartbeat: 'heartbeat',
    float: 'float',
    drip: 'drip',
    jell: 'jell',
    flash: 'flash',
  },

  /**
   * Animation durations
   */
  duration: {
    fastest: '150ms',
    faster: '200ms',
    fast: '250ms',
    standard: '300ms',
    slow: '375ms',
  },

  /**
   * Animation delays
   */
  delay: {
    none: '0ms',
    short: '100ms',
    medium: '200ms',
    long: '300ms',
  },

  /**
   * Animation easing functions
   */
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  },

  /**
   * Animation fill modes
   */
  fillMode: {
    none: 'none',
    forwards: 'forwards',
    backwards: 'backwards',
    both: 'both',
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
  gradients,
  animations,
} as const;

export default tokens;

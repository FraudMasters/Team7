import React, { ReactNode } from 'react';
import { ThemeProvider as EmotionCoreThemeProvider } from '@emotion/react';
import { EmotionThemeProvider, EmotionTheme, useEmotionTheme } from '../contexts/EmotionThemeContext';

/**
 * Theme Provider Props
 */
interface ThemeProviderProps {
  /** Children components */
  children: ReactNode;
  /** Initial theme mode (optional, defaults to localStorage or system preference) */
  initialThemeMode?: 'light' | 'dark';
}

/**
 * Theme Provider Component
 *
 * Wraps the application with both Emotion's ThemeProvider and our custom EmotionThemeProvider.
 * This enables theme values to be accessed in Emotion-styled components via the theme prop.
 *
 * Emotion's ThemeProvider passes the theme object to all Emotion-styled components,
 * while our EmotionThemeProvider manages theme state (light/dark mode) and provides
 * utility functions (toggleTheme, setThemeMode).
 *
 * @example
 * ```tsx
 * // Wrap your app with ThemeProvider
 * <ThemeProvider>
 *   <App />
 * </ThemeProvider>
 *
 * // Use in styled components
 * const StyledDiv = styled.div(({ theme }) => ({
 *   color: theme.text.primary,
 *   backgroundColor: theme.background.paper,
 *   padding: theme.spacing.md,
 * }));
 *
 * // Use theme context in components
 * const MyComponent = () => {
 *   const { themeMode, toggleTheme, theme } = useEmotionTheme();
 *
 *   return (
 *     <div>
 *       <p>Current theme: {themeMode}</p>
 *       <button onClick={toggleTheme}>Toggle Theme</button>
 *     </div>
 *   );
 * };
 * ```
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  initialThemeMode,
}) => {
  /**
   * Inner component that connects EmotionThemeProvider with Emotion's ThemeProvider
   */
  const ThemeProviderConnector: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { theme } = useEmotionTheme();

    return (
      <EmotionCoreThemeProvider theme={theme}>
        {children}
      </EmotionCoreThemeProvider>
    );
  };

  return (
    <EmotionThemeProvider initialThemeMode={initialThemeMode}>
      <ThemeProviderConnector>
        {children}
      </ThemeProviderConnector>
    </EmotionThemeProvider>
  );
};

/**
 * Re-export useEmotionTheme hook for convenience
 * This allows consumers to import the hook from the same location as the provider
 */
export { useEmotionTheme } from '../contexts/EmotionThemeContext';

/**
 * Re-export EmotionTheme type for convenience
 */
export type { EmotionTheme } from '../contexts/EmotionThemeContext';

export default ThemeProvider;

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
} from '@mui/icons-material';
import { useThemeContext } from '@/contexts/ThemeContext';

/**
 * ThemeSwitcher Component
 *
 * Provides a toggle button for switching between light and dark themes.
 * Displays sun icon for light mode and moon icon for dark mode.
 *
 * Features:
 * - Shows current theme mode with appropriate icon
 * - Toggles between light and dark themes on click
 * - Integrates with ThemeContext for state management
 * - Persists theme preference to localStorage
 * - Displays tooltip indicating the alternate theme option
 *
 * @example
 * ```tsx
 * // In Layout component header
 * <ThemeSwitcher />
 * ```
 */
const ThemeSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const { themeMode, toggleTheme } = useThemeContext();
  const muiTheme = useTheme();

  /**
   * Get icon for current theme mode
   *
   * Returns the appropriate icon for each theme mode.
   * Light mode shows the sun icon, dark mode shows the moon icon.
   * The button shows what will happen when clicked (the alternate theme).
   *
   * @returns Icon component for alternate theme
   */
  const getToggleIcon = () => {
    return themeMode === 'light' ? <DarkModeIcon /> : <LightModeIcon />;
  };

  /**
   * Get aria-label for accessibility
   *
   * Returns the appropriate label for the toggle button based on current theme.
   *
   * @returns Accessibility label string
   */
  const getAriaLabel = () => {
    return themeMode === 'light'
      ? t('theme.switchToDark') || 'Switch to dark mode'
      : t('theme.switchToLight') || 'Switch to light mode';
  };

  /**
   * Get tooltip title
   *
   * Returns the tooltip text indicating what will happen when clicked.
   *
   * @returns Tooltip title string
   */
  const getTooltipTitle = () => {
    return themeMode === 'light'
      ? t('theme.switchToDark') || 'Switch to dark mode'
      : t('theme.switchToLight') || 'Switch to light mode';
  };

  return (
    <Box sx={{ ml: 1 }}>
      <Tooltip title={getTooltipTitle()} arrow>
        <IconButton
          onClick={toggleTheme}
          aria-label={getAriaLabel()}
          sx={{
            color: 'inherit',
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 1,
            padding: 1,
            transition: 'background-color 0.2s ease-in-out',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.2)',
            },
            '&:active': {
              bgcolor: 'rgba(255, 255, 255, 0.3)',
            },
          }}
        >
          {getToggleIcon()}
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default ThemeSwitcher;

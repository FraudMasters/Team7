import React from 'react';
import { Box, CircularProgress, Typography, CircularProgressProps, SxProps, Theme } from '@mui/material';

/**
 * LoadingSpinner Component Props
 */
export interface LoadingSpinnerProps {
  /** Size of the spinner in pixels */
  size?: number | string;
  /** Optional label to display below the spinner */
  label?: string;
  /** Color of the spinner */
  color?: CircularProgressProps['color'];
  /** Whether to disable the shimmer effect */
  disableShrink?: boolean;
  /** Variant of the spinner (circular or determinate) */
  variant?: 'indeterminate' | 'determinate';
  /** Progress value (only for determinate variant) */
  value?: number;
  /** Additional container styles */
  sx?: SxProps<Theme>;
  /** Thickness of the spinner circle */
  thickness?: number;
}

/**
 * LoadingSpinner Component
 *
 * A reusable loading spinner component for consistent loading states across the application.
 * Provides a standardized way to show loading indicators with optional labels.
 *
 * Features:
 * - Configurable size and color
 * - Optional label text for context
 * - Supports both indeterminate and determinate variants
 * - Theme-aware styling (works with light and dark modes)
 * - Centered layout with proper spacing
 * - Consistent with Material-UI design patterns
 *
 * @example
 * ```tsx
 * // Basic usage
 * <LoadingSpinner />
 *
 * // With custom size and label
 * <LoadingSpinner size={60} label="Loading your data..." />
 *
 * // Determinate progress
 * <LoadingSpinner variant="determinate" value={75} />
 *
 * // Custom color and styling
 * <LoadingSpinner color="secondary" sx={{ mt: 4 }} />
 * ```
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  label,
  color = 'primary',
  disableShrink = false,
  variant = 'indeterminate',
  value = 0,
  sx = {},
  thickness = 3.6,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...sx,
      }}
    >
      <CircularProgress
        size={size}
        color={color}
        disableShrink={disableShrink}
        variant={variant}
        value={value}
        thickness={thickness}
        sx={{
          marginBottom: label ? 2 : 0,
        }}
      />
      {label && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1 }}
        >
          {label}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingSpinner;

/**
 * Компонент для отображения состояния загрузки
 *
 * Показывает индикатор загрузки с опциональным текстовым сообщением.
 * Использует MUI CircularProgress для анимации загрузки.
 *
 * @example
 * ```tsx
 * <LoadingState message="Загрузка данных..." />
 * ```
 */

import { Box, CircularProgress, Typography, type CircularProgressProps } from '@mui/material';

// Интерфейс для свойств компонента LoadingState
export interface LoadingStateProps extends CircularProgressProps {
  /** Текстовое сообщение о состоянии загрузки */
  message?: string;
}

/**
 * Компонент для отображения состояния загрузки с индикатором и сообщением
 */
export function LoadingState({ message = 'Loading...', size = 40, ...props }: LoadingStateProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="200px"
      gap={2}
    >
      <CircularProgress size={size} {...props} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );
}

export default LoadingState;

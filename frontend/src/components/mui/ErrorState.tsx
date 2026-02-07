/**
 * Компонент для отображения состояния ошибки
 *
 * Показывает ошибку с заголовком, сообщением и кнопкой повтора.
 * Использует MUI Alert для отображения ошибок.
 *
 * @example
 * ```tsx
 * <ErrorState
 *   title="Ошибка загрузки"
 *   message="Не удалось загрузить данные. Попробуйте снова."
 *   onRetry={() => window.location.reload()}
 * />
 * ```
 */

import { Alert, Box, Button, Stack, Typography, type AlertProps } from '@mui/material';
import { ErrorOutline } from '@mui/icons-material';

// Интерфейс для свойств компонента ErrorState
export interface ErrorStateProps {
  /** Заголовок ошибки */
  title?: string;
  /** Подробное сообщение об ошибке */
  message?: string;
  /** Обработчик нажатия кнопки повтора */
  onRetry?: () => void;
  /** Текст кнопки повтора */
  retryText?: string;
  /** Серьезность ошибки (для MUI Alert) */
  severity?: AlertProps['severity'];
}

/**
 * Компонент для отображения состояния ошибки с возможностью повтора
 */
export function ErrorState({
  title = 'Error',
  message = 'Something went wrong.',
  onRetry,
  retryText = 'Try Again',
  severity = 'error',
}: ErrorStateProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="300px"
      px={3}
    >
      <Alert
        severity={severity}
        icon={<ErrorOutline fontSize="inherit" />}
        sx={{
          maxWidth: 500,
          width: '100%',
        }}
        action={
          onRetry && (
            <Button color="inherit" size="small" onClick={onRetry}>
              {retryText}
            </Button>
          )
        }
      >
        <Stack spacing={1}>
          <Typography variant="subtitle1" fontWeight="bold">
            {title}
          </Typography>
          <Typography variant="body2">{message}</Typography>
        </Stack>
      </Alert>
    </Box>
  );
}

export default ErrorState;

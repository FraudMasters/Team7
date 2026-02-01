import { Alert, Button, Box, SxProps, Theme } from '@mui/material';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  sx?: SxProps<Theme>;
}

export function ErrorState({ title = 'Error', message, onRetry, sx }: ErrorStateProps) {
  return (
    <Box sx={sx}>
      <Alert severity="error" action={onRetry && <Button color="inherit" size="small" onClick={onRetry}>Try Again</Button>}>
        <strong>{title}</strong> - {message}
      </Alert>
    </Box>
  );
}

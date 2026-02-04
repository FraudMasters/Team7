import { Alert, Button, Box } from '@/components/ui';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  css?: any;
}

export function ErrorState({ title = 'Error', message, onRetry, css }: ErrorStateProps) {
  return (
    <Box css={css}>
      <Alert severity="error" action={onRetry && <Button color="inherit" size="small" onClick={onRetry}>Try Again</Button>}>
        <strong>{title}</strong> - {message}
      </Alert>
    </Box>
  );
}

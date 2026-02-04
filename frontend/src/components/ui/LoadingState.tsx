import { CircularProgress, Box, Typography } from '@/components/ui';

export interface LoadingStateProps {
  message?: string;
  size?: number | string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  css?: any;
}

export function LoadingState({ message, size = 48, color = 'primary', css }: LoadingStateProps) {
  return (
    <Box
      css={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...css,
      }}
    >
      <CircularProgress size={size} color={color} />
      {message && (
        <Typography variant="body2" color="secondary" css={{ mt: '$md' }}>
          {message}
        </Typography>
      )}
    </Box>
  );
}

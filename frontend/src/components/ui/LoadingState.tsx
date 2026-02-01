import { CircularProgress, Box, Typography, SxProps, Theme } from '@mui/material';

export interface LoadingStateProps {
  message?: string;
  size?: number | string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  sx?: SxProps<Theme>;
}

export function LoadingState({ message, size = 48, color = 'primary', sx }: LoadingStateProps) {
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
      <CircularProgress size={size} color={color} />
      {message && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {message}
        </Typography>
      )}
    </Box>
  );
}

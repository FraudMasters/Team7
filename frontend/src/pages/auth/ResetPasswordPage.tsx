import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  CircularProgress,
} from '@mui/material';
import { authClient } from '@/api/auth';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Check if token exists
    if (!token) {
      setError('Invalid or missing reset token. Please request a new password reset link.');
      return;
    }

    // Basic validation
    if (!password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    // Password length validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    // Password matching validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      // Call password reset API
      await authClient.resetPassword(token, password);

      // On success, show success message and redirect to login after delay
      setSuccess(true);

      // Auto-redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      // Show user-friendly error message
      const errorMessage = err?.detail || err?.message || 'Failed to reset password. Please try again or request a new reset link.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
        <Paper sx={{ p: 4, width: '100%', maxWidth: 450 }}>
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Reset Password
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Enter your new password below
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              Password reset successfully! You can now sign in with your new password.
            </Alert>
          )}

          {!success && (
            <form onSubmit={handleSubmit}>
              <Stack spacing={3}>
                <TextField
                  label="New Password"
                  type="password"
                  fullWidth
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  autoFocus
                  disabled={isLoading}
                  helperText="Must be at least 8 characters long"
                />

                <TextField
                  label="Confirm Password"
                  type="password"
                  fullWidth
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={isLoading}
                />

                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={isLoading}
                  sx={{ mt: 2 }}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Reset Password'}
                </Button>
              </Stack>
            </form>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Remember your password?{' '}
              <Typography component="a" href="/login" color="primary" sx={{ fontWeight: 600 }}>
                Sign in
              </Typography>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stack,
  useTheme,
} from '@mui/material';
import { LockReset as LockResetIcon } from '@mui/icons-material';
import { passwordResetRequest } from '@/api/auth';

interface FormErrors {
  email?: string;
  general?: string;
}

const PasswordResetPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [generalError, setGeneralError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setGeneralError('');
    setSuccessMessage('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await passwordResetRequest(email.trim());

      // Show success message
      setSuccessMessage(
        'If an account exists with this email, you will receive password reset instructions shortly.'
      );
      setEmail('');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while processing your request. Please try again.';
      setGeneralError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      {/* Skip Link for Keyboard Users */}
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          top: 0,
          zIndex: 9999,
          '&:focus': {
            left: '10px',
            top: '10px',
            bgcolor: 'primary.main',
            color: 'white',
            p: 2,
            borderRadius: 1,
          },
        }}
      >
        Skip to main content
      </Box>

      <Container maxWidth="sm">
        <Box
          sx={{
            animation: 'fadeInUp 0.6s ease-out both',
            '@keyframes fadeInUp': {
              '0%': {
                opacity: 0,
                transform: 'translateY(20px)',
              },
              '100%': {
                opacity: 1,
                transform: 'translateY(0)',
              },
            },
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: 3,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 3,
                mx: 'auto',
                color: 'white',
              }}
            >
              <LockResetIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
              }}
            >
              Reset Password
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Enter your email to receive password reset instructions
            </Typography>
          </Box>

          {/* Password Reset Form Card */}
          <Card
            sx={{
              boxShadow: 3,
              animation: 'fadeInUp 0.5s ease-out 0.2s both',
            }}
          >
            <CardContent sx={{ p: 4 }}>
              {generalError && (
                <Alert severity="error" sx={{ mb: 3 }} role="alert">
                  {generalError}
                </Alert>
              )}

              {successMessage && (
                <Alert severity="success" sx={{ mb: 3 }} role="status">
                  {successMessage}
                </Alert>
              )}

              <Box
                component="form"
                onSubmit={handleSubmit}
                noValidate
                id="main-content"
                aria-label="Password reset form"
              >
                <Stack spacing={3}>
                  {/* Email Field */}
                  <TextField
                    label="Email Address"
                    type="email"
                    autoComplete="email"
                    required
                    fullWidth
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (errors.email) {
                        setErrors({ ...errors, email: undefined });
                      }
                    }}
                    error={!!errors.email}
                    helperText={errors.email}
                    disabled={isLoading || !!successMessage}
                    autoFocus
                    aria-describedby={errors.email ? 'email-error' : undefined}
                  />

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={isLoading || !!successMessage}
                    sx={{
                      py: 1.5,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                      },
                    }}
                  >
                    {isLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Send Reset Instructions'
                    )}
                  </Button>
                </Stack>
              </Box>
            </CardContent>
          </Card>

          {/* Footer Links */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Remember your password?{' '}
              <Link
                to="/login"
                style={{
                  color: theme.palette.primary.main,
                  textDecoration: 'none',
                  fontWeight: 600,
                }}
              >
                Sign in
              </Link>
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default PasswordResetPage;

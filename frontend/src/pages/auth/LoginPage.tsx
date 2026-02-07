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
import { Lock as LockIcon } from '@mui/icons-material';
import { login } from '@/api/auth';
import { useAuthContext } from '@/contexts/AuthContext';

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { login: authLogin } = useAuthContext();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [generalError, setGeneralError] = useState('');

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

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setGeneralError('');
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Call login API and update auth context
      const response = await login(email.trim(), password);
      await authLogin(email.trim(), password);

      // Check if there's a saved redirect location
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      sessionStorage.removeItem('redirectAfterLogin');

      // Redirect to saved location or default dashboard
      navigate(redirectPath || '/recruiter/dashboard');
    } catch (error) {
      // Handle API errors
      const errorMessage = error instanceof Error ? error.message : 'An error occurred during login. Please try again.';
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
              <LockIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
              }}
            >
              Welcome Back
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Sign in to your AgentHR account
            </Typography>
          </Box>

          {/* Login Form Card */}
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

              <Box
                component="form"
                onSubmit={handleSubmit}
                noValidate
                id="main-content"
                aria-label="Login form"
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
                    disabled={isLoading}
                    autoFocus
                    aria-describedby={errors.email ? 'email-error' : undefined}
                  />

                  {/* Password Field */}
                  <TextField
                    label="Password"
                    type="password"
                    autoComplete="current-password"
                    required
                    fullWidth
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) {
                        setErrors({ ...errors, password: undefined });
                      }
                    }}
                    error={!!errors.password}
                    helperText={errors.password}
                    disabled={isLoading}
                    aria-describedby={errors.password ? 'password-error' : undefined}
                  />

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={isLoading}
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
                      'Sign In'
                    )}
                  </Button>
                </Stack>
              </Box>
            </CardContent>
          </Card>

          {/* Footer Links */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Link
                to="/register"
                style={{
                  color: theme.palette.primary.main,
                  textDecoration: 'none',
                  fontWeight: 600,
                }}
              >
                Sign up
              </Link>
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;

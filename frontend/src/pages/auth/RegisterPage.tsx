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
import { PersonAdd as PersonAddIcon } from '@mui/icons-material';
import { register } from '@/api/auth';

interface FormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [generalError, setGeneralError] = useState('');

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): boolean => {
    // Password must be at least 8 characters with uppercase, lowercase, and number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(password);
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!firstName.trim()) {
      newErrors.firstName = 'First name is required';
    } else if (firstName.trim().length < 2) {
      newErrors.firstName = 'First name must be at least 2 characters';
    }

    if (!lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    } else if (lastName.trim().length < 2) {
      newErrors.lastName = 'Last name must be at least 2 characters';
    }

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (!validatePassword(password)) {
      newErrors.password =
        'Password must be at least 8 characters with uppercase, lowercase, and number';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      // Call registration API
      const fullName = `${firstName.trim()} ${lastName.trim()}`.trim();
      await register({
        email: email.trim(),
        password,
        full_name: fullName || undefined,
      });

      // Successful registration - redirect to login with success message
      navigate('/login', {
        state: { message: 'Registration successful! Please sign in.' },
      });
    } catch (error) {
      // Handle API errors
      const errorMessage = error instanceof Error ? error.message : 'An error occurred during registration. Please try again.';
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
              <PersonAddIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
              }}
            >
              Create Account
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Join AgentHR to streamline your hiring process
            </Typography>
          </Box>

          {/* Register Form Card */}
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
                aria-label="Registration form"
              >
                <Stack spacing={3}>
                  {/* Name Fields */}
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                    <TextField
                      label="First Name"
                      type="text"
                      autoComplete="given-name"
                      required
                      fullWidth
                      value={firstName}
                      onChange={(e) => {
                        setFirstName(e.target.value);
                        if (errors.firstName) {
                          setErrors({ ...errors, firstName: undefined });
                        }
                      }}
                      error={!!errors.firstName}
                      helperText={errors.firstName || 'Your legal first name'}
                      disabled={isLoading}
                      autoFocus
                      aria-describedby={errors.firstName ? 'firstName-error' : 'firstName-helper'}
                    />
                    <TextField
                      label="Last Name"
                      type="text"
                      autoComplete="family-name"
                      required
                      fullWidth
                      value={lastName}
                      onChange={(e) => {
                        setLastName(e.target.value);
                        if (errors.lastName) {
                          setErrors({ ...errors, lastName: undefined });
                        }
                      }}
                      error={!!errors.lastName}
                      helperText={errors.lastName || 'Your legal last name'}
                      disabled={isLoading}
                      aria-describedby={errors.lastName ? 'lastName-error' : 'lastName-helper'}
                    />
                  </Stack>

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
                    helperText={errors.email || "We'll send account updates to this address"}
                    disabled={isLoading}
                    aria-describedby={errors.email ? 'email-error' : 'email-helper'}
                  />

                  {/* Password Field */}
                  <TextField
                    label="Password"
                    type="password"
                    autoComplete="new-password"
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
                    helperText={errors.password || 'Must be 8+ characters with uppercase, lowercase, and number'}
                    disabled={isLoading}
                    aria-describedby={errors.password ? 'password-error' : 'password-helper'}
                  />

                  {/* Confirm Password Field */}
                  <TextField
                    label="Confirm Password"
                    type="password"
                    autoComplete="new-password"
                    required
                    fullWidth
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (errors.confirmPassword) {
                        setErrors({ ...errors, confirmPassword: undefined });
                      }
                    }}
                    error={!!errors.confirmPassword}
                    helperText={errors.confirmPassword || 'Re-enter your password to confirm'}
                    disabled={isLoading}
                    aria-describedby={
                      errors.confirmPassword ? 'confirmPassword-error' : 'confirmPassword-helper'
                    }
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
                      'Create Account'
                    )}
                  </Button>
                </Stack>
              </Box>
            </CardContent>
          </Card>

          {/* Footer Links */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{' '}
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

export default RegisterPage;

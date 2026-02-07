import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Link,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  PersonAdd as RegisterIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useAuth } from 'react-oidc-context';

/**
 * Form state interface for registration
 */
interface RegistrationForm {
  email: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
}

/**
 * Form error state interface
 */
interface FormErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  agreeToTerms?: string;
}

/**
 * RegisterPage Component
 *
 * Registration page that initiates OIDC registration flow with Keycloak.
 * Since we're using OIDC with Keycloak, the actual registration happens
 * on the Keycloak server. This page serves as the entry point to trigger
 * the registration redirect.
 *
 * Features:
 * - Redirects to Keycloak registration page when register button is clicked
 * - Visual form for user reference (actual registration on Keycloak)
 * - Terms and conditions agreement checkbox
 * - Email verification information
 * - Provides link back to login page
 *
 * @example
 * ```tsx
 * <Route path="/register" element={<RegisterPage />} />
 * ```
 */
const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();

  // Form state
  const [formData, setFormData] = React.useState<RegistrationForm>({
    email: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false,
  });

  // Form validation errors
  const [errors, setErrors] = React.useState<FormErrors>({});

  /**
   * Validate form fields
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Terms agreement validation
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle input field changes
   */
  const handleInputChange = (field: keyof RegistrationForm) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value,
    }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  /**
   * Handle register button click
   * Triggers OIDC registration redirect to Keycloak
   */
  const handleRegister = () => {
    if (validateForm()) {
      // Trigger OIDC registration flow
      // Keycloak will handle the actual registration
      auth.signinRedirect();
    }
  };

  /**
   * Handle login link click
   * Navigates back to login page
   */
  const handleLogin = () => {
    navigate('/login', { state: { from: location.state } });
  };

  /**
   * Redirect authenticated users away from registration page
   */
  React.useEffect(() => {
    if (auth.user && !auth.auth.isLoading) {
      navigate('/', { replace: true });
    }
  }, [auth.user, auth.auth.isLoading, navigate]);

  // Password strength indicator
  const getPasswordStrength = () => {
    const { password } = formData;
    if (!password) return { strength: 0, label: '', color: '' };

    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    const levels = [
      { strength: 1, label: 'Weak', color: '#f44336' },
      { strength: 2, label: 'Fair', color: '#ff9800' },
      { strength: 3, label: 'Good', color: '#2196f3' },
      { strength: 4, label: 'Strong', color: '#4caf50' },
    ];

    return levels[strength - 1] || { strength: 0, label: 'Too short', color: '#9e9e9e' };
  };

  const passwordStrength = getPasswordStrength();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'success.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 2,
              }}
            >
              <RegisterIcon sx={{ fontSize: 36, color: 'white' }} />
            </Box>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
              Create Account
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Join the AgentHR platform today
            </Typography>
          </Box>

          {/* Info Alert about Email Verification */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              After registration, you'll receive a verification email. Please click the link
              in the email to activate your account.
            </Typography>
          </Alert>

          {/* Registration Form */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Email Field */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Email Address
              </Typography>
              <TextField
                fullWidth
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleInputChange('email')}
                error={!!errors.email}
                helperText={errors.email}
                disabled={auth.isLoading}
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Box>

            {/* Password Field */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Password
              </Typography>
              <TextField
                fullWidth
                type="password"
                placeholder="Create a password"
                value={formData.password}
                onChange={handleInputChange('password')}
                error={!!errors.password}
                helperText={errors.password}
                disabled={auth.isLoading}
                InputProps={{
                  startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
              {/* Password Strength Indicator */}
              {formData.password && (
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        flex: 1,
                        height: 4,
                        bgcolor: 'divider',
                        borderRadius: 2,
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          width: `${passwordStrength.strength * 25}%`,
                          height: '100%',
                          bgcolor: passwordStrength.color,
                          transition: 'all 0.3s ease',
                        }}
                      />
                    </Box>
                    <Typography variant="caption" sx={{ color: passwordStrength.color }}>
                      {passwordStrength.label}
                    </Typography>
                  </Box>
                </Box>
              )}
            </Box>

            {/* Confirm Password Field */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Confirm Password
              </Typography>
              <TextField
                fullWidth
                type="password"
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleInputChange('confirmPassword')}
                error={!!errors.confirmPassword}
                helperText={errors.confirmPassword}
                disabled={auth.isLoading}
                InputProps={{
                  startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Box>

            {/* Terms and Conditions */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.agreeToTerms}
                  onChange={handleInputChange('agreeToTerms')}
                  color="primary"
                  disabled={auth.isLoading}
                />
              }
              label={
                <Typography variant="body2">
                  I agree to the{' '}
                  <Link component="button" variant="body2">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link component="button" variant="body2">
                    Privacy Policy
                  </Link>
                </Typography>
              }
            />
            {errors.agreeToTerms && (
              <Typography variant="caption" color="error" sx={{ mt: -1, ml: 3 }}>
                {errors.agreeToTerms}
              </Typography>
            )}

            {/* Register Button */}
            <Button
              fullWidth
              variant="contained"
              size="large"
              startIcon={auth.isLoading ? <CircularProgress size={20} color="inherit" /> : <CheckIcon />}
              onClick={handleRegister}
              disabled={auth.isLoading}
              sx={{
                py: 1.5,
                mt: 2,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
              }}
            >
              {auth.isLoading ? 'Creating account...' : 'Create Account'}
            </Button>

            {/* Divider */}
            <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
              <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
              <Typography variant="body2" sx={{ mx: 2, color: 'text.secondary' }}>
                Already have an account?
              </Typography>
              <Box sx={{ flex: 1, height: 1, bgcolor: 'divider' }} />
            </Box>

            {/* Login Link */}
            <Box sx={{ textAlign: 'center' }}>
              <Link
                component="button"
                variant="body2"
                onClick={handleLogin}
                sx={{ fontWeight: 600, color: 'primary.main' }}
              >
                Sign in instead
              </Link>
            </Box>
          </Box>
        </Paper>

        {/* Additional Information */}
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Alert severity="success" variant="outlined">
            <Typography variant="body2">
              <CheckIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
              Your data is secure and protected by enterprise-grade security
            </Typography>
          </Alert>
        </Box>
      </Container>
    </Box>
  );
};

export default RegisterPage;

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { VerifiedUser as VerifiedUserIcon } from '@mui/icons-material';
import { verifyEmail } from '@/api/auth';

const EmailVerificationPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [tokenValid, setTokenValid] = useState(false);

  useEffect(() => {
    const verifyEmailToken = async () => {
      const token = searchParams.get('token');

      if (!token) {
        setErrorMessage('Invalid verification link. No token provided.');
        setIsLoading(false);
        return;
      }

      try {
        await verifyEmail(token);
        setSuccessMessage('Your email has been successfully verified! You can now sign in to your account.');
        setTokenValid(true);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'An error occurred while verifying your email. The token may be invalid or expired.';
        setErrorMessage(errorMsg);
        setTokenValid(false);
      } finally {
        setIsLoading(false);
      }
    };

    verifyEmailToken();
  }, [searchParams]);

  const handleLoginClick = () => {
    navigate('/auth/login');
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
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 3,
                mx: 'auto',
                color: 'white',
              }}
            >
              <VerifiedUserIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                mb: 1,
              }}
            >
              Email Verification
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {isLoading ? 'Verifying your email address...' : tokenValid ? 'Email Verified' : 'Verification Failed'}
            </Typography>
          </Box>

          {/* Verification Status Card */}
          <Card
            sx={{
              boxShadow: 3,
              animation: 'fadeInUp 0.5s ease-out 0.2s both',
            }}
          >
            <CardContent sx={{ p: 4 }} id="main-content">
              {isLoading && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    py: 3,
                  }}
                >
                  <CircularProgress size={48} sx={{ mb: 3 }} />
                  <Typography variant="body1" color="text.secondary">
                    Please wait while we verify your email...
                  </Typography>
                </Box>
              )}

              {!isLoading && errorMessage && (
                <>
                  <Alert severity="error" sx={{ mb: 3 }} role="alert">
                    {errorMessage}
                  </Alert>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      The verification link may have expired or is invalid. Please request a new verification email.
                    </Typography>
                    <Button
                      fullWidth
                      variant="outlined"
                      onClick={handleLoginClick}
                      sx={{
                        py: 1.5,
                      }}
                    >
                      Back to Sign In
                    </Button>
                  </Box>
                </>
              )}

              {!isLoading && successMessage && (
                <>
                  <Alert severity="success" sx={{ mb: 3 }} role="status">
                    {successMessage}
                  </Alert>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      size="large"
                      onClick={handleLoginClick}
                      sx={{
                        py: 1.5,
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                        },
                      }}
                    >
                      Proceed to Sign In
                    </Button>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>

          {/* Footer Links */}
          {!isLoading && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Need help?{' '}
                <Link
                  to="/"
                  style={{
                    color: theme.palette.primary.main,
                    textDecoration: 'none',
                    fontWeight: 600,
                  }}
                >
                  Go to Homepage
                </Link>
              </Typography>
            </Box>
          )}
        </Box>
      </Container>
    </Box>
  );
};

export default EmailVerificationPage;

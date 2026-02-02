import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Stack,
  Box,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Work as WorkIcon, BusinessCenter as BusinessIcon } from '@mui/icons-material';

interface RoleCard {
  title: string;
  description: string;
  icon: React.ReactElement;
  gradient: string;
  path: string;
  buttonText: string;
}

const roles: RoleCard[] = [
  {
    title: 'Job Seeker',
    description: 'Find your dream job with AI-powered matching and intelligent recommendations',
    icon: <WorkIcon sx={{ fontSize: 48 }} />,
    gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    path: '/jobs',
    buttonText: 'Browse Jobs',
  },
  {
    title: 'Recruiter',
    description: 'Source top talent with advanced analytics and workflow management',
    icon: <BusinessIcon sx={{ fontSize: 48 }} />,
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
    path: '/recruiter/dashboard',
    buttonText: 'Go to Dashboard',
  },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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

      <Container maxWidth="lg">
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
          <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 10 } }}>
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', md: '4rem' },
                fontWeight: 700,
                mb: 2,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AgentHR
            </Typography>
            <Typography variant="h5" color="text.secondary" component="h2">
              AI-Powered Recruitment Platform
            </Typography>
          </Box>

          {/* Role Cards */}
          <nav aria-label="Select your role" id="main-content">
            <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={4}
            justifyContent="center"
            alignItems="stretch"
            role="list"
          >
            {roles.map((role, index) => (
              <Card
                key={role.title}
                component="article"
                onClick={() => navigate(role.path)}
                tabIndex={0}
                role="listitem"
                aria-label={`Select ${role.title} role: ${role.description}`}
                sx={{
                  flex: 1,
                  maxWidth: { xs: '100%', md: 400 },
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  animation: `fadeInUp 0.5s ease-out ${200 + index * 100}ms both`,
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
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 8,
                  },
                  '&:focus-visible': {
                    outline: '3px solid',
                    outlineColor: 'primary.main',
                    outlineOffset: '4px',
                  },
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    navigate(role.path);
                  }
                }}
              >
                <CardContent sx={{ p: 4, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box
                    sx={{
                      width: 64,
                      height: 64,
                      borderRadius: 3,
                      background: role.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 3,
                      color: 'white',
                    }}
                    aria-hidden="true"
                  >
                    {role.icon}
                  </Box>
                  <Typography variant="h4" fontWeight={700} gutterBottom component="h3">
                    {role.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4, flexGrow: 1 }}>
                    {role.description}
                  </Typography>
                  <Box
                    component="span"
                    sx={{
                      py: 1.5,
                      px: 3,
                      borderRadius: 2,
                      background: role.gradient,
                      color: 'white',
                      textAlign: 'center',
                      fontWeight: 600,
                      display: 'inline-block',
                    }}
                    aria-label={`Button: ${role.buttonText}`}
                  >
                    {role.buttonText}
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
          </nav>
        </Box>
      </Container>
    </Box>
  );
};

export default LandingPage;

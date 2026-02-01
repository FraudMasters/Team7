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
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

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
      <Container maxWidth="lg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
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
            <Typography variant="h5" color="text.secondary">
              AI-Powered Recruitment Platform
            </Typography>
          </Box>

          {/* Role Cards */}
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={4}
            justifyContent="center"
            alignItems="stretch"
          >
            {roles.map((role, index) => (
              <MotionCard
                key={role.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.1 }}
                whileHover={{ y: -4 }}
                onClick={() => navigate(role.path)}
                sx={{
                  flex: 1,
                  maxWidth: { xs: '100%', md: 400 },
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    boxShadow: 8,
                  },
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
                  >
                    {role.icon}
                  </Box>
                  <Typography variant="h4" fontWeight={700} gutterBottom>
                    {role.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4, flexGrow: 1 }}>
                    {role.description}
                  </Typography>
                  <Box
                    sx={{
                      py: 1.5,
                      px: 3,
                      borderRadius: 2,
                      background: role.gradient,
                      color: 'white',
                      textAlign: 'center',
                      fontWeight: 600,
                    }}
                  >
                    {role.buttonText}
                  </Box>
                </CardContent>
              </MotionCard>
            ))}
          </Stack>
        </motion.div>
      </Container>
    </Box>
  );
};

export default LandingPage;

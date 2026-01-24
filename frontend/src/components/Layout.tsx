import React, { ReactNode } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  IconButton,
} from '@mui/material';
import {
  Description as ResumeIcon,
  CloudUpload as UploadIcon,
  Analytics as AnalysisIcon,
  Compare as CompareIcon,
} from '@mui/icons-material';

/**
 * Layout Component
 *
 * Provides consistent app structure with navigation bar and main content area.
 * Uses React Router Outlet to render child routes.
 */
interface LayoutProps {
  children?: ReactNode;
}

const Layout: React.FC<LayoutProps> = () => {
  const location = useLocation();

  // Navigation items configuration
  const navItems = [
    { label: 'Home', path: '/', icon: <ResumeIcon /> },
    { label: 'Upload Resume', path: '/upload', icon: <UploadIcon /> },
    { label: 'Results', path: '/results', icon: <AnalysisIcon /> },
    { label: 'Compare', path: '/compare', icon: <CompareIcon /> },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar / Navigation */}
      <AppBar position="static" elevation={2}>
        <Container maxWidth="lg">
          <Toolbar disableGutters>
            {/* Logo / Brand */}
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
              <ResumeIcon sx={{ mr: 1, fontSize: 32 }} />
              <Typography
                variant="h6"
                component={Link}
                to="/"
                sx={{
                  fontWeight: 700,
                  color: 'inherit',
                  textDecoration: 'none',
                  letterSpacing: '-0.5px',
                }}
              >
                Resume Analysis Platform
              </Typography>
            </Box>

            {/* Navigation Links */}
            <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path ||
                  (item.path !== '/' && location.pathname.startsWith(item.path));

                return (
                  <Button
                    key={item.path}
                    component={Link}
                    to={item.path}
                    startIcon={item.icon}
                    sx={{
                      color: isActive ? 'inherit' : 'rgba(255, 255, 255, 0.7)',
                      bgcolor: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                      fontWeight: isActive ? 600 : 400,
                      textTransform: 'none',
                      borderRadius: 1,
                      px: 2,
                      '&:hover': {
                        bgcolor: 'rgba(255, 255, 255, 0.15)',
                        color: 'inherit',
                      },
                    }}
                  >
                    {item.label}
                  </Button>
                );
              })}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Main Content Area */}
      <Box sx={{ flexGrow: 1, py: 4 }}>
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: (theme) =>
            theme.palette.mode === 'light'
              ? theme.palette.grey[200]
              : theme.palette.grey[800],
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            {'© '}
            {new Date().getFullYear()}
            {' Iconicompany. AI-powered resume analysis platform.'}
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;

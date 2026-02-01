import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Paper,
  BottomNavigation,
  BottomNavigationAction,
} from '@mui/material';
import {
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
  Description as DescriptionIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
}

const navItems: NavItem[] = [
  { label: 'Search', path: '/jobs', icon: <SearchIcon /> },
  { label: 'Saved', path: '/jobs/saved', icon: <BookmarkIcon /> },
  { label: 'Applications', path: '/jobs/applications', icon: <DescriptionIcon /> },
  { label: 'Profile', path: '/profile', icon: <PersonIcon /> },
];

const JobSeekerLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [value, setValue] = useState(0);

  // Update active tab based on current route
  useEffect(() => {
    const index = navItems.findIndex((item) =>
      location.pathname === item.path || location.pathname.startsWith(item.path + '/')
    );
    if (index >= 0) {
      setValue(index);
    }
  }, [location.pathname]);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
    navigate(navItems[newValue].path);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: 'background.default',
        pb: 7,
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

      {/* Sticky Top AppBar */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar sx={{ justifyContent: 'center' }}>
          <Typography
            variant="h6"
            component="h1"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AgentHR
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box
        component="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          p: 2,
        }}
        tabIndex={-1}
      >
        <Outlet />
      </Box>

      {/* Bottom Navigation */}
      <Paper
        component="nav"
        aria-label="Main navigation"
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          elevation: 3,
          borderRadius: 0,
          zIndex: (theme) => theme.zIndex.appBar - 1,
        }}
      >
        <BottomNavigation
          value={value}
          onChange={handleChange}
          aria-label="Job seeker navigation"
          showLabels
        >
          {navItems.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              icon={item.icon}
              aria-current={value === index ? 'page' : undefined}
              aria-label={`Navigate to ${item.label}`}
            />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
};

export default JobSeekerLayout;

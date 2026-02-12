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
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery,
  useTheme,
  IconButton,
  Collapse,
  CircularProgress,
  Backdrop,
  Fade,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  CheckCircle as ApproveIcon,
  RateReview as ReviewIcon,
} from '@mui/icons-material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useAuthContext } from '@/contexts/AuthContext';
import NotificationCenter from '@/components/NotificationCenter';

// Drawer width for desktop sidebar
const DRAWER_WIDTH = 280;

// Navigation item interface
interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
  children?: NavItem[];
}

// Navigation section interface
interface NavSection {
  title?: string;
  items: NavItem[];
}

// Navigation sections for hiring manager - simplified compared to recruiter
const navSections: NavSection[] = [
  {
    items: [
      { label: 'Dashboard', path: '/hiring-manager/dashboard', icon: <DashboardIcon /> },
    ],
  },
  {
    title: 'Candidates',
    items: [
      { label: 'Review Queue', path: '/hiring-manager/review-queue', icon: <ReviewIcon /> },
      { label: 'Approvals', path: '/hiring-manager/approvals', icon: <ApproveIcon /> },
    ],
  },
  {
    title: 'Schedule',
    items: [
      { label: 'Interviews', path: '/hiring-manager/schedule', icon: <ScheduleIcon /> },
    ],
  },
  {
    title: 'Account',
    items: [
      { label: 'Profile', path: '/hiring-manager/profile', icon: <PersonIcon /> },
      { label: 'Settings', path: '/hiring-manager/settings', icon: <SettingsIcon /> },
    ],
  },
];

// Bottom navigation items for mobile devices
const bottomNavItems: NavItem[] = [
  { label: 'Dashboard', path: '/hiring-manager/dashboard', icon: <DashboardIcon /> },
  { label: 'Review', path: '/hiring-manager/review-queue', icon: <ReviewIcon /> },
  { label: 'Schedule', path: '/hiring-manager/schedule', icon: <ScheduleIcon /> },
  { label: 'Profile', path: '/hiring-manager/profile', icon: <PersonIcon /> },
];

// Main HiringManagerLayout component
const HiringManagerLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { isInitialized } = useAuthContext();
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Candidates: true,
    Schedule: false,
    Account: false,
  });
  // State for transition animation
  const [transitionKey, setTransitionKey] = useState(location.pathname);

  // Update active tab based on current route (bottom navigation)
  useEffect(() => {
    const index = bottomNavItems.findIndex((item) =>
      location.pathname === item.path || location.pathname.startsWith(item.path + '/')
    );
    if (index >= 0) {
      setBottomNavValue(index);
    }
  }, [location.pathname]);

  // Trigger transition animation on route change
  useEffect(() => {
    setTransitionKey(location.pathname);
  }, [location.pathname]);

  // Handler for bottom navigation change
  const handleBottomNavChange = (_event: React.SyntheticEvent, newValue: number) => {
    setBottomNavValue(newValue);
    navigate(bottomNavItems[newValue].path);
  };

  // Handler for mobile menu toggle
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // Handler for navigation section toggle
  const handleSectionToggle = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // Drawer content
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo */}
      <Box
        sx={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          px: 3,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="h6"
          role="heading"
          aria-level={1}
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          AgentHR
        </Typography>
      </Box>

      {/* Navigation sections */}
      <nav aria-label="Hiring Manager navigation">
        <List sx={{ px: 2, py: 2 }} role="menubar">
          {navSections.map((section, sectionIdx) => (
            <Box key={section.title || sectionIdx}>
              {section.title && (
                <>
                  <ListItem
                    disablePadding
                    sx={{ mt: sectionIdx > 0 ? 2 : 0, mb: 1 }}
                    role="none"
                  >
                    <ListItemButton
                      onClick={() => handleSectionToggle(section.title!)}
                      sx={{
                        borderRadius: 2,
                        px: 2,
                        py: 1,
                        '&:hover': { backgroundColor: 'action.hover' },
                      }}
                    >
                      <ListItemText
                        primary={section.title}
                        sx={{
                          '& .MuiTypography-root': {
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: 0.5,
                            color: 'text.secondary',
                          },
                        }}
                      />
                      {expandedSections[section.title!] ? <ExpandLess /> : <ExpandMore />}
                    </ListItemButton>
                  </ListItem>
                </>
              )}

              <Collapse in={!section.title || expandedSections[section.title!]} timeout="auto" unmountOnExit>
                {section.items.map((item) => {
                  const isActive = location.pathname === item.path ||
                    (item.path !== '/hiring-manager/dashboard' && location.pathname.startsWith(item.path + '/'));

                  return (
                    <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }} role="none">
                      <ListItemButton
                        role="menuitem"
                        aria-current={isActive ? 'page' : undefined}
                        onClick={() => {
                          navigate(item.path);
                          if (isMobile) setMobileOpen(false);
                        }}
                        sx={{
                          borderRadius: 2,
                          px: 2,
                          py: 1,
                          backgroundColor: isActive ? 'action.selected' : 'transparent',
                          '&:hover': {
                            backgroundColor: isActive ? 'action.selected' : 'action.hover',
                          },
                          '&:focus-visible': {
                            outline: '2px solid',
                            outlineColor: 'primary.main',
                            outlineOffset: '2px',
                          },
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            minWidth: 40,
                            color: isActive ? 'primary.main' : 'text.primary',
                          }}
                          aria-hidden="true"
                        >
                          {item.icon}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.label}
                          sx={{
                            '& .MuiTypography-root': {
                              fontWeight: isActive ? 600 : 500,
                              fontSize: '0.875rem',
                            },
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </Collapse>

              {sectionIdx < navSections.length - 1 && (
                <Divider sx={{ my: 1, mx: 2 }} />
              )}
            </Box>
          ))}
        </List>
      </nav>
    </Box>
  );

  /**
   * Show loading state during initial auth check
   */
  if (!isInitialized) {
    return (
      <Backdrop
        sx={{
          color: 'primary.main',
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: 'background.default',
        }}
        open
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <CircularProgress size={48} thickness={4} />
          <Typography variant="body1" color="text.secondary">
            Loading...
          </Typography>
        </Box>
      </Backdrop>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Skip to main content link for keyboard users */}
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

      {/* Top app bar */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ justifyContent: { xs: 'center', md: 'space-between' } }}>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
            <Typography variant="h6" fontWeight={600} color="text.primary" component="h2">
              Hiring Manager Portal
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
              <NotificationCenter
                onNotificationClick={(notification) => {
                  if (notification.action_url) {
                    navigate(notification.action_url);
                  }
                }}
              />
            </Box>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
              sx={{ display: { xs: 'flex', md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Desktop sidebar */}
      <Box
        component="nav"
        sx={{
          width: { md: DRAWER_WIDTH },
          flexShrink: { md: 0 },
          display: { xs: 'none', md: 'block' },
        }}
        aria-label="Hiring Manager sidebar navigation"
      >
        <Drawer
          variant="permanent"
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: DRAWER_WIDTH,
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: 'background.default',
          pb: { xs: 7, md: 0 }, // Padding for bottom navigation on mobile
        }}
        tabIndex={-1}
      >
        <Fade in timeout={{ enter: 300, exit: 200 }} key={transitionKey}>
          <Box>
            <Outlet />
          </Box>
        </Fade>
      </Box>

      {/* Bottom navigation (mobile only) */}
      <Paper
        component="nav"
        aria-label="Mobile navigation"
        sx={{
          display: { xs: 'block', md: 'none' },
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
          value={bottomNavValue}
          onChange={handleBottomNavChange}
          aria-label="Hiring Manager navigation"
          showLabels
        >
          {bottomNavItems.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              icon={item.icon}
              aria-current={bottomNavValue === index ? 'page' : undefined}
            />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
};

export default HiringManagerLayout;

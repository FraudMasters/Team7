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
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Collapse,
} from '@/components/ui';
import { Icon } from '@/components/ui';
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';
import { useResponsive } from '@/hooks/useResponsive';

interface NavItem {
  label: string;
  path: string;
  iconName: string;
  children?: NavItem[];
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    items: [
      { label: 'Find Jobs', path: '/jobs', iconName: 'search' },
    ],
  },
  {
    title: 'Jobs',
    items: [
      { label: 'Browse', path: '/jobs', iconName: 'briefcase' },
      { label: 'Recommended', path: '/jobs/recommended', iconName: 'sparkles' },
      { label: 'Saved', path: '/jobs/saved', iconName: 'bookmark' },
      { label: 'Applications', path: '/jobs/applications', iconName: 'file-text' },
    ],
  },
  {
    title: 'Career',
    items: [
      { label: 'Skill Assessment', path: '/jobs/assessment', iconName: 'bar-chart-2' },
      { label: 'Learning', path: '/jobs/learning', iconName: 'graduation-cap' },
      { label: 'Salary Calculator', path: '/jobs/salary', iconName: 'dollar-sign' },
      { label: 'Interview Tips', path: '/jobs/tips', iconName: 'lightbulb' },
    ],
  },
  {
    title: 'Account',
    items: [
      { label: 'Profile', path: '/profile', iconName: 'user' },
      { label: 'Resume', path: '/jobs/upload', iconName: 'file-text' },
      { label: 'Job Alerts', path: '/jobs/alerts', iconName: 'bell' },
      { label: 'Settings', path: '/jobs/settings', iconName: 'settings' },
    ],
  },
];

const bottomNavItems: NavItem[] = [
  { label: 'Jobs', path: '/jobs', iconName: 'briefcase' },
  { label: 'Saved', path: '/jobs/saved', iconName: 'bookmark' },
  { label: 'Applications', path: '/jobs/applications', iconName: 'file-text' },
  { label: 'Profile', path: '/profile', iconName: 'user' },
];

const DRAWER_WIDTH = 280;

const JobSeekerLayout: React.FC = () => {
  const { theme } = useEmotionTheme();
  const responsive = useResponsive();
  const navigate = useNavigate();
  const location = useLocation();
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Jobs: true,
    Career: false,
    Account: false,
  });

  // Update active tab based on current route (bottom nav)
  useEffect(() => {
    const index = bottomNavItems.findIndex(
      (item) => location.pathname === item.path || location.pathname.startsWith(item.path + '/')
    );
    if (index >= 0) {
      setBottomNavValue(index);
    }
  }, [location.pathname]);

  const handleBottomNavChange = (_event: React.SyntheticEvent, newValue: number) => {
    setBottomNavValue(newValue);
    navigate(bottomNavItems[newValue].path);
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleSectionToggle = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo */}
      <Box
        sx={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          px: theme.spacing.lg,
          borderBottom: `1px solid ${theme.divider}`,
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

      {/* Navigation Sections */}
      <Box as="nav" aria-label="Main navigation">
        <List sx={{ px: theme.spacing.sm, py: theme.spacing.sm }} role="menubar">
          {navSections.map((section, sectionIdx) => (
            <Box as="div" key={section.title || sectionIdx}>
              {section.title && (
                <>
                  <ListItem
                    disablePadding
                    sx={{ mt: sectionIdx > 0 ? theme.spacing.md : 0, mb: theme.spacing.sm }}
                    role="none"
                    onClick={() => handleSectionToggle(section.title!)}
                  >
                    <Box
                      sx={{
                        borderRadius: theme.borderRadius.lg,
                        px: theme.spacing.md,
                        py: theme.spacing.sm,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                        '&:hover': { backgroundColor: theme.action.hover },
                      }}
                    >
                      <Typography
                        sx={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: 0.5,
                          color: theme.text.secondary,
                        }}
                      >
                        {section.title}
                      </Typography>
                      <Icon
                        name={expandedSections[section.title!] ? 'chevron-up' : 'chevron-down'}
                        size="small"
                        color="secondary"
                      />
                    </Box>
                  </ListItem>
                </>
              )}

              <Collapse in={!section.title || expandedSections[section.title!]} timeout="auto" unmountOnExit>
                {section.items.map((item) => {
                  const isActive =
                    location.pathname === item.path ||
                    (item.path !== '/jobs' && location.pathname.startsWith(item.path + '/'));

                  return (
                    <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }} role="none">
                      <Box
                        role="menuitem"
                        aria-current={isActive ? 'page' : undefined}
                        onClick={() => {
                          navigate(item.path);
                          if (responsive.isMdDown) setMobileOpen(false);
                        }}
                        sx={{
                          borderRadius: theme.borderRadius.lg,
                          px: theme.spacing.md,
                          py: theme.spacing.sm,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          width: '100%',
                          backgroundColor: isActive ? theme.palette.action.selected : 'transparent',
                          '&:hover': {
                            backgroundColor: isActive ? theme.palette.action.selected : theme.action.hover,
                          },
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            minWidth: 40,
                            color: isActive ? theme.primary.main : theme.text.primary,
                          }}
                          aria-hidden="true"
                        >
                          <Icon name={item.iconName} size="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.label}
                          sx={{
                            '& > div:first-child': {
                              fontWeight: isActive ? 600 : 500,
                              fontSize: '0.875rem',
                            },
                          }}
                        />
                      </Box>
                    </ListItem>
                  );
                })}
              </Collapse>

              {sectionIdx < navSections.length - 1 && (
                <Divider sx={{ my: theme.spacing.sm, mx: theme.spacing.sm }} />
              )}
            </Box>
          ))}
        </List>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Skip Link for Keyboard Users */}
      <Box
        as="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          top: 0,
          zIndex: theme.zIndex.tooltip + 1,
          '&:focus': {
            left: '10px',
            top: '10px',
            bgcolor: theme.primary.main,
            color: 'white',
            p: theme.spacing.md,
            borderRadius: theme.borderRadius.md,
          },
        }}
      >
        Skip to main content
      </Box>

      {/* Sticky Top AppBar */}
      <AppBar
        position="sticky"
        elevation={0}
        color="default"
        sx={{
          bgcolor: theme.background.paper,
          borderBottom: `1px solid ${theme.divider}`,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ justifyContent: { xs: 'center', md: 'space-between' } }}>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
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
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <IconButton
              color="inherit"
              name="bell"
              onClick={() => navigate('/jobs/alerts')}
              aria-label="Job alerts"
              sx={{ display: { xs: 'none', md: 'flex' } }}
            />
            <IconButton
              color="inherit"
              edge="start"
              name="menu"
              onClick={handleDrawerToggle}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
              sx={{ display: { xs: 'flex', md: 'none' } }}
            />
          </Box>
        </Toolbar>
      </AppBar>

      {/* Desktop Sidebar */}
      <Box
        as="nav"
        sx={{
          width: { md: DRAWER_WIDTH },
          flexShrink: { md: 0 },
          display: { xs: 'none', md: 'block' },
        }}
        aria-label="Job seeker sidebar navigation"
      >
        <Drawer variant="permanent" width={DRAWER_WIDTH} open>
          {drawerContent}
        </Drawer>
      </Box>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        width={DRAWER_WIDTH}
        sx={{
          display: { xs: 'block', md: 'none' },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Main Content */}
      <Box
        as="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: theme.background.default,
          pb: { xs: '56px', md: 0 }, // Add bottom padding for mobile nav
        }}
        tabIndex={-1}
      >
        <Outlet />
      </Box>

      {/* Bottom Navigation (Mobile Only) */}
      <Paper
        as="nav"
        aria-label="Mobile navigation"
        sx={{
          display: { xs: 'block', md: 'none' },
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          elevation: 3,
          borderRadius: 0,
          zIndex: theme.zIndex.appBar - 1,
        }}
      >
        <BottomNavigation
          value={bottomNavValue}
          onChange={handleBottomNavChange}
          aria-label="Job seeker navigation"
          showLabels
        >
          {bottomNavItems.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              icon={<Icon name={item.iconName} />}
            />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
};

export default JobSeekerLayout;

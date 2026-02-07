import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Collapse,
  useMediaQuery,
  useTheme,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  VpnKey as ApiKeysIcon,
  Webhook as WebhooksIcon,
  Extension as PluginsIcon,
  AccountTree as WorkflowsIcon,
  Description as DocsIcon,
  Analytics as AnalyticsIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';

const DRAWER_WIDTH = 280;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    items: [
      { label: 'Overview', path: '/developer', icon: <DocsIcon /> },
    ],
  },
  {
    title: 'API Management',
    items: [
      { label: 'API Keys', path: '/developer/api-keys', icon: <ApiKeysIcon /> },
      { label: 'Webhooks', path: '/developer/webhooks', icon: <WebhooksIcon /> },
      { label: 'Analytics', path: '/developer/analytics', icon: <AnalyticsIcon /> },
    ],
  },
  {
    title: 'Extensions',
    items: [
      { label: 'Plugins', path: '/developer/plugins', icon: <PluginsIcon /> },
      { label: 'Workflows', path: '/developer/workflows', icon: <WorkflowsIcon /> },
    ],
  },
];

const DeveloperLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'API Management': true,
    Extensions: true,
  });

  const navigate = useNavigate();
  const location = useLocation();

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

      {/* Navigation Sections */}
      <nav aria-label="Main navigation">
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
                    (item.path !== '/developer' && location.pathname.startsWith(item.path + '/'));

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

  return (
    <Box sx={{ display: 'flex' }}>
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

      {/* Top AppBar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileOpen}
            aria-controls="drawer-menu"
            sx={{ mr: 2, display: { xs: 'flex', md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" fontWeight={600} color="text.primary" component="h2">
            Developer Portal
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        aria-label="Developer sidebar navigation"
        id="drawer-menu"
      >
        {/* Mobile Drawer */}
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

        {/* Desktop Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
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

      {/* Main Content */}
      <Box
        component="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
        tabIndex={-1}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default DeveloperLayout;

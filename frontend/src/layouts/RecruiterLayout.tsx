import React, { useState, createContext, useContext, useRef, useCallback, useMemo } from 'react';
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
  Tooltip,
} from '@mui/material';
import { PullToRefresh } from '../components/ui';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Work as WorkIcon,
  People as PeopleIcon,
  BarChart as BarChartIcon,
  Tune as TuneIcon,
  ExpandLess,
  ExpandMore,
  Description as DocsIcon,
  Search as SearchIcon,
  BookmarkBorder as SavedIcon,
  CloudUpload as CloudUploadIcon,
  Folder as FolderIcon,
  Assessment as AnalyticsIcon,
  Settings as SettingsIcon,
  Backup as BackupIcon,
  Timeline as TimelineIcon,
  Psychology as PsychologyIcon,
  Storage as StorageIcon,
  Compare as CompareIcon,
  ViewColumn as KanbanIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';

const DRAWER_WIDTH = 280;

// Context for allowing child pages to register refresh handlers
interface RefreshContextType {
  registerRefreshHandler: (handler: (() => Promise<void>) | null) => void;
}

const RefreshContext = createContext<RefreshContextType | undefined>(undefined);

export const useRefreshHandler = () => {
  const context = useContext(RefreshContext);
  if (!context) {
    throw new Error('useRefreshHandler must be used within RecruiterLayout');
  }
  return context;
};

// Helper to check if current route supports pull-to-refresh
const isRefreshableRoute = (pathname: string): boolean => {
  return (
    pathname.startsWith('/recruiter/resumes') ||
    pathname.startsWith('/recruiter/candidates')
  );
};

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
  children?: NavItem[];
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    items: [
      { label: 'Dashboard', path: '/recruiter/dashboard', icon: <DashboardIcon /> },
    ],
  },
  {
    title: 'Hiring',
    items: [
      { label: 'Vacancies', path: '/recruiter/vacancies', icon: <WorkIcon /> },
      { label: 'Candidates', path: '/recruiter/candidates', icon: <PeopleIcon /> },
      { label: 'Pipeline', path: '/recruiter/candidates', icon: <KanbanIcon /> },
      { label: 'Applications', path: '/recruiter/applications', icon: <TimelineIcon /> },
    ],
  },
  {
    title: 'Resumes',
    items: [
      { label: 'Database', path: '/recruiter/resumes', icon: <StorageIcon /> },
      { label: 'Upload', path: '/recruiter/upload', icon: <UploadIcon /> },
      { label: 'Batch Upload', path: '/recruiter/batch-upload', icon: <CloudUploadIcon /> },
    ],
  },
  {
    title: 'Search',
    items: [
      { label: 'Candidate Search', path: '/recruiter/search', icon: <SearchIcon /> },
      { label: 'Saved Searches', path: '/recruiter/saved-searches', icon: <SavedIcon /> },
      { label: 'Compare', path: '/recruiter/compare', icon: <CompareIcon /> },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { label: 'Overview', path: '/recruiter/analytics', icon: <BarChartIcon /> },
      { label: 'Skill Gap Analysis', path: '/recruiter/skill-gap', icon: <PsychologyIcon /> },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Weights', path: '/recruiter/weights', icon: <TuneIcon /> },
      { label: 'Backups', path: '/recruiter/backups', icon: <BackupIcon /> },
      { label: 'Workflow', path: '/recruiter/workflow', icon: <TimelineIcon /> },
    ],
  },
];

const RecruiterLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Hiring: true,
    Resumes: false,
    Search: false,
    Analytics: false,
    Settings: false,
  });

  const navigate = useNavigate();
  const location = useLocation();

  // Store refresh callback from child page
  const refreshHandlerRef = useRef<(() => Promise<void>) | null>(null);

  // Register refresh handler from child page
  const registerRefreshHandler = useCallback((handler: (() => Promise<void>) | null) => {
    refreshHandlerRef.current = handler;
  }, []);

  // Handle pull-to-refresh action
  const handleRefresh = useCallback(async () => {
    if (refreshHandlerRef.current) {
      try {
        setRefreshing(true);
        await refreshHandlerRef.current();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setRefreshing(false);
      }
    }
  }, []);

  // Check if current route should have pull-to-refresh enabled
  const enableRefresh = isMobile && isRefreshableRoute(location.pathname);

  // Context value for child pages
  const refreshContext = useMemo(
    () => ({ registerRefreshHandler }),
    [registerRefreshHandler]
  );

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
      <nav aria-label="Main navigation" sx={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
        <List
          sx={{ px: 2, py: 2 }}
          role="menubar"
          aria-label="Recruiter navigation menu"
        >
          {navSections.map((section, sectionIdx) => (
            <Box key={sectionIdx || 'root'}>
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
                    (item.path !== '/recruiter/dashboard' && location.pathname.startsWith(item.path + '/'));

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
            Recruiter Portal
          </Typography>
          <Box sx={{ ml: 'auto', display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            <Tooltip title="Quick Search (Ctrl+K)">
              <IconButton
                color="inherit"
                onClick={() => navigate('/recruiter/search')}
                aria-label="Quick search"
              >
                <SearchIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        aria-label="Recruiter sidebar navigation"
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
        <RefreshContext.Provider value={refreshContext}>
          <PullToRefresh
            onRefresh={handleRefresh}
            refreshing={refreshing}
            enabled={enableRefresh}
            loadingMessage="Refreshing..."
            pullMessage="Pull down to refresh"
            releaseMessage="Release to refresh"
          >
            <Outlet />
          </PullToRefresh>
        </RefreshContext.Provider>
      </Box>
    </Box>
  );
};

export default RecruiterLayout;

import React, { ReactNode, useState, useCallback } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  Menu,
  MenuItem,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Collapse,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Description as ResumeIcon,
  Work as WorkIcon,
  Person as PersonIcon,
  BusinessCenter as RecruiterIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Settings as SettingsIcon,
  Upload as UploadIcon,
  School as SchoolIcon,
  Tune as TuneIcon,
  Menu as MenuIcon,
} from '@mui/icons-material';
import LanguageSwitcher from './LanguageSwitcher';
import KeyboardShortcutsHelp from './KeyboardShortcutsHelp';
import { useGlobalKeyboardShortcuts, COMMON_SHORTCUTS } from '@/hooks/useGlobalKeyboardShortcuts';

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
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();

  // Responsive breakpoints
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  // Desktop menu states
  const [jobSeekerAnchorEl, setJobSeekerAnchorEl] = useState<null | HTMLElement>(null);
  const [recruiterAnchorEl, setRecruiterAnchorEl] = useState<null | HTMLElement>(null);
  const [adminAnchorEl, setAdminAnchorEl] = useState<null | HTMLElement>(null);

  // Mobile drawer state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // Mobile accordion states
  const [mobileJobSeekerOpen, setMobileJobSeekerOpen] = useState(false);
  const [mobileRecruiterOpen, setMobileRecruiterOpen] = useState(false);
  const [mobileAdminOpen, setMobileAdminOpen] = useState(false);

  // Keyboard shortcuts help dialog state
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  const jobSeekerMenuOpen = Boolean(jobSeekerAnchorEl);
  const recruiterMenuOpen = Boolean(recruiterAnchorEl);
  const adminMenuOpen = Boolean(adminAnchorEl);

  // Menu handlers with keyboard support
  const handleJobSeekerMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setJobSeekerAnchorEl(event.currentTarget);
  };

  const handleJobSeekerMenuClose = () => {
    setJobSeekerAnchorEl(null);
  };

  const handleRecruiterMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setRecruiterAnchorEl(event.currentTarget);
  };

  const handleRecruiterMenuClose = () => {
    setRecruiterAnchorEl(null);
  };

  const handleAdminMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAdminAnchorEl(event.currentTarget);
  };

  const handleAdminMenuClose = () => {
    setAdminAnchorEl(null);
  };

  // Mobile drawer handlers
  const handleDrawerToggle = () => {
    setMobileDrawerOpen(!mobileDrawerOpen);
  };

  const handleMobileMenuClose = () => {
    setMobileDrawerOpen(false);
  };

  const handleMobileJobSeekerToggle = () => {
    setMobileJobSeekerOpen(!mobileJobSeekerOpen);
  };

  const handleMobileRecruiterToggle = () => {
    setMobileRecruiterOpen(!mobileRecruiterOpen);
  };

  const handleMobileAdminToggle = () => {
    setMobileAdminOpen(!mobileAdminOpen);
  };

  const handleMobileNavClick = (path: string) => {
    handleMobileMenuClose();
    // Close any open accordions
    setMobileJobSeekerOpen(false);
    setMobileRecruiterOpen(false);
    setMobileAdminOpen(false);
  };

  // Keyboard shortcuts help handlers
  const handleShortcutsOpen = useCallback(() => {
    setShortcutsOpen(true);
  }, []);

  const handleShortcutsClose = useCallback(() => {
    setShortcutsOpen(false);
  }, []);

  // Close all open menus and modals with Escape key
  const handleEscape = useCallback(() => {
    if (shortcutsOpen) {
      handleShortcutsClose();
    } else if (jobSeekerMenuOpen) {
      handleJobSeekerMenuClose();
    } else if (recruiterMenuOpen) {
      handleRecruiterMenuClose();
    } else if (adminMenuOpen) {
      handleAdminMenuClose();
    } else if (mobileDrawerOpen) {
      handleMobileMenuClose();
    }
  }, [
    shortcutsOpen,
    handleShortcutsClose,
    jobSeekerMenuOpen,
    handleJobSeekerMenuClose,
    recruiterMenuOpen,
    handleRecruiterMenuClose,
    adminMenuOpen,
    handleAdminMenuClose,
    mobileDrawerOpen,
    handleMobileMenuClose,
  ]);

  // Navigate to search page with Ctrl+K
  const handleGlobalSearch = useCallback(() => {
    navigate('/recruiter/search');
  }, [navigate]);

  // Register global keyboard shortcuts
  useGlobalKeyboardShortcuts([
    // Ctrl+K - Open global search
    {
      id: 'global.search',
      keyCombination: COMMON_SHORTCUTS.GLOBAL_SEARCH,
      handler: handleGlobalSearch,
    },
    // Ctrl+/ - Show keyboard shortcuts help
    {
      id: 'global.showShortcuts',
      keyCombination: COMMON_SHORTCUTS.SHOW_SHORTCUTS,
      handler: handleShortcutsOpen,
    },
    // Escape - Close modals, menus, and drawer
    {
      id: 'global.closeModal',
      keyCombination: COMMON_SHORTCUTS.ESCAPE,
      handler: handleEscape,
      condition: () =>
        shortcutsOpen ||
        jobSeekerMenuOpen ||
        recruiterMenuOpen ||
        adminMenuOpen ||
        mobileDrawerOpen,
    },
  ]);

  // Job Seeker Module menu items
  const jobSeekerItems = [
    { labelKey: 'nav.browseJobs', path: '/jobs', icon: <WorkIcon fontSize="small" /> },
    { labelKey: 'nav.uploadResumeNav', path: '/jobs/upload', icon: <ResumeIcon fontSize="small" /> },
    { labelKey: 'nav.batchUpload', path: '/jobs/batch-upload', icon: <UploadIcon fontSize="small" /> },
    { labelKey: 'nav.myApplications', path: '/jobs/applications', icon: <PersonIcon fontSize="small" /> },
  ];

  // Recruiter Module menu items
  const recruiterItems = [
    { labelKey: 'nav.dashboard', path: '/recruiter', icon: <RecruiterIcon fontSize="small" /> },
    { labelKey: 'nav.manageVacancies', path: '/recruiter/vacancies', icon: <WorkIcon fontSize="small" /> },
    { labelKey: 'nav.resumeDatabase', path: '/recruiter/resumes', icon: <PersonIcon fontSize="small" /> },
    { labelKey: 'nav.searchCandidates', path: '/recruiter/search', icon: <RecruiterIcon fontSize="small" /> },
    { labelKey: 'nav.skillGapAnalysis', path: '/recruiter/skill-gap', icon: <SchoolIcon fontSize="small" /> },
    { labelKey: 'nav.matchingWeights', path: '/recruiter/weights', icon: <TuneIcon fontSize="small" /> },
  ];

  // Admin Module menu items
  const adminItems = [
    { labelKey: 'nav.adminSynonyms', path: '/admin/synonyms', icon: <SettingsIcon fontSize="small" /> },
    { labelKey: 'nav.adminTaxonomies', path: '/admin/taxonomies', icon: <SettingsIcon fontSize="small" /> },
    { labelKey: 'nav.adminTaxonomyAnalytics', path: '/admin/taxonomy-analytics', icon: <SettingsIcon fontSize="small" /> },
    { labelKey: 'nav.adminPublicTaxonomies', path: '/admin/public-taxonomies', icon: <SettingsIcon fontSize="small" /> },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar / Navigation */}
      <AppBar position="static" elevation={2}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ px: { xs: 1, sm: 2 } }}>
            {/* Logo / Brand */}
            <Box sx={{ display: 'flex', alignItems: 'center', mr: { xs: 1, sm: 2, md: 4 } }}>
              <ResumeIcon sx={{ mr: 1, fontSize: { xs: 24, sm: 28, md: 32 } }} />
              <Typography
                variant={isMobile ? 'body1' : 'h6'}
                component={Link}
                to="/"
                onClick={() => {
                  handleMobileMenuClose();
                  window.scrollTo(0, 0);
                }}
                sx={{
                  fontWeight: 700,
                  color: 'inherit',
                  textDecoration: 'none',
                  letterSpacing: '-0.5px',
                  fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
                }}
              >
                {t('appName')}
              </Typography>
            </Box>

            {/* Desktop Navigation - Hidden on Mobile */}
            {!isMobile && (
              <Box
                sx={{
                  flexGrow: 1,
                  display: 'flex',
                  gap: { sm: 0.5, md: 1 },
                  alignItems: 'center',
                }}
              >
                {/* Job Seeker Module */}
                <Button
                  color="inherit"
                  startIcon={!isTablet && <WorkIcon />}
                  endIcon={<ExpandMoreIcon />}
                  onClick={handleJobSeekerMenuClick}
                  aria-expanded={jobSeekerMenuOpen}
                  aria-haspopup="true"
                  aria-label={t('nav.findJobs')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 500,
                    borderRadius: 1,
                    px: { sm: 1, md: 2 },
                    fontSize: { sm: '0.875rem', md: '1rem' },
                    minWidth: 'auto',
                  }}
                >
                  {isTablet ? <WorkIcon /> : t('nav.findJobs')}
                </Button>
                <Menu
                  anchorEl={jobSeekerAnchorEl}
                  open={jobSeekerMenuOpen}
                  onClose={handleJobSeekerMenuClose}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                  }}
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                  }}
                  MenuListProps={{
                    'aria-labelledby': 'job-seeker-menu-button',
                    role: 'menu',
                  }}
                  slotProps={{
                    paper: {
                      sx: { minWidth: 200 },
                    },
                  }}
                >
                  {jobSeekerItems.map((item) => (
                    <MenuItem
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={handleJobSeekerMenuClose}
                      selected={location.pathname === item.path}
                      role="menuitem"
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 180 }}>
                        {item.icon}
                        <Typography variant="body2">{t(item.labelKey)}</Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Menu>

                {/* Recruiter Module */}
                <Button
                  color="inherit"
                  startIcon={!isTablet && <RecruiterIcon />}
                  endIcon={<ExpandMoreIcon />}
                  onClick={handleRecruiterMenuClick}
                  aria-expanded={recruiterMenuOpen}
                  aria-haspopup="true"
                  aria-label={t('nav.findEmployees')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 500,
                    borderRadius: 1,
                    px: { sm: 1, md: 2 },
                    fontSize: { sm: '0.875rem', md: '1rem' },
                    minWidth: 'auto',
                  }}
                >
                  {isTablet ? <RecruiterIcon /> : t('nav.findEmployees')}
                </Button>
                <Menu
                  anchorEl={recruiterAnchorEl}
                  open={recruiterMenuOpen}
                  onClose={handleRecruiterMenuClose}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                  }}
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                  }}
                  MenuListProps={{
                    'aria-labelledby': 'recruiter-menu-button',
                    role: 'menu',
                  }}
                  slotProps={{
                    paper: {
                      sx: { minWidth: 200 },
                    },
                  }}
                >
                  {recruiterItems.map((item) => (
                    <MenuItem
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={handleRecruiterMenuClose}
                      selected={location.pathname === item.path}
                      role="menuitem"
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 180 }}>
                        {item.icon}
                        <Typography variant="body2">{t(item.labelKey)}</Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Menu>

                {/* Admin Module */}
                <Button
                  color="inherit"
                  startIcon={!isTablet && <SettingsIcon />}
                  endIcon={<ExpandMoreIcon />}
                  onClick={handleAdminMenuClick}
                  aria-expanded={adminMenuOpen}
                  aria-haspopup="true"
                  aria-label={t('nav.admin')}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 500,
                    borderRadius: 1,
                    px: { sm: 1, md: 2 },
                    fontSize: { sm: '0.875rem', md: '1rem' },
                    minWidth: 'auto',
                  }}
                >
                  {isTablet ? <SettingsIcon /> : t('nav.admin')}
                </Button>
                <Menu
                  anchorEl={adminAnchorEl}
                  open={adminMenuOpen}
                  onClose={handleAdminMenuClose}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                  }}
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                  }}
                  MenuListProps={{
                    'aria-labelledby': 'admin-menu-button',
                    role: 'menu',
                  }}
                  slotProps={{
                    paper: {
                      sx: { minWidth: 220 },
                    },
                  }}
                >
                  {adminItems.map((item) => (
                    <MenuItem
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={handleAdminMenuClose}
                      selected={location.pathname === item.path}
                      role="menuitem"
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
                        {item.icon}
                        <Typography variant="body2">{t(item.labelKey)}</Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Menu>
              </Box>
            )}

            {/* Right side actions */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* Language Switcher */}
              <LanguageSwitcher />

              {/* Mobile Menu Button */}
              {isMobile && (
                <IconButton
                  edge="end"
                  color="inherit"
                  aria-label="Open menu"
                  aria-controls="mobile-menu-drawer"
                  aria-haspopup="true"
                  onClick={handleDrawerToggle}
                  sx={{ ml: 1 }}
                >
                  <MenuIcon />
                </IconButton>
              )}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Mobile Navigation Drawer */}
      <Drawer
        id="mobile-menu-drawer"
        anchor="right"
        open={mobileDrawerOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better mobile performance
          onBackdropClick: handleMobileMenuClose,
        }}
        sx={{
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
          }}
          role="presentation"
        >
          {/* Drawer Header */}
          <Box
            sx={{
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" component="div">
              Menu
            </Typography>
            <IconButton
              edge="end"
              onClick={handleMobileMenuClose}
              aria-label="Close menu"
            >
              <MenuIcon />
            </IconButton>
          </Box>

          {/* Navigation Menu */}
          <List sx={{ flexGrow: 1, py: 1 }}>
            {/* Job Seeker Module */}
            <>
              <ListItemButton onClick={handleMobileJobSeekerToggle} aria-expanded={mobileJobSeekerOpen}>
                <ListItemIcon>
                  <WorkIcon />
                </ListItemIcon>
                <ListItemText primary={t('nav.findJobs')} />
                {mobileJobSeekerOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItemButton>
              <Collapse in={mobileJobSeekerOpen} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {jobSeekerItems.map((item) => (
                    <ListItemButton
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: 4 }}
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </>

            <Divider />

            {/* Recruiter Module */}
            <>
              <ListItemButton onClick={handleMobileRecruiterToggle} aria-expanded={mobileRecruiterOpen}>
                <ListItemIcon>
                  <RecruiterIcon />
                </ListItemIcon>
                <ListItemText primary={t('nav.findEmployees')} />
                {mobileRecruiterOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItemButton>
              <Collapse in={mobileRecruiterOpen} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {recruiterItems.map((item) => (
                    <ListItemButton
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: 4 }}
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </>

            <Divider />

            {/* Admin Module */}
            <>
              <ListItemButton onClick={handleMobileAdminToggle} aria-expanded={mobileAdminOpen}>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary={t('nav.admin')} />
                {mobileAdminOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItemButton>
              <Collapse in={mobileAdminOpen} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {adminItems.map((item) => (
                    <ListItemButton
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: 4 }}
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </>
          </List>
        </Box>
      </Drawer>

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
            {t('footer.copyright', { year: new Date().getFullYear() })}
          </Typography>
        </Container>
      </Box>

      {/* Keyboard Shortcuts Help Dialog */}
      <KeyboardShortcutsHelp open={shortcutsOpen} onClose={handleShortcutsClose} />
    </Box>
  );
};

export default Layout;

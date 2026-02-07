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
  ListItemIcon,
  ListItemText,
  Divider,
  Collapse,
} from '@/components/ui';
import { Icon } from '@/components/ui';
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';
import { useResponsive } from '@/hooks/useResponsive';
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
  const { theme } = useEmotionTheme();
  const responsive = useResponsive();

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
    { labelKey: 'nav.browseJobs', path: '/jobs', iconName: 'briefcase' },
    { labelKey: 'nav.uploadResumeNav', path: '/jobs/upload', iconName: 'file-text' },
    { labelKey: 'nav.batchUpload', path: '/jobs/batch-upload', iconName: 'upload-cloud' },
    { labelKey: 'nav.myApplications', path: '/jobs/applications', iconName: 'user' },
  ];

  // Recruiter Module menu items
  const recruiterItems = [
    { labelKey: 'nav.dashboard', path: '/recruiter', iconName: 'layout-dashboard' },
    { labelKey: 'nav.manageVacancies', path: '/recruiter/vacancies', iconName: 'briefcase' },
    { labelKey: 'nav.candidatePipeline', path: '/recruiter/candidates', iconName: 'columns' },
    { labelKey: 'nav.resumeDatabase', path: '/recruiter/resumes', iconName: 'users' },
    { labelKey: 'nav.searchCandidates', path: '/recruiter/search', iconName: 'search' },
    { labelKey: 'nav.skillGapAnalysis', path: '/recruiter/skill-gap', iconName: 'graduation-cap' },
    { labelKey: 'nav.matchingWeights', path: '/recruiter/weights', iconName: 'sliders' },
  ];

  // Admin Module menu items
  const adminItems = [
    { labelKey: 'nav.adminSynonyms', path: '/admin/synonyms', iconName: 'settings' },
    { labelKey: 'nav.adminTaxonomies', path: '/admin/taxonomies', iconName: 'settings' },
    { labelKey: 'nav.adminTaxonomyAnalytics', path: '/admin/taxonomy-analytics', iconName: 'settings' },
    { labelKey: 'nav.adminPublicTaxonomies', path: '/admin/public-taxonomies', iconName: 'settings' },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar / Navigation */}
      <AppBar position="static" elevation={2}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ px: { xs: theme.spacing.sm, sm: theme.spacing.md, md: theme.spacing.xl } }}>
            {/* Logo / Brand */}
            <Box sx={{ display: 'flex', alignItems: 'center', mr: { xs: theme.spacing.sm, sm: theme.spacing.md, md: theme.spacing.xl } }}>
              <Box
                sx={{
                  mr: theme.spacing.sm,
                  fontSize: { xs: '24px', sm: '28px', md: '32px' },
                  color: 'inherit',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Icon name="file-text" size="large" color="inherit" />
              </Box>
              <Typography
                variant={responsive.isSmDown ? 'body1' : 'h6'}
                as={Link}
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
            {!responsive.isSmDown && (
              <Box
                sx={{
                  flexGrow: 1,
                  display: 'flex',
                  gap: { sm: theme.spacing.xs, md: theme.spacing.sm },
                  alignItems: 'center',
                }}
              >
                {/* Job Seeker Module */}
                <Box sx={{ position: 'relative' }}>
                  <Button
                    color="inherit"
                    startIcon={!responsive.isMdUp && <Icon name="briefcase" size="small" />}
                    endIcon={<Icon name="chevron-down" size="small" />}
                    onClick={handleJobSeekerMenuClick}
                    aria-expanded={jobSeekerMenuOpen}
                    aria-haspopup="true"
                    aria-label={t('nav.findJobs')}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 500,
                      borderRadius: theme.borderRadius.sm,
                      px: { sm: theme.spacing.sm, md: theme.spacing.md },
                      fontSize: { sm: '0.875rem', md: '1rem' },
                      minWidth: 'auto',
                    }}
                  >
                    {responsive.isMdUp ? t('nav.findJobs') : null}
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
                    minWidth={200}
                  >
                    {jobSeekerItems.map((item) => (
                      <MenuItem
                        key={item.path}
                        as={Link}
                        to={item.path}
                        onClick={handleJobSeekerMenuClose}
                        selected={location.pathname === item.path}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm, minWidth: 180 }}>
                          <Icon name={item.iconName} size="small" />
                          <Typography variant="body2">{t(item.labelKey)}</Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Menu>
                </Box>

                {/* Recruiter Module */}
                <Box sx={{ position: 'relative' }}>
                  <Button
                    color="inherit"
                    startIcon={!responsive.isMdUp && <Icon name="briefcase" size="small" />}
                    endIcon={<Icon name="chevron-down" size="small" />}
                    onClick={handleRecruiterMenuClick}
                    aria-expanded={recruiterMenuOpen}
                    aria-haspopup="true"
                    aria-label={t('nav.findEmployees')}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 500,
                      borderRadius: theme.borderRadius.sm,
                      px: { sm: theme.spacing.sm, md: theme.spacing.md },
                      fontSize: { sm: '0.875rem', md: '1rem' },
                      minWidth: 'auto',
                    }}
                  >
                    {responsive.isMdUp ? t('nav.findEmployees') : null}
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
                    minWidth={200}
                  >
                    {recruiterItems.map((item) => (
                      <MenuItem
                        key={item.path}
                        as={Link}
                        to={item.path}
                        onClick={handleRecruiterMenuClose}
                        selected={location.pathname === item.path}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm, minWidth: 180 }}>
                          <Icon name={item.iconName} size="small" />
                          <Typography variant="body2">{t(item.labelKey)}</Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Menu>
                </Box>

                {/* Admin Module */}
                <Box sx={{ position: 'relative' }}>
                  <Button
                    color="inherit"
                    startIcon={!responsive.isMdUp && <Icon name="settings" size="small" />}
                    endIcon={<Icon name="chevron-down" size="small" />}
                    onClick={handleAdminMenuClick}
                    aria-expanded={adminMenuOpen}
                    aria-haspopup="true"
                    aria-label={t('nav.admin')}
                    sx={{
                      textTransform: 'none',
                      fontWeight: 500,
                      borderRadius: theme.borderRadius.sm,
                      px: { sm: theme.spacing.sm, md: theme.spacing.md },
                      fontSize: { sm: '0.875rem', md: '1rem' },
                      minWidth: 'auto',
                    }}
                  >
                    {responsive.isMdUp ? t('nav.admin') : null}
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
                    minWidth={220}
                  >
                    {adminItems.map((item) => (
                      <MenuItem
                        key={item.path}
                        as={Link}
                        to={item.path}
                        onClick={handleAdminMenuClose}
                        selected={location.pathname === item.path}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm, minWidth: 200 }}>
                          <Icon name={item.iconName} size="small" />
                          <Typography variant="body2">{t(item.labelKey)}</Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Menu>
                </Box>
              </Box>
            )}

            {/* Right side actions */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
              {/* Language Switcher */}
              <LanguageSwitcher />

              {/* Mobile Menu Button */}
              {responsive.isSmDown && (
                <IconButton
                  edge="end"
                  color="inherit"
                  aria-label="Open menu"
                  aria-controls="mobile-menu-drawer"
                  aria-haspopup="true"
                  onClick={handleDrawerToggle}
                  sx={{ ml: theme.spacing.sm }}
                  name="menu"
                />
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
        width={280}
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
              p: theme.spacing.md,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${theme.divider}`,
            }}
          >
            <Typography variant="h6" as="div">
              Menu
            </Typography>
            <IconButton
              edge="end"
              onClick={handleMobileMenuClose}
              aria-label="Close menu"
              name="x"
              color="inherit"
            />
          </Box>

          {/* Navigation Menu */}
          <List sx={{ flexGrow: 1, py: theme.spacing.sm }}>
            {/* Job Seeker Module */}
            <>
              <ListItem
                disablePadding
                onClick={handleMobileJobSeekerToggle}
                aria-expanded={mobileJobSeekerOpen}
              >
                <ListItemIcon>
                  <Icon name="briefcase" size="small" />
                </ListItemIcon>
                <ListItemText primary={t('nav.findJobs')} />
                <Icon
                  name={mobileJobSeekerOpen ? 'chevron-up' : 'chevron-down'}
                  size="small"
                  color="secondary"
                />
              </ListItem>
              <Collapse in={mobileJobSeekerOpen} timeout="auto" unmountOnExit>
                <List as="div" disablePadding>
                  {jobSeekerItems.map((item) => (
                    <ListItem
                      key={item.path}
                      as={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: theme.spacing.xl }}
                      disablePadding
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Icon name={item.iconName} size="small" />
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </>

            <Divider />

            {/* Recruiter Module */}
            <>
              <ListItem
                disablePadding
                onClick={handleMobileRecruiterToggle}
                aria-expanded={mobileRecruiterOpen}
              >
                <ListItemIcon>
                  <Icon name="briefcase" size="small" />
                </ListItemIcon>
                <ListItemText primary={t('nav.findEmployees')} />
                <Icon
                  name={mobileRecruiterOpen ? 'chevron-up' : 'chevron-down'}
                  size="small"
                  color="secondary"
                />
              </ListItem>
              <Collapse in={mobileRecruiterOpen} timeout="auto" unmountOnExit>
                <List as="div" disablePadding>
                  {recruiterItems.map((item) => (
                    <ListItem
                      key={item.path}
                      as={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: theme.spacing.xl }}
                      disablePadding
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Icon name={item.iconName} size="small" />
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </>

            <Divider />

            {/* Admin Module */}
            <>
              <ListItem
                disablePadding
                onClick={handleMobileAdminToggle}
                aria-expanded={mobileAdminOpen}
              >
                <ListItemIcon>
                  <Icon name="settings" size="small" />
                </ListItemIcon>
                <ListItemText primary={t('nav.admin')} />
                <Icon
                  name={mobileAdminOpen ? 'chevron-up' : 'chevron-down'}
                  size="small"
                  color="secondary"
                />
              </ListItem>
              <Collapse in={mobileAdminOpen} timeout="auto" unmountOnExit>
                <List as="div" disablePadding>
                  {adminItems.map((item) => (
                    <ListItem
                      key={item.path}
                      as={Link}
                      to={item.path}
                      onClick={() => handleMobileNavClick(item.path)}
                      selected={location.pathname === item.path}
                      sx={{ pl: theme.spacing.xl }}
                      disablePadding
                    >
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Icon name={item.iconName} size="small" />
                      </ListItemIcon>
                      <ListItemText primary={t(item.labelKey)} />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </>
          </List>
        </Box>
      </Drawer>

      {/* Main Content Area */}
      <Box sx={{ flexGrow: 1, py: theme.spacing.xl }}>
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>

      {/* Footer */}
      <Box
        as="footer"
        sx={{
          py: theme.spacing.md,
          px: theme.spacing.sm,
          mt: 'auto',
          backgroundColor: theme.mode === 'light' ? theme.grey[200] : theme.grey[800],
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

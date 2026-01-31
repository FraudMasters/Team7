import React, { ReactNode, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
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
  ListItemText,
  ListItemIcon,
  Divider,
  Collapse,
} from '@mui/material';
import {
  Description as ResumeIcon,
  Work as WorkIcon,
  Person as PersonIcon,
  BusinessCenter as RecruiterIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Upload as UploadIcon,
  School as SchoolIcon,
  Tune as TuneIcon,
  Backup as BackupIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore as ExpandMoreArrow,
} from '@mui/icons-material';
import LanguageSwitcher from './LanguageSwitcher';
import ThemeSwitcher from './ThemeSwitcher';
import ResponsiveWrapper from './ResponsiveWrapper';

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
  const [jobSeekerAnchorEl, setJobSeekerAnchorEl] = useState<null | HTMLElement>(null);
  const [recruiterAnchorEl, setRecruiterAnchorEl] = useState<null | HTMLElement>(null);
  const [adminAnchorEl, setAdminAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileJobSeekerOpen, setMobileJobSeekerOpen] = useState(false);
  const [mobileRecruiterOpen, setMobileRecruiterOpen] = useState(false);
  const [mobileAdminOpen, setMobileAdminOpen] = useState(false);

  const jobSeekerMenuOpen = Boolean(jobSeekerAnchorEl);
  const recruiterMenuOpen = Boolean(recruiterAnchorEl);
  const adminMenuOpen = Boolean(adminAnchorEl);

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
    { labelKey: 'nav.adminBackups', path: '/admin/backups', icon: <BackupIcon fontSize="small" /> },
  ];

  // Mobile menu handlers
  const handleMobileMenuOpen = () => setMobileMenuOpen(true);
  const handleMobileMenuClose = () => {
    setMobileMenuOpen(false);
    setMobileJobSeekerOpen(false);
    setMobileRecruiterOpen(false);
    setMobileAdminOpen(false);
  };

  const handleMobileJobSeekerToggle = () => {
    setMobileJobSeekerOpen(!mobileJobSeekerOpen);
    setMobileRecruiterOpen(false);
    setMobileAdminOpen(false);
  };

  const handleMobileRecruiterToggle = () => {
    setMobileRecruiterOpen(!mobileRecruiterOpen);
    setMobileJobSeekerOpen(false);
    setMobileAdminOpen(false);
  };

  const handleMobileAdminToggle = () => {
    setMobileAdminOpen(!mobileAdminOpen);
    setMobileJobSeekerOpen(false);
    setMobileRecruiterOpen(false);
  };

  // Mobile menu drawer content
  const mobileMenuContent = (
    <Box sx={{ width: 280 }} role="presentation">
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <ResumeIcon sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {t('appName')}
          </Typography>
        </Box>
        <IconButton onClick={handleMobileMenuClose} size="large">
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />
      <List>
        {/* Job Seeker Module */}
        <ListItem button onClick={handleMobileJobSeekerToggle}>
          <ListItemIcon><WorkIcon /></ListItemIcon>
          <ListItemText primary={t('nav.findJobs')} />
          {mobileJobSeekerOpen ? <ExpandLess /> : <ExpandMoreArrow />}
        </ListItem>
        <Collapse in={mobileJobSeekerOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {jobSeekerItems.map((item) => (
              <ListItem
                key={item.path}
                button
                component={Link}
                to={item.path}
                onClick={handleMobileMenuClose}
                selected={location.pathname === item.path}
                sx={{ pl: 4 }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={t(item.labelKey)} />
              </ListItem>
            ))}
          </List>
        </Collapse>

        {/* Recruiter Module */}
        <ListItem button onClick={handleMobileRecruiterToggle}>
          <ListItemIcon><RecruiterIcon /></ListItemIcon>
          <ListItemText primary={t('nav.findEmployees')} />
          {mobileRecruiterOpen ? <ExpandLess /> : <ExpandMoreArrow />}
        </ListItem>
        <Collapse in={mobileRecruiterOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {recruiterItems.map((item) => (
              <ListItem
                key={item.path}
                button
                component={Link}
                to={item.path}
                onClick={handleMobileMenuClose}
                selected={location.pathname === item.path}
                sx={{ pl: 4 }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={t(item.labelKey)} />
              </ListItem>
            ))}
          </List>
        </Collapse>

        {/* Admin Module */}
        <ListItem button onClick={handleMobileAdminToggle}>
          <ListItemIcon><SettingsIcon /></ListItemIcon>
          <ListItemText primary={t('nav.admin')} />
          {mobileAdminOpen ? <ExpandLess /> : <ExpandMoreArrow />}
        </ListItem>
        <Collapse in={mobileAdminOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {adminItems.map((item) => (
              <ListItem
                key={item.path}
                button
                component={Link}
                to={item.path}
                onClick={handleMobileMenuClose}
                selected={location.pathname === item.path}
                sx={{ pl: 4 }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={t(item.labelKey)} />
              </ListItem>
            ))}
          </List>
        </Collapse>
      </List>
      <Divider />
      <Box sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <LanguageSwitcher />
        <ThemeSwitcher />
      </Box>
    </Box>
  );

  return (
    <ResponsiveWrapper>
      {(isMobile) => (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {/* App Bar / Navigation */}
          <AppBar position="static" elevation={2}>
            <Container maxWidth="lg">
              <Toolbar disableGutters>
                {/* Logo / Brand */}
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
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
                    {t('appName')}
                  </Typography>
                </Box>

                {/* Mobile Menu: Hamburger */}
                {isMobile ? (
                  <>
                    <Box sx={{ flexGrow: 1 }} />
                    <IconButton
                      size="large"
                      edge="end"
                      color="inherit"
                      aria-label="menu"
                      onClick={handleMobileMenuOpen}
                    >
                      <MenuIcon />
                    </IconButton>
                    <Drawer
                      anchor="left"
                      open={mobileMenuOpen}
                      onClose={handleMobileMenuClose}
                      ModalProps={{
                        keepMounted: true,
                      }}
                    >
                      {mobileMenuContent}
                    </Drawer>
                  </>
                ) : (
                  <>
                    {/* Desktop Navigation Links - Module Based */}
                    <Box sx={{ flexGrow: 1, display: 'flex', gap: 1, ml: 2 }}>
              {/* Job Seeker Module */}
              <Button
                color="inherit"
                startIcon={<WorkIcon />}
                endIcon={<ExpandMoreIcon />}
                onClick={(e) => setJobSeekerAnchorEl(e.currentTarget)}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  borderRadius: 1,
                  px: 2,
                }}
              >
                {t('nav.findJobs')}
              </Button>
              <Menu
                anchorEl={jobSeekerAnchorEl}
                open={jobSeekerMenuOpen}
                onClose={() => setJobSeekerAnchorEl(null)}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
              >
                {jobSeekerItems.map((item) => (
                  <MenuItem
                    key={item.path}
                    component={Link}
                    to={item.path}
                    onClick={() => setJobSeekerAnchorEl(null)}
                    selected={location.pathname === item.path}
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
                startIcon={<RecruiterIcon />}
                endIcon={<ExpandMoreIcon />}
                onClick={(e) => setRecruiterAnchorEl(e.currentTarget)}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  borderRadius: 1,
                  px: 2,
                }}
              >
                {t('nav.findEmployees')}
              </Button>
              <Menu
                anchorEl={recruiterAnchorEl}
                open={recruiterMenuOpen}
                onClose={() => setRecruiterAnchorEl(null)}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
              >
                {recruiterItems.map((item) => (
                  <MenuItem
                    key={item.path}
                    component={Link}
                    to={item.path}
                    onClick={() => setRecruiterAnchorEl(null)}
                    selected={location.pathname === item.path}
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
                startIcon={<SettingsIcon />}
                endIcon={<ExpandMoreIcon />}
                onClick={(e) => setAdminAnchorEl(e.currentTarget)}
                sx={{
                  textTransform: 'none',
                  fontWeight: 500,
                  borderRadius: 1,
                  px: 2,
                }}
              >
                {t('nav.admin')}
              </Button>
              <Menu
                anchorEl={adminAnchorEl}
                open={adminMenuOpen}
                onClose={() => setAdminAnchorEl(null)}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
              >
                {adminItems.map((item) => (
                  <MenuItem
                    key={item.path}
                    component={Link}
                    to={item.path}
                    onClick={() => setAdminAnchorEl(null)}
                    selected={location.pathname === item.path}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
                      {item.icon}
                      <Typography variant="body2">{t(item.labelKey)}</Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Menu>
                </Box>

                {/* Language Switcher - Desktop */}
                <LanguageSwitcher />
                {/* Theme Switcher - Desktop */}
                <ThemeSwitcher />
                  </>
                )}
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
            {t('footer.copyright', { year: new Date().getFullYear() })}
          </Typography>
        </Container>
      </Box>
    </Box>
      )}
    </ResponsiveWrapper>
  );
};

export default Layout;

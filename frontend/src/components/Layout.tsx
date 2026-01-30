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
} from '@mui/material';
import {
  Description as ResumeIcon,
  Work as WorkIcon,
  Person as PersonIcon,
  BusinessCenter as RecruiterIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import LanguageSwitcher from './LanguageSwitcher';

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
                {t('appName')}
              </Typography>
            </Box>

            {/* Navigation Links - Module Based */}
            <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
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

            {/* Language Switcher */}
            <LanguageSwitcher />
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
  );
};

export default Layout;

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Typography,
  IconButton,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Close as CloseIcon,
  Description as PolicyIcon,
} from '@mui/icons-material';
import { useCookieContext } from '@/contexts/CookieContext';

/**
 * CookieBanner Component
 *
 * Provides GDPR-compliant cookie consent banner with granular control options.
 * Displays on first visit and allows users to customize their cookie preferences.
 *
 * Features:
 * - Shows banner on first visit (no consent stored)
 * - Provides quick actions: Accept All, Reject All, Customize
 * - Detailed consent dialog with category toggles
 * - Responsive design for mobile and desktop
 * - Accessible with ARIA labels and keyboard navigation
 * - Integrates with CookieContext for state management
 * - Persists consent to localStorage
 *
 * @example
 * ```tsx
 * // In Layout component, render conditionally
 * {!hasConsented && <CookieBanner />}
 * ```
 */
const CookieBanner: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { acceptAll, rejectAll, saveConsent } = useCookieContext();

  // Dialog state for detailed consent options
  const [dialogOpen, setDialogOpen] = useState(false);

  // Temporary consent state for dialog
  const [tempConsent, setTempConsent] = useState({
    necessary: true,
    analytics: false,
    marketing: false,
  });

  /**
   * Handle "Accept All" button click
   *
   * Accepts all cookie categories and hides banner.
   */
  const handleAcceptAll = () => {
    acceptAll();
  };

  /**
   * Handle "Reject All" button click
   *
   * Rejects all optional cookies, keeps only necessary, and hides banner.
   */
  const handleRejectAll = () => {
    rejectAll();
  };

  /**
   * Handle "Customize" button click
   *
   * Opens the detailed consent dialog.
   */
  const handleCustomize = () => {
    setDialogOpen(true);
  };

  /**
   * Handle dialog close
   *
   * Closes the dialog without saving.
   */
  const handleDialogClose = () => {
    setDialogOpen(false);
    // Reset temp consent to defaults
    setTempConsent({
      necessary: true,
      analytics: false,
      marketing: false,
    });
  };

  /**
   * Handle saving custom consent preferences
   *
   * Saves user's selected cookie preferences and hides banner.
   */
  const handleSavePreferences = () => {
    saveConsent(tempConsent);
    setDialogOpen(false);
  };

  /**
   * Handle consent checkbox change
   *
   * @param category - Cookie category to update
   * @param checked - New checked state
   */
  const handleConsentChange = (category: 'analytics' | 'marketing', checked: boolean) => {
    setTempConsent((prev) => ({
      ...prev,
      [category]: checked,
    }));
  };

  return (
    <>
      {/* Cookie Banner */}
      <Paper
        elevation={8}
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 9999,
          borderRadius: 0,
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Box
          sx={{
            p: { xs: 2, sm: 3 },
            maxWidth: 'lg',
            mx: 'auto',
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'stretch', sm: 'center' },
            gap: 2,
          }}
        >
          {/* Description */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PolicyIcon color="primary" sx={{ fontSize: 20 }} />
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 600,
                  color: 'text.primary',
                }}
              >
                {t('cookies.banner.title')}
              </Typography>
            </Box>
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {t('cookies.banner.description')}
            </Typography>
          </Box>

          {/* Action Buttons */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 1,
              minWidth: { xs: '100%', sm: 'auto' },
              flexShrink: 0,
            }}
          >
            <Button
              variant="text"
              color="inherit"
              onClick={handleCustomize}
              sx={{
                minWidth: { xs: '100%', sm: 120 },
                textTransform: 'none',
                fontWeight: 500,
              }}
            >
              {t('cookies.banner.customize')}
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              onClick={handleRejectAll}
              sx={{
                minWidth: { xs: '100%', sm: 120 },
                textTransform: 'none',
                fontWeight: 500,
              }}
            >
              {t('cookies.banner.reject')}
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleAcceptAll}
              sx={{
                minWidth: { xs: '100%', sm: 120 },
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              {t('cookies.banner.accept')}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Customization Dialog */}
      <Dialog
        fullScreen={fullScreen}
        open={dialogOpen}
        onClose={handleDialogClose}
        aria-labelledby="cookie-dialog-title"
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: { xs: 0, sm: 2 },
          },
        }}
      >
        <DialogTitle
          id="cookie-dialog-title"
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            pb: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PolicyIcon color="primary" />
            <Typography variant="h6" component="span">
              {t('cookies.dialog.title')}
            </Typography>
          </Box>
          <IconButton
            edge="end"
            onClick={handleDialogClose}
            aria-label={t('common.close')}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers>
          <Typography variant="body2" sx={{ mb: 3, color: 'text.secondary' }}>
            {t('cookies.dialog.description')}
          </Typography>

          {/* Necessary Cookies (Always Enabled) */}
          <Box sx={{ mb: 3 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={true}
                  disabled
                  size="small"
                  sx={{
                    '&.Mui-disabled': {
                      color: 'text.primary',
                    },
                  }}
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {t('cookies.categories.necessary.name')}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {t('cookies.categories.necessary.description')}
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start', ml: 0 }}
            />
          </Box>

          {/* Analytics Cookies */}
          <Box sx={{ mb: 3 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={tempConsent.analytics}
                  onChange={(e) => handleConsentChange('analytics', e.target.checked)}
                  size="small"
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {t('cookies.categories.analytics.name')}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {t('cookies.categories.analytics.description')}
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start', ml: 0 }}
            />
          </Box>

          {/* Marketing Cookies */}
          <Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={tempConsent.marketing}
                  onChange={(e) => handleConsentChange('marketing', e.target.checked)}
                  size="small"
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {t('cookies.categories.marketing.name')}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {t('cookies.categories.marketing.description')}
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start', ml: 0 }}
            />
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            onClick={handleDialogClose}
            color="inherit"
            sx={{ textTransform: 'none' }}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleSavePreferences}
            variant="contained"
            color="primary"
            sx={{ textTransform: 'none', fontWeight: 600 }}
          >
            {t('cookies.dialog.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default CookieBanner;

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  DialogContentText,
  IconButton,
  Snackbar,
  Alert,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

/**
 * PWAInstallPrompt Component
 *
 * Provides an install-to-homescreen prompt for Progressive Web App installation.
 * Detects when the app can be installed and shows an appropriate UI to guide users.
 * Handles the beforeinstallprompt event and manages the installation flow.
 *
 * Features:
 * - Detects PWA install capability via beforeinstallprompt event
 * - Shows install button in appropriate locations
 * - Displays installation dialog with app information
 * - Handles successful/failed installation states
 * - Remembers if app was already installed to avoid re-prompting
 * - Responsive design for mobile and desktop
 * - Integrates with i18n for localized messages
 *
 * Behavior:
 * - Button only appears when the browser fires beforeinstallprompt event
 * - Clicking opens a dialog explaining PWA installation benefits
 * - User can proceed with installation or dismiss
 * - After successful install, the prompt is hidden permanently
 * - Shows success/error feedback via snackbar notifications
 *
 * @example
 * ```tsx
 * // In App component or Layout
 * <PWAInstallPrompt />
 * ```
 */
const PWAInstallPrompt: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  // State for install prompt
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  /**
   * Check if app is already installed
   *
   * Checks localStorage and window.matchMedia for standalone display modes
   * to determine if the app is already installed.
   */
  useEffect(() => {
    const checkIfInstalled = () => {
      // Check localStorage
      const installed = localStorage.getItem('pwa-installed');
      if (installed === 'true') {
        setIsInstalled(true);
        return;
      }

      // Check if currently running in standalone mode (already installed)
      const isStandalone =
        window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true;

      if (isStandalone) {
        setIsInstalled(true);
        localStorage.setItem('pwa-installed', 'true');
      }
    };

    checkIfInstalled();
  }, []);

  /**
   * Handle beforeinstallprompt event
   *
   * Captures the event and prevents default browser install prompt.
   * Stores the event for later use when user clicks install button.
   */
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();

      // Stash the event so it can be triggered later
      setDeferredPrompt(e);

      // Show install button
      setShowInstallButton(true);
    };

    // Check if app is already installed
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setShowInstallButton(false);
      setDeferredPrompt(null);
      localStorage.setItem('pwa-installed', 'true');
      showSnackbar(
        t('pwa.installSuccess') || 'App installed successfully!',
        'success'
      );
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener(
        'beforeinstallprompt',
        handleBeforeInstallPrompt
      );
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [t]);

  /**
   * Show snackbar notification
   *
   * Displays a temporary notification message to the user.
   *
   * @param message - Message to display
   * @param severity - Severity level (success or error)
   */
  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  /**
   * Handle install button click
   *
   * Opens the installation dialog to guide the user through the process.
   */
  const handleInstallClick = () => {
    setShowDialog(true);
  };

  /**
   * Handle dialog close
   *
   * Closes the installation dialog without proceeding.
   */
  const handleDialogClose = () => {
    setShowDialog(false);
  };

  /**
   * Handle install confirmation
   *
   * Triggers the actual PWA installation prompt using the deferred event.
   */
  const handleInstallConfirm = async () => {
    if (!deferredPrompt) {
      showSnackbar(
        t('pwa.installError') || 'Installation not available',
        'error'
      );
      return;
    }

    try {
      // Show the install prompt
      deferredPrompt.prompt();

      // Wait for the user to respond to the prompt
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        showSnackbar(
          t('pwa.installSuccess') || 'App installed successfully!',
          'success'
        );
      } else {
        showSnackbar(
          t('pwa.installDismissed') || 'Install prompt dismissed',
          'success'
        );
      }

      // Clear the deferred prompt
      setDeferredPrompt(null);
      setShowInstallButton(false);
    } catch (error) {
      showSnackbar(
        t('pwa.installError') || 'Installation failed',
        'error'
      );
    }

    setShowDialog(false);
  };

  /**
   * Handle snackbar close
   *
   * Closes the snackbar notification.
   */
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Don't render if already installed or no install prompt available
  if (isInstalled || !showInstallButton) {
    return null;
  }

  return (
    <>
      {/* Install Button - Floating action button */}
      <Box
        sx={{
          position: 'fixed',
          bottom: { xs: 80, sm: 24 },
          right: 24,
          zIndex: 1000,
        }}
      >
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleInstallClick}
          sx={{
            borderRadius: 2,
            px: 2,
            py: 1.5,
            boxShadow: 3,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              boxShadow: 6,
              background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            },
            transition: 'all 0.3s ease-in-out',
          }}
        >
          {t('pwa.installButton') || 'Install App'}
        </Button>
      </Box>

      {/* Install Dialog */}
      <Dialog
        fullScreen={fullScreen}
        open={showDialog}
        onClose={handleDialogClose}
        aria-labelledby="pwa-install-dialog-title"
        sx={{
          '& .MuiDialog-paper': {
            borderRadius: 2,
            maxWidth: 500,
          },
        }}
      >
        <DialogTitle id="pwa-install-dialog-title">
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            {t('pwa.dialogTitle') || 'Install Application'}
            <IconButton
              onClick={handleDialogClose}
              aria-label={t('common.close') || 'Close'}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText component="div">
            <Box sx={{ mb: 2 }}>
              {t('pwa.dialogMessage') ||
                'Install this application on your device for quick access and offline functionality.'}
            </Box>
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: 'rgba(103, 126, 234, 0.1)',
                borderRadius: 1,
              }}
            >
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <Box component="li" sx={{ mb: 1 }}>
                  {t('pwa.benefit1') || 'Fast access from your home screen'}
                </Box>
                <Box component="li" sx={{ mb: 1 }}>
                  {t('pwa.benefit2') || 'Works offline'}
                </Box>
                <Box component="li" sx={{ mb: 1 }}>
                  {t('pwa.benefit3') || 'Smoother experience'}
                </Box>
                <Box component="li">
                  {t('pwa.benefit4') || 'No app store needed'}
                </Box>
              </Box>
            </Box>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2, pt: 0 }}>
          <Button onClick={handleDialogClose}>
            {t('common.cancel') || 'Cancel'}
          </Button>
          <Button
            onClick={handleInstallConfirm}
            variant="contained"
            startIcon={<DownloadIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
              },
            }}
          >
            {t('pwa.install') || 'Install'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default PWAInstallPrompt;

import React, { useState, useCallback, useRef, forwardRef, useImperativeHandle, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  LinearProgress,
  Alert,
  Stack,
} from '@mui/material';
import {
  LinkedIn as LinkedInIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  PersonAdd as ImportIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api';

/**
 * LinkedIn import state interface
 */
interface ImportState {
  linkedinUrl: string;
  importing: boolean;
  progress: number;
  error: string | null;
  success: boolean;
  profileId: string | null;
  resumeId: string | null;
}

/**
 * Imperative handle exposed by LinkedInImport
 */
export interface LinkedInImportHandle {
  /**
   * Trigger the import with the current URL
   */
  triggerImport: () => void;
  /**
   * Cancel current import and reset state
   */
  cancelImport: () => void;
  /**
   * Set LinkedIn URL programmatically
   */
  setUrl: (url: string) => void;
}

/**
 * LinkedInImport Component Props
 */
interface LinkedInImportProps {
  /** Callback when import completes successfully */
  onImportComplete?: (profileId: string, resumeId: string) => void;
  /** Callback when import fails */
  onImportError?: (error: string) => void;
  /** Callback when importing state changes */
  onImportingChange?: (isImporting: boolean) => void;
  /** Initial LinkedIn URL value */
  initialUrl?: string;
}

/**
 * LinkedInImport Component
 *
 * Provides LinkedIn profile import functionality with:
 * - URL validation and format checking
 * - Import progress tracking
 * - Error handling and display
 * - Success state with profile and resume IDs
 *
 * @example
 * ```tsx
 * const importerRef = useRef<LinkedInImportHandle>(null);
 * <LinkedInImport
 *   ref={importerRef}
 *   onImportComplete={(profileId, resumeId) => navigate(`/candidates/${resumeId}`)}
 * />
 *
 * // Programmatic control
 * importerRef.current?.setUrl('https://www.linkedin.com/in/johndoe');
 * importerRef.current?.triggerImport();
 * importerRef.current?.cancelImport();
 * ```
 */
const LinkedInImport = forwardRef<LinkedInImportHandle, LinkedInImportProps>(({
  onImportComplete,
  onImportError,
  onImportingChange,
  initialUrl = '',
}, ref) => {
  const { t } = useTranslation();

  const [importState, setImportState] = useState<ImportState>({
    linkedinUrl: initialUrl,
    importing: false,
    progress: 0,
    error: null,
    success: false,
    profileId: null,
    resumeId: null,
  });

  const [urlError, setUrlError] = useState<string | null>(null);

  /**
   * Notify parent of importing state changes
   */
  useEffect(() => {
    onImportingChange?.(importState.importing);
  }, [importState.importing, onImportingChange]);

  /**
   * Reset import state
   */
  const handleReset = useCallback(() => {
    setImportState({
      linkedinUrl: '',
      importing: false,
      progress: 0,
      error: null,
      success: false,
      profileId: null,
      resumeId: null,
    });
    setUrlError(null);
  }, []);

  /**
   * Expose methods via ref for parent component access
   */
  useImperativeHandle(ref, () => ({
    triggerImport: () => {
      if (!importState.importing && importState.linkedinUrl) {
        handleImport();
      }
    },
    cancelImport: () => {
      handleReset();
    },
    setUrl: (url: string) => {
      setImportState((prev) => ({ ...prev, linkedinUrl: url }));
      setUrlError(null);
    },
  }), [importState.importing, importState.linkedinUrl, handleReset]);

  /**
   * Validate LinkedIn URL format
   */
  const validateLinkedInUrl = useCallback(
    (url: string): string | null => {
      if (!url || url.trim() === '') {
        return t('linkedin.import.errors.urlRequired');
      }

      const trimmedUrl = url.trim();
      const linkedinUrlPattern = /^https?:\/\/(www\.)?linkedin\.com\/(in|pub)\/[\w-]+\/?$/;

      if (!linkedinUrlPattern.test(trimmedUrl)) {
        return t('linkedin.import.errors.invalidFormat');
      }

      return null;
    },
    [t]
  );

  /**
   * Handle URL input change
   */
  const handleUrlChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const url = event.target.value;
      setImportState((prev) => ({ ...prev, linkedinUrl: url }));

      // Clear previous errors
      if (urlError) {
        setUrlError(null);
      }
      if (importState.error) {
        setImportState((prev) => ({ ...prev, error: null }));
      }
    },
    [urlError, importState.error]
  );

  /**
   * Handle blur event for URL validation
   */
  const handleUrlBlur = useCallback(() => {
    const error = validateLinkedInUrl(importState.linkedinUrl);
    setUrlError(error);
  }, [importState.linkedinUrl, validateLinkedInUrl]);

  /**
   * Import LinkedIn profile
   */
  const handleImport = useCallback(async () => {
    // Validate URL
    const validationError = validateLinkedInUrl(importState.linkedinUrl);
    if (validationError) {
      setUrlError(validationError);
      setImportState((prev) => ({ ...prev, error: validationError }));
      onImportError?.(validationError);
      return;
    }

    setImportState((prev) => ({
      ...prev,
      importing: true,
      progress: 0,
      error: null,
      success: false,
    }));

    try {
      // Simulate progress for better UX (LinkedIn API calls can be slow)
      const progressInterval = setInterval(() => {
        setImportState((prev) => {
          if (prev.progress < 90) {
            return { ...prev, progress: prev.progress + 10 };
          }
          return prev;
        });
      }, 200);

      const response = await apiClient.importLinkedInProfile({
        linkedin_url: importState.linkedinUrl.trim(),
      });

      clearInterval(progressInterval);

      if (response.success && response.profile_id) {
        setImportState({
          linkedinUrl: importState.linkedinUrl,
          importing: false,
          progress: 100,
          error: null,
          success: true,
          profileId: response.profile_id,
          resumeId: response.resume_id || null,
        });

        onImportComplete?.(
          response.profile_id,
          response.resume_id || ''
        );
      } else {
        throw new Error(response.message || t('linkedin.import.errors.importFailed'));
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : t('linkedin.import.errors.importFailed');

      setImportState((prev) => ({
        ...prev,
        importing: false,
        error: errorMessage,
      }));

      onImportError?.(errorMessage);
    }
  }, [importState.linkedinUrl, validateLinkedInUrl, onImportComplete, onImportError, t]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      if (!importState.importing) {
        handleImport();
      }
    },
    [importState.importing, handleImport]
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        elevation={2}
        sx={{
          p: 4,
          border: '2px solid',
          borderColor: importState.error
            ? 'error.main'
            : importState.success
              ? 'success.main'
              : 'divider',
          bgcolor: 'background.paper',
          transition: 'all 0.2s ease-in-out',
        }}
      >
        {/* Error Alert */}
        {importState.error && (
          <Alert
            severity="error"
            icon={<ErrorIcon />}
            sx={{ mb: 2 }}
            action={
              !importState.importing && (
                <Button
                  color="inherit"
                  size="small"
                  onClick={handleReset}
                  disabled={importState.importing}
                >
                  {t('common.tryAgain')}
                </Button>
              )
            }
          >
            {importState.error}
          </Alert>
        )}

        {/* Success Alert */}
        {importState.success && (
          <Alert
            severity="success"
            icon={<SuccessIcon />}
            sx={{ mb: 2 }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={handleReset}
                disabled={importState.importing}
              >
                {t('linkedin.import.importAnother')}
              </Button>
            }
          >
            {t('linkedin.import.success', {
              profileId: importState.profileId,
            })}
          </Alert>
        )}

        {/* Import Form */}
        {!importState.success && !importState.error && (
          <Box component="form" onSubmit={handleSubmit}>
            {/* LinkedIn Icon */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mb: 2,
              }}
            >
              <LinkedInIcon
                sx={{
                  fontSize: 64,
                  color: 'primary.main',
                }}
              />
            </Box>

            {/* Main Text */}
            <Typography variant="h6" align="center" gutterBottom fontWeight={600}>
              {importState.importing
                ? t('linkedin.import.importing')
                : t('linkedin.import.title')}
            </Typography>

            {/* Subtitle */}
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              paragraph
            >
              {t('linkedin.import.helpText')}
            </Typography>

            {/* URL Input Field */}
            <TextField
              fullWidth
              label={t('linkedin.import.urlLabel')}
              placeholder="https://www.linkedin.com/in/johndoe"
              value={importState.linkedinUrl}
              onChange={handleUrlChange}
              onBlur={handleUrlBlur}
              error={!!urlError}
              helperText={urlError || t('linkedin.import.urlHelper')}
              disabled={importState.importing}
              sx={{ mb: 2 }}
              autoComplete="off"
            />

            {/* Import Button */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<ImportIcon />}
                type="submit"
                disabled={importState.importing || !importState.linkedinUrl.trim()}
              >
                {importState.importing
                  ? t('linkedin.import.importing')
                  : t('linkedin.import.importButton')}
              </Button>
            </Box>
          </Box>
        )}

        {/* Progress Bar */}
        {importState.importing && (
          <Box sx={{ mt: 3 }}>
            <LinearProgress
              variant="determinate"
              value={importState.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              sx={{ mt: 1 }}
            >
              {t('linkedin.import.progress', { percent: importState.progress })}
            </Typography>
          </Box>
        )}

        {/* URL Info (when showing error/success) */}
        {(importState.error || importState.success) && importState.linkedinUrl && (
          <Box sx={{ mt: 2 }}>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              justifyContent="center"
            >
              <Typography variant="body2" color="text.primary">
                <strong>{t('linkedin.import.profileUrl')}:</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {importState.linkedinUrl}
              </Typography>
            </Stack>
          </Box>
        )}
      </Paper>

      {/* Help Text */}
      {!importState.success && (
        <Typography
          variant="caption"
          color="text.secondary"
          align="center"
          display="block"
          sx={{ mt: 2 }}
        >
          {t('linkedin.import.footerText')}
        </Typography>
      )}
    </Box>
  );
});

LinkedInImport.displayName = 'LinkedInImport';

export default LinkedInImport;

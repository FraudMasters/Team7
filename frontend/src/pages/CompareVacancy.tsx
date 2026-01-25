import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Box, Container, Typography, Paper, Alert, Stack, Snackbar, Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, CircularProgress, IconButton } from '@mui/material';
import { ContentCopy as CopyIcon, Check as CheckIcon } from '@mui/icons-material';
import { ResumeComparisonMatrix } from '@components/ResumeComparisonMatrix';
import { ComparisonControls } from '@components/ComparisonControls';
import { apiClient } from '@/api/client';
import type { ComparisonCreate } from '@/types/api';

/**
 * CompareVacancy Page Component
 *
 * Provides a comprehensive interface for comparing multiple resumes against a specific vacancy:
 * - Select 2-5 resumes for comparison
 * - Filter by match percentage range
 * - Sort by different criteria
 * - Visual comparison matrix with skill highlighting
 * - Ranked results by match percentage
 *
 * Route: /compare-vacancy/:vacancyId
 * Query Params: ?resumes=id1,id2,id3 (optional - pre-selects resumes)
 */
const CompareVacancyPage: React.FC = () => {
  const { vacancyId } = useParams<{ vacancyId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  // State for managing comparison
  const [resumeIds, setResumeIds] = useState<string[]>([]);

  // State for save dialog
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [comparisonName, setComparisonName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // State for share dialog
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareableUrl, setShareableUrl] = useState('');
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);

  // State for notifications
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  /**
   * Initialize resume IDs from URL query params on mount
   */
  useEffect(() => {
    const resumesParam = searchParams.get('resumes');
    if (resumesParam) {
      const ids = resumesParam.split(',').filter((id) => id.trim().length > 0);
      if (ids.length >= 2 && ids.length <= 5) {
        setResumeIds(ids);
      }
    }
  }, [searchParams]);

  /**
   * Handle resume IDs change from ComparisonControls
   */
  const handleResumeIdsChange = (newResumeIds: string[]) => {
    setResumeIds(newResumeIds);

    // Update URL query params to reflect current selection
    if (newResumeIds.length > 0) {
      setSearchParams({ resumes: newResumeIds.join(',') });
    } else {
      searchParams.delete('resumes');
      setSearchParams(searchParams);
    }
  };

  /**
   * Handle filters change (for future enhancement)
   */
  const handleFiltersChange = (filters: { min_match_percentage: number; max_match_percentage: number }) => {
    // Filters can be applied to the comparison results in future iterations
    // For now, the ResumeComparisonMatrix displays all results
  };

  /**
   * Handle sort change (for future enhancement)
   */
  const handleSortChange = (sort: { field: string; order: string }) => {
    // Sorting can be applied to the comparison results in future iterations
    // For now, ResumeComparisonMatrix sorts by match_percentage descending
  };

  /**
   * Handle save comparison - opens dialog to enter comparison name
   */
  const handleSave = () => {
    if (resumeIds.length < 2 || resumeIds.length > 5) {
      setNotification({
        open: true,
        message: 'Please select 2-5 resumes before saving.',
        severity: 'error',
      });
      return;
    }
    setComparisonName(`Comparison for ${vacancyId}`);
    setSaveDialogOpen(true);
  };

  /**
   * Confirm save comparison - sends API request to create comparison
   */
  const handleConfirmSave = async () => {
    if (!vacancyId) {
      return;
    }

    setIsSaving(true);

    try {
      const createRequest: ComparisonCreate = {
        vacancy_id: vacancyId,
        resume_ids: resumeIds,
        name: comparisonName || `Comparison for ${vacancyId}`,
        filters: {},
      };

      const response = await apiClient.createComparison(createRequest);

      setSaveDialogOpen(false);
      setComparisonName('');
      setNotification({
        open: true,
        message: `Comparison "${response.name}" saved successfully! ID: ${response.id}`,
        severity: 'success',
      });
    } catch (error) {
      setNotification({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to save comparison',
        severity: 'error',
      });
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle share comparison - generates shareable URL
   */
  const handleShare = () => {
    if (resumeIds.length < 2) {
      setNotification({
        open: true,
        message: 'Please select at least 2 resumes before sharing.',
        severity: 'error',
      });
      return;
    }

    // Generate shareable URL based on current state
    const baseUrl = window.location.origin;
    const url = new URL(`${baseUrl}/compare-vacancy/${vacancyId}`);
    url.searchParams.set('resumes', resumeIds.join(','));

    setShareableUrl(url.toString());
    setShareDialogOpen(true);
    setCopiedToClipboard(false);
  };

  /**
   * Copy shareable URL to clipboard
   */
  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(shareableUrl);
      setCopiedToClipboard(true);

      // Reset the copied state after 2 seconds
      setTimeout(() => {
        setCopiedToClipboard(false);
      }, 2000);
    } catch (error) {
      setNotification({
        open: true,
        message: 'Failed to copy URL to clipboard',
        severity: 'error',
      });
    }
  };

  /**
   * Close notification snackbar
   */
  const handleNotificationClose = () => {
    setNotification((prev) => ({ ...prev, open: false }));
  };

  if (!vacancyId) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          <Typography variant="h6" fontWeight={600}>
            Invalid Vacancy
          </Typography>
          <Typography variant="body2">No vacancy ID provided in the URL.</Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
            Compare Resumes for Vacancy
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Compare multiple resumes side-by-side to identify the best candidates for this position.
            Select 2-5 resumes to see a detailed skill matrix and rankings.
          </Typography>
        </Box>

        {/* Comparison Controls */}
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Comparison Settings
          </Typography>
          <ComparisonControls
            resumeIds={resumeIds}
            onResumeIdsChange={handleResumeIdsChange}
            onFiltersChange={handleFiltersChange}
            onSortChange={handleSortChange}
            onSave={handleSave}
            onShare={handleShare}
            minResumes={2}
            maxResumes={5}
          />
        </Paper>

        {/* Comparison Matrix */}
        {resumeIds.length >= 2 && resumeIds.length <= 5 && (
          <ResumeComparisonMatrix resumeIds={resumeIds} vacancyId={vacancyId} showRanking={true} />
        )}

        {/* Guidance when no resumes selected */}
        {resumeIds.length < 2 && (
          <Paper elevation={0} sx={{ p: 4, bgcolor: 'info.50', border: '1px solid', borderColor: 'info.200' }}>
            <Typography variant="h6" gutterBottom fontWeight={600} color="info.main">
              Getting Started
            </Typography>
            <Typography variant="body2" paragraph>
              Add at least 2 resume IDs to begin the comparison. You can add up to 5 resumes at once.
            </Typography>
            <Typography variant="body2" paragraph>
              Use the controls above to add resume IDs one at a time, or visit a URL like:
            </Typography>
            <Typography variant="body2" component="div" sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, fontFamily: 'monospace' }}>
              /compare-vacancy/{vacancyId}?resumes=resume-1,resume-2,resume-3
            </Typography>
          </Paper>
        )}

        {/* Warning if too many resumes */}
        {resumeIds.length > 5 && (
          <Alert severity="warning">
            <Typography variant="subtitle1" fontWeight={600}>
              Too Many Resumes
            </Typography>
            <Typography variant="body2">
              Please remove some resumes. Maximum 5 resumes can be compared at once.
            </Typography>
          </Alert>
        )}
      </Stack>

      {/* Save Comparison Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save Comparison</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Comparison Name"
              value={comparisonName}
              onChange={(e) => setComparisonName(e.target.value)}
              placeholder="Enter a name for this comparison"
              autoFocus
              disabled={isSaving}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              This will save the current comparison with {resumeIds.length} resume(s) for vacancy{' '}
              <strong>{vacancyId}</strong>.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleConfirmSave} variant="contained" disabled={isSaving || !comparisonName.trim()}>
            {isSaving ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Comparison Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Share Comparison</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Share this comparison by sending the link below. Anyone with the link will be able to view
              the comparison.
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
              <TextField
                fullWidth
                value={shareableUrl}
                InputProps={{
                  readOnly: true,
                }}
                size="small"
              />
              <IconButton
                onClick={handleCopyToClipboard}
                color={copiedToClipboard ? 'success' : 'primary'}
                sx={{ border: 1, borderColor: 'divider' }}
              >
                {copiedToClipboard ? <CheckIcon /> : <CopyIcon />}
              </IconButton>
            </Box>
            {copiedToClipboard && (
              <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                URL copied to clipboard!
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>{copiedToClipboard ? 'Done' : 'Close'}</Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleNotificationClose} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CompareVacancyPage;

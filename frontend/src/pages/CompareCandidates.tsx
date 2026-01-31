import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Alert,
  Stack,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  IconButton,
} from '@mui/material';
import { ContentCopy as CopyIcon, Check as CheckIcon } from '@mui/icons-material';
import ResumeComparisonMatrix from '@components/ResumeComparisonMatrix';
import ComparisonControls from '@components/ComparisonControls';
import ComparisonNotes from '@components/ComparisonNotes';
import { apiClient } from '@/api/client';
import type { ComparisonCreate } from '@/types/api';

/**
 * CompareCandidates Page Component
 *
 * Provides a comprehensive interface for comparing multiple candidates (resumes) against a specific vacancy:
 * - Select 2-5 candidates for comparison
 * - Filter by match percentage range
 * - Sort by different criteria
 * - Visual comparison matrix with skill highlighting
 * - Ranked results by match percentage
 *
 * Route: /recruiter/vacancies/:vacancyId/compare
 * Query Params: ?candidates=id1,id2,id3 (optional - pre-selects candidates)
 */
const CompareCandidatesPage: React.FC = () => {
  const { vacancyId } = useParams<{ vacancyId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  // State for managing comparison
  const [candidateIds, setCandidateIds] = useState<string[]>([]);

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

  // State for candidate names (for notes display)
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({});

  // State for PDF export
  const [isExporting, setIsExporting] = useState(false);

  /**
   * Initialize candidate IDs from URL query params on mount
   */
  useEffect(() => {
    const candidatesParam = searchParams.get('candidates');
    if (candidatesParam) {
      const ids = candidatesParam.split(',').filter((id) => id.trim().length > 0);
      if (ids.length >= 2 && ids.length <= 5) {
        setCandidateIds(ids);
      }
    }
  }, [searchParams]);

  /**
   * Handle candidate IDs change from ComparisonControls
   */
  const handleCandidateIdsChange = (newCandidateIds: string[]) => {
    setCandidateIds(newCandidateIds);

    // Update URL query params to reflect current selection
    if (newCandidateIds.length > 0) {
      setSearchParams({ candidates: newCandidateIds.join(',') });
    } else {
      searchParams.delete('candidates');
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
    if (candidateIds.length < 2 || candidateIds.length > 5) {
      setNotification({
        open: true,
        message: 'Please select 2-5 candidates before saving.',
        severity: 'error',
      });
      return;
    }
    setComparisonName(`Candidate Comparison for ${vacancyId}`);
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
        resume_ids: candidateIds,
        name: comparisonName || `Candidate Comparison for ${vacancyId}`,
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
    if (candidateIds.length < 2) {
      setNotification({
        open: true,
        message: 'Please select at least 2 candidates before sharing.',
        severity: 'error',
      });
      return;
    }

    // Generate shareable URL based on current state
    const baseUrl = window.location.origin;
    const url = new URL(`${baseUrl}/recruiter/vacancies/${vacancyId}/compare`);
    url.searchParams.set('candidates', candidateIds.join(','));

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

  /**
   * Handle note saved callback from ComparisonNotes
   */
  const handleNoteSaved = (candidateId: string, note: string) => {
    // Notes are automatically persisted to localStorage by ComparisonNotes component
    // This callback can be used for additional functionality if needed
    // For now, we just track that a note was saved
  };

  /**
   * Handle export to PDF - triggers browser print dialog
   */
  const handleExportPDF = () => {
    if (candidateIds.length < 2) {
      setNotification({
        open: true,
        message: 'Please select at least 2 candidates before exporting.',
        severity: 'error',
      });
      return;
    }

    setIsExporting(true);

    // Use browser's native print functionality which includes "Save as PDF" option
    setTimeout(() => {
      window.print();
      setIsExporting(false);
    }, 100);
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
        <Box className="comparison-section">
          <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
            Compare Candidates
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Compare multiple candidates side-by-side to identify the best fit for this position. Select 2-5
            candidates to see a detailed skill matrix and rankings based on their qualifications against the
            vacancy requirements.
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Vacancy ID: {vacancyId} | Generated: {new Date().toLocaleString()}
          </Typography>
        </Box>

        {/* Comparison Controls */}
        <Paper elevation={1} sx={{ p: 3 }} className="no-print">
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Comparison Settings
          </Typography>
          <ComparisonControls
            resumeIds={candidateIds}
            onResumeIdsChange={handleCandidateIdsChange}
            onFiltersChange={handleFiltersChange}
            onSortChange={handleSortChange}
            onSave={handleSave}
            onShare={handleShare}
            onExportPDF={handleExportPDF}
            minResumes={2}
            maxResumes={5}
          />
        </Paper>

        {/* Comparison Matrix */}
        {candidateIds.length >= 2 && candidateIds.length <= 5 && (
          <Box className="comparison-section">
            <ResumeComparisonMatrix resumeIds={candidateIds} vacancyId={vacancyId} showRanking={true} />
          </Box>
        )}

        {/* Notes Section - Only show when candidates are selected */}
        {candidateIds.length >= 2 && candidateIds.length <= 5 && (
          <Paper elevation={1} sx={{ p: 3 }} className="comparison-section">
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Recruiter Notes
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph className="no-print">
              Add notes for each candidate during your comparison. Notes are automatically saved as you type and
              will persist when you return to this comparison.
            </Typography>
            <Stack spacing={2}>
              {candidateIds.map((candidateId) => (
                <div key={candidateId} className="comparison-notes-item">
                  <ComparisonNotes
                    candidateId={candidateId}
                    candidateName={candidateNames[candidateId]}
                    vacancyId={vacancyId}
                    onNoteSaved={handleNoteSaved}
                  />
                </div>
              ))}
            </Stack>
          </Paper>
        )}

        {/* Guidance when no candidates selected */}
        {candidateIds.length < 2 && (
          <Paper
            elevation={0}
            sx={{
              p: 4,
              bgcolor: 'info.50',
              border: '1px solid',
              borderColor: 'info.200',
            }}
            className="no-print"
          >
            <Typography variant="h6" gutterBottom fontWeight={600} color="info.main">
              Getting Started
            </Typography>
            <Typography variant="body2" paragraph>
              Add at least 2 candidate IDs to begin the comparison. You can add up to 5 candidates at once.
            </Typography>
            <Typography variant="body2" paragraph>
              Use the controls above to add candidate IDs one at a time, or visit a URL like:
            </Typography>
            <Typography
              variant="body2"
              component="div"
              sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, fontFamily: 'monospace' }}
            >
              /recruiter/vacancies/{vacancyId}?candidates=candidate-1,candidate-2,candidate-3
            </Typography>
          </Paper>
        )}

        {/* Warning if too many candidates */}
        {candidateIds.length > 5 && (
          <Alert severity="warning" className="no-print">
            <Typography variant="subtitle1" fontWeight={600}>
              Too Many Candidates
            </Typography>
            <Typography variant="body2">
              Please remove some candidates. Maximum 5 candidates can be compared at once.
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
              This will save the current comparison with {candidateIds.length} candidate(s) for vacancy{' '}
              <strong>{vacancyId}</strong>.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)} disabled={isSaving}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmSave}
            variant="contained"
            disabled={isSaving || !comparisonName.trim()}
          >
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
              Share this comparison by sending the link below. Anyone with the link will be able to view the
              comparison.
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

export default CompareCandidatesPage;

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Box, Container, Typography, Paper, Alert, Stack } from '@mui/material';
import { ResumeComparisonMatrix } from '@components/ResumeComparisonMatrix';
import { ComparisonControls } from '@components/ComparisonControls';

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
   * Handle save comparison (for future enhancement)
   */
  const handleSave = () => {
    // TODO: Implement save comparison to backend
    // This will be implemented in subtask-5-2
  };

  /**
   * Handle share comparison (for future enhancement)
   */
  const handleShare = () => {
    // TODO: Implement share comparison
    // This will be implemented in subtask-5-2
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
    </Container>
  );
};

export default CompareVacancyPage;

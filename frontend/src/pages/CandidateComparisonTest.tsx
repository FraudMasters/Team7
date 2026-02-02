import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
  TextField,
  Button,
} from '@mui/material';
import CandidateComparisonTable from '@components/CandidateComparisonTable';

const CandidateComparisonTest: React.FC = () => {
  const [vacancyId, setVacancyId] = useState('test-vacancy-id');
  const [resumeIds, setResumeIds] = useState('resume-1,resume-2,resume-3');

  const resumeIdArray = resumeIds.split(',').map(id => id.trim()).filter(id => id);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Candidate Comparison Table - Component Test
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Testing the CandidateComparisonTable component with top 3 candidates
          </Typography>
        </Box>

        {/* Configuration */}
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Configuration
          </Typography>
          <Stack spacing={2}>
            <TextField
              label="Vacancy ID"
              value={vacancyId}
              onChange={(e) => setVacancyId(e.target.value)}
              fullWidth
              helperText="ID of the job vacancy to compare against"
            />
            <TextField
              label="Resume IDs (comma-separated)"
              value={resumeIds}
              onChange={(e) => setResumeIds(e.target.value)}
              fullWidth
              helperText="List of resume IDs to compare (1-10 candidates)"
              placeholder="resume-1,resume-2,resume-3"
            />
            <Typography variant="caption" color="text.secondary">
              Active Resume IDs: {resumeIdArray.length > 0 ? resumeIdArray.join(', ') : 'None'}
            </Typography>
          </Stack>
        </Paper>

        {/* Test Case 1: Real API Call */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Real API Integration
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Fetching comparison for {resumeIdArray.length} candidate(s)
          </Typography>
          <Box sx={{ mt: 2 }}>
            {resumeIdArray.length > 0 ? (
              <CandidateComparisonTable
                vacancyId={vacancyId}
                resumeIds={resumeIdArray}
              />
            ) : (
              <Typography variant="body2" color="warning.main">
                Please enter at least one resume ID above
              </Typography>
            )}
          </Box>
        </Paper>

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" component="div">
            ✓ Table displays 3 candidates side-by-side<br />
            ✓ Shows overall score and component scores<br />
            ✓ Highlighting for best scores in each column<br />
            ✓ Responsive layout on smaller screens<br />
            ✓ No console errors
          </Typography>
        </Paper>

        {/* Component Features */}
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Component Features:
          </Typography>
          <Box component="ul" sx={{ pl: 2, mt: 1 }}>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Side-by-side comparison:</strong> Shows top 3 candidates in a clear table format
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Score breakdown:</strong> Displays overall score plus component scores (Keyword 50%, TF-IDF 30%, Vector 20%)
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Best score highlighting:</strong> Trophy icon and visual emphasis for best scores in each category
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Responsive design:</strong> Desktop table view and mobile card view for optimal readability
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Visual score bars:</strong> Linear progress bars showing percentage for each algorithm component
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 1 }}>
              <strong>Skills summary:</strong> Shows count of matched and missing skills for each candidate
            </Typography>
          </Box>
        </Paper>
      </Stack>
    </Container>
  );
};

export default CandidateComparisonTest;

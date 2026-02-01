import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
} from '@mui/material';
import MatchScoreBreakdown from '@components/MatchScoreBreakdown';

const MatchScoreBreakdownTest: React.FC = () => {
  // Test data - typical scenario
  const testCase1 = {
    keywordScore: 0.8,
    tfidfScore: 0.7,
    vectorScore: 0.6,
  };

  // Test data - excellent candidate
  const testCase2 = {
    keywordScore: 0.95,
    tfidfScore: 0.9,
    vectorScore: 0.85,
  };

  // Test data - poor candidate
  const testCase3 = {
    keywordScore: 0.3,
    tfidfScore: 0.2,
    vectorScore: 0.4,
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Match Score Breakdown - Component Test
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Testing the MatchScoreBreakdown component with various scenarios
          </Typography>
        </Box>

        {/* Test Case 1: Typical Scenario */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Typical Candidate (Good match)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Keyword: 80%, TF-IDF: 70%, Vector: 60%
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchScoreBreakdown
              keywordScore={testCase1.keywordScore}
              tfidfScore={testCase1.tfidfScore}
              vectorScore={testCase1.vectorScore}
            />
          </Box>
        </Paper>

        {/* Test Case 2: Excellent Candidate */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 2: Excellent Candidate
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Keyword: 95%, TF-IDF: 90%, Vector: 85%
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchScoreBreakdown
              keywordScore={testCase2.keywordScore}
              tfidfScore={testCase2.tfidfScore}
              vectorScore={testCase2.vectorScore}
            />
          </Box>
        </Paper>

        {/* Test Case 3: Poor Candidate */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 3: Poor Candidate (Weak match)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Keyword: 30%, TF-IDF: 20%, Vector: 40%
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchScoreBreakdown
              keywordScore={testCase3.keywordScore}
              tfidfScore={testCase3.tfidfScore}
              vectorScore={testCase3.vectorScore}
            />
          </Box>
        </Paper>

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" component="div">
            ✓ Component renders without errors<br />
            ✓ Shows three score bars (Keyword, TF-IDF, Vector)<br />
            ✓ Displays weight percentages (50%, 30%, 20%)<br />
            ✓ No console errors
          </Typography>
        </Paper>
      </Stack>
    </Container>
  );
};

export default MatchScoreBreakdownTest;

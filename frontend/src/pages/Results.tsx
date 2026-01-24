import React from 'react';
import { Typography, Box } from '@mui/material';
import { useParams } from 'react-router-dom';
import AnalysisResults from '@components/AnalysisResults';

/**
 * Results Page Component
 *
 * Displays comprehensive resume analysis results including:
 * - Error detection with severity badges
 * - Grammar and spelling checking
 * - Keyword and skill extraction
 * - Experience summary
 * - Skill highlighting (green for matched, red for missing)
 */
const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          Analysis Results
        </Typography>
        <Typography variant="body1" color="error.main">
          Error: No resume ID provided
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        Analysis Results
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Resume ID: <strong>{id}</strong>
      </Typography>

      <AnalysisResults resumeId={id} />
    </Box>
  );
};

export default ResultsPage;

import React from 'react';
import { Typography, Box, Paper } from '@mui/material';
import { useParams } from 'react-router-dom';

/**
 * Results Page Component
 *
 * Placeholder for analysis results display.
 * This will be implemented in subtask-6-4.
 */
const ResultsPage: React.FC = () {
  const { id } = useParams<{ id: string }>();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        Analysis Results
      </Typography>
      <Paper elevation={1} sx={{ p: 4, mt: 3 }}>
        <Typography variant="body1" paragraph>
          Analysis results for resume ID: <strong>{id || 'N/A'}</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This will display error analysis with severity badges, skill highlighting, and recommendations.
        </Typography>
      </Paper>
    </Box>
  );
};

export default ResultsPage;

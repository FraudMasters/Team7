import React from 'react';
import { Typography, Box, Paper } from '@mui/material';
import { useParams } from 'react-router-dom';

/**
 * Compare Page Component
 *
 * Placeholder for job comparison functionality.
 * This will be implemented in subtask-6-5.
 */
const ComparePage: React.FC = () => {
  const { resumeId, vacancyId } = useParams<{ resumeId: string; vacancyId: string }>();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        Job Comparison
      </Typography>
      <Paper elevation={1} sx={{ p: 4, mt: 3 }}>
        <Typography variant="body1" paragraph>
          Comparing resume <strong>{resumeId || 'N/A'}</strong> with vacancy{' '}
          <strong>{vacancyId || 'N/A'}</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This will show side-by-side comparison with matched/missing skills and experience verification.
        </Typography>
      </Paper>
    </Box>
  );
};

export default ComparePage;

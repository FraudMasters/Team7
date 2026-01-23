import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

/**
 * Upload Page Component
 *
 * Placeholder for resume upload functionality.
 * This will be implemented in subtask-6-3.
 */
const UploadPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        Upload Resume
      </Typography>
      <Paper elevation={1} sx={{ p: 4, mt: 3 }}>
        <Typography variant="body1" paragraph>
          Resume upload component will be implemented here.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This will include drag-and-drop support, file validation, and progress indicators.
        </Typography>
      </Paper>
    </Box>
  );
};

export default UploadPage;

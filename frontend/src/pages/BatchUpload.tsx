import React from 'react';
import {
  Typography,
  Box,
  Paper,
  Container,
} from '@mui/material';

/**
 * Batch Upload Page Component
 *
 * Page for uploading multiple resumes in batch.
 * TODO: Implement batch upload functionality
 */
const BatchUploadPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Batch Upload
          </Typography>
          <Typography variant="body1">
            Batch upload functionality coming soon.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default BatchUploadPage;

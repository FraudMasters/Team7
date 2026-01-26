import React from 'react';
import {
  Typography,
  Box,
  Paper,
  Container,
} from '@mui/material';

/**
 * Feedback Templates Page Component
 *
 * Page for managing feedback templates.
 * TODO: Implement feedback templates functionality
 */
const FeedbackTemplatesPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Feedback Templates
          </Typography>
          <Typography variant="body1">
            Feedback templates management coming soon.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default FeedbackTemplatesPage;

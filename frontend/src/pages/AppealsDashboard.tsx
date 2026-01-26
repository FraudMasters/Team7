import React from 'react';
import {
  Typography,
  Box,
  Paper,
  Container,
} from '@mui/material';

/**
 * Appeals Dashboard Page Component
 *
 * Dashboard for managing and viewing score appeals.
 * TODO: Implement appeals dashboard functionality
 */
const AppealsDashboardPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Appeals Dashboard
          </Typography>
          <Typography variant="body1">
            Appeals dashboard functionality coming soon.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default AppealsDashboardPage;

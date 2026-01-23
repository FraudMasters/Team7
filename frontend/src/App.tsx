import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';

/**
 * Main App Component
 *
 * This is the root component of the application.
 * It will eventually contain routing and layout components.
 */
function App() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Resume Analysis Platform
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI-powered resume analysis with intelligent job matching
          </Typography>
        </Paper>
      </Box>

      <Box sx={{ mt: 4 }}>
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Welcome
          </Typography>
          <Typography variant="body2">
            This platform helps you analyze resumes, detect errors, and match candidates with job vacancies using advanced AI/ML techniques.
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            More features coming soon...
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
}

export default App;

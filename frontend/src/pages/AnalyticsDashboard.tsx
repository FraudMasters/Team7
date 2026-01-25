import React from 'react';
import { Container, Paper, Typography, Box, Alert, AlertTitle } from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';

/**
 * AnalyticsDashboardPage Component
 *
 * Main analytics dashboard for viewing hiring metrics, funnel visualization,
 * skill demand analytics, recruiter performance, and source tracking.
 */
const AnalyticsDashboardPage: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Hiring Analytics Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor key hiring metrics, track candidate progression, analyze skill demand,
          compare recruiter performance, and identify sourcing trends
        </Typography>
      </Box>

      <Paper elevation={1} sx={{ p: 3 }}>
        <Alert severity="info" icon={<InfoIcon />}>
          <AlertTitle>Dashboard Components Coming Soon</AlertTitle>
          The analytics dashboard is being built. Components will include:
          <ul style={{ marginTop: '0.5em', marginBottom: 0, paddingLeft: '1.5em' }}>
            <li>Key Metrics (time-to-hire, resumes processed, match rates)</li>
            <li>Funnel Visualization (candidate progression through pipeline)</li>
            <li>Skill Demand Analytics (trending skills analysis)</li>
            <li>Source Tracking (job board, referral, etc.)</li>
            <li>Recruiter Performance (comparative metrics)</li>
          </ul>
        </Alert>
      </Paper>
    </Container>
  );
};

export default AnalyticsDashboardPage;

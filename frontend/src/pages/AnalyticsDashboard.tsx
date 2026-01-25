import React from 'react';
import { Container, Paper, Typography, Box, Alert, AlertTitle, Stack } from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';
import KeyMetrics from '../components/analytics/KeyMetrics';
import FunnelVisualization from '../components/analytics/FunnelVisualization';

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

      <Stack spacing={3}>
        {/* Key Metrics Section */}
        <KeyMetrics />

        {/* Funnel Visualization Section */}
        <FunnelVisualization />

        {/* Other Components Coming Soon */}
        <Paper elevation={1} sx={{ p: 3 }}>
          <Alert severity="info" icon={<InfoIcon />}>
            <AlertTitle>More Dashboard Components Coming Soon</AlertTitle>
            Additional analytics components will include:
            <ul style={{ marginTop: '0.5em', marginBottom: 0, paddingLeft: '1.5em' }}>
              <li>Skill Demand Analytics (trending skills analysis)</li>
              <li>Source Tracking (job board, referral, etc.)</li>
              <li>Recruiter Performance (comparative metrics)</li>
            </ul>
          </Alert>
        </Paper>
      </Stack>
    </Container>
  );
};

export default AnalyticsDashboardPage;

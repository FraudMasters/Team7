import React, { useState } from 'react';
import { Container, Paper, Typography, Box, Alert, AlertTitle, Stack } from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';
import KeyMetrics from '../components/analytics/KeyMetrics';
import FunnelVisualization from '../components/analytics/FunnelVisualization';
import SkillDemandChart from '../components/analytics/SkillDemandChart';
import SourceTracking from '../components/analytics/SourceTracking';
import RecruiterPerformance from '../components/analytics/RecruiterPerformance';
import DateRangeFilter, { DateRangeFilter as DateRangeFilterType } from '../components/analytics/DateRangeFilter';

/**
 * AnalyticsDashboardPage Component
 *
 * Main analytics dashboard for viewing hiring metrics, funnel visualization,
 * skill demand analytics, recruiter performance, and source tracking.
 */
const AnalyticsDashboardPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    startDate: '',
    endDate: '',
    preset: 'last_30_days',
  });

  /**
   * Handle date range change
   */
  const handleDateRangeChange = (newDateRange: DateRangeFilterType) => {
    setDateRange(newDateRange);
  };

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
        {/* Date Range Filter Section */}
        <DateRangeFilter onDateRangeChange={handleDateRangeChange} />

        {/* Key Metrics Section */}
        <KeyMetrics startDate={dateRange.startDate} endDate={dateRange.endDate} />

        {/* Funnel Visualization Section */}
        <FunnelVisualization startDate={dateRange.startDate} endDate={dateRange.endDate} />

        {/* Skill Demand Analytics Section */}
        <SkillDemandChart startDate={dateRange.startDate} endDate={dateRange.endDate} />

        {/* Source Tracking Section */}
        <SourceTracking startDate={dateRange.startDate} endDate={dateRange.endDate} />

        {/* Recruiter Performance Section */}
        <RecruiterPerformance startDate={dateRange.startDate} endDate={dateRange.endDate} />

        {/* Other Components Coming Soon */}
        <Paper elevation={1} sx={{ p: 3 }}>
          <Alert severity="info" icon={<InfoIcon />}>
            <AlertTitle>More Dashboard Components Coming Soon</AlertTitle>
            Additional analytics components will include:
            <ul style={{ marginTop: '0.5em', marginBottom: 0, paddingLeft: '1.5em' }}>
              <li>Custom Report Builder (drag-and-drop metrics)</li>
              <li>PDF and CSV Export functionality</li>
              <li>Scheduled email report delivery</li>
            </ul>
          </Alert>
        </Paper>
      </Stack>
    </Container>
  );
};

export default AnalyticsDashboardPage;

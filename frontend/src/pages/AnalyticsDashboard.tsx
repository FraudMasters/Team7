import React, { useState, useEffect } from 'react';
import { Container, Paper, Typography, Box, Tabs, Tab, Stack } from '@mui/material';
import { useSearchParams } from 'react-router-dom';
import KeyMetrics from '../components/analytics/KeyMetrics';
import FunnelVisualization from '../components/analytics/FunnelVisualization';
import SkillDemandChart from '../components/analytics/SkillDemandChart';
import SourceTracking from '../components/analytics/SourceTracking';
import RecruiterPerformance from '../components/analytics/RecruiterPerformance';
import DateRangeFilter, { DateRangeFilter as DateRangeFilterType } from '../components/analytics/DateRangeFilter';
import ReportBuilder from '../components/analytics/ReportBuilder';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `analytics-tab-${index}`,
    'aria-controls': `analytics-tabpanel-${index}`,
  };
}

/**
 * AnalyticsDashboardPage Component
 *
 * Main analytics dashboard for viewing hiring metrics, funnel visualization,
 * skill demand analytics, recruiter performance, source tracking, and custom reports.
 */
const AnalyticsDashboardPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    startDate: '',
    endDate: '',
    preset: 'last_30_days',
  });

  // Get tab from URL query parameter
  const tabParam = searchParams.get('tab');
  const tabValue = tabParam === 'reports' ? 1 : 0;

  /**
   * Handle tab change
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    const tab = newValue === 1 ? 'reports' : 'dashboard';
    setSearchParams({ tab });
  };

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
          compare recruiter performance, and build custom reports
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper elevation={1} sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="Analytics tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Dashboard" {...a11yProps(0)} />
          <Tab label="Reports" {...a11yProps(1)} />
        </Tabs>
      </Paper>

      {/* Dashboard Tab */}
      <TabPanel value={tabValue} index={0}>
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
        </Stack>
      </TabPanel>

      {/* Reports Tab */}
      <TabPanel value={tabValue} index={1}>
        <ReportBuilder />
      </TabPanel>
    </Container>
  );
};

export default AnalyticsDashboardPage;

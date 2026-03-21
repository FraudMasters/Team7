import React, { useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Stack,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  AlertTitle,
  ToggleButton,
  ToggleButtonGroup,
  Divider,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  Visibility as VisibilityIcon,
  Shield as ShieldIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import ConfidenceScoreCard from '@components/confidence/ConfidenceScoreCard';
import ModelAccuracyTrend from '@components/confidence/ModelAccuracyTrend';
import FeatureImportanceChart from '@components/confidence/FeatureImportanceChart';
import UncertaintyIndicator from '@components/confidence/UncertaintyIndicator';
import AIHumanComparison from '@components/confidence/AIHumanComparison';
import ConfidenceReportExport from '@components/confidence/ConfidenceReportExport';

/**
 * Date range preset type
 */
type DateRangePreset = '7d' | '30d' | '90d' | 'custom';

/**
 * Format date for display
 */
const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

/**
 * Get date N days ago
 */
const getDateDaysAgo = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return formatDate(date);
};

/**
 * TransparencyDashboard Component
 *
 * Admin dashboard for AI transparency and confidence scoring.
 * Provides visibility into:
 * - AI confidence scores for candidate rankings
 * - Model transparency metrics
 * - Decision explainability
 * - Trust and accountability insights
 *
 * @example
 * ```tsx
 * <TransparencyDashboard />
 * ```
 */
const TransparencyDashboard: React.FC = () => {
  // Filter states
  const [dateRange, setDateRange] = useState<DateRangePreset>('30d');
  const [customStartDate, setCustomStartDate] = useState<string>(getDateDaysAgo(30));
  const [customEndDate, setCustomEndDate] = useState<string>(formatDate(new Date()));
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // Loading and error states
  const [globalLoading, setGlobalLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  /**
   * Calculate date range values based on selected preset
   */
  const getDateRangeValues = useCallback((): { startDate: string; endDate: string } => {
    if (dateRange === 'custom') {
      return { startDate: customStartDate, endDate: customEndDate };
    }
    const daysMap: Record<string, number> = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
    };
    return {
      startDate: getDateDaysAgo(daysMap[dateRange]),
      endDate: formatDate(new Date()),
    };
  }, [dateRange, customStartDate, customEndDate]);

  const { startDate, endDate } = getDateRangeValues();

  /**
   * Handle date range preset change
   */
  const handleDateRangeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newRange: DateRangePreset | null
  ) => {
    if (newRange !== null) {
      setDateRange(newRange);
    }
  };

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle manual refresh
   */
  const handleRefresh = () => {
    setGlobalLoading(true);
    setGlobalError(null);

    // Simulate data refresh
    setTimeout(() => {
      setGlobalLoading(false);
    }, 500);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
          <Shield sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
              AI Transparency Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Monitor AI confidence scores, model transparency, and decision explainability
            </Typography>
          </Box>
          <Chip
            size="small"
            label={autoRefreshEnabled ? 'Auto-refresh: ON' : 'Auto-refresh: OFF'}
            color={autoRefreshEnabled ? 'success' : 'default'}
            variant={autoRefreshEnabled ? 'filled' : 'outlined'}
            onClick={toggleAutoRefresh}
            sx={{ cursor: 'pointer' }}
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={globalLoading}
          >
            Refresh
          </Button>
        </Stack>

        <Divider sx={{ my: 3 }} />

        {/* Date Range Filter */}
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <Typography variant="body2" fontWeight={500} color="text.secondary">
            Date Range:
          </Typography>
          <ToggleButtonGroup
            value={dateRange}
            exclusive
            onChange={handleDateRangeChange}
            size="small"
            aria-label="date range"
          >
            <ToggleButton value="7d" aria-label="last 7 days">
              Last 7 Days
            </ToggleButton>
            <ToggleButton value="30d" aria-label="last 30 days">
              Last 30 Days
            </ToggleButton>
            <ToggleButton value="90d" aria-label="last 90 days">
              Last 90 Days
            </ToggleButton>
            <ToggleButton value="custom" aria-label="custom range">
              Custom
            </ToggleButton>
          </ToggleButtonGroup>
          <Typography variant="caption" color="text.secondary">
            {startDate} to {endDate}
          </Typography>
        </Stack>
      </Box>

      {/* Error Alert */}
      {globalError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setGlobalError(null)}>
          <AlertTitle>Error</AlertTitle>
          {globalError}
        </Alert>
      )}

      {/* Loading State */}
      {globalLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Main Content */}
      {!globalLoading && (
        <Grid container spacing={3}>
          {/* Export and Actions Bar */}
          <Grid item xs={12}>
            <Stack direction="row" justifyContent="flex-end" spacing={2}>
              <ConfidenceReportExport
                startDate={startDate}
                endDate={endDate}
                compact={false}
                onExportComplete={() => {
                  // Export completed successfully
                }}
              />
            </Stack>
          </Grid>

          {/* Sample Confidence Score Cards - Top Candidates */}
          <Grid item xs={12}>
            <Typography variant="h6" component="h2" fontWeight={600} gutterBottom>
              Sample Confidence Scores
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <ConfidenceScoreCard
                  score={{
                    candidateId: 'sample-1',
                    candidateName: 'Jane Doe',
                    confidence: 89,
                    rankScore: 0.92,
                    rankPosition: 1,
                    model: 'ML Ranking v3.2',
                  }}
                  size="medium"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <ConfidenceScoreCard
                  score={{
                    candidateId: 'sample-2',
                    candidateName: 'John Smith',
                    confidence: 72,
                    rankScore: 0.78,
                    rankPosition: 2,
                    model: 'ML Ranking v3.2',
                  }}
                  size="medium"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <ConfidenceScoreCard
                  score={{
                    candidateId: 'sample-3',
                    candidateName: 'Alice Johnson',
                    confidence: 45,
                    rankScore: 0.52,
                    rankPosition: 3,
                    model: 'ML Ranking v3.2',
                  }}
                  size="medium"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <ConfidenceScoreCard
                    score={{
                      candidateId: 'sample-4',
                      candidateName: 'Bob Williams',
                      confidence: 28,
                      rankScore: 0.35,
                      rankPosition: 4,
                      model: 'ML Ranking v3.2',
                    }}
                    size="medium"
                  />
                  {/* Uncertainty Indicator for low confidence */}
                  <Box sx={{ mt: 1 }}>
                    <UncertaintyIndicator
                      confidence={28}
                      mode="alert"
                      candidateName="Bob Williams"
                      showDetails={true}
                    />
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Grid>

          {/* Model Accuracy Trend - Full width */}
          <Grid item xs={12}>
            <ModelAccuracyTrend />
          </Grid>

          {/* Feature Importance Chart and AI vs Human Comparison */}
          <Grid item xs={12} md={6}>
            <FeatureImportanceChart
              features={[
                {
                  feature_name: 'Years of Experience',
                  importance: 0.85,
                  direction: 'positive',
                  description: 'Total years of relevant work experience',
                  category: 'Experience',
                },
                {
                  feature_name: 'Technical Skills Match',
                  importance: 0.78,
                  direction: 'positive',
                  description: 'Alignment with required technical skills',
                  category: 'Skills',
                },
                {
                  feature_name: 'Education Level',
                  importance: 0.65,
                  direction: 'positive',
                  description: 'Highest degree obtained',
                  category: 'Education',
                },
                {
                  feature_name: 'Industry Experience',
                  importance: 0.52,
                  direction: 'positive',
                  description: 'Experience in relevant industry',
                  category: 'Experience',
                },
                {
                  feature_name: 'Location Proximity',
                  importance: 0.38,
                  direction: 'neutral',
                  description: 'Distance from office location',
                  category: 'Logistics',
                },
              ]}
              title="Top Ranking Factors"
              description="Key features influencing AI candidate rankings"
              maxFeatures={5}
              showTooltips={true}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <AIHumanComparison
              startDate={startDate}
              endDate={endDate}
              autoRefresh={autoRefreshEnabled}
            />
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default TransparencyDashboard;

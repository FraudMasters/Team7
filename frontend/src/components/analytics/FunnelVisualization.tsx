import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  LinearProgress,
  Chip,
  Divider,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

/**
 * Funnel stage interface from backend
 */
interface FunnelStage {
  stage_name: string;
  count: number;
  conversion_rate: number;
}

/**
 * Funnel metrics response from backend
 */
interface FunnelMetricsResponse {
  stages: FunnelStage[];
  total_resumes: number;
  overall_hire_rate: number;
}

/**
 * FunnelVisualization Component Props
 */
interface FunnelVisualizationProps {
  /** API endpoint URL for funnel metrics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
}

/**
 * Format stage name for display
 */
const formatStageName = (stageName: string): string => {
  const nameMap: Record<string, string> = {
    resumes_uploaded: 'Resumes Uploaded',
    resumes_processed: 'Resumes Processed',
    candidates_matched: 'Candidates Matched',
    candidates_shortlisted: 'Candidates Shortlisted',
    candidates_interviewed: 'Candidates Interviewed',
    candidates_hired: 'Candidates Hired',
  };
  return nameMap[stageName] || stageName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Get icon for stage
 */
const getStageIcon = (stageName: string) => {
  const iconMap: Record<string, string> = {
    resumes_uploaded: 'upload',
    resumes_processed: 'description',
    candidates_matched: 'person',
    candidates_shortlisted: 'work',
    candidates_interviewed: 'school',
    candidates_hired: 'celebration',
  };
  return iconMap[stageName] || 'check-circle';
};

/**
 * Get color for conversion rate
 */
const getConversionColor = (rate: number): string => {
  if (rate >= 0.7) return '$success';
  if (rate >= 0.5) return '$warning';
  return '$error';
};

/**
 * FunnelVisualization Component
 *
 * Displays recruitment funnel visualization showing:
 * - Candidate progression through each pipeline stage
 * - Conversion rates between stages
 * - Overall hire rate
 * - Visual representation of drop-offs
 *
 * @example
 * ```tsx
 * <FunnelVisualization />
 * ```
 *
 * @example
 * ```tsx
 * <FunnelVisualization startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const FunnelVisualization: React.FC<FunnelVisualizationProps> = ({
  apiUrl = '/api/analytics/funnel',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [funnelData, setFunnelData] = useState<FunnelMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Fetch funnel metrics from backend
   */
  const fetchFunnelData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }

      const response = await axios.get<FunnelMetricsResponse>(apiUrl, { params });
      setFunnelData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load funnel data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchFunnelData();
  }, [apiUrl, startDate, endDate]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchFunnelData();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, apiUrl, startDate, endDate]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        css={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '64px 0',
        }}
      >
        <CircularProgress size={60} css={{ marginBottom: '24px' }} />
        <Typography variant="h6" color="secondary">
          Loading funnel data...
        </Typography>
        <Typography variant="body2" color="secondary" css={{ marginTop: '8px' }}>
          This may take a few moments
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchFunnelData} startIcon={<Icon name="refresh" />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Funnel Data</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!funnelData) {
    return null;
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} css={{ padding: '24px' }}>
        <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Recruitment Funnel
            </Typography>
            <Typography variant="body2" color="secondary" css={{ marginTop: '4px' }}>
              Track candidate progression through the hiring pipeline
            </Typography>
          </Box>
          <Box css={{ display: 'flex', gap: '8px' }}>
            <Button
              variant={autoRefreshEnabled ? 'contained' : 'outlined'}
              startIcon={<Icon name={autoRefreshEnabled ? 'pause' : 'play-arrow'} />}
              onClick={toggleAutoRefresh}
              size="small"
              color={autoRefreshEnabled ? 'primary' : 'default'}
            >
              {autoRefreshEnabled ? 'Auto-refresh' : 'Paused'}
            </Button>
            <Button variant="outlined" startIcon={<Icon name="refresh" />} onClick={fetchFunnelData} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Overall Metrics */}
        <Box
          css={{
            display: 'flex',
            gap: '24px',
            marginBottom: '32px',
            flexWrap: 'wrap',
          }}
        >
          <Box css={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="secondary">
              Total Resumes Uploaded
            </Typography>
            <Typography variant="h4" fontWeight={700} color="$primary">
              {funnelData.total_resumes.toLocaleString()}
            </Typography>
          </Box>
          <Box css={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="secondary">
              Overall Hire Rate
            </Typography>
            <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={funnelData.overall_hire_rate >= 0.05 ? '$success' : '$warning'}
              >
                {(funnelData.overall_hire_rate * 100).toFixed(2)}%
              </Typography>
              {funnelData.overall_hire_rate >= 0.05 ? (
                <Icon name="check-circle" size={20} color="$success" />
              ) : (
                <Icon name="trending-down" size={20} color="$warning" />
              )}
            </Box>
          </Box>
        </Box>

        <Divider css={{ marginBottom: '24px' }} />

        {/* Funnel Stages */}
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Pipeline Stages
          </Typography>

          {funnelData.stages.map((stage, index) => {
            const stageWidth = stage.count / funnelData.total_resumes;
            const previousStage = index > 0 ? funnelData.stages[index - 1] : null;
            const isLastStage = index === funnelData.stages.length - 1;

            return (
              <Card
                key={stage.stage_name}
                variant="outlined"
                css={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                  },
                }}
              >
                <CardContent css={{ padding: '16px' }}>
                  <Box
                    css={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '12px',
                    }}
                  >
                    {/* Stage Name and Icon */}
                    <Box css={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                      <Box
                        css={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '36px',
                          height: '36px',
                          borderRadius: '4px',
                          backgroundColor: isLastStage ? '$successLight' : '$primaryLight',
                          color: isLastStage ? '$successDark' : '$primaryDark',
                        }}
                      >
                        <Icon name={getStageIcon(stage.stage_name)} size={20} />
                      </Box>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {formatStageName(stage.stage_name)}
                        </Typography>
                        <Typography variant="caption" color="secondary">
                          Stage {index + 1} of {funnelData.stages.length}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Count and Conversion Rate */}
                    <Box css={{ textAlign: 'right', minWidth: '150px' }}>
                      <Typography variant="h5" fontWeight={700} color="$primary">
                        {stage.count.toLocaleString()}
                      </Typography>
                      <Box css={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                        {index === 0 ? (
                          <Chip
                            label="Starting Point"
                            size="small"
                            color="info"
                            variant="outlined"
                            css={{ height: '20px', fontSize: '0.7rem' }}
                          />
                        ) : (
                          <>
                            <Typography variant="caption" color="secondary">
                              {(stage.conversion_rate * 100).toFixed(1)}% conversion
                            </Typography>
                            <Chip
                              label={previousStage ? `-${((1 - stage.conversion_rate) * 100).toFixed(1)}%` : ''}
                              size="small"
                              color={stage.conversion_rate >= 0.5 ? 'success' : 'warning'}
                              variant="outlined"
                              css={{ height: '20px', fontSize: '0.7rem' }}
                            />
                          </>
                        )}
                      </Box>
                    </Box>
                  </Box>

                  {/* Visual Funnel Bar */}
                  <Box>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <Typography variant="caption" color="secondary">
                        Stage Width: {(stageWidth * 100).toFixed(1)}% of total
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={stageWidth * 100}
                      css={{
                        height: '12px',
                        borderRadius: '4px',
                        backgroundColor: '$hover',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: isLastStage ? '$success' : getConversionColor(stage.conversion_rate),
                        },
                      }}
                    />
                  </Box>

                  {/* Drop-off Information (if not first stage) */}
                  {index > 0 && previousStage && (
                    <Box css={{ marginTop: '8px' }}>
                      <Typography variant="caption" color="secondary">
                        {(previousStage.count - stage.count).toLocaleString()} candidates dropped from previous stage
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Insights */}
        {funnelData.stages.length > 0 && (
          <Box css={{ marginTop: '24px' }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Pipeline Insights
            </Typography>
            <Stack spacing={1}>
              {funnelData.stages.map((stage, index) => {
                if (index === 0) return null;

                const previousStage = funnelData.stages[index - 1];
                const dropOffRate = 1 - stage.conversion_rate;

                return (
                  dropOffRate > 0.3 && previousStage && (
                    <Typography key={stage.stage_name} variant="body2" color="secondary">
                      <strong>{formatStageName(stage.stage_name)}:</strong> {(dropOffRate * 100).toFixed(1)}% drop-off
                      from {formatStageName(previousStage.stage_name)}
                    </Typography>
                  )
                );
              })}
              {funnelData.stages.every((stage, index) => index === 0 || 1 - stage.conversion_rate <= 0.3) && (
                <Typography variant="body2" color="$success">
                  <Icon name="check-circle" size={16} css={{ verticalAlign: 'middle', marginRight: '4px' }} />
                  Pipeline shows healthy conversion rates across all stages
                </Typography>
              )}
            </Stack>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default FunnelVisualization;

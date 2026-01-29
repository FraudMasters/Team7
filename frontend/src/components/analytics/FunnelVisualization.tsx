import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckIcon,
  Description as DescriptionIcon,
  Upload as UploadIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  School as InterviewIcon,
  Celebration as HiredIcon,
} from '@mui/icons-material';

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
  const iconMap: Record<string, React.ReactElement> = {
    resumes_uploaded: <UploadIcon />,
    resumes_processed: <DescriptionIcon />,
    candidates_matched: <PersonIcon />,
    candidates_shortlisted: <WorkIcon />,
    candidates_interviewed: <InterviewIcon />,
    candidates_hired: <HiredIcon />,
  };
  return iconMap[stageName] || <CheckIcon />;
};

/**
 * Get color for conversion rate
 */
const getConversionColor = (rate: number): string => {
  if (rate >= 0.7) return 'success.main';
  if (rate >= 0.5) return 'warning.main';
  return 'error.main';
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
  apiUrl = 'http://localhost:8000/api/analytics/funnel',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [funnelData, setFunnelData] = useState<FunnelMetricsResponse | null>(null);

  /**
   * Fetch funnel metrics from backend
   */
  const fetchFunnelData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build URL with query parameters
      const url = new URL(apiUrl);
      if (startDate) {
        url.searchParams.append('start_date', startDate);
      }
      if (endDate) {
        url.searchParams.append('end_date', endDate);
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch funnel data: ${response.statusText}`);
      }

      const result: FunnelMetricsResponse = await response.json();
      setFunnelData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load funnel data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFunnelData();
  }, [apiUrl, startDate, endDate]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading funnel data...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
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
          <Button color="inherit" onClick={fetchFunnelData} startIcon={<RefreshIcon />}>
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
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Recruitment Funnel
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Track candidate progression through the hiring pipeline
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchFunnelData} size="small">
            Refresh
          </Button>
        </Box>

        {/* Overall Metrics */}
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            mb: 4,
            flexWrap: 'wrap',
          }}
        >
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Total Resumes Uploaded
            </Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {funnelData.total_resumes.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Overall Hire Rate
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={funnelData.overall_hire_rate >= 0.05 ? 'success.main' : 'warning.main'}
              >
                {(funnelData.overall_hire_rate * 100).toFixed(2)}%
              </Typography>
              {funnelData.overall_hire_rate >= 0.05 ? (
                <CheckIcon color="success" fontSize="small" />
              ) : (
                <TrendingDownIcon color="warning" fontSize="small" />
              )}
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

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
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: 2,
                  },
                }}
              >
                <CardContent sx={{ py: 2 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 1.5,
                    }}
                  >
                    {/* Stage Name and Icon */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 36,
                          height: 36,
                          borderRadius: 1,
                          bgcolor: isLastStage ? 'success.light' : 'primary.light',
                          color: isLastStage ? 'success.dark' : 'primary.dark',
                        }}
                      >
                        {getStageIcon(stage.stage_name)}
                      </Box>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {formatStageName(stage.stage_name)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Stage {index + 1} of {funnelData.stages.length}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Count and Conversion Rate */}
                    <Box sx={{ textAlign: 'right', minWidth: 150 }}>
                      <Typography variant="h5" fontWeight={700} color="primary.main">
                        {stage.count.toLocaleString()}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                        {index === 0 ? (
                          <Chip
                            label="Starting Point"
                            size="small"
                            color="info"
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        ) : (
                          <>
                            <Typography variant="caption" color="text.secondary">
                              {(stage.conversion_rate * 100).toFixed(1)}% conversion
                            </Typography>
                            <Chip
                              label={previousStage ? `-${((1 - stage.conversion_rate) * 100).toFixed(1)}%` : ''}
                              size="small"
                              color={stage.conversion_rate >= 0.5 ? 'success' : 'warning'}
                              variant="outlined"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          </>
                        )}
                      </Box>
                    </Box>
                  </Box>

                  {/* Visual Funnel Bar */}
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Stage Width: {(stageWidth * 100).toFixed(1)}% of total
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={stageWidth * 100}
                      sx={{
                        height: 12,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: isLastStage ? 'success.main' : getConversionColor(stage.conversion_rate),
                        },
                      }}
                    />
                  </Box>

                  {/* Drop-off Information (if not first stage) */}
                  {index > 0 && previousStage && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
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
          <Box sx={{ mt: 3 }}>
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
                    <Typography key={stage.stage_name} variant="body2" color="text.secondary">
                      <strong>{formatStageName(stage.stage_name)}:</strong> {(dropOffRate * 100).toFixed(1)}% drop-off
                      from {formatStageName(previousStage.stage_name)}
                    </Typography>
                  )
                );
              })}
              {funnelData.stages.every((stage, index) => index === 0 || 1 - stage.conversion_rate <= 0.3) && (
                <Typography variant="body2" color="success.main">
                  <CheckIcon fontSize="inherit" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
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

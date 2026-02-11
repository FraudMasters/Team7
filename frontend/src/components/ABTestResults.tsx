import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as TrendingFlatIcon,
  Science as ScienceIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Speed as SpeedIcon,
  EmojiEvents as TrophyIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import {
  CheckCircleOutline as CheckCircleOutlineIcon,
} from '@mui/icons-material';

/**
 * Statistical test result interface
 */
interface StatisticalTestResult {
  test_type: string;
  statistic: number;
  p_value: number;
  is_significant: boolean;
  significance_level: number;
  confidence_interval: [number, number] | null;
  effect_size: number | null;
  interpretation: string;
}

/**
 * Model metrics interface
 */
interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  auc_score?: number;
  sample_size?: number;
  performance_score?: number;
  successes?: number;
  failures?: number;
  [key: string]: number | undefined;
}

/**
 * Model version interface
 */
interface ModelVersion {
  id: string;
  model_name: string;
  version: string;
  is_active: boolean;
  is_experiment: boolean;
  accuracy_metrics: ModelMetrics | null;
  performance_score: number | null;
  model_metadata: {
    training_date?: string;
    algorithm?: string;
    training_samples?: number;
    [key: string]: unknown;
  } | null;
  created_at: string;
}

/**
 * A/B test results response from API
 */
interface ABTestResultsData {
  model_name: string;
  control_model: ModelVersion | null;
  treatment_model: ModelVersion | null;
  control_metrics: ModelMetrics | null;
  treatment_metrics: ModelMetrics | null;
  statistical_tests: StatisticalTestResult[];
  winner: 'control' | 'treatment' | 'tie' | 'inconclusive';
  confidence: number;
  recommendation: string;
  sample_sizes: {
    control: number;
    treatment: number;
  };
  is_statistically_significant: boolean;
  timestamp: string;
}

/**
 * ABTestResults Component Props
 */
interface ABTestResultsProps {
  /** Model name to fetch A/B test results for */
  modelName: string;
  /** Significance level for statistical tests */
  significanceLevel?: number;
  /** API endpoint URL */
  apiUrl?: string;
  /** Callback when a winner is determined */
  onWinnerDetermined?: (winner: string, confidence: number) => void;
}

/**
 * Get metric display label
 */
const getMetricLabel = (metricName: string): string => {
  const labels: Record<string, string> = {
    accuracy: 'Accuracy',
    precision: 'Precision',
    recall: 'Recall',
    f1_score: 'F1 Score',
    auc_score: 'AUC Score',
    sample_size: 'Sample Size',
    performance_score: 'Performance Score',
  };
  return labels[metricName] || metricName;
};

/**
 * Format metric value for display
 */
const formatMetricValue = (value: number | undefined, metricName: string): string => {
  if (value === undefined || value === null) return 'N/A';
  if (metricName === 'sample_size') {
    return value.toLocaleString();
  }
  if (metricName === 'auc_score') {
    return value.toFixed(4);
  }
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format p-value with appropriate precision
 */
const formatPValue = (pValue: number): string => {
  if (pValue < 0.001) return '< 0.001';
  if (pValue < 0.01) return pValue.toFixed(4);
  return pValue.toFixed(3);
};

/**
 * Get test type display label
 */
const getTestTypeLabel = (testType: string): string => {
  const labels: Record<string, string> = {
    chi_square: 'Chi-Square Test',
    t_test: "Student's T-Test",
    welch_t_test: "Welch's T-Test",
    mann_whitney: 'Mann-Whitney U',
    fisher_exact: "Fisher's Exact Test",
    z_test: 'Z-Test',
  };
  return labels[testType] || testType;
};

/**
 * Get effect size interpretation
 */
const getEffectSizeInterpretation = (effectSize: number | null): { label: string; color: string } => {
  if (effectSize === null) return { label: 'N/A', color: 'text.secondary' };
  const absEffect = Math.abs(effectSize);
  if (absEffect < 0.2) return { label: 'Negligible', color: 'text.secondary' };
  if (absEffect < 0.5) return { label: 'Small', color: 'info.main' };
  if (absEffect < 0.8) return { label: 'Medium', color: 'warning.main' };
  return { label: 'Large', color: 'success.main' };
};

/**
 * ABTestResults Component
 *
 * Displays A/B test results with statistical significance analysis including:
 * - Control vs Treatment model comparison
 * - Statistical test results (Chi-square, T-test, etc.)
 * - P-values, confidence intervals, and effect sizes
 * - Winner determination with confidence level
 * - Actionable recommendations
 *
 * @example
 * ```tsx
 * <ABTestResults
 *   modelName="ranking"
 *   significanceLevel={0.05}
 *   onWinnerDetermined={(winner, confidence) => console.log(winner, confidence)}
 * />
 * ```
 */
const ABTestResults: React.FC<ABTestResultsProps> = ({
  modelName,
  significanceLevel = 0.05,
  apiUrl = 'http://localhost:8000/api/model-versions',
  onWinnerDetermined,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ABTestResultsData | null>(null);

  /**
   * Fetch A/B test results from API
   */
  const fetchABTestResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${apiUrl}/ab-test/${modelName}?significance_level=${significanceLevel}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`No active model found for: ${modelName}`);
        }
        throw new Error(`Failed to fetch A/B test results: ${response.statusText}`);
      }

      const result: ABTestResultsData = await response.json();
      setData(result);

      // Notify parent component if winner is determined
      if (result.winner !== 'inconclusive' && onWinnerDetermined) {
        onWinnerDetermined(result.winner, result.confidence);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load A/B test results';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (modelName) {
      fetchABTestResults();
    } else {
      setError('Model name is required');
      setLoading(false);
    }
  }, [modelName, significanceLevel]);

  /**
   * Get winner display configuration
   */
  const getWinnerConfig = (winner: string) => {
    switch (winner) {
      case 'treatment':
        return {
          label: 'Treatment Model Wins',
          shortLabel: 'Treatment',
          icon: <TrophyIcon />,
          color: 'success' as const,
          bgColor: 'success.50',
          borderColor: 'success.main',
        };
      case 'control':
        return {
          label: 'Control Model Wins',
          shortLabel: 'Control',
          icon: <CheckCircleOutlineIcon />,
          color: 'primary' as const,
          bgColor: 'primary.50',
          borderColor: 'primary.main',
        };
      case 'tie':
        return {
          label: 'Models Tied',
          shortLabel: 'Tie',
          icon: <TrendingFlatIcon />,
          color: 'info' as const,
          bgColor: 'info.50',
          borderColor: 'info.main',
        };
      default:
        return {
          label: 'Inconclusive',
          shortLabel: 'Inconclusive',
          icon: <WarningIcon />,
          color: 'warning' as const,
          bgColor: 'warning.50',
          borderColor: 'warning.main',
        };
    }
  };

  /**
   * Render model card
   */
  const renderModelCard = (
    model: ModelVersion | null,
    metrics: ModelMetrics | null,
    label: 'Control' | 'Treatment',
    isWinner: boolean
  ) => {
    const cardColor = label === 'Control' ? 'primary' : 'secondary';

    return (
      <Card
        variant="outlined"
        sx={{
          borderColor: isWinner ? 'success.main' : `${cardColor}.main`,
          borderWidth: isWinner ? 3 : 2,
          bgcolor: isWinner ? 'success.50' : label === 'Control' ? 'primary.50' : 'secondary.50',
          height: '100%',
          position: 'relative',
        }}
      >
        {isWinner && (
          <Box
            sx={{
              position: 'absolute',
              top: -1,
              right: -1,
              bgcolor: 'success.main',
              color: 'white',
              px: 1,
              py: 0.25,
              borderRadius: '0 4px 0 4px',
              fontSize: '0.7rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
            }}
          >
            <TrophyIcon sx={{ fontSize: 14 }} />
            Winner
          </Box>
        )}
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography
              variant="subtitle1"
              fontWeight={600}
              color={isWinner ? 'success.main' : `${cardColor}.main`}
            >
              {label} Model
            </Typography>
            {model?.is_active && (
              <Chip label="Active" size="small" color="success" variant="outlined" />
            )}
            {model?.is_experiment && (
              <Chip
                label="Experiment"
                size="small"
                color="info"
                variant="outlined"
                icon={<ScienceIcon />}
              />
            )}
          </Box>

          {model ? (
            <>
              <Typography variant="h5" fontWeight={700} gutterBottom>
                {model.version}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {model.model_name}
              </Typography>

              {/* Key Metrics */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {metrics && (
                  <>
                    {metrics.accuracy !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Accuracy:
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {formatMetricValue(metrics.accuracy, 'accuracy')}
                        </Typography>
                      </Box>
                    )}
                    {metrics.f1_score !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          F1 Score:
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {formatMetricValue(metrics.f1_score, 'f1_score')}
                        </Typography>
                      </Box>
                    )}
                    {metrics.sample_size !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Sample Size:
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {formatMetricValue(metrics.sample_size, 'sample_size')}
                        </Typography>
                      </Box>
                    )}
                  </>
                )}
              </Box>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
              No model available
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  };

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
          Analyzing A/B Test Results...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Performing statistical significance tests
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
          <Button color="inherit" onClick={fetchABTestResults} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Failed to Load A/B Test Results
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No A/B Test Data Available
        </Typography>
        <Typography variant="body2">
          No A/B test results found for the selected model.
        </Typography>
      </Alert>
    );
  }

  const winnerConfig = getWinnerConfig(data.winner);
  const isControlWinner = data.winner === 'control';
  const isTreatmentWinner = data.winner === 'treatment';

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AnalyticsIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                A/B Test Results
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Model: <strong>{data.model_name}</strong>
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchABTestResults}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        {/* Model Cards Side by Side */}
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            {renderModelCard(data.control_model, data.control_metrics, 'Control', isControlWinner)}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderModelCard(data.treatment_model, data.treatment_metrics, 'Treatment', isTreatmentWinner)}
          </Grid>
        </Grid>
      </Paper>

      {/* Winner & Significance Banner */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          bgcolor: winnerConfig.bgColor,
          border: `2px solid ${winnerConfig.borderColor}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ color: `${winnerConfig.color}.main` }}>
            {winnerConfig.icon}
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" fontWeight={600} color={`${winnerConfig.color}.dark`}>
              {winnerConfig.label}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <Chip
                size="small"
                label={data.is_statistically_significant ? 'Statistically Significant' : 'Not Significant'}
                color={data.is_statistically_significant ? 'success' : 'default'}
                icon={data.is_statistically_significant ? <CheckIcon /> : <CancelIcon />}
              />
              <Typography variant="body2" color="text.secondary">
                Confidence: {(data.confidence * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption" color="text.secondary">
              Significance Level
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              α = {significanceLevel}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Recommendation Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <InfoIcon sx={{ fontSize: 20, color: 'info.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Recommendation
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
          {data.recommendation}
        </Typography>
      </Paper>

      {/* Statistical Tests Table */}
      {data.statistical_tests.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ScienceIcon sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Statistical Test Results
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Detailed results from statistical significance tests comparing control and treatment models
          </Typography>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Test</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                    Statistic
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                    P-Value
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                    Significant
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                    Effect Size
                  </TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                    95% CI
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.statistical_tests.map((test, index) => {
                  const effectInterp = getEffectSizeInterpretation(test.effect_size);
                  return (
                    <TableRow
                      key={index}
                      sx={{
                        '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                        bgcolor: test.is_significant ? 'success.50' : undefined,
                      }}
                    >
                      <TableCell sx={{ fontWeight: 600 }}>
                        {getTestTypeLabel(test.test_type)}
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" fontWeight={600}>
                          {test.statistic.toFixed(4)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={`P-value: ${test.p_value}`}>
                          <Chip
                            label={formatPValue(test.p_value)}
                            size="small"
                            color={test.p_value < test.significance_level ? 'success' : 'default'}
                            variant={test.p_value < test.significance_level ? 'filled' : 'outlined'}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        {test.is_significant ? (
                          <CheckIcon sx={{ color: 'success.main' }} />
                        ) : (
                          <CancelIcon sx={{ color: 'text.secondary' }} />
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {test.effect_size !== null ? (
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {test.effect_size.toFixed(3)}
                            </Typography>
                            <Typography variant="caption" sx={{ color: effectInterp.color }}>
                              ({effectInterp.label})
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {test.confidence_interval ? (
                          <Typography variant="body2">
                            [{test.confidence_interval[0].toFixed(3)}, {test.confidence_interval[1].toFixed(3)}]
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Confidence Level Progress */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <SpeedIcon sx={{ fontSize: 20, color: 'info.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Confidence Level
          </Typography>
        </Box>
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Overall confidence in the result
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {(data.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={data.confidence * 100}
            sx={{
              height: 10,
              borderRadius: 5,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 5,
                bgcolor: data.confidence >= 0.8 ? 'success.main' : data.confidence >= 0.5 ? 'warning.main' : 'error.main',
              },
            }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Confidence ≥80% indicates a strong result that can be used for deployment decisions
        </Typography>
      </Paper>

      {/* Sample Sizes */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AnalyticsIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Sample Sizes
          </Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Control Model
              </Typography>
              <Typography variant="h5" fontWeight={700} color="primary.main">
                {data.sample_sizes.control.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                samples
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Treatment Model
              </Typography>
              <Typography variant="h5" fontWeight={700} color="secondary.main">
                {data.sample_sizes.treatment.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                samples
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Test Interpretations */}
      {data.statistical_tests.some((t) => t.interpretation) && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <InfoIcon sx={{ fontSize: 20, color: 'info.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Test Interpretations
            </Typography>
          </Box>
          <Stack spacing={2}>
            {data.statistical_tests.map((test, index) => (
              <Box key={index}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {getTestTypeLabel(test.test_type)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  {test.interpretation}
                </Typography>
                {index < data.statistical_tests.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Timestamp */}
      <Typography variant="caption" color="text.secondary" align="center" display="block">
        Analysis performed: {new Date(data.timestamp).toLocaleString()}
      </Typography>
    </Stack>
  );
};

export default ABTestResults;

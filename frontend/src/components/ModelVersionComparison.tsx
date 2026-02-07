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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as TrendingFlatIcon,
  Compare as CompareIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckIcon,
  Science as ExperimentIcon,
} from '@mui/icons-material';

/**
 * Model version metrics interface
 */
interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  loss?: number;
  auc_roc?: number;
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
 * Metric comparison result
 */
interface MetricComparison {
  name: string;
  label: string;
  version_a_value: number | null;
  version_b_value: number | null;
  difference: number | null;
  percent_change: number | null;
  is_better: 'a' | 'b' | 'tie' | null;
}

/**
 * A/B test result interface
 */
interface ABTestResult {
  control_version: ModelVersion;
  treatment_version: ModelVersion;
  metric_comparisons: MetricComparison[];
  statistical_significance: {
    z_score: number;
    p_value: number;
    is_significant: boolean;
    confidence_level: number;
  } | null;
  recommendation: 'deploy' | 'keep_current' | 'inconclusive' | 'rollback';
  sample_size: {
    control: number;
    treatment: number;
  };
}

/**
 * Comparison response from backend
 */
interface ModelComparisonData {
  model_name: string;
  version_a: ModelVersion;
  version_b: ModelVersion;
  ab_test_results: ABTestResult | null;
  processing_time?: number;
}

/**
 * ModelVersionComparison Component Props
 */
interface ModelVersionComparisonProps {
  /** Version A ID to compare */
  versionAId: string;
  /** Version B ID to compare */
  versionBId: string;
  /** Model name for the comparison */
  modelName: string;
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
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
    loss: 'Loss',
    auc_roc: 'AUC-ROC',
    performance_score: 'Performance Score',
  };
  return labels[metricName] || metricName;
};

/**
 * Get metric format (percentage or decimal)
 */
const formatMetricValue = (value: number, metricName: string): string => {
  if (metricName === 'loss' || metricName === 'auc_roc') {
    return value.toFixed(4);
  }
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * ModelVersionComparison Component
 *
 * Displays side-by-side comparison of two model versions (A/B testing) with:
 * - Model metadata (version, training date, algorithm)
 * - Performance metrics comparison (accuracy, precision, recall, F1)
 * - Visual highlighting of metric differences
 * - Statistical significance testing results
 * - Deployment recommendation based on comparison
 *
 * @example
 * ```tsx
 * <ModelVersionComparison
 *   versionAId="version-1"
 *   versionBId="version-2"
 *   modelName="skill_matching"
 * />
 * ```
 */
const ModelVersionComparison: React.FC<ModelVersionComparisonProps> = ({
  versionAId,
  versionBId,
  modelName,
  apiUrl = 'http://localhost:8000/api/model-versions',
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ModelComparisonData | null>(null);

  /**
   * Fetch comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          version_a_id: versionAId,
          version_b_id: versionBId,
          model_name: modelName,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result: ModelComparisonData = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fallback: Create comparison data from individual version fetches
   * This allows the component to work even without a compare endpoint
   */
  const fetchVersionsAndCompare = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch both versions
      const [responseA, responseB] = await Promise.all([
        fetch(`${apiUrl}/${versionAId}`),
        fetch(`${apiUrl}/${versionBId}`),
      ]);

      if (!responseA.ok || !responseB.ok) {
        throw new Error('Failed to fetch model versions');
      }

      const versionA: ModelVersion = await responseA.json();
      const versionB: ModelVersion = await responseB.json();

      // Create metric comparisons
      const metricComparisons: MetricComparison[] = [];
      const allMetrics = new Set([
        ...Object.keys(versionA.accuracy_metrics || {}),
        ...Object.keys(versionB.accuracy_metrics || {}),
      ]);

      allMetrics.forEach((metric) => {
        const valueA = versionA.accuracy_metrics?.[metric] ?? null;
        const valueB = versionB.accuracy_metrics?.[metric] ?? null;

        if (valueA !== null && valueB !== null) {
          const difference = valueB - valueA;
          const isLossMetric = metric === 'loss';
          const is_better = isLossMetric
            ? difference < 0
              ? 'b'
              : difference > 0
                ? 'a'
                : 'tie'
            : difference > 0
              ? 'b'
              : difference < 0
                ? 'a'
                : 'tie';

          metricComparisons.push({
            name: metric,
            label: getMetricLabel(metric),
            version_a_value: valueA,
            version_b_value: valueB,
            difference,
            percent_change: valueA !== 0 ? (difference / valueA) * 100 : null,
            is_better,
          });
        }
      });

      // Determine recommendation
      const improvements = metricComparisons.filter((m) => m.is_better === 'b').length;
      const regressions = metricComparisons.filter((m) => m.is_better === 'a').length;
      let recommendation: 'deploy' | 'keep_current' | 'inconclusive' | 'rollback' = 'inconclusive';
      if (improvements > regressions) {
        recommendation = 'deploy';
      } else if (regressions > improvements) {
        recommendation = 'rollback';
      } else {
        recommendation = 'keep_current';
      }

      setData({
        model_name: modelName,
        version_a: versionA,
        version_b: versionB,
        ab_test_results: {
          control_version: versionA,
          treatment_version: versionB,
          metric_comparisons: metricComparisons,
          statistical_significance: null,
          recommendation,
          sample_size: {
            control: versionA.model_metadata?.training_samples as number || 0,
            treatment: versionB.model_metadata?.training_samples as number || 0,
          },
        },
        processing_time: undefined,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (versionAId && versionBId && modelName) {
      if (versionAId === versionBId) {
        setError('Version A and Version B must be different');
        setLoading(false);
      } else {
        // Try the compare endpoint first, fall back to individual fetches
        fetchComparison().catch(() => {
          // If compare endpoint fails, try individual version fetches
          fetchVersionsAndCompare();
        });
      }
    } else {
      setError('Version A, Version B, and Model Name are required');
      setLoading(false);
    }
  }, [versionAId, versionBId, modelName]);

  /**
   * Get performance change icon and color
   */
  const getPerformanceChangeConfig = (comparison: MetricComparison) => {
    if (comparison.is_better === 'b') {
      return {
        icon: <TrendingUpIcon />,
        label: comparison.percent_change !== null ? `+${comparison.percent_change.toFixed(1)}%` : 'Improved',
        color: 'success' as const,
        bgColor: 'success.50',
        borderColor: 'success.main',
      };
    }
    if (comparison.is_better === 'a') {
      return {
        icon: <TrendingDownIcon />,
        label: comparison.percent_change !== null ? `${comparison.percent_change.toFixed(1)}%` : 'Declined',
        color: 'error' as const,
        bgColor: 'error.50',
        borderColor: 'error.main',
      };
    }
    return {
      icon: <TrendingFlatIcon />,
      label: 'No Change',
      color: 'default' as const,
      bgColor: 'grey.50',
      borderColor: 'grey.300',
    };
  };

  /**
   * Get recommendation color and label
   */
  const getRecommendationConfig = (rec: string) => {
    switch (rec) {
      case 'deploy':
        return {
          label: 'Deploy New Version',
          color: 'success' as const,
          icon: <CheckIcon />,
        };
      case 'rollback':
        return {
          label: 'Keep Current Version',
          color: 'error' as const,
          icon: <TrendingDownIcon />,
        };
      case 'keep_current':
        return {
          label: 'No Significant Difference',
          color: 'info' as const,
          icon: <TrendingFlatIcon />,
        };
      default:
        return {
          label: 'Inconclusive - More Data Needed',
          color: 'warning' as const,
          icon: <SpeedIcon />,
        };
    }
  };

  /**
   * Render model metadata
   */
  const renderModelMetadata = (version: ModelVersion, label: string) => {
    return (
      <Card
        variant="outlined"
        sx={{
          borderColor: label === 'A' ? 'primary.main' : 'secondary.main',
          borderWidth: 2,
          bgcolor: label === 'A' ? 'primary.50' : 'secondary.50',
          height: '100%',
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle1" fontWeight={600} color={label === 'A' ? 'primary.main' : 'secondary.main'}>
              Version {label}
            </Typography>
            {version.is_active && (
              <Chip label="Active" size="small" color="success" variant="outlined" />
            )}
            {version.is_experiment && (
              <Chip
                label="Experiment"
                size="small"
                color="info"
                variant="outlined"
                icon={<ExperimentIcon />}
              />
            )}
          </Box>
          <Typography variant="h5" fontWeight={700} gutterBottom>
            {version.version}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {version.model_name}
          </Typography>
          {version.model_metadata?.training_date && (
            <Typography variant="caption" color="text.secondary">
              Trained: {new Date(version.model_metadata.training_date).toLocaleDateString()}
            </Typography>
          )}
          {version.model_metadata?.algorithm && (
            <Chip
              label={version.model_metadata.algorithm}
              size="small"
              sx={{ mt: 1 }}
            />
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
          Comparing model versions...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing performance metrics and statistical significance
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
          <Button color="inherit" onClick={fetchComparison} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Comparison Failed
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data || !data.version_a || !data.version_b) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No comparison data found for the selected versions.
        </Typography>
      </Alert>
    );
  }

  const abResults = data.ab_test_results;
  const recommendation = abResults?.recommendation ? getRecommendationConfig(abResults.recommendation) : null;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CompareIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Model Version Comparison
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Model: <strong>{data.model_name}</strong>
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            Refresh
          </Button>
        </Box>

        {/* Model Cards Side by Side */}
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            {renderModelMetadata(data.version_a, 'A')}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderModelMetadata(data.version_b, 'B')}
          </Grid>
        </Grid>
      </Paper>

      {/* Recommendation Banner */}
      {recommendation && (
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: `${recommendation.color}.50`,
            border: `2px solid ${recommendation.color}.main`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ color: `${recommendation.color}.main` }}>
              {recommendation.icon}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={600} color={`${recommendation.color}.dark`}>
                {recommendation.label}
              </Typography>
              {abResults?.statistical_significance && (
                <Typography variant="body2" color="text.secondary">
                  {abResults.statistical_significance.is_significant
                    ? `Statistically significant (p=${abResults.statistical_significance.p_value})`
                    : 'Not statistically significant - more data needed'}
                </Typography>
              )}
            </Box>
          </Box>
        </Paper>
      )}

      {/* Metrics Comparison Table */}
      {abResults && abResults.metric_comparisons.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Performance Metrics Comparison
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Showing how performance metrics differ between Version A and Version B
          </Typography>

          <TableContainer sx={{ maxHeight: 600, overflow: 'auto' }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'grey.100',
                      minWidth: 150,
                      position: 'sticky',
                      left: 0,
                      zIndex: 3,
                    }}
                  >
                    Metric
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'primary.50',
                      minWidth: 120,
                    }}
                  >
                    Version A
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'secondary.50',
                      minWidth: 120,
                    }}
                  >
                    Version B
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'grey.100',
                      minWidth: 120,
                    }}
                  >
                    Difference
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'grey.100',
                      minWidth: 120,
                    }}
                  >
                    Change
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {abResults.metric_comparisons.map((comparison) => {
                  const changeConfig = getPerformanceChangeConfig(comparison);
                  return (
                    <TableRow
                      key={comparison.name}
                      sx={{ '&:nth-of-type(odd)': { bgcolor: 'action.hover' } }}
                    >
                      <TableCell
                        sx={{
                          fontWeight: 600,
                          position: 'sticky',
                          left: 0,
                          bgcolor: 'background.paper',
                          zIndex: 2,
                        }}
                      >
                        {comparison.label}
                      </TableCell>
                      <TableCell align="center">
                        {comparison.version_a_value !== null ? (
                          <Chip
                            label={formatMetricValue(comparison.version_a_value, comparison.name)}
                            size="small"
                            color="primary"
                            variant="outlined"
                            sx={{ fontWeight: 600 }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {comparison.version_b_value !== null ? (
                          <Chip
                            label={formatMetricValue(comparison.version_b_value, comparison.name)}
                            size="small"
                            color="secondary"
                            variant="outlined"
                            sx={{ fontWeight: 600 }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {comparison.difference !== null && (
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={comparison.is_better === 'b' ? 'success.main' : comparison.is_better === 'a' ? 'error.main' : 'text.primary'}
                          >
                            {comparison.difference > 0 ? '+' : ''}
                            {formatMetricValue(comparison.difference, comparison.name)}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 0.5,
                            bgcolor: changeConfig.bgColor,
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            border: `1px solid ${changeConfig.borderColor}`,
                          }}
                        >
                          <Box sx={{ color: `${changeConfig.color}.main` }}>
                            {changeConfig.icon}
                          </Box>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={`${changeConfig.color}.main`}
                          >
                            {changeConfig.label}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Sample Size Info */}
      {abResults && (abResults.sample_size.control > 0 || abResults.sample_size.treatment > 0) && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <SpeedIcon sx={{ fontSize: 20, color: 'info.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Sample Information
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.50', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Version A Samples
                </Typography>
                <Typography variant="h5" fontWeight={700} color="primary.main">
                  {abResults.sample_size.control.toLocaleString()}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.50', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Version B Samples
                </Typography>
                <Typography variant="h5" fontWeight={700} color="secondary.main">
                  {abResults.sample_size.treatment.toLocaleString()}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Processing Time */}
      {data.processing_time && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Comparison completed in {data.processing_time.toFixed(2)} seconds
        </Typography>
      )}
    </Stack>
  );
};

export default ModelVersionComparison;

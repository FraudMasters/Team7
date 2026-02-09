import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Button,
  LinearProgress,
  Stack,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  AlertTitle,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Lightbulb as InsightsIcon,
  Balance as FairnessIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  BugReport as BiasIcon,
} from '@mui/icons-material';
import { fairness } from '@/api/fairness';
import type { FairnessScorecard } from '@/types/api';

/**
 * FairnessScorecard Component Props
 */
interface FairnessScorecardProps {
  /** Optional vacancy ID for specific scorecard */
  vacancyId?: string;
  /** Optional model version for filtering */
  modelVersion?: string;
  /** API endpoint URL override */
  apiUrl?: string;
}

/**
 * Get score color based on value
 */
function getScoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'error';
}

/**
 * Get score label based on value
 */
function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 80) return 'Good';
  if (score >= 70) return 'Fair';
  if (score >= 60) return 'Needs Improvement';
  return 'Critical';
}

/**
 * Get severity icon
 */
function getSeverityIcon(severity: string) {
  switch (severity.toLowerCase()) {
    case 'critical':
      return <ErrorIcon fontSize="small" />;
    case 'high':
      return <ErrorIcon fontSize="small" />;
    case 'medium':
      return <WarningIcon fontSize="small" />;
    case 'low':
      return <InfoIcon fontSize="small" />;
    default:
      return <InfoIcon fontSize="small" />;
  }
}

/**
 * FairnessScorecard Component
 *
 * Displays comprehensive fairness scorecard including:
 * - Overall fairness score (0-100) with circular progress indicator
 * - Score breakdown showing disparate impact, statistical parity, and alert penalty
 * - Metrics by demographic group with selection rates
 * - Feature bias sources with severity indicators
 * - Actionable insights and recommendations
 *
 * @example
 * ```tsx
 * <FairnessScorecard />
 * ```
 *
 * @example
 * ```tsx
 * <FairnessScorecard vacancyId="vacancy-123" />
 * ```
 */
const FairnessScorecard: React.FC<FairnessScorecardProps> = ({
  vacancyId,
  modelVersion,
  apiUrl = `${config.api.url}/api/fairness`,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scorecard, setScorecard] = useState<FairnessScorecard | null>(null);

  /**
   * Fetch scorecard data from backend
   */
  const fetchScorecard = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await fairness.getScorecard({
        vacancy_id: vacancyId,
        model_version: modelVersion,
      });

      setScorecard(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load fairness scorecard';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScorecard();
  }, [vacancyId, modelVersion]);

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
          Loading fairness scorecard...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing demographic metrics and bias indicators
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
          <Button color="inherit" onClick={fetchScorecard} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Scorecard</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!scorecard) {
    return null;
  }

  const scoreColor = getScoreColor(scorecard.fairness_score);
  const scoreColorMain = `${scoreColor}.main` as const;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Fairness Scorecard
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {scorecard.vacancy_title && (
              <Chip label={scorecard.vacancy_title} size="small" variant="outlined" />
            )}
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchScorecard} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Overall Score Card */}
          <Grid item xs={12} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: scoreColorMain,
                background: `linear-gradient(135deg, ${scoreColor === 'success' ? 'rgba(76, 175, 80, 0.05)' : scoreColor === 'warning' ? 'rgba(255, 152, 0, 0.05)' : 'rgba(244, 67, 54, 0.05)'}, transparent 100%)`,
              }}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex', mb: 2 }}>
                  <CircularProgress
                    variant="determinate"
                    value={scorecard.fairness_score}
                    size={120}
                    thickness={8}
                    sx={{
                      color: scoreColorMain,
                      '& .MuiCircularProgress-circle': {
                        strokeLinecap: 'round',
                      },
                    }}
                  />
                  <Box
                    sx={{
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      position: 'absolute',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                    }}
                  >
                    <Typography variant="h3" fontWeight={700} color={scoreColorMain}>
                      {scorecard.fairness_score.toFixed(0)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      out of 100
                    </Typography>
                  </Box>
                </Box>

                <Typography variant="h6" fontWeight={600} gutterBottom color={scoreColorMain}>
                  {getScoreLabel(scorecard.fairness_score)}
                </Typography>

                <Stack spacing={1} sx={{ mt: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Sample Size
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {scorecard.total_sample_size.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Demographics
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {scorecard.demographics_analyzed.length}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Model Version
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {scorecard.model_version}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Score Breakdown Card */}
          <Grid item xs={12} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Score Breakdown
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Stack spacing={2}>
                  {/* Disparate Impact Score */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Disparate Impact
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {scorecard.score_breakdown.disparate_impact_score.toFixed(1)}/50
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(scorecard.score_breakdown.disparate_impact_score / 50) * 100}
                      sx={{ height: 8, borderRadius: 1 }}
                      color="success"
                    />
                  </Box>

                  {/* Statistical Parity Score */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Statistical Parity
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {scorecard.score_breakdown.statistical_parity_score.toFixed(1)}/30
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(scorecard.score_breakdown.statistical_parity_score / 30) * 100}
                      sx={{ height: 8, borderRadius: 1 }}
                      color="info"
                    />
                  </Box>

                  {/* Alert Penalty */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Alert Penalty
                      </Typography>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={scorecard.score_breakdown.alert_penalty > 0 ? 'error.main' : 'success.main'}
                      >
                        -{scorecard.score_breakdown.alert_penalty.toFixed(1)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={0}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: scorecard.score_breakdown.alert_penalty > 0 ? 'error.main' : 'success.main',
                      }}
                    />
                  </Box>

                  {/* Final Score */}
                  <Box sx={{ mt: 1, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" fontWeight={600}>
                        Final Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="h5" fontWeight={700} color={scoreColorMain}>
                          {scorecard.score_breakdown.final_score.toFixed(1)}
                        </Typography>
                        {scorecard.score_breakdown.final_score >= 70 ? (
                          <TrendingUpIcon fontSize="small" color="success" />
                        ) : (
                          <TrendingDownIcon fontSize="small" color="error" />
                        )}
                      </Box>
                    </Box>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Alerts Summary Card */}
          <Grid item xs={12} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: scorecard.alerts_summary.total > 0 ? 'warning.main' : 'success.main',
              }}
            >
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Alerts Summary
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Stack spacing={1.5}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ErrorIcon fontSize="small" sx={{ color: 'error.main' }} />
                      <Typography variant="body2">Critical</Typography>
                    </Box>
                    <Chip
                      label={scorecard.alerts_summary.critical}
                      size="small"
                      color={scorecard.alerts_summary.critical > 0 ? 'error' : 'default'}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ErrorIcon fontSize="small" sx={{ color: 'orange' }} />
                      <Typography variant="body2">High</Typography>
                    </Box>
                    <Chip
                      label={scorecard.alerts_summary.high}
                      size="small"
                      color={scorecard.alerts_summary.high > 0 ? 'error' : 'default'}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WarningIcon fontSize="small" sx={{ color: 'warning.main' }} />
                      <Typography variant="body2">Medium</Typography>
                    </Box>
                    <Chip
                      label={scorecard.alerts_summary.medium}
                      size="small"
                      color={scorecard.alerts_summary.medium > 0 ? 'warning' : 'default'}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <InfoIcon fontSize="small" sx={{ color: 'info.main' }} />
                      <Typography variant="body2">Low</Typography>
                    </Box>
                    <Chip
                      label={scorecard.alerts_summary.low}
                      size="small"
                      color={scorecard.alerts_summary.low > 0 ? 'info' : 'default'}
                    />
                  </Box>

                  <Divider />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="subtitle2" fontWeight={600}>
                      Total Alerts
                    </Typography>
                    <Chip
                      label={scorecard.alerts_summary.total}
                      size="small"
                      color={scorecard.alerts_summary.total > 0 ? 'error' : 'success'}
                      variant={scorecard.alerts_summary.total > 0 ? 'filled' : 'outlined'}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Metrics by Demographic Section */}
      {scorecard.metrics_by_demographic.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <FairnessIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Metrics by Demographic Group
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={2}>
            {scorecard.metrics_by_demographic.map((metric, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderColor: metric.is_acceptable ? 'success.main' : 'warning.main',
                    borderLeft: 4,
                    borderLeftColor: metric.is_acceptable ? 'success.main' : 'warning.main',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600} noWrap>
                        {metric.demographic_group}
                      </Typography>
                      {metric.is_acceptable ? (
                        <CheckIcon fontSize="small" color="success" />
                      ) : (
                        <WarningIcon fontSize="small" color="warning" />
                      )}
                    </Box>

                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      {metric.protected_attribute}
                    </Typography>

                    <Stack spacing={1} sx={{ mt: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          DI Ratio
                        </Typography>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color={metric.disparate_impact_ratio >= 0.8 ? 'success.main' : 'warning.main'}
                        >
                          {metric.disparate_impact_ratio.toFixed(3)}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Selection Rate
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {(metric.group_selection_rate * 100).toFixed(1)}%
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Sample Size
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {metric.sample_size}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Feature Bias Sources Section */}
      {scorecard.bias_sources.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <BiasIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Feature Bias Sources
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <List disablePadding>
            {scorecard.bias_sources.map((source, index) => (
              <React.Fragment key={index}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    px: 2,
                    py: 1.5,
                    bgcolor: index % 2 === 0 ? 'action.hover' : 'transparent',
                    borderRadius: 1,
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40, mt: 0 }}>
                    <Box sx={{ color: `${source.severity === 'critical' || source.severity === 'high' ? 'error' : source.severity === 'medium' ? 'warning' : 'info'}.main` }}>
                      {getSeverityIcon(source.severity)}
                    </Box>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {source.feature_label}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Chip
                            label={source.severity.toUpperCase()}
                            size="small"
                            color={source.severity === 'critical' || source.severity === 'high' ? 'error' : source.severity === 'medium' ? 'warning' : 'info'}
                          />
                          <Chip
                            label={source.bias_indicator.replace(/_/g, ' ')}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                    }
                    secondary={
                      <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          Demographic: <strong>{source.demographic_group}</strong> •
                          Importance: <strong>{source.importance_score.toFixed(3)}</strong> •
                          Correlation: <strong>{source.correlation_strength.toFixed(3)}</strong>
                        </Typography>
                        <Typography variant="body2" color="text.primary">
                          {source.recommendation}
                        </Typography>
                      </Stack>
                    }
                  />
                </ListItem>
                {index < scorecard.bias_sources.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Recommendations Section */}
      {scorecard.recommendations.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <InsightsIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Actionable Insights
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Stack spacing={2}>
            {scorecard.recommendations.map((recommendation, index) => (
              <Alert
                key={index}
                severity={scorecard.fairness_score >= 80 ? 'success' : scorecard.fairness_score >= 60 ? 'warning' : 'error'}
                icon={<InsightsIcon />}
              >
                <AlertTitle sx={{ typography: 'subtitle2', fontWeight: 600 }}>
                  Recommendation {index + 1}
                </AlertTitle>
                <Typography variant="body2">{recommendation}</Typography>
              </Alert>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Footer with timestamp */}
      <Box sx={{ textAlign: 'center', py: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Last analyzed: {new Date(scorecard.analyzed_at).toLocaleString()}
        </Typography>
      </Box>
    </Stack>
  );
};

export default FairnessScorecard;

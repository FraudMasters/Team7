import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Alert as MuiAlert,
  Stack,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  EmojiEvents as ChampionIcon,
  Science as ChallengerIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as TrendingFlatIcon,
  Refresh as RefreshIcon,
  RocketLaunch as PromoteIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  Timeline as MetricsIcon,
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
 * Model version details interface
 */
interface ModelVersionDetails {
  id: string;
  version: string;
  performance_score: number | null;
  accuracy_metrics: ModelMetrics | null;
  created_at: string;
  is_active: boolean;
  model_metadata?: {
    training_date?: string;
    algorithm?: string;
    training_samples?: number;
    [key: string]: unknown;
  } | null;
}

/**
 * Performance comparison interface
 */
interface PerformanceComparison {
  best_challenger_version: string;
  best_challenger_id: string;
  best_challenger_score: number;
  champion_score: number;
  improvement_pct: number;
  metrics_comparison?: {
    metric: string;
    champion_value: number;
    challenger_value: number;
    improvement: number;
  }[];
}

/**
 * Champion/Challenger status response interface
 */
interface ChampionChallengerStatus {
  model_name: string;
  champion: ModelVersionDetails | null;
  challengers: ModelVersionDetails[] | null;
  has_challenger: boolean;
  challenger_count: number;
  comparison: PerformanceComparison | null;
}

/**
 * Promotion response interface
 */
interface PromotionResponse {
  success: boolean;
  model_name: string;
  challenger_version: string | null;
  challenger_id: string | null;
  previous_champion_version: string | null;
  promotion_reason: string | null;
  forced: boolean | null;
  promoted_at: string | null;
  error: string | null;
  statistical_analysis?: {
    is_significant: boolean;
    p_value: number;
    confidence_level: number;
    recommendation: string;
  } | null;
}

/**
 * Component props
 */
interface ChampionChallengerDashboardProps {
  /** Maximum height for the scrollable content */
  maxHeight?: number | string;
  /** Initial model to display */
  initialModel?: string;
  /** Callback when a challenger is promoted */
  onChallengerPromoted?: (modelName: string, version: string) => void;
  /** API base URL */
  apiUrl?: string;
}

/**
 * Format metric value for display
 */
const formatMetricValue = (value: number | null | undefined, metricName?: string): string => {
  if (value === null || value === undefined) return 'N/A';
  if (metricName === 'loss' || metricName === 'auc_roc') {
    return value.toFixed(4);
  }
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format time ago
 */
const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

/**
 * Get improvement color
 */
const getImprovementColor = (improvementPct: number): 'success' | 'error' | 'warning' => {
  if (improvementPct >= 5) return 'success';
  if (improvementPct > 0) return 'warning';
  return 'error';
};

/**
 * ChampionChallengerDashboard Component
 *
 * Displays the champion/challenger model workflow with:
 * - Current champion model details
 * - List of challenger models
 * - Performance comparison between champion and best challenger
 * - Promote button to promote challengers to champion
 * - Statistical significance analysis
 *
 * @example
 * ```tsx
 * <ChampionChallengerDashboard
 *   initialModel="skill_matching"
 *   onChallengerPromoted={(model, version) => console.log('Promoted:', model, version)}
 * />
 * ```
 */
const ChampionChallengerDashboard: React.FC<ChampionChallengerDashboardProps> = ({
  maxHeight = 600,
  initialModel = 'skill_matching',
  onChallengerPromoted,
  apiUrl = 'http://localhost:8888/api/model-versions',
}) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState(initialModel);
  const [status, setStatus] = useState<ChampionChallengerStatus | null>(null);

  // Promotion dialog state
  const [promoteDialogOpen, setPromoteDialogOpen] = useState(false);
  const [selectedChallenger, setSelectedChallenger] = useState<ModelVersionDetails | null>(null);
  const [promoteLoading, setPromoteLoading] = useState(false);
  const [forcePromote, setForcePromote] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  /**
   * Fetch champion/challenger status from API
   */
  const fetchStatus = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const response = await fetch(`${apiUrl}/champion-challenger/status/${selectedModel}`);

      if (!response.ok) {
        if (response.status === 404) {
          // Model not found - show empty state
          setStatus({
            model_name: selectedModel,
            champion: null,
            challengers: [],
            has_challenger: false,
            challenger_count: 0,
            comparison: null,
          });
          return;
        }
        throw new Error(`Failed to fetch status: ${response.statusText}`);
      }

      const data: ChampionChallengerStatus = await response.json();
      setStatus(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load champion/challenger data';
      setError(errorMessage);

      // Provide mock data for visualization when API is unavailable
      setStatus({
        model_name: selectedModel,
        champion: {
          id: 'champion-1',
          version: 'v1.0.0',
          performance_score: 85.5,
          accuracy_metrics: {
            accuracy: 0.855,
            precision: 0.842,
            recall: 0.868,
            f1_score: 0.855,
          },
          created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          is_active: true,
          model_metadata: {
            training_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            algorithm: 'XGBoost',
            training_samples: 50000,
          },
        },
        challengers: [
          {
            id: 'challenger-1',
            version: 'v1.1.0-rc',
            performance_score: 89.2,
            accuracy_metrics: {
              accuracy: 0.892,
              precision: 0.881,
              recall: 0.903,
              f1_score: 0.892,
            },
            created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            is_active: false,
            model_metadata: {
              training_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
              algorithm: 'XGBoost v2',
              training_samples: 60000,
            },
          },
          {
            id: 'challenger-2',
            version: 'v1.2.0-beta',
            performance_score: 87.8,
            accuracy_metrics: {
              accuracy: 0.878,
              precision: 0.865,
              recall: 0.891,
              f1_score: 0.878,
            },
            created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
            is_active: false,
            model_metadata: {
              training_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
              algorithm: 'LightGBM',
              training_samples: 55000,
            },
          },
        ],
        has_challenger: true,
        challenger_count: 2,
        comparison: {
          best_challenger_version: 'v1.1.0-rc',
          best_challenger_id: 'challenger-1',
          best_challenger_score: 89.2,
          champion_score: 85.5,
          improvement_pct: 4.33,
          metrics_comparison: [
            { metric: 'accuracy', champion_value: 0.855, challenger_value: 0.892, improvement: 4.33 },
            { metric: 'precision', champion_value: 0.842, challenger_value: 0.881, improvement: 4.63 },
            { metric: 'recall', champion_value: 0.868, challenger_value: 0.903, improvement: 4.03 },
            { metric: 'f1_score', champion_value: 0.855, challenger_value: 0.892, improvement: 4.33 },
          ],
        },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedModel, apiUrl]);

  /**
   * Handle refresh button click
   */
  const handleRefresh = () => {
    fetchStatus(true);
  };

  /**
   * Open promotion dialog
   */
  const openPromoteDialog = (challenger: ModelVersionDetails) => {
    setSelectedChallenger(challenger);
    setForcePromote(false);
    setPromoteDialogOpen(true);
  };

  /**
   * Close promotion dialog
   */
  const closePromoteDialog = () => {
    setPromoteDialogOpen(false);
    setSelectedChallenger(null);
    setForcePromote(false);
  };

  /**
   * Handle challenger promotion
   */
  const handlePromote = async () => {
    if (!selectedChallenger) return;

    try {
      setPromoteLoading(true);

      const response = await fetch(`${apiUrl}/champion-challenger/promote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_name: selectedModel,
          challenger_version_id: selectedChallenger.id,
          force: forcePromote,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Promotion failed: ${response.statusText}`);
      }

      const result: PromotionResponse = await response.json();

      if (result.success) {
        setSnackbar({
          open: true,
          message: `Successfully promoted ${result.challenger_version} to champion`,
          severity: 'success',
        });
        closePromoteDialog();
        await fetchStatus(true);
        onChallengerPromoted?.(selectedModel, result.challenger_version || '');
      } else {
        throw new Error(result.error || 'Promotion failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to promote challenger';
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setPromoteLoading(false);
    }
  };

  /**
   * Close snackbar
   */
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  /**
   * Render model card
   */
  const renderModelCard = (
    model: ModelVersionDetails,
    type: 'champion' | 'challenger',
    isBest?: boolean
  ) => {
    const isChampion = type === 'champion';

    return (
      <Card
        variant="outlined"
        sx={{
          borderLeft: 4,
          borderLeftColor: isChampion ? 'warning.main' : isBest ? 'success.main' : 'info.main',
          height: '100%',
          position: 'relative',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: 2,
          },
        }}
      >
        {isBest && (
          <Chip
            label="Best Challenger"
            size="small"
            color="success"
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
            }}
          />
        )}
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            {isChampion ? (
              <ChampionIcon sx={{ color: 'warning.main' }} />
            ) : (
              <ChallengerIcon sx={{ color: 'info.main' }} />
            )}
            <Typography variant="subtitle1" fontWeight={600}>
              {isChampion ? 'Champion' : 'Challenger'}
            </Typography>
          </Box>

          <Typography variant="h5" fontWeight={700} gutterBottom>
            {model.version}
          </Typography>

          {model.model_metadata?.algorithm && (
            <Chip label={model.model_metadata.algorithm} size="small" sx={{ mb: 1 }} />
          )}

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Performance Score
            </Typography>
            <Typography variant="h6" fontWeight={600} color={isChampion ? 'warning.main' : 'info.main'}>
              {model.performance_score !== null ? `${model.performance_score.toFixed(1)}%` : 'N/A'}
            </Typography>
          </Box>

          {model.accuracy_metrics && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Accuracy: {formatMetricValue(model.accuracy_metrics.accuracy)} | F1: {formatMetricValue(model.accuracy_metrics.f1_score)}
              </Typography>
            </Box>
          )}

          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {formatTimeAgo(model.created_at)}
            </Typography>
            {!isChampion && (
              <Tooltip title="Promote this challenger to champion">
                <Button
                  size="small"
                  variant="contained"
                  color="primary"
                  startIcon={<PromoteIcon />}
                  onClick={() => openPromoteDialog(model)}
                >
                  Promote
                </Button>
              </Tooltip>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={32} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading champion/challenger status...
        </Typography>
      </Paper>
    );
  }

  return (
    <Box className="champion-challenger-dashboard">
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ChampionIcon sx={{ fontSize: 24, color: 'warning.main' }} />
          <Typography variant="h6" fontWeight={500}>
            Champion/Challenger Dashboard
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Model</InputLabel>
            <Select
              value={selectedModel}
              label="Model"
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              <MenuItem value="skill_matching">Skill Matching</MenuItem>
              <MenuItem value="ranking">Ranking</MenuItem>
              <MenuItem value="resume_parser">Resume Parser</MenuItem>
            </Select>
          </FormControl>
          <Button
            size="small"
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <MuiAlert severity="warning" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error} (Showing sample data)
        </MuiAlert>
      )}

      {/* No Data State */}
      {status && !status.champion && !status.has_challenger && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <InfoIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Champion or Challengers Found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No model versions have been configured for {selectedModel}. Create a model version and set it as champion or challenger to get started.
          </Typography>
        </Paper>
      )}

      {/* Main Content */}
      {status && (status.champion || status.has_challenger) && (
        <Stack spacing={2} sx={{ maxHeight, overflow: 'auto' }}>
          {/* Comparison Summary Banner */}
          {status.comparison && (
            <Paper
              elevation={1}
              sx={{
                p: 2,
                bgcolor: status.comparison.improvement_pct > 0 ? 'success.50' : 'grey.50',
                border: `2px solid ${status.comparison.improvement_pct > 0 ? 'success.main' : 'grey.300'}`,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {status.comparison.improvement_pct > 0 ? (
                  <TrendingUpIcon sx={{ color: 'success.main', fontSize: 28 }} />
                ) : (
                  <TrendingFlatIcon sx={{ color: 'grey.500', fontSize: 28 }} />
                )}
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {status.comparison.improvement_pct > 0
                      ? `Best challenger shows ${status.comparison.improvement_pct.toFixed(1)}% improvement`
                      : 'No improvement detected in challengers'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Champion: {status.comparison.champion_score.toFixed(1)}% | Best Challenger ({status.comparison.best_challenger_version}): {status.comparison.best_challenger_score.toFixed(1)}%
                  </Typography>
                </Box>
                {status.comparison.improvement_pct >= 5 && (
                  <Chip
                    icon={<CheckIcon />}
                    label="Ready for Promotion"
                    color="success"
                    variant="outlined"
                  />
                )}
              </Box>
            </Paper>
          )}

          {/* Champion and Challengers Grid */}
          <Grid container spacing={2}>
            {/* Champion Card */}
            <Grid item xs={12} md={status.has_challenger ? 4 : 12}>
              {status.champion ? (
                renderModelCard(status.champion, 'champion')
              ) : (
                <Card variant="outlined" sx={{ height: '100%', borderLeft: 4, borderLeftColor: 'grey.400' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <WarningIcon sx={{ color: 'grey.500' }} />
                      <Typography variant="subtitle1" fontWeight={600}>
                        No Champion
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      No champion model has been set for this model. Promote a challenger to become the champion.
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Grid>

            {/* Challengers */}
            {status.has_challenger && status.challengers && (
              <Grid item xs={12} md={8}>
                <Grid container spacing={2}>
                  {status.challengers.map((challenger) => {
                    const isBest = status.comparison?.best_challenger_id === challenger.id;
                    return (
                      <Grid item xs={12} sm={status.challengers!.length > 1 ? 6 : 12} key={challenger.id}>
                        {renderModelCard(challenger, 'challenger', isBest)}
                      </Grid>
                    );
                  })}
                </Grid>
              </Grid>
            )}
          </Grid>

          {/* Detailed Metrics Comparison */}
          {status.comparison?.metrics_comparison && status.comparison.metrics_comparison.length > 0 && (
            <Paper elevation={1} sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <MetricsIcon sx={{ fontSize: 20, color: 'info.main' }} />
                <Typography variant="subtitle1" fontWeight={600}>
                  Metrics Comparison
                </Typography>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Metric</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Champion</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Best Challenger</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Improvement</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {status.comparison.metrics_comparison.map((metric) => (
                      <TableRow key={metric.metric}>
                        <TableCell sx={{ textTransform: 'capitalize' }}>{metric.metric.replace('_', ' ')}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={formatMetricValue(metric.champion_value, metric.metric)}
                            size="small"
                            color="warning"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={formatMetricValue(metric.challenger_value, metric.metric)}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                            {metric.improvement > 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
                            ) : metric.improvement < 0 ? (
                              <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
                            ) : (
                              <TrendingFlatIcon sx={{ fontSize: 16, color: 'grey.500' }} />
                            )}
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              color={metric.improvement >= 0 ? 'success.main' : 'error.main'}
                            >
                              {metric.improvement > 0 ? '+' : ''}{metric.improvement.toFixed(2)}%
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Info Banner */}
          {status.has_challenger && (
            <Paper sx={{ p: 2, bgcolor: 'info.50', border: '1px solid info.main' }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <InfoIcon sx={{ color: 'info.main', fontSize: 20 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Champion/Challenger Workflow:</strong> The champion model handles all production traffic.
                    Challengers are experimental models being evaluated for promotion. When a challenger shows
                    statistically significant improvement (≥5%), it can be promoted to become the new champion.
                  </Typography>
                </Box>
              </Box>
            </Paper>
          )}
        </Stack>
      )}

      {/* Promotion Confirmation Dialog */}
      <Dialog
        open={promoteDialogOpen}
        onClose={closePromoteDialog}
        aria-labelledby="promote-dialog-title"
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle id="promote-dialog-title">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PromoteIcon color="primary" />
            Promote Challenger to Champion
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {selectedChallenger && (
              <>
                You are about to promote <strong>{selectedChallenger.version}</strong> to be the new champion
                for <strong>{selectedModel}</strong>.
              </>
            )}
          </DialogContentText>

          {status?.comparison && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Performance Improvement: <strong>{status.comparison.improvement_pct.toFixed(1)}%</strong>
              </Typography>
              {status.comparison.improvement_pct < 5 && (
                <MuiAlert severity="warning" sx={{ mt: 1 }}>
                  Improvement is below the typical 5% threshold for promotion.
                  You may want to gather more data before promoting.
                </MuiAlert>
              )}
            </Box>
          )}

          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <input
              type="checkbox"
              id="force-promote"
              checked={forcePromote}
              onChange={(e) => setForcePromote(e.target.checked)}
            />
            <label htmlFor="force-promote">
              <Typography variant="body2">
                Force promotion (bypass significance threshold)
              </Typography>
            </label>
          </Box>

          {forcePromote && (
            <MuiAlert severity="warning" sx={{ mt: 2 }}>
              Forcing promotion will bypass statistical significance checks.
              This should only be done in exceptional circumstances.
            </MuiAlert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={closePromoteDialog} disabled={promoteLoading}>
            Cancel
          </Button>
          <Button
            onClick={handlePromote}
            variant="contained"
            color="primary"
            disabled={promoteLoading}
            startIcon={promoteLoading ? <CircularProgress size={16} /> : <PromoteIcon />}
          >
            {promoteLoading ? 'Promoting...' : 'Promote to Champion'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      {snackbar.open && (
        <MuiAlert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1300,
          }}
        >
          {snackbar.message}
        </MuiAlert>
      )}
    </Box>
  );
};

export default ChampionChallengerDashboard;

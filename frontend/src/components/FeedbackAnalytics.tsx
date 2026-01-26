import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Button,
  LinearProgress,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  School as LearningIcon,
  Model as ModelIcon,
} from '@mui/icons-material';

/**
 * Feedback entry interface from backend
 */
interface FeedbackEntry {
  id: string;
  resume_id: string;
  vacancy_id: string;
  match_result_id?: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source: string;
  processed: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Feedback list response from backend
 */
interface FeedbackListResponse {
  feedback: FeedbackEntry[];
  total_count: number;
}

/**
 * Model version interface from backend
 */
interface ModelVersion {
  id: string;
  model_name: string;
  version: string;
  is_active: boolean;
  is_experiment: boolean;
  experiment_config?: Record<string, unknown>;
  model_metadata?: Record<string, unknown>;
  accuracy_metrics?: Record<string, number>;
  performance_score?: number;
  created_at: string;
  updated_at: string;
}

/**
 * Model version list response from backend
 */
interface ModelVersionListResponse {
  models: ModelVersion[];
  total_count: number;
}

/**
 * Tab panel props
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * FeedbackAnalytics Component Props
 */
interface FeedbackAnalyticsProps {
  /** API endpoint URL for feedback */
  feedbackApiUrl?: string;
  /** API endpoint URL for model versions */
  modelApiUrl?: string;
}

/**
 * TabPanel component for tab content
 */
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
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * FeedbackAnalytics Component
 *
 * Displays comprehensive feedback analytics dashboard including:
 * - Match accuracy metrics (total feedback, correct/incorrect counts, accuracy percentage)
 * - Learning progress (processed vs unprocessed feedback)
 * - Model version information with A/B testing status
 * - Recent feedback entries with confidence scores
 * - Performance trends and recommendations
 *
 * @example
 * ```tsx
 * <FeedbackAnalytics />
 * ```
 */
const FeedbackAnalytics: React.FC<FeedbackAnalyticsProps> = ({
  feedbackApiUrl = 'http://localhost:8000/api/feedback',
  modelApiUrl = 'http://localhost:8000/api/model-versions',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<FeedbackEntry[]>([]);
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [tabValue, setTabValue] = useState(0);

  /**
   * Fetch feedback data from backend
   */
  const fetchFeedback = async () => {
    try {
      const response = await fetch(`${feedbackApiUrl}/?limit=100`);

      if (!response.ok) {
        throw new Error(`Failed to fetch feedback: ${response.statusText}`);
      }

      const result: FeedbackListResponse = await response.json();
      setFeedback(result.feedback || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('adminAnalytics.errors.failedToLoadFeedback');
      setError(errorMessage);
    }
  };

  /**
   * Fetch model versions from backend
   */
  const fetchModels = async () => {
    try {
      const response = await fetch(`${modelApiUrl}/`);

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const result: ModelVersionListResponse = await response.json();
      setModels(result.models || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('adminAnalytics.errors.failedToLoadModels');
      setError(errorMessage);
    }
  };

  /**
   * Fetch all analytics data
   */
  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    await Promise.all([fetchFeedback(), fetchModels()]);

    setLoading(false);
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  /**
   * Calculate feedback statistics
   */
  const feedbackStats = {
    total: feedback.length,
    correct: feedback.filter((f) => f.was_correct).length,
    incorrect: feedback.filter((f) => !f.was_correct).length,
    processed: feedback.filter((f) => f.processed).length,
    unprocessed: feedback.filter((f) => !f.processed).length,
    accuracy:
      feedback.length > 0
        ? (feedback.filter((f) => f.was_correct).length / feedback.length) * 100
        : 0,
  };

  /**
   * Get active model
   */
  const activeModel = models.find((m) => m.is_active && !m.is_experiment);

  /**
   * Get experiment models
   */
  const experimentModels = models.filter((m) => m.is_experiment);

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
          {t('adminAnalytics.loading')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('adminAnalytics.loadingMessage')}
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
          <Button color="inherit" onClick={fetchAnalytics} startIcon={<RefreshIcon />}>
            {t('common.tryAgain')}
          </Button>
        }
      >
        <AlertTitle>{t('adminAnalytics.errorTitle')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('adminAnalytics.title')}
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchAnalytics} size="small">
            {t('adminAnalytics.refreshButton')}
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {feedbackStats.total}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('adminAnalytics.overview.totalFeedback')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {feedbackStats.correct}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('adminAnalytics.overview.correctMatches')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'error.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="error.main" fontWeight={700}>
                  {feedbackStats.incorrect}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('adminAnalytics.overview.incorrectMatches')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card
              variant="outlined"
              sx={{
                borderColor:
                  feedbackStats.accuracy >= 80
                    ? 'success.main'
                    : feedbackStats.accuracy >= 60
                      ? 'warning.main'
                      : 'error.main',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                  <Typography variant="h4" color={feedbackStats.accuracy >= 80 ? 'success.main' : feedbackStats.accuracy >= 60 ? 'warning.main' : 'error.main'} fontWeight={700}>
                    {feedbackStats.accuracy.toFixed(1)}%
                  </Typography>
                  {feedbackStats.accuracy >= 70 ? (
                    <TrendingUpIcon fontSize="small" color="success" />
                  ) : (
                    <TrendingDownIcon fontSize="small" color="error" />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {t('adminAnalytics.overview.accuracy')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs for different views */}
      <Paper elevation={1} sx={{ px: 3, pt: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="Analytics tabs"
        >
          <Tab label={t('adminAnalytics.tabs.learningProgress')} />
          <Tab label={t('adminAnalytics.tabs.modelVersions')} />
          <Tab label={t('adminAnalytics.tabs.recentFeedback')} />
        </Tabs>

        {/* Learning Progress Tab */}
        <TabPanel value={tabValue} index={0}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              <LearningIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
              {t('adminAnalytics.learningProgress.title')}
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('adminAnalytics.overview.processed')}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {feedbackStats.processed} / {feedbackStats.total}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={feedbackStats.total > 0 ? (feedbackStats.processed / feedbackStats.total) * 100 : 0}
                    sx={{ height: 10, borderRadius: 1 }}
                    color="success"
                  />
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('adminAnalytics.overview.unprocessed')}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {feedbackStats.unprocessed} / {feedbackStats.total}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={feedbackStats.total > 0 ? (feedbackStats.unprocessed / feedbackStats.total) * 100 : 0}
                    sx={{ height: 10, borderRadius: 1 }}
                    color="warning"
                  />
                </Box>

                <Alert
                  severity={
                    feedbackStats.accuracy >= 80
                      ? 'success'
                      : feedbackStats.accuracy >= 60
                        ? 'warning'
                        : 'info'
                  }
                >
                  <AlertTitle>{t('adminAnalytics.learningProgress.statusTitle')}</AlertTitle>
                  {feedbackStats.total === 0
                    ? t('adminAnalytics.learningProgress.statusNoData')
                    : feedbackStats.unprocessed > 0
                      ? t('adminAnalytics.learningProgress.statusPending', { count: feedbackStats.unprocessed })
                      : t('adminAnalytics.learningProgress.statusComplete')}
                </Alert>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  {t('adminAnalytics.learningProgress.accuracyTrends')}
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary={t('adminAnalytics.learningProgress.currentAccuracy')}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Typography variant="h4" fontWeight={700} color={feedbackStats.accuracy >= 80 ? 'success.main' : feedbackStats.accuracy >= 60 ? 'warning.main' : 'error.main'}>
                            {feedbackStats.accuracy.toFixed(1)}%
                          </Typography>
                          {feedbackStats.accuracy >= 80 ? (
                            <Chip label={t('adminAnalytics.learningProgress.excellent')} size="small" color="success" />
                          ) : feedbackStats.accuracy >= 60 ? (
                            <Chip label={t('adminAnalytics.learningProgress.good')} size="small" color="warning" />
                          ) : (
                            <Chip label={t('adminAnalytics.learningProgress.needsImprovement')} size="small" color="error" />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary={t('adminAnalytics.learningProgress.targetAccuracy')}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Typography variant="h5" fontWeight={600}>
                            90.0%
                          </Typography>
                          <Chip label={t('adminAnalytics.learningProgress.goal')} size="small" color="info" variant="outlined" />
                        </Box>
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary={t('adminAnalytics.learningProgress.gapToTarget')}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Typography variant="h5" fontWeight={600} color={Math.max(0, 90 - feedbackStats.accuracy) <= 10 ? 'success.main' : 'warning.main'}>
                            {Math.max(0, 90 - feedbackStats.accuracy).toFixed(1)}%
                          </Typography>
                          {Math.max(0, 90 - feedbackStats.accuracy) <= 10 ? (
                            <TrendingUpIcon fontSize="small" color="success" />
                          ) : (
                            <TrendingDownIcon fontSize="small" color="warning" />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                </List>
              </Grid>
            </Grid>
          </Paper>
        </TabPanel>

        {/* Model Versions Tab */}
        <TabPanel value={tabValue} index={1}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              <ModelIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
              {t('adminAnalytics.models.title')}
            </Typography>
            <Divider sx={{ mb: 3 }} />

            {models.length === 0 ? (
              <Alert severity="info">
                <AlertTitle>{t('adminAnalytics.models.noModelsTitle')}</AlertTitle>
                {t('adminAnalytics.models.noModelsMessage')}
              </Alert>
            ) : (
              <Stack spacing={3}>
                {/* Active Model */}
                {activeModel && (
                  <Box>
                    <Typography variant="subtitle2" color="success.main" gutterBottom fontWeight={600}>
                      <CheckIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                      {t('adminAnalytics.models.activeProductionModel')}
                    </Typography>
                    <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
                      <CardContent>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              {t('adminAnalytics.models.modelName')}
                            </Typography>
                            <Typography variant="body1" fontWeight={600}>
                              {activeModel.model_name}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              {t('adminAnalytics.models.version')}
                            </Typography>
                            <Typography variant="body1" fontWeight={600}>
                              {activeModel.version}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              {t('adminAnalytics.models.performanceScore')}
                            </Typography>
                            <Typography variant="body1" fontWeight={600} color={activeModel.performance_score && activeModel.performance_score >= 80 ? 'success.main' : 'warning.main'}>
                              {activeModel.performance_score?.toFixed(1) || 'N/A'} / 100
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              {t('adminAnalytics.models.lastUpdated')}
                            </Typography>
                            <Typography variant="body1">
                              {new Date(activeModel.updated_at).toLocaleDateString()}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Box>
                )}

                {/* Experiment Models */}
                {experimentModels.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="primary.main" gutterBottom fontWeight={600}>
                      <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                      {t('adminAnalytics.models.abTestingExperiments', { count: experimentModels.length })}
                    </Typography>
                    <Grid container spacing={2}>
                      {experimentModels.map((model) => (
                        <Grid item xs={12} md={6} key={model.id}>
                          <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
                            <CardContent>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="subtitle2" fontWeight={600}>
                                  {model.version}
                                </Typography>
                                <Chip
                                  label={t('adminAnalytics.models.experiment')}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              </Box>
                              <Typography variant="caption" color="text.secondary">
                                {model.model_name}
                              </Typography>
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  {t('adminAnalytics.models.performance', { score: model.performance_score?.toFixed(1) || 'N/A' })}
                                </Typography>
                                <LinearProgress
                                  variant="determinate"
                                  value={model.performance_score || 0}
                                  sx={{ height: 6, borderRadius: 1, mt: 0.5 }}
                                />
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}

                {/* No Active Model */}
                {!activeModel && models.length > 0 && (
                  <Alert severity="warning">
                    <AlertTitle>{t('adminAnalytics.models.noActiveModelTitle')}</AlertTitle>
                    {t('adminAnalytics.models.noActiveModelMessage', { count: models.length })}
                  </Alert>
                )}
              </Stack>
            )}
          </Paper>
        </TabPanel>

        {/* Recent Feedback Tab */}
        <TabPanel value={tabValue} index={2}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              {t('adminAnalytics.feedback.title')}
            </Typography>
            <Divider sx={{ mb: 3 }} />

            {feedback.length === 0 ? (
              <Alert severity="info">
                <AlertTitle>{t('adminAnalytics.feedback.noFeedbackTitle')}</AlertTitle>
                {t('adminAnalytics.feedback.noFeedbackMessage')}
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.skill')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.correct')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.confidence')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.correction')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.source')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.processed')}</TableCell>
                      <TableCell>{t('adminAnalytics.feedback.tableHeaders.date')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {feedback.slice(0, 20).map((entry) => (
                      <TableRow key={entry.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {entry.skill}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {entry.was_correct ? (
                            <Chip label={t('common.yes')} size="small" color="success" icon={<CheckIcon />} />
                          ) : (
                            <Chip label={t('common.no')} size="small" color="error" icon={<ErrorIcon />} />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {entry.confidence_score !== undefined && entry.confidence_score !== null
                              ? `${(entry.confidence_score * 100).toFixed(0)}%`
                              : 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {entry.recruiter_correction || entry.actual_skill || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={entry.feedback_source} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          {entry.processed ? (
                            <Chip label={t('common.yes')} size="small" color="success" variant="outlined" />
                          ) : (
                            <Chip label={t('common.no')} size="small" color="warning" variant="outlined" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(entry.created_at).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {feedback.length > 20 && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  {t('adminAnalytics.feedback.showingEntries', { total: feedback.length })}
                </Typography>
              </Box>
            )}
          </Paper>
        </TabPanel>
      </Paper>
    </Stack>
  );
};

export default FeedbackAnalytics;

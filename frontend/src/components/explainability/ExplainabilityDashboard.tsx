import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack,
  Chip,
  LinearProgress,
  Tooltip,
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Divider,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  TrendingUp as PositiveIcon,
  TrendingDown as NegativeIcon,
  Psychology as AIIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  BarChart as ImportanceIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Lightbulb as BulbIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api/client';

/**
 * Feature explanation from backend API
 */
interface FeatureExplanation {
  feature_name: string;
  contribution: number;
  contribution_percentage: number;
  direction: 'positive' | 'negative';
  description: string;
  value?: number;
}

/**
 * Confidence interval from backend API
 */
interface ConfidenceInterval {
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
  interpretation: string;
}

/**
 * Explainability response from backend API
 */
interface ExplainabilityResponse {
  resume_id: string;
  vacancy_id: string;
  candidate_name: string | null;
  rank_score: number;
  rank_position: number | null;
  narrative: string;
  feature_explanations: FeatureExplanation[];
  confidence_interval: ConfidenceInterval | null;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  highlight_sections: Record<string, string>;
  provider: string;
  model: string;
  generated_at: string;
}

/**
 * ExplainabilityDashboard Component Props
 */
interface ExplainabilityDashboardProps {
  /** Resume ID for explanation */
  resumeId: string;
  /** Vacancy ID for explanation */
  vacancyId: string;
  /** Whether to use LLM for narrative generation */
  useLLM?: boolean;
  /** API endpoint URL (optional, uses default if not provided) */
  apiUrl?: string;
}

/**
 * ExplainabilityDashboard Component
 *
 * Displays comprehensive explainability for AI candidate rankings including:
 * - Natural language narrative explanations
 * - Feature contribution breakdowns with visual bars
 * - Confidence intervals for predictions
 * - Candidate strengths and weaknesses
 * - Hiring recommendations
 * - Resume section highlighting suggestions
 *
 * @example
 * ```tsx
 * <ExplainabilityDashboard
 *   resumeId="abc-123"
 *   vacancyId="vacancy-456"
 *   useLLM={true}
 * />
 * ```
 */
const ExplainabilityDashboard: React.FC<ExplainabilityDashboardProps> = ({
  resumeId,
  vacancyId,
  useLLM = true,
  apiUrl = '/api/explainability/explain',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ExplainabilityResponse | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [strengthsOpen, setStrengthsOpen] = useState(true);
  const [weaknessesOpen, setWeaknessesOpen] = useState(true);

  /**
   * Fetch explainability data from backend
   */
  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ExplainabilityResponse>(apiUrl, {
        resume_id: resumeId,
        vacancy_id: vacancyId,
        use_llm: useLLM,
      });

      setData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('explainability.error.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId && vacancyId) {
      fetchExplanation();
    }
  }, [resumeId, vacancyId, useLLM]);

  /**
   * Get contribution color for display
   */
  const getContributionColor = (contribution: number) => {
    if (contribution > 0) return 'success';
    if (contribution < 0) return 'error';
    return 'default';
  };

  /**
   * Format contribution value for display
   */
  const getContributionValue = (contribution: number) => {
    const absValue = Math.abs(contribution * 100);
    return `${contribution > 0 ? '+' : ''}${absValue.toFixed(1)}%`;
  };

  /**
   * Get recommendation config based on score
   */
  const getRecommendationConfig = () => {
    if (!data) return { color: 'default' as const, label: '', icon: <InfoIcon /> };

    const score = data.rank_score;
    if (score >= 0.8) {
      return {
        color: 'success' as const,
        label: t('explainability.recommendation.excellent'),
        icon: <CheckIcon />,
      };
    } else if (score >= 0.6) {
      return {
        color: 'success' as const,
        label: t('explainability.recommendation.good'),
        icon: <CheckIcon />,
      };
    } else if (score >= 0.4) {
      return {
        color: 'warning' as const,
        label: t('explainability.recommendation.fair'),
        icon: <WarningIcon />,
      };
    } else {
      return {
        color: 'error' as const,
        label: t('explainability.recommendation.poor'),
        icon: <WarningIcon />,
      };
    }
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
          {t('explainability.loading.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('explainability.loading.subtitle')}
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
          <Button color="inherit" onClick={fetchExplanation} startIcon={<RefreshIcon />}>
            {t('explainability.error.retry')}
          </Button>
        }
      >
        <AlertTitle>{t('explainability.error.title')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('explainability.noData.title')}</AlertTitle>
        {t('explainability.noData.message')}
      </Alert>
    );
  }

  const recommendationConfig = getRecommendationConfig();

  /**
   * Feature bar component for displaying individual feature contributions
   */
  const FeatureBar: React.FC<{
    feature: FeatureExplanation;
  }> = ({ feature }) => {
    const absContribution = Math.abs(feature.contribution_percentage);
    const isPositive = feature.direction === 'positive';

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isPositive ? (
              <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
            ) : (
              <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
            )}
            <Typography variant="body2" fontWeight={600}>
              {feature.feature_name}
            </Typography>
          </Box>
          <Chip
            label={`${isPositive ? '+' : ''}${feature.contribution_percentage.toFixed(1)}%`}
            size="small"
            color={getContributionColor(feature.contribution) as 'success' | 'error' | 'default'}
            sx={{ fontWeight: 700, height: 24 }}
          />
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min(absContribution, 100)}
          color={getContributionColor(feature.contribution) === 'default' ? 'primary' : (getContributionColor(feature.contribution) as 'success' | 'error')}
          sx={{
            height: 8,
            borderRadius: 4,
            mb: 0.5,
          }}
        />
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
          {feature.description}
        </Typography>
      </Box>
    );
  };

  /**
   * Detail row component for metrics table
   */
  const DetailRow: React.FC<{
    label: string;
    value: string | number | React.ReactNode;
  }> = ({ label, value }) => (
    <TableRow>
      <TableCell component="th" scope="row" sx={{ borderBottom: 'none', pb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </TableCell>
      <TableCell sx={{ borderBottom: 'none', pb: 1 }}>
        <Typography variant="body2" fontWeight={600}>
          {value}
        </Typography>
      </TableCell>
    </TableRow>
  );

  return (
    <Stack spacing={3}>
      {/* Header Section with Summary */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          bgcolor: `${recommendationConfig.color}.main`,
          color: `${recommendationConfig.color}.contrastText`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <AIIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                {t('explainability.title')}
              </Typography>
            </Box>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
              {recommendationConfig.label}
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.95, whiteSpace: 'pre-line' }}>
              {data.narrative}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.2)',
              textAlign: 'center',
              ml: 2,
              minWidth: 120,
            }}
          >
            <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>
              {t('explainability.rankScore')}
            </Typography>
            <Typography variant="h3" fontWeight={700}>
              {Math.round(data.rank_score * 100)}%
            </Typography>
            {data.rank_position && (
              <>
                <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.3)' }} />
                <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>
                  {t('explainability.rankPosition')}
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  #{data.rank_position}
                </Typography>
              </>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Confidence Interval Display */}
      {data.confidence_interval && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon color="info" />
              <Typography variant="subtitle1" fontWeight={600}>
                {t('explainability.confidenceInterval.title')}
              </Typography>
            </Box>
            <Chip
              label={`${data.confidence_interval.confidence_level}% ${t('explainability.confidenceInterval.confidence')}`}
              size="small"
              color="info"
              sx={{ fontWeight: 600 }}
            />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('explainability.confidenceInterval.range')}:
            </Typography>
            <Typography variant="h6" fontWeight={600} color="primary.main">
              {Math.round(data.confidence_interval.lower_bound * 100)}% - {Math.round(data.confidence_interval.upper_bound * 100)}%
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {data.confidence_interval.interpretation}
          </Typography>
        </Paper>
      )}

      {/* Feature Contributions Grid */}
      <Grid container spacing={2}>
        {/* Positive Factors */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: 'success.50',
              borderLeft: 4,
              borderColor: 'success.main',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PositiveIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="subtitle1" fontWeight={600} color="success.main">
                {t('explainability.strengths.title')}
              </Typography>
              <Chip
                label={data.feature_explanations.filter(f => f.direction === 'positive').length}
                size="small"
                color="success"
                sx={{ ml: 'auto', fontWeight: 700 }}
              />
            </Box>
            {data.feature_explanations.filter(f => f.direction === 'positive').length > 0 ? (
              <Stack spacing={1.5}>
                {data.feature_explanations
                  .filter(f => f.direction === 'positive')
                  .slice(0, 3)
                  .map((feature, index) => (
                    <FeatureBar key={index} feature={feature} />
                  ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t('explainability.strengths.none')}
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Negative Factors */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: 'error.50',
              borderLeft: 4,
              borderColor: 'error.main',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <NegativeIcon color="error" sx={{ mr: 1 }} />
              <Typography variant="subtitle1" fontWeight={600} color="error.main">
                {t('explainability.weaknesses.title')}
              </Typography>
              <Chip
                label={data.feature_explanations.filter(f => f.direction === 'negative').length}
                size="small"
                color="error"
                sx={{ ml: 'auto', fontWeight: 700 }}
              />
            </Box>
            {data.feature_explanations.filter(f => f.direction === 'negative').length > 0 ? (
              <Stack spacing={1.5}>
                {data.feature_explanations
                  .filter(f => f.direction === 'negative')
                  .slice(0, 3)
                  .map((feature, index) => (
                    <FeatureBar key={index} feature={feature} />
                  ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="success.main">
                {t('explainability.weaknesses.none')}
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Strengths List */}
      {data.strengths && data.strengths.length > 0 && (
        <Paper elevation={2} sx={{ p: 2 }}>
          <Box
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setStrengthsOpen(!strengthsOpen)}
          >
            <BulbIcon color="success" sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              {t('explainability.candidateStrengths')}
            </Typography>
            <Chip
              label={data.strengths.length}
              size="small"
              color="success"
              sx={{ ml: 1, fontWeight: 700 }}
            />
            <IconButton size="small" sx={{ ml: 'auto' }}>
              {strengthsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          <Collapse in={strengthsOpen} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <Stack spacing={1}>
                {data.strengths.map((strength, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <CheckIcon
                      fontSize="small"
                      color="success"
                      sx={{ mt: 0.3, flexShrink: 0 }}
                    />
                    <Typography variant="body2">{strength}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Collapse>
        </Paper>
      )}

      {/* Weaknesses List */}
      {data.weaknesses && data.weaknesses.length > 0 && (
        <Paper elevation={2} sx={{ p: 2 }}>
          <Box
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setWeaknessesOpen(!weaknessesOpen)}
          >
            <WarningIcon color="warning" sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              {t('explainability.improvementAreas')}
            </Typography>
            <Chip
              label={data.weaknesses.length}
              size="small"
              color="warning"
              sx={{ ml: 1, fontWeight: 700 }}
            />
            <IconButton size="small" sx={{ ml: 'auto' }}>
              {weaknessesOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          <Collapse in={weaknessesOpen} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <Stack spacing={1}>
                {data.weaknesses.map((weakness, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <WarningIcon
                      fontSize="small"
                      color="warning"
                      sx={{ mt: 0.3, flexShrink: 0 }}
                    />
                    <Typography variant="body2">{weakness}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Collapse>
        </Paper>
      )}

      {/* Expandable Feature Details */}
      <Paper
        elevation={2}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': { elevation: 4, bgcolor: 'action.hover' },
        }}
        onClick={() => setDetailsOpen(!detailsOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ImportanceIcon color="primary" />
            <Typography variant="subtitle1" fontWeight={600}>
              {t('explainability.featureDetails.title')}
            </Typography>
            <Tooltip title={t('explainability.featureDetails.tooltip')}>
              <InfoIcon fontSize="small" color="info" sx={{ ml: 0.5 }} />
            </Tooltip>
          </Box>
          <IconButton size="small">
            {detailsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={detailsOpen} timeout="auto" unmountOnExit>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Grid container spacing={3}>
              {/* All Feature Contributions */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {t('explainability.featureDetails.contributions')}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  {data.feature_explanations.map((feature, index) => (
                    <FeatureBar key={index} feature={feature} />
                  ))}
                </Box>
              </Grid>

              {/* Metrics Table */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {t('explainability.featureDetails.metrics')}
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <DetailRow
                        label={t('explainability.metrics.rankScore')}
                        value={`${Math.round(data.rank_score * 100)}%`}
                      />
                      <DetailRow
                        label={t('explainability.metrics.rankPosition')}
                        value={data.rank_position ? `#${data.rank_position}` : t('explainability.metrics.notAvailable')}
                      />
                      <DetailRow
                        label={t('explainability.metrics.recommendation')}
                        value={data.recommendation}
                      />
                      <DetailRow
                        label={t('explainability.metrics.positiveFactors')}
                        value={data.feature_explanations.filter(f => f.direction === 'positive').length}
                      />
                      <DetailRow
                        label={t('explainability.metrics.negativeFactors')}
                        value={data.feature_explanations.filter(f => f.direction === 'negative').length}
                      />
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Feature Legend */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" fontWeight={600} gutterBottom display="block">
                    {t('explainability.legend.title')}:
                  </Typography>
                  <Stack spacing={0.5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
                      <Typography variant="caption" color="text.secondary">
                        {t('explainability.legend.positive')}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
                      <Typography variant="caption" color="text.secondary">
                        {t('explainability.legend.negative')}
                      </Typography>
                    </Box>
                  </Stack>
                </Box>
              </Grid>
            </Grid>

            {/* Resume Highlight Sections */}
            {data.highlight_sections && Object.keys(data.highlight_sections).length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {t('explainability.highlightSections.title')}
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(data.highlight_sections).map(([section, explanation]) => (
                    <Grid item xs={12} md={6} key={section}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" fontWeight={600} color="primary.main">
                          {section}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          {explanation}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </>
            )}

            {/* Technical Info */}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                <strong>{t('explainability.method')}:</strong> Explainable AI (SHAP values)
                {' • '}
                <strong>{t('explainability.provider')}:</strong> {data.provider}
                {' • '}
                <strong>{t('explainability.model')}:</strong> {data.model}
                {' • '}
                <strong>{t('explainability.features')}:</strong> {data.feature_explanations.length}
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </Paper>

      {/* Compact Footer */}
      {!detailsOpen && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>{t('explainability.aiModel')}:</strong> Candidate Ranking v1.0
            {' • '}
            <strong>{t('explainability.method')}:</strong> SHAP (SHapley Additive exPlanations)
            {' • '}
            <strong>{t('explainability.features')}:</strong> {data.feature_explanations.length}
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default ExplainabilityDashboard;

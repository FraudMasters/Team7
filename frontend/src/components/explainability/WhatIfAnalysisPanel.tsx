import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Divider,
  Slider,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Psychology as PsychologyIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { explainability } from '@/api/explainability';
import type {
  WhatIfAnalysisResponse,
  FeaturePerturbation,
} from '@/api/explainability';

/**
 * Feature adjustment configuration
 */
interface FeatureAdjustment {
  feature_name: string;
  current_value: number;
  min_value: number;
  max_value: number;
  step: number;
  unit: string;
  category: 'experience' | 'skills' | 'scoring' | 'education';
}

/**
 * Available feature adjustments for what-if analysis
 */
interface AvailableAdjustments {
  experience_months?: number;
  skills_match_ratio?: number;
  keyword_score?: number;
  tfidf_score?: number;
  vector_score?: number;
  education_level?: number;
}

/**
 * WhatIfAnalysisPanel Component Props
 */
interface WhatIfAnalysisPanelProps {
  /** Resume ID for what-if analysis */
  resumeId: string;
  /** Vacancy ID for what-if analysis */
  vacancyId: string;
  /** Original ranking score for comparison */
  originalScore?: number;
  /** Original recommendation level */
  originalRecommendation?: string;
  /** Callback when analysis completes */
  onAnalysisComplete?: (result: WhatIfAnalysisResponse) => void;
  /** API endpoint URL (optional, uses default if not provided) */
  apiUrl?: string;
}

/**
 * Available feature adjustments with their configurations
 */
const FEATURE_ADJUSTMENTS: Omit<FeatureAdjustment, 'current_value'>[] = [
  {
    feature_name: 'experience_months',
    min_value: -36,
    max_value: 36,
    step: 1,
    unit: 'months',
    category: 'experience',
  },
  {
    feature_name: 'skills_match_ratio',
    min_value: -0.3,
    max_value: 0.3,
    step: 0.01,
    unit: '%',
    category: 'skills',
  },
  {
    feature_name: 'keyword_score',
    min_value: -0.2,
    max_value: 0.2,
    step: 0.01,
    unit: '',
    category: 'scoring',
  },
  {
    feature_name: 'tfidf_score',
    min_value: -0.2,
    max_value: 0.2,
    step: 0.01,
    unit: '',
    category: 'scoring',
  },
  {
    feature_name: 'vector_score',
    min_value: -0.2,
    max_value: 0.2,
    step: 0.01,
    unit: '',
    category: 'scoring',
  },
  {
    feature_name: 'education_level',
    min_value: -1,
    max_value: 2,
    step: 1,
    unit: 'levels',
    category: 'education',
  },
];

/**
 * Recommendation level colors
 */
const RECOMMENDATION_COLORS: Record<string, string> = {
  excellent: 'success',
  good: 'primary',
  fair: 'warning',
  poor: 'error',
};

/**
 * WhatIfAnalysisPanel Component
 *
 * Provides interactive what-if scenario analysis for candidate rankings.
 * Users can adjust various features using sliders and see how these changes
 * would affect the candidate's ranking in real-time.
 *
 * Features:
 * - Interactive sliders for feature adjustments
 * - Real-time score updates
 * - Visual feedback for score changes (positive/negative)
 * - Feature impact breakdown
 * - Scenario explanations
 * - Preset scenarios for quick analysis
 *
 * @example
 * ```tsx
 * <WhatIfAnalysisPanel
 *   resumeId="abc-123"
 *   vacancyId="vacancy-456"
 *   originalScore={0.75}
 *   originalRecommendation="good"
 * />
 * ```
 */
const WhatIfAnalysisPanel: React.FC<WhatIfAnalysisPanelProps> = ({
  resumeId,
  vacancyId,
  originalScore,
  originalRecommendation,
  onAnalysisComplete,
  apiUrl = '/api/explainability/what-if',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WhatIfAnalysisResponse | null>(null);

  // Feature adjustment values
  const [adjustments, setAdjustments] = useState<AvailableAdjustments>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  /**
   * Fetch what-if analysis from backend
   */
  const fetchWhatIfAnalysis = async (adjustmentsData: AvailableAdjustments) => {
    // Filter out zero/undefined values
    const activeAdjustments = Object.fromEntries(
      Object.entries(adjustmentsData).filter(([_, value]) => value !== undefined && value !== 0)
    ) as Record<string, number>;

    if (Object.keys(activeAdjustments).length === 0) {
      setResult(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await explainability.whatIfAnalysis({
        resume_id: resumeId,
        vacancy_id: vacancyId,
        adjustments: activeAdjustments,
      });

      setResult(response);

      if (onAnalysisComplete) {
        onAnalysisComplete(response);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('whatIfAnalysis.error.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Debounced analysis fetch
   */
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchWhatIfAnalysis(adjustments);
    }, 500);

    return () => clearTimeout(timer);
  }, [adjustments, resumeId, vacancyId]);

  /**
   * Handle slider value change
   */
  const handleSliderChange = (featureName: keyof AvailableAdjustments, value: number) => {
    setAdjustments((prev) => ({
      ...prev,
      [featureName]: value,
    }));
    setSelectedPreset('');
  };

  /**
   * Apply preset scenario
   */
  const handleApplyPreset = (preset: string) => {
    setSelectedPreset(preset);
    let newAdjustments: AvailableAdjustments = {};

    switch (preset) {
      case 'moreExperience':
        newAdjustments = { experience_months: 12 };
        break;
      case 'lessExperience':
        newAdjustments = { experience_months: -12 };
        break;
      case 'improveSkills':
        newAdjustments = { skills_match_ratio: 0.15 };
        break;
      case 'higherEducation':
        newAdjustments = { education_level: 1 };
        break;
      case 'betterKeywords':
        newAdjustments = { keyword_score: 0.1 };
        break;
      case 'allImprovements':
        newAdjustments = {
          experience_months: 6,
          skills_match_ratio: 0.1,
          keyword_score: 0.05,
          education_level: 1,
        };
        break;
      default:
        newAdjustments = {};
    }

    setAdjustments(newAdjustments);
  };

  /**
   * Reset all adjustments
   */
  const handleReset = () => {
    setAdjustments({});
    setSelectedPreset('');
    setResult(null);
    setError(null);
  };

  /**
   * Get feature display name
   */
  const getFeatureDisplayName = (featureName: string): string => {
    const key = `whatIfAnalysis.features.${featureName}` as const;
    return t(key);
  };

  /**
   * Get feature category display name
   */
  const getCategoryDisplayName = (category: string): string => {
    const key = `whatIfAnalysis.categories.${category}` as const;
    return t(key);
  };

  /**
   * Format value for display
   */
  const formatValue = (featureName: string, value: number): string => {
    if (featureName === 'experience_months') {
      return value > 0 ? `+${value}` : `${value}`;
    }
    if (featureName.includes('_score') || featureName.includes('_ratio')) {
      return `${value > 0 ? '+' : ''}${(value * 100).toFixed(0)}%`;
    }
    if (featureName === 'education_level') {
      return value > 0 ? `+${value}` : `${value}`;
    }
    return `${value > 0 ? '+' : ''}${value}`;
  };

  /**
   * Render loading state
   */
  if (loading && !result) {
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
          {t('whatIfAnalysis.loading.title')}
        </Typography>
      </Box>
    );
  }

  /**
   * Calculate current adjusted score for display
   */
  const currentAdjustedScore = result?.new_score ?? originalScore;
  const scoreDelta = result?.score_delta ?? 0;
  const scoreDeltaPercent = result?.score_delta_percent ?? 0;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PsychologyIcon color="primary" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {t('whatIfAnalysis.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('whatIfAnalysis.subtitle')}
              </Typography>
            </Box>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleReset}
              disabled={Object.keys(adjustments).length === 0}
              size="small"
            >
              {t('whatIfAnalysis.reset')}
            </Button>
          </Stack>
        </Box>

        {/* Score Comparison Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'divider' }}>
              <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  {t('whatIfAnalysis.originalScore')}
                </Typography>
                <Typography variant="h4" color="text.primary" fontWeight={700}>
                  {originalScore !== undefined ? `${(originalScore * 100).toFixed(0)}%` : 'N/A'}
                </Typography>
                {originalRecommendation && (
                  <Chip
                    label={t(`explainability.recommendation.${originalRecommendation}`)}
                    size="small"
                    color={RECOMMENDATION_COLORS[originalRecommendation] as any}
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: scoreDelta > 0 ? 'success.main' : scoreDelta < 0 ? 'error.main' : 'divider',
                bgcolor: scoreDelta > 0 ? 'success.50' : scoreDelta < 0 ? 'error.50' : 'transparent',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  {t('whatIfAnalysis.adjustedScore')}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                  {result ? (
                    <>
                      <Typography variant="h4" fontWeight={700} color="primary.main">
                        {(result.new_score * 100).toFixed(0)}%
                      </Typography>
                      {scoreDelta !== 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {scoreDelta > 0 ? (
                            <TrendingUpIcon color="success" fontSize="small" />
                          ) : (
                            <TrendingDownIcon color="error" fontSize="small" />
                          )}
                        </Box>
                      )}
                    </>
                  ) : (
                    <Typography variant="h4" color="text.secondary" fontWeight={700}>
                      {originalScore !== undefined ? `${(originalScore * 100).toFixed(0)}%` : 'N/A'}
                    </Typography>
                  )}
                </Box>
                {result?.new_recommendation && (
                  <Chip
                    label={t(`explainability.recommendation.${result.new_recommendation}`)}
                    size="small"
                    color={RECOMMENDATION_COLORS[result.new_recommendation] as any}
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: scoreDelta > 0 ? 'success.main' : scoreDelta < 0 ? 'error.main' : 'divider',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  {t('whatIfAnalysis.scoreChange')}
                </Typography>
                {result ? (
                  <>
                    <Typography
                      variant="h4"
                      fontWeight={700}
                      color={scoreDelta > 0 ? 'success.main' : scoreDelta < 0 ? 'error.main' : 'text.primary'}
                    >
                      {scoreDelta > 0 ? '+' : ''}{(scoreDelta * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {scoreDeltaPercent > 0 ? '+' : ''}{scoreDeltaPercent.toFixed(1)}% {t('whatIfAnalysis.changeFromOriginal')}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="h4" color="text.secondary">
                    0.0%
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Preset Scenarios */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {t('whatIfAnalysis.presets.title')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
            {t('whatIfAnalysis.presets.description')}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
            <Chip
              label={t('whatIfAnalysis.presets.moreExperience')}
              onClick={() => handleApplyPreset('moreExperience')}
              sx={{ cursor: 'pointer' }}
              color={selectedPreset === 'moreExperience' ? 'primary' : 'default'}
              variant={selectedPreset === 'moreExperience' ? 'filled' : 'outlined'}
            />
            <Chip
              label={t('whatIfAnalysis.presets.improveSkills')}
              onClick={() => handleApplyPreset('improveSkills')}
              sx={{ cursor: 'pointer' }}
              color={selectedPreset === 'improveSkills' ? 'primary' : 'default'}
              variant={selectedPreset === 'improveSkills' ? 'filled' : 'outlined'}
            />
            <Chip
              label={t('whatIfAnalysis.presets.higherEducation')}
              onClick={() => handleApplyPreset('higherEducation')}
              sx={{ cursor: 'pointer' }}
              color={selectedPreset === 'higherEducation' ? 'primary' : 'default'}
              variant={selectedPreset === 'higherEducation' ? 'filled' : 'outlined'}
            />
            <Chip
              label={t('whatIfAnalysis.presets.betterKeywords')}
              onClick={() => handleApplyPreset('betterKeywords')}
              sx={{ cursor: 'pointer' }}
              color={selectedPreset === 'betterKeywords' ? 'primary' : 'default'}
              variant={selectedPreset === 'betterKeywords' ? 'filled' : 'outlined'}
            />
            <Chip
              label={t('whatIfAnalysis.presets.allImprovements')}
              onClick={() => handleApplyPreset('allImprovements')}
              sx={{ cursor: 'pointer' }}
              color={selectedPreset === 'allImprovements' ? 'primary' : 'default'}
              variant={selectedPreset === 'allImprovements' ? 'filled' : 'outlined'}
            />
          </Stack>
        </Box>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" action={<Button color="inherit" onClick={() => fetchWhatIfAnalysis(adjustments)}>{t('common.tryAgain')}</Button>}>
          <AlertTitle>{t('whatIfAnalysis.error.title')}</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Feature Adjustment Sliders */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          {t('whatIfAnalysis.adjustments.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t('whatIfAnalysis.adjustments.description')}
        </Typography>

        <Stack spacing={3}>
          {FEATURE_ADJUSTMENTS.map((feature) => {
            const currentValue = adjustments[feature.feature_name as keyof AvailableAdjustments] ?? 0;
            const featureConfig = FEATURE_ADJUSTMENTS.find((f) => f.feature_name === feature.feature_name)!;

            return (
              <Box key={feature.feature_name}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" fontWeight={500}>
                    {getFeatureDisplayName(feature.feature_name)}
                  </Typography>
                  <Chip
                    label={formatValue(feature.feature_name, currentValue)}
                    size="small"
                    color={currentValue > 0 ? 'success' : currentValue < 0 ? 'error' : 'default'}
                    variant={currentValue !== 0 ? 'filled' : 'outlined'}
                  />
                </Box>
                <Slider
                  value={currentValue}
                  onChange={(_, value) => handleSliderChange(feature.feature_name as keyof AvailableAdjustments, value as number)}
                  min={featureConfig.min_value}
                  max={featureConfig.max_value}
                  step={featureConfig.step}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => formatValue(feature.feature_name, value as number)}
                  marks={[
                    { value: featureConfig.min_value, label: formatValue(feature.feature_name, featureConfig.min_value) },
                    { value: 0, label: '0' },
                    { value: featureConfig.max_value, label: formatValue(feature.feature_name, featureConfig.max_value) },
                  ]}
                  sx={{
                    '& .MuiSlider-thumb': {
                      width: currentValue === 0 ? 12 : 20,
                      height: currentValue === 0 ? 12 : 20,
                    },
                    color: currentValue > 0 ? 'success.main' : currentValue < 0 ? 'error.main' : 'primary.main',
                  }}
                  disabled={loading}
                />
                <Typography variant="caption" color="text.secondary">
                  {t(`whatIfAnalysis.features.${feature.feature_name}Description`)}
                </Typography>
              </Box>
            );
          })}
        </Stack>

        <Alert severity="info" variant="outlined" sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <InfoIcon fontSize="small" sx={{ mt: 0.2 }} />
            <Typography variant="body2">
              {t('whatIfAnalysis.adjustments.hint')}
            </Typography>
          </Box>
        </Alert>
      </Paper>

      {/* Analysis Results */}
      {result && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {t('whatIfAnalysis.results.title')}
          </Typography>

          <Alert
            severity={result.score_delta > 0 ? 'success' : result.score_delta < 0 ? 'warning' : 'info'}
            sx={{ mb: 3 }}
          >
            <AlertTitle>{result.scenario_description || t('whatIfAnalysis.results.scenarioAnalysis')}</AlertTitle>
            <Typography variant="body2">{result.explanation}</Typography>
          </Alert>

          {/* Feature Perturbations */}
          {result.perturbations && result.perturbations.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                {t('whatIfAnalysis.results.featureChanges')}
              </Typography>
              <Grid container spacing={1}>
                {result.perturbations.map((perturbation: FeaturePerturbation, index: number) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card variant="outlined" size="small">
                      <CardContent sx={{ py: 1.5, px: 2 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                          {perturbation.feature_name}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" fontWeight={500}>
                            {perturbation.original_value.toFixed(3)} → {perturbation.perturbed_value.toFixed(3)}
                          </Typography>
                          <Chip
                            label={`${perturbation.perturbation_percent > 0 ? '+' : ''}${perturbation.perturbation_percent.toFixed(1)}%`}
                            size="small"
                            color={perturbation.perturbation_amount > 0 ? 'success' : 'error'}
                            variant="filled"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Feature Impacts */}
          {result.feature_impacts && Object.keys(result.feature_impacts).length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {t('whatIfAnalysis.results.featureImpacts')}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(result.feature_impacts).map(([feature, impact], index) => (
                  <Chip
                    key={index}
                    label={`${feature}: ${impact > 0 ? '+' : ''}${(impact * 100).toFixed(2)}%`}
                    size="small"
                    color={impact > 0 ? 'success' : impact < 0 ? 'error' : 'default'}
                    variant={impact !== 0 ? 'filled' : 'outlined'}
                  />
                ))}
              </Stack>
            </Box>
          )}
        </Paper>
      )}

      {/* Loading indicator for analysis updates */}
      {loading && result && (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, py: 2 }}>
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">
            {t('whatIfAnalysis.updating')}
          </Typography>
        </Box>
      )}
    </Stack>
  );
};

export default WhatIfAnalysisPanel;

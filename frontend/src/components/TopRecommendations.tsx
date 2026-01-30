import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Stack,
  LinearProgress,
  Tooltip,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Star as StarIcon,
  EmojiEvents as TrophyIcon,
  Psychology as AIIcon,
  TrendingUp as TrendingUpIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { RecommendationsResponse, RankedCandidate, FeatureExplanation } from '../types/api';

interface TopRecommendationsProps {
  vacancyId: string;
  vacancyTitle?: string;
}

/**
 * TopRecommendations Component
 *
 * Displays top 3 AI-recommended candidates for a vacancy with explanations.
 * Uses ML-based ranking to show the most promising candidates.
 */
const TopRecommendations: React.FC<TopRecommendationsProps> = ({ vacancyId, vacancyTitle }) => {
  const { t } = useTranslation();
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set([0])); // Expand first card by default

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!vacancyId) return;

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get<RecommendationsResponse>(
          `/api/ranking/recommendations/${vacancyId}`
        );
        setRecommendations(response.data);
      } catch (err: any) {
        console.error('Error fetching recommendations:', err);
        setError(err.response?.data?.detail || t('recommendations.fetchError'));
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [vacancyId, t]);

  const toggleCardExpansion = (index: number) => {
    setExpandedCards((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'excellent':
        return 'success';
      case 'good':
        return 'info';
      case 'fair':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <TrophyIcon sx={{ fontSize: 32, color: 'warning.main' }} />;
      case 2:
        return <TrophyIcon sx={{ fontSize: 28, color: 'grey.400' }} />;
      case 3:
        return <TrophyIcon sx={{ fontSize: 24, color: 'error.main' }} />;
      default:
        return <StarIcon sx={{ fontSize: 20, color: 'text.secondary' }} />;
    }
  };

  const FeatureExplanationItem: React.FC<{ feature: FeatureExplanation }> = ({ feature }) => (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 0.5,
        px: 1,
        borderRadius: 1,
        bgcolor: feature.direction === 'positive' ? 'success.50' : 'error.50',
        mb: 0.5,
      }}
    >
      <Typography variant="body2" sx={{ flex: 1 }}>
        {feature.description}
      </Typography>
      <Chip
        label={`${feature.contribution_percentage.toFixed(1)}%`}
        size="small"
        color={feature.direction === 'positive' ? 'success' : 'error'}
        sx={{ fontWeight: 600, minWidth: 60 }}
      />
    </Box>
  );

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {t('recommendations.loading')}
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!recommendations || recommendations.top_candidates.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <AIIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          {t('recommendations.noRecommendations')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('recommendations.notEnoughData')}
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 3,
          background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'primary.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <StarIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                {t('recommendations.title')}
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {vacancyTitle || t('recommendations.forVacancy')}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
              {t('recommendations.basedOn', { count: recommendations.total_candidates_considered })}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.2)',
              textAlign: 'center',
            }}
          >
            <Typography variant="h3" fontWeight={700}>
              {recommendations.top_candidates.length}
            </Typography>
            <Typography variant="caption">{t('recommendations.topCandidates')}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Top 3 Candidates */}
      <Grid container spacing={3}>
        {recommendations.top_candidates.map((candidate, index) => {
          const isExpanded = expandedCards.has(index);
          const rank = index + 1;

          return (
            <Grid item xs={12} md={4} key={candidate.resume_id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  border: 2,
                  borderColor: `${getRecommendationColor(candidate.recommendation)}.main`,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                  position: 'relative',
                  overflow: 'visible',
                }}
              >
                {/* Rank Badge */}
                <Box
                  sx={{
                    position: 'absolute',
                    top: -12,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    p: 1,
                    borderRadius: '50%',
                    bgcolor: `${getRecommendationColor(candidate.recommendation)}.main`,
                    color: `${getRecommendationColor(candidate.recommendation)}.contrastText`,
                    boxShadow: 3,
                    zIndex: 1,
                  }}
                >
                  {getRankIcon(rank)}
                </Box>

                <CardContent sx={{ flexGrow: 1, pt: 3 }}>
                  {/* Candidate Header */}
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      {candidate.candidate_name || t('recommendations.anonymousCandidate')}
                    </Typography>
                    <Stack direction="row" spacing={1} justifyContent="center" alignItems="center">
                      <Chip
                        label={`#${rank}`}
                        color={getRecommendationColor(candidate.recommendation) as any}
                        sx={{ fontWeight: 700 }}
                      />
                      {/* A/B Test Badge */}
                      {candidate.is_experiment && (
                        <Tooltip title={`Experiment: ${candidate.experiment_group === 'treatment' ? 'New AI Model' : 'Standard Model'} (${candidate.model_version || 'v1.0'})`}>
                          <Chip
                            icon={<ScienceIcon sx={{ fontSize: 14 }} />}
                            label="A/B TEST"
                            size="small"
                            color={candidate.experiment_group === 'treatment' ? 'secondary' : 'default'}
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.65rem',
                              height: 22,
                              border: candidate.experiment_group === 'treatment' ? 2 : 1,
                              borderColor: candidate.experiment_group === 'treatment' ? 'secondary.main' : 'divider',
                              animation: candidate.experiment_group === 'treatment' ? 'pulse 2s infinite' : 'none',
                              '@keyframes pulse': {
                                    '0%, 100%': { opacity: 1 },
                                    '50%': { opacity: 0.7 },
                                  },
                            }}
                          />
                        </Tooltip>
                      )}
                    </Stack>
                  </Box>

                  {/* Ranking Score */}
                  <Box sx={{ mb: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {t('recommendations.rankingScore')}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="h3" fontWeight={700} color="primary.main">
                        {Math.round(candidate.ranking_score)}
                      </Typography>
                      <Typography variant="h5" color="text.secondary">
                        /100
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={candidate.ranking_score}
                      sx={{ height: 8, borderRadius: 4, mt: 1 }}
                      color={getRecommendationColor(candidate.recommendation) as any}
                    />
                  </Box>

                  {/* Hire Probability */}
                  <Box sx={{ mb: 2, textAlign: 'center' }}>
                    <Tooltip title={t('recommendations.hireProbabilityTooltip')}>
                      <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                        <TrendingUpIcon fontSize="small" color="info" />
                        <Typography variant="caption" color="text.secondary">
                          {t('recommendations.hireProbability')}:{' '}
                          <strong>{(candidate.hire_probability * 100).toFixed(0)}%</strong>
                        </Typography>
                      </Box>
                    </Tooltip>
                  </Box>

                  {/* Recommendation Badge */}
                  <Box sx={{ mb: 2, textAlign: 'center' }}>
                    <Chip
                      icon={<AIIcon />}
                      label={t(`recommendations.levels.${candidate.recommendation}`)}
                      color={getRecommendationColor(candidate.recommendation) as any}
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  {/* Expand Button */}
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                    <IconButton
                      size="small"
                      onClick={() => toggleCardExpansion(index)}
                      sx={{ bgcolor: 'action.hover' }}
                    >
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      <Typography variant="caption" sx={{ ml: 0.5 }}>
                        {isExpanded ? t('recommendations.hide') : t('recommendations.show')}
                      </Typography>
                    </IconButton>
                  </Box>

                  {/* AI Explanation (Collapsible) */}
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                      {/* Summary */}
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                          <InfoIcon fontSize="small" color="primary" />
                          <Typography variant="subtitle2" fontWeight={600} color="primary">
                            {t('recommendations.whyRecommended')}
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {candidate.explanation.summary}
                        </Typography>
                      </Box>

                      {/* Top Positive Factors */}
                      {candidate.explanation.top_positive_factors.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="success.main" fontWeight={600} display="block" sx={{ mb: 1 }}>
                            {t('recommendations.strengths')}
                          </Typography>
                          <Stack spacing={0.5}>
                            {candidate.explanation.top_positive_factors.map((factor, idx) => (
                              <FeatureExplanationItem key={`pos-${idx}`} feature={factor} />
                            ))}
                          </Stack>
                        </Box>
                      )}

                      {/* Top Negative Factors */}
                      {candidate.explanation.top_negative_factors.length > 0 && (
                        <Box>
                          <Typography variant="caption" color="error.main" fontWeight={600} display="block" sx={{ mb: 1 }}>
                            {t('recommendations.areasForImprovement')}
                          </Typography>
                          <Stack spacing={0.5}>
                            {candidate.explanation.top_negative_factors.map((factor, idx) => (
                              <FeatureExplanationItem key={`neg-${idx}`} feature={factor} />
                            ))}
                          </Stack>
                        </Box>
                      )}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Model Info Footer */}
      <Paper sx={{ p: 2, mt: 3, bgcolor: 'action.hover' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>{t('recommendations.modelVersion')}:</strong> {recommendations.model_version}
          {' • '}
          <strong>{t('recommendations.generatedAt')}:</strong>{' '}
          {new Date(recommendations.generated_at).toLocaleString()}
          {' • '}
          <strong>{t('recommendations.aiPowered')}</strong>
        </Typography>
      </Paper>
    </Box>
  );
};

export default TopRecommendations;

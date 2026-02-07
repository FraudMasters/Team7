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
  Work as WorkIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { BestFitResponse, BestFitCandidate } from '../types/api';
import { trackRecommendationImpression, trackRecommendationClick, trackBatchImpressions } from '../api/recommendations';

interface BestFitCandidatesProps {
  vacancyId: string;
  vacancyTitle?: string;
  limit?: number;
}

/**
 * BestFitCandidates Component
 *
 * Displays AI-recommended best-fit candidates for a vacancy.
 * Shows match scores, skills, missing skills, and fit recommendations.
 */
const BestFitCandidates: React.FC<BestFitCandidatesProps> = ({ vacancyId, vacancyTitle, limit = 20 }) => {
  const { t } = useTranslation();
  const [bestFit, setBestFit] = useState<BestFitResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set([0])); // Expand first card by default

  useEffect(() => {
    const fetchBestFit = async () => {
      if (!vacancyId) return;

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get<BestFitResponse>(
          `/api/recommendations/best-fit/${vacancyId}`,
          { params: { limit, use_experiment: true } }
        );
        setBestFit(response.data);

        // Track impressions for all recommended candidates
        const candidateIds = response.data.candidates.map(c => c.resume_id);
        trackBatchImpressions(candidateIds, 'best_fit');
      } catch (err: any) {
        setError(err.response?.data?.detail || t('bestFitCandidates.fetchError'));
      } finally {
        setLoading(false);
      }
    };

    fetchBestFit();
  }, [vacancyId, limit, t]);

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

  const getMatchColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'info';
    if (score >= 0.4) return 'warning';
    return 'error';
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'excellent':
      case 'highly recommended':
        return 'success';
      case 'good':
      case 'recommended':
        return 'info';
      case 'fair':
      case 'consider':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {t('bestFitCandidates.loading')}
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

  if (!bestFit || bestFit.candidates.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <WorkIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          {t('bestFitCandidates.noCandidates')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('bestFitCandidates.notEnoughData')}
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
          background: (theme) => `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
          color: 'success.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <StarIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                {t('bestFitCandidates.title')}
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {vacancyTitle || t('bestFitCandidates.forVacancy')}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
              {t('bestFitCandidates.found', { count: bestFit.total_candidates })}
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
              {bestFit.candidates.length}
            </Typography>
            <Typography variant="caption">{t('bestFitCandidates.candidates')}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Candidates Grid */}
      <Grid container spacing={3}>
        {bestFit.candidates.map((candidate, index) => {
          const isExpanded = expandedCards.has(index);
          const matchPercentage = Math.round(candidate.match_score * 100);

          const handleCardClick = () => {
            // Track click event
            trackRecommendationClick(candidate.resume_id, 'best_fit');
          };

          return (
            <Grid item xs={12} md={6} lg={4} key={candidate.resume_id}>
              <Card
                onClick={handleCardClick}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  border: 2,
                  borderColor: `${getMatchColor(candidate.match_score)}.main`,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6, cursor: 'pointer' },
                  position: 'relative',
                  overflow: 'visible',
                }}
              >
                <CardContent sx={{ flexGrow: 1, pt: 2 }}>
                  {/* Candidate Header */}
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      {candidate.name || t('bestFitCandidates.anonymousCandidate')}
                    </Typography>
                    {candidate.title && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {candidate.title}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={1} justifyContent="center" alignItems="center" sx={{ mt: 1 }}>
                      {/* A/B Test Badge */}
                      {bestFit.is_experiment && (
                        <Tooltip title={`Experiment: ${bestFit.experiment_group === 'treatment' ? 'New AI Model' : 'Standard Model'} (${bestFit.algorithm_version})`}>
                          <Chip
                            icon={<ScienceIcon sx={{ fontSize: 14 }} />}
                            label="A/B TEST"
                            size="small"
                            color={bestFit.experiment_group === 'treatment' ? 'secondary' : 'default'}
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.65rem',
                              height: 22,
                              border: bestFit.experiment_group === 'treatment' ? 2 : 1,
                              borderColor: bestFit.experiment_group === 'treatment' ? 'secondary.main' : 'divider',
                              animation: bestFit.experiment_group === 'treatment' ? 'pulse 2s infinite' : 'none',
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

                  {/* Match Score */}
                  <Box sx={{ mb: 2, textAlign: 'center' }}>
                    <Tooltip title={t('bestFitCandidates.matchScoreTooltip')}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('bestFitCandidates.matchScore')}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mt: 0.5 }}>
                          <Typography variant="h3" fontWeight={700} color="success.main">
                            {matchPercentage}
                          </Typography>
                          <Typography variant="h5" color="text.secondary">
                            %
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={matchPercentage}
                          sx={{ height: 8, borderRadius: 4, mt: 1 }}
                          color={getMatchColor(candidate.match_score) as any}
                        />
                      </Box>
                    </Tooltip>
                  </Box>

                  {/* Recommendation Badge */}
                  {candidate.recommendation && (
                    <Box sx={{ mb: 2, textAlign: 'center' }}>
                      <Chip
                        icon={<AIIcon />}
                        label={candidate.recommendation}
                        color={getRecommendationColor(candidate.recommendation) as any}
                        sx={{ fontWeight: 600 }}
                      />
                    </Box>
                  )}

                  {/* Years of Experience */}
                  {candidate.years_experience !== null && (
                    <Box sx={{ mb: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {t('bestFitCandidates.experience')}
                      </Typography>
                      <Typography variant="body1" fontWeight={600} color="primary.main">
                        {candidate.years_experience.toFixed(1)} {t('bestFitCandidates.years')}
                      </Typography>
                    </Box>
                  )}

                  {/* Expand Button */}
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                    <IconButton
                      size="small"
                      onClick={() => toggleCardExpansion(index)}
                      sx={{ bgcolor: 'action.hover' }}
                    >
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      <Typography variant="caption" sx={{ ml: 0.5 }}>
                        {isExpanded ? t('bestFitCandidates.hide') : t('bestFitCandidates.show')}
                      </Typography>
                    </IconButton>
                  </Box>

                  {/* Skills and Details (Collapsible) */}
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                      {/* Matched Skills */}
                      {candidate.skills_match && candidate.skills_match.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                            <CheckCircleIcon fontSize="small" color="success" />
                            <Typography variant="subtitle2" fontWeight={600} color="success.main">
                              {t('bestFitCandidates.matchedSkills')}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {candidate.skills_match.slice(0, 10).map((skill, idx) => (
                              <Chip
                                key={`match-${idx}`}
                                label={skill}
                                size="small"
                                color="success"
                                variant="outlined"
                              />
                            ))}
                            {candidate.skills_match.length > 10 && (
                              <Chip
                                label={`+${candidate.skills_match.length - 10} ${t('bestFitCandidates.more')}`}
                                size="small"
                                color="success"
                              />
                            )}
                          </Box>
                        </Box>
                      )}

                      {/* Missing Skills */}
                      {candidate.missing_skills && candidate.missing_skills.length > 0 && (
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                            <CancelIcon fontSize="small" color="error" />
                            <Typography variant="subtitle2" fontWeight={600} color="error.main">
                              {t('bestFitCandidates.missingSkills')}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {candidate.missing_skills.slice(0, 10).map((skill, idx) => (
                              <Chip
                                key={`missing-${idx}`}
                                label={skill}
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                            ))}
                            {candidate.missing_skills.length > 10 && (
                              <Chip
                                label={`+${candidate.missing_skills.length - 10} ${t('bestFitCandidates.more')}`}
                                size="small"
                                color="error"
                              />
                            )}
                          </Box>
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

      {/* Footer Info */}
      <Paper sx={{ p: 2, mt: 3, bgcolor: 'action.hover' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>{t('bestFitCandidates.algorithmVersion')}:</strong> {bestFit.algorithm_version}
          {' • '}
          <strong>{t('bestFitCandidates.generatedAt')}:</strong>{' '}
          {new Date().toLocaleString()}
          {' • '}
          <strong>{t('bestFitCandidates.aiPowered')}</strong>
        </Typography>
      </Paper>
    </Box>
  );
};

export default BestFitCandidates;

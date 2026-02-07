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
  Avatar,
} from '@mui/material';
import {
  Person as PersonIcon,
  Psychology as AIIcon,
  Work as WorkIcon,
  AutoAwesome as SimilarIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Science as ScienceIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { SimilarCandidatesResponse, SimilarCandidate } from '../types/api';
import { trackRecommendationImpression, trackRecommendationClick, trackBatchImpressions } from '../api/recommendations';

interface SimilarCandidatesProps {
  resumeId: string;
  candidateName?: string;
  limit?: number;
}

/**
 * SimilarCandidates Component
 *
 * Displays candidates similar to a given candidate based on embeddings.
 * Shows similarity scores, shared skills, and reasons for similarity.
 */
const SimilarCandidates: React.FC<SimilarCandidatesProps> = ({ resumeId, candidateName, limit = 10 }) => {
  const { t } = useTranslation();
  const [similarCandidates, setSimilarCandidates] = useState<SimilarCandidatesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set([0])); // Expand first card by default

  useEffect(() => {
    const fetchSimilarCandidates = async () => {
      if (!resumeId) return;

      try {
        setLoading(true);
        setError(null);
        const response = await axios.get<SimilarCandidatesResponse>(
          `/api/recommendations/similar/${resumeId}`,
          { params: { limit } }
        );
        setSimilarCandidates(response.data);

        // Track impressions for all recommended candidates
        const candidateIds = response.data.candidates.map(c => c.resume_id);
        trackBatchImpressions(candidateIds, 'similar');
      } catch (err: any) {
        setError(err.response?.data?.detail || t('similarCandidates.fetchError'));
      } finally {
        setLoading(false);
      }
    };

    fetchSimilarCandidates();
  }, [resumeId, limit, t]);

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

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'info';
    if (score >= 0.4) return 'warning';
    return 'default';
  };

  const SimilarCandidateCard: React.FC<{ candidate: SimilarCandidate; index: number }> = ({ candidate, index }) => {
    const isExpanded = expandedCards.has(index);
    const similarityColor = getSimilarityColor(candidate.similarity_score);
    const similarityPercent = Math.round(candidate.similarity_score * 100);

    const handleCardClick = () => {
      // Track click event
      trackRecommendationClick(candidate.resume_id, 'similar');
    };

    return (
      <Card
        onClick={handleCardClick}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: 2,
          borderColor: `${similarityColor}.main`,
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: 6, cursor: 'pointer' },
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          {/* Candidate Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Avatar
              sx={{
                bgcolor: `${similarityColor}.main`,
                width: 56,
                height: 56,
              }}
            >
              <PersonIcon sx={{ fontSize: 32 }} />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {candidate.name || t('similarCandidates.anonymousCandidate')}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <WorkIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {candidate.title || t('similarCandidates.noTitle')}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Similarity Score */}
          <Box sx={{ mb: 2, textAlign: 'center' }}>
            <Tooltip title={t('similarCandidates.similarityScoreTooltip')}>
              <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                <SimilarIcon fontSize="small" color={similarityColor as any} />
                <Typography variant="caption" color="text.secondary">
                  {t('similarCandidates.similarityScore')}
                </Typography>
              </Box>
            </Tooltip>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <Typography variant="h3" fontWeight={700} color={`${similarityColor}.main` as any}>
                {similarityPercent}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={similarityPercent}
              sx={{ height: 8, borderRadius: 4, mt: 1 }}
              color={similarityColor as any}
            />
          </Box>

          {/* A/B Test Badge */}
          {similarCandidates?.is_experiment && (
            <Box sx={{ mb: 2, textAlign: 'center' }}>
              <Tooltip title={`Experiment: ${similarCandidates.experiment_group === 'treatment' ? 'New AI Model' : 'Standard Model'} (${similarCandidates.algorithm_version})`}>
                <Chip
                  icon={<ScienceIcon sx={{ fontSize: 14 }} />}
                  label="A/B TEST"
                  size="small"
                  color={similarCandidates.experiment_group === 'treatment' ? 'secondary' : 'default'}
                  sx={{
                    fontWeight: 600,
                    fontSize: '0.65rem',
                    height: 22,
                    border: similarCandidates.experiment_group === 'treatment' ? 2 : 1,
                    borderColor: similarCandidates.experiment_group === 'treatment' ? 'secondary.main' : 'divider',
                  }}
                />
              </Tooltip>
            </Box>
          )}

          {/* Match Reason */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              <InfoIcon fontSize="small" color="primary" />
              <Typography variant="subtitle2" fontWeight={600} color="primary">
                {t('similarCandidates.whySimilar')}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {candidate.match_reason}
            </Typography>
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
                {isExpanded ? t('similarCandidates.hide') : t('similarCandidates.show')}
              </Typography>
            </IconButton>
          </Box>

          {/* Shared Skills (Collapsible) */}
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
              {candidate.shared_skills.length > 0 ? (
                <>
                  <Typography variant="caption" color="success.main" fontWeight={600} display="block" sx={{ mb: 1 }}>
                    {t('similarCandidates.sharedSkills')} ({candidate.shared_skills.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {candidate.shared_skills.slice(0, 10).map((skill, idx) => (
                      <Chip
                        key={idx}
                        label={skill}
                        size="small"
                        color="success"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    ))}
                    {candidate.shared_skills.length > 10 && (
                      <Chip
                        label={`+${candidate.shared_skills.length - 10} more`}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    )}
                  </Box>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary" italic>
                  {t('similarCandidates.noSharedSkills')}
                </Typography>
              )}
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {t('similarCandidates.loading')}
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

  if (!similarCandidates || similarCandidates.candidates.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <SimilarIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          {t('similarCandidates.noSimilarCandidates')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('similarCandidates.notEnoughData')}
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
          background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.dark} 100%)`,
          color: 'info.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <SimilarIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                {t('similarCandidates.title')}
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {candidateName ? t('similarCandidates.forCandidate', { name: candidateName }) : t('similarCandidates.forThisCandidate')}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
              {t('similarCandidates.found', { count: similarCandidates.total_candidates })}
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
              {similarCandidates.candidates.length}
            </Typography>
            <Typography variant="caption">{t('similarCandidates.candidates')}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Similar Candidates Grid */}
      <Grid container spacing={3}>
        {similarCandidates.candidates.map((candidate, index) => (
          <Grid item xs={12} md={6} lg={4} key={candidate.resume_id}>
            <SimilarCandidateCard candidate={candidate} index={index} />
          </Grid>
        ))}
      </Grid>

      {/* Algorithm Info Footer */}
      <Paper sx={{ p: 2, mt: 3, bgcolor: 'action.hover' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>{t('similarCandidates.algorithmVersion')}:</strong> {similarCandidates.algorithm_version}
          {' • '}
          <strong>{t('similarCandidates.generatedAt')}:</strong>{' '}
          {new Date().toLocaleString()}
          {' • '}
          <strong>{t('similarCandidates.aiPowered')}</strong>
        </Typography>
      </Paper>
    </Box>
  );
};

export default SimilarCandidates;

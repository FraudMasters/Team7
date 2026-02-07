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
  Button,
} from '@mui/material';
import {
  Person as PersonIcon,
  Psychology as AIIcon,
  Work as WorkIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Science as ScienceIcon,
  Phone as PhoneIcon,
  Event as EventIcon,
  CardGiftcard as OfferIcon,
  MarkEmailRead as FollowUpIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { AtRiskResponse, AtRiskCandidate } from '../types/api';
import { trackRecommendationImpression, trackRecommendationClick, trackBatchImpressions } from '../api/recommendations';

interface AtRiskCandidatesProps {
  limit?: number;
  vacancyId?: string;
  minRiskScore?: number;
}

/**
 * AtRiskCandidates Component
 *
 * Displays candidates at risk of loss (attrition prediction).
 * Shows risk scores, risk factors, and recommended actions.
 */
const AtRiskCandidates: React.FC<AtRiskCandidatesProps> = ({
  limit = 10,
  vacancyId,
  minRiskScore = 0.3
}) => {
  const { t } = useTranslation();
  const [atRiskData, setAtRiskData] = useState<AtRiskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set([0])); // Expand first card by default

  useEffect(() => {
    const fetchAtRiskCandidates = async () => {
      try {
        setLoading(true);
        setError(null);
        const params: any = { limit, min_risk_score: minRiskScore };
        if (vacancyId) {
          params.vacancy_id = vacancyId;
        }
        const response = await axios.get<AtRiskResponse>(
          '/api/recommendations/at-risk',
          { params }
        );
        setAtRiskData(response.data);

        // Track impressions for all recommended candidates
        const candidateIds = response.data.candidates.map(c => c.resume_id);
        trackBatchImpressions(candidateIds, 'at_risk');
      } catch (err: any) {
        setError(err.response?.data?.detail || t('atRiskCandidates.fetchError'));
      } finally {
        setLoading(false);
      }
    };

    fetchAtRiskCandidates();
  }, [limit, vacancyId, minRiskScore, t]);

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

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    return <WarningIcon sx={{ fontSize: 20 }} />;
  };

  const getActionIcon = (action: string) => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('contact')) return <PhoneIcon fontSize="small" />;
    if (actionLower.includes('interview') || actionLower.includes('schedule')) return <EventIcon fontSize="small" />;
    if (actionLower.includes('offer')) return <OfferIcon fontSize="small" />;
    return <FollowUpIcon fontSize="small" />;
  };

  const AtRiskCandidateCard: React.FC<{ candidate: AtRiskCandidate; index: number }> = ({ candidate, index }) => {
    const isExpanded = expandedCards.has(index);
    const riskColor = getRiskColor(candidate.risk_level);
    const riskPercent = Math.round(candidate.risk_score * 100);

    const handleCardClick = () => {
      // Track click event
      trackRecommendationClick(candidate.resume_id, 'at_risk');
    };

    return (
      <Card
        onClick={handleCardClick}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: 2,
          borderColor: `${riskColor}.main`,
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: 6, cursor: 'pointer' },
          position: 'relative',
          overflow: 'visible',
        }}
      >
        {/* Risk Level Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: -12,
            right: -12,
            p: 1,
            borderRadius: '50%',
            bgcolor: `${riskColor}.main`,
            color: `${riskColor}.contrastText`,
            boxShadow: 3,
            zIndex: 1,
          }}
        >
          {getRiskIcon(candidate.risk_level)}
        </Box>

        <CardContent sx={{ flexGrow: 1, pt: 3 }}>
          {/* Candidate Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Avatar
              sx={{
                bgcolor: `${riskColor}.main`,
                width: 56,
                height: 56,
              }}
            >
              <PersonIcon sx={{ fontSize: 32 }} />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {candidate.name || t('atRiskCandidates.anonymousCandidate')}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <WorkIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {candidate.title || t('atRiskCandidates.noTitle')}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Risk Score */}
          <Box sx={{ mb: 2, textAlign: 'center' }}>
            <Tooltip title={t('atRiskCandidates.riskScoreTooltip')}>
              <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                <WarningIcon fontSize="small" color={riskColor as any} />
                <Typography variant="caption" color="text.secondary">
                  {t('atRiskCandidates.riskScore')}
                </Typography>
              </Box>
            </Tooltip>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <Typography variant="h3" fontWeight={700} color={`${riskColor}.main` as any}>
                {riskPercent}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={riskPercent}
              sx={{ height: 8, borderRadius: 4, mt: 1 }}
              color={riskColor as any}
            />
          </Box>

          {/* Risk Level Badge */}
          <Box sx={{ mb: 2, textAlign: 'center' }}>
            <Chip
              icon={<WarningIcon />}
              label={t(`atRiskCandidates.${candidate.risk_level.toLowerCase()}`)}
              color={riskColor as any}
              sx={{ fontWeight: 600 }}
            />
          </Box>

          {/* Days Since Contact */}
          <Box sx={{ mb: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {t('atRiskCandidates.daysSinceContact')}:{' '}
              <strong>
                {candidate.days_since_contact !== null
                  ? `${candidate.days_since_contact} ${t('common.days')}`
                  : t('atRiskCandidates.neverContacted')}
              </strong>
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
                {isExpanded ? t('atRiskCandidates.hide') : t('atRiskCandidates.show')}
              </Typography>
            </IconButton>
          </Box>

          {/* Risk Details (Collapsible) */}
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              {/* Risk Factors */}
              {candidate.risk_factors && candidate.risk_factors.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                    <WarningIcon fontSize="small" color="error" />
                    <Typography variant="subtitle2" fontWeight={600} color="error">
                      {t('atRiskCandidates.riskFactors')}
                    </Typography>
                  </Box>
                  <Stack spacing={0.5}>
                    {candidate.risk_factors.map((factor, idx) => (
                      <Box
                        key={`factor-${idx}`}
                        sx={{
                          px: 1,
                          py: 0.5,
                          borderRadius: 1,
                          bgcolor: 'error.50',
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          • {factor}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                </Box>
              )}

              {/* Recommended Action */}
              {candidate.recommended_action && (
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                    <InfoIcon fontSize="small" color="info" />
                    <Typography variant="subtitle2" fontWeight={600} color="primary">
                      {t('atRiskCandidates.recommendedAction')}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      px: 1,
                      py: 1,
                      borderRadius: 1,
                      bgcolor: 'info.50',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    {getActionIcon(candidate.recommended_action)}
                    <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
                      {candidate.recommended_action}
                    </Typography>
                  </Box>
                </Box>
              )}

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<PhoneIcon />}
                  color="primary"
                >
                  {t('atRiskCandidates.contactNow')}
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<EventIcon />}
                  color="primary"
                >
                  {t('atRiskCandidates.scheduleInterview')}
                </Button>
              </Box>
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
          {t('atRiskCandidates.loading')}
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

  if (!atRiskData || atRiskData.candidates.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <AIIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          {t('atRiskCandidates.noCandidates')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('atRiskCandidates.notEnoughData')}
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
          background: (theme) => `linear-gradient(135deg, ${theme.palette.error.main} 0%, ${theme.palette.warning.main} 100%)`,
          color: 'error.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <WarningIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                {t('atRiskCandidates.title')}
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {t('atRiskCandidates.subtitle')}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
              {t('atRiskCandidates.found', { count: atRiskData.total_candidates })}
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
              {atRiskData.candidates.length}
            </Typography>
            <Typography variant="caption">{t('atRiskCandidates.candidates')}</Typography>
          </Box>
        </Box>
      </Paper>

      {/* At-Risk Candidates Grid */}
      <Grid container spacing={3}>
        {atRiskData.candidates.map((candidate, index) => (
          <Grid item xs={12} md={6} lg={4} key={candidate.resume_id}>
            <AtRiskCandidateCard candidate={candidate} index={index} />
          </Grid>
        ))}
      </Grid>

      {/* Model Info Footer */}
      <Paper sx={{ p: 2, mt: 3, bgcolor: 'action.hover' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>{t('atRiskCandidates.algorithmVersion')}:</strong> {atRiskData.algorithm_version}
          {' • '}
          <strong>{t('atRiskCandidates.generatedAt')}:</strong>{' '}
          {new Date().toLocaleString()}
          {' • '}
          <strong>{t('atRiskCandidates.aiPowered')}</strong>
        </Typography>
      </Paper>
    </Box>
  );
};

export default AtRiskCandidates;

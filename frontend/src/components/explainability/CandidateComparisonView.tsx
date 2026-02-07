import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  Grid,
  Divider,
  Card,
  CardContent,
  Tooltip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  EmojiEvents as TrophyIcon,
  Person as PersonIcon,
  Key as KeywordIcon,
  Tune as TfidfIcon,
  Psychology as VectorIcon,
  TrendingUp as PositiveIcon,
  TrendingDown as NegativeIcon,
  CompareArrows as CompareIcon,
  CheckCircle as BetterIcon,
  Cancel as WorseIcon,
  Remove as EqualIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api/client';

/**
 * Individual candidate score breakdown from backend
 */
interface CandidateScoreBreakdown {
  resume_id: string;
  filename: string;
  candidate_name?: string;
  match_score: {
    overall_score: number;
    keyword_score: number;
    tfidf_score: number;
    vector_score: number;
  };
  passed: boolean;
  recommendation: string;
  matched_skills: string[];
  missing_skills: string[];
  rank: number;
  feature_contributions?: {
    feature_name: string;
    contribution: number;
    direction: 'positive' | 'negative';
  }[];
}

/**
 * Candidate comparison data structure from backend
 */
interface CandidateComparisonData {
  vacancy_id: string;
  vacancy_title: string;
  candidates: CandidateScoreBreakdown[];
  summary: {
    total_candidates: number;
    best_score: number;
    average_score: number;
    worst_score: number;
    passed_count: number;
  };
  differences?: {
    feature_name: string;
    best_candidate_id: string;
    difference_percentage: number;
    explanation: string;
  }[];
  processing_time_ms: number;
}

/**
 * CandidateComparisonView Component Props
 */
interface CandidateComparisonViewProps {
  /** Vacancy ID for the comparison */
  vacancyId: string;
  /** Array of resume IDs to compare (2-10 candidates) */
  resumeIds: string[];
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
  /** Whether to show detailed feature-level differences */
  showDetailedDifferences?: boolean;
}

/**
 * Helper to get score color
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  const percentage = score * 100;
  if (percentage >= 70) return 'success';
  if (percentage >= 40) return 'warning';
  return 'error';
};

/**
 * Helper to get score label
 */
const getScoreLabel = (score: number): string => {
  const percentage = score * 100;
  if (percentage >= 70) return 'Excellent';
  if (percentage >= 40) return 'Moderate';
  return 'Poor';
};

/**
 * Calculate difference indicator between two values
 */
const getDifferenceIndicator = (
  value1: number,
  value2: number,
  isFirstBetter: boolean
): 'better' | 'worse' | 'equal' => {
  const diff = Math.abs(value1 - value2);
  if (diff < 0.01) return 'equal';
  if (isFirstBetter) return value1 > value2 ? 'better' : 'worse';
  return value2 > value1 ? 'better' : 'worse';
};

/**
 * CandidateComparisonView Component
 *
 * Displays side-by-side comparison of top candidates with highlighted differences:
 * - Visual comparison cards for each candidate
 * - Side-by-side score breakdowns
 * - Difference highlighting showing why one candidate ranked higher
 * - Feature-level comparison with win/loss indicators
 * - Skills matched vs missing comparison
 * - Responsive layout (cards on mobile, side-by-side on desktop)
 *
 * @example
 * ```tsx
 * <CandidateComparisonView
 *   vacancyId="vacancy-123"
 *   resumeIds={['resume-1', 'resume-2', 'resume-3']}
 *   showDetailedDifferences={true}
 * />
 * ```
 */
const CandidateComparisonView: React.FC<CandidateComparisonViewProps> = ({
  vacancyId,
  resumeIds,
  apiUrl = '/api/matching/compare-candidates',
  showDetailedDifferences = true,
}) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CandidateComparisonData | null>(null);
  const [expandedCandidates, setExpandedCandidates] = useState<Set<string>>(new Set());

  /**
   * Fetch candidate comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<CandidateComparisonData>(apiUrl, {
        vacancy_id: vacancyId,
        resume_ids: resumeIds,
      });

      setData(response.data);

      // Auto-expand top 2 candidates
      if (response.data.candidates.length >= 2) {
        setExpandedCandidates(new Set([
          response.data.candidates[0].resume_id,
          response.data.candidates[1].resume_id,
        ]));
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('candidateComparison.error.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (vacancyId && resumeIds && resumeIds.length > 0) {
      fetchComparison();
    } else if (!resumeIds || resumeIds.length === 0) {
      setError(t('candidateComparison.error.noCandidates'));
      setLoading(false);
    }
  }, [vacancyId, resumeIds]);

  /**
   * Toggle candidate card expansion
   */
  const toggleExpand = (resumeId: string) => {
    setExpandedCandidates((prev) => {
      const next = new Set(prev);
      if (next.has(resumeId)) {
        next.delete(resumeId);
      } else {
        next.add(resumeId);
      }
      return next;
    });
  };

  /**
   * Find best score in a specific category
   */
  const getBestScore = (
    category: 'overall_score' | 'keyword_score' | 'tfidf_score' | 'vector_score'
  ): number => {
    if (!data || !data.candidates || data.candidates.length === 0) return 0;
    return Math.max(...data.candidates.map((c) => c.match_score[category]));
  };

  /**
   * Get difference icon for comparison
   */
  const getDifferenceIcon = (indicator: 'better' | 'worse' | 'equal') => {
    switch (indicator) {
      case 'better':
        return <BetterIcon fontSize="small" color="success" />;
      case 'worse':
        return <WorseIcon fontSize="small" color="error" />;
      case 'equal':
        return <EqualIcon fontSize="small" color="disabled" />;
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
          {t('candidateComparison.loading.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('candidateComparison.loading.subtitle', { count: resumeIds.length })}
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
            {t('candidateComparison.error.retry')}
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          {t('candidateComparison.error.title')}
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data || !data.candidates || data.candidates.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          {t('candidateComparison.noData.title')}
        </Typography>
        <Typography variant="body2">
          {t('candidateComparison.noData.message')}
        </Typography>
      </Alert>
    );
  }

  // Get best scores for highlighting
  const bestOverall = getBestScore('overall_score');
  const bestKeyword = getBestScore('keyword_score');
  const bestTfidf = getBestScore('tfidf_score');
  const bestVector = getBestScore('vector_score');

  /**
   * Render score comparison with highlighting
   */
  const ScoreComparison: React.FC<{
    label: string;
    icon: React.ReactNode;
    score: number;
    bestScore: number;
    weight?: string;
    showComparison?: boolean;
    referenceScore?: number;
  }> = ({ label, icon, score, bestScore, weight, showComparison = false, referenceScore }) => {
    const percentage = Math.round(score * 100);
    const color = getScoreColor(score);
    const isBest = score === bestScore;

    let comparisonIcon: React.ReactNode = null;
    if (showComparison && referenceScore !== undefined) {
      const indicator = getDifferenceIndicator(score, referenceScore, true);
      comparisonIcon = getDifferenceIcon(indicator);
    }

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {icon}
            <Typography variant="caption" color="text.secondary">
              {label} {weight && `(${weight})`}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography
              variant="body2"
              fontWeight={600}
              color={isBest ? `${color}.main` : 'text.primary'}
            >
              {percentage}%
            </Typography>
            {isBest && <TrophyIcon sx={{ fontSize: 14, color: `${color}.main` }} />}
            {comparisonIcon}
          </Box>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={color}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: isBest ? `${color}.100` : 'grey.200',
            ...(isBest && {
              boxShadow: `0 0 0 2px ${color}.main`,
            }),
          }}
        />
      </Box>
    );
  };

  /**
   * Render candidate card
   */
  const CandidateCard: React.FC<{
    candidate: CandidateScoreBreakdown;
    rank: number;
    isExpanded: boolean;
    referenceCandidate?: CandidateScoreBreakdown;
  }> = ({ candidate, rank, isExpanded, referenceCandidate }) => {
    const isBestOverall = candidate.match_score.overall_score === bestOverall;

    return (
      <Card
        elevation={isBestOverall ? 4 : 2}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: isBestOverall ? 2 : 0,
          borderColor: `${getScoreColor(candidate.match_score.overall_score)}.main`,
          transition: 'all 0.2s',
          '&:hover': {
            elevation: isBestOverall ? 6 : 4,
          },
        }}
      >
        <CardContent sx={{ flex: 1, p: 2 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar
              sx={{
                mr: 2,
                bgcolor: rank === 1 ? 'warning.main' : 'primary.main',
                width: 48,
                height: 48,
              }}
            >
              {rank === 1 ? <TrophyIcon /> : <PersonIcon />}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={700} noWrap>
                #{rank} {candidate.candidate_name || candidate.filename}
              </Typography>
              <Typography variant="caption" color="text.secondary" noWrap>
                {candidate.filename}
              </Typography>
            </Box>
            <Chip
              label={`${Math.round(candidate.match_score.overall_score * 100)}%`}
              color={getScoreColor(candidate.match_score.overall_score)}
              sx={{ fontWeight: 700 }}
            />
          </Box>

          {/* Overall Score */}
          <Box
            sx={{
              mb: 2,
              p: 1.5,
              borderRadius: 2,
              bgcolor: `${getScoreColor(candidate.match_score.overall_score)}.50`,
              textAlign: 'center',
            }}
          >
            <Typography variant="caption" color="text.secondary" display="block">
              {t('candidateComparison.overallScore')}
            </Typography>
            <Typography variant="h4" fontWeight={700} color={`${getScoreColor(candidate.match_score.overall_score)}.main`}>
              {Math.round(candidate.match_score.overall_score * 100)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {getScoreLabel(candidate.match_score.overall_score)} Match
            </Typography>
          </Box>

          {/* Score Breakdown */}
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('candidateComparison.scoreBreakdown')}
          </Typography>

          <ScoreComparison
            label={t('candidateComparison.keywordScore')}
            icon={<KeywordIcon sx={{ fontSize: 16, color: 'primary.main' }} />}
            score={candidate.match_score.keyword_score}
            bestScore={bestKeyword}
            weight="50%"
            showComparison={!!referenceCandidate}
            referenceScore={referenceCandidate?.match_score.keyword_score}
          />

          <ScoreComparison
            label={t('candidateComparison.tfidfScore')}
            icon={<TfidfIcon sx={{ fontSize: 16, color: 'secondary.main' }} />}
            score={candidate.match_score.tfidf_score}
            bestScore={bestTfidf}
            weight="30%"
            showComparison={!!referenceCandidate}
            referenceScore={referenceCandidate?.match_score.tfidf_score}
          />

          <ScoreComparison
            label={t('candidateComparison.vectorScore')}
            icon={<VectorIcon sx={{ fontSize: 16, color: 'info.main' }} />}
            score={candidate.match_score.vector_score}
            bestScore={bestVector}
            weight="20%"
            showComparison={!!referenceCandidate}
            referenceScore={referenceCandidate?.match_score.vector_score}
          />

          {/* Skills Summary */}
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              {t('candidateComparison.skills')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
              <Typography variant="body2" color="success.main" fontWeight={600}>
                {candidate.matched_skills.length} {t('candidateComparison.matched')}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
              <Typography variant="body2" color="error.main" fontWeight={600}>
                {candidate.missing_skills.length} {t('candidateComparison.missing')}
              </Typography>
            </Box>
          </Box>

          {/* Feature Contributions (if available and expanded) */}
          {showDetailedDifferences && candidate.feature_contributions && isExpanded && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('candidateComparison.featureContributions')}
              </Typography>
              <Stack spacing={1}>
                {candidate.feature_contributions.slice(0, 5).map((feature, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      p: 1,
                      borderRadius: 1,
                      bgcolor: feature.direction === 'positive' ? 'success.50' : 'error.50',
                    }}
                  >
                    {feature.direction === 'positive' ? (
                      <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
                    ) : (
                      <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
                    )}
                    <Typography variant="caption" sx={{ flex: 1 }}>
                      {feature.feature_name}
                    </Typography>
                    <Typography variant="caption" fontWeight={600} color={feature.direction === 'positive' ? 'success.main' : 'error.main'}>
                      {feature.direction === 'positive' ? '+' : ''}{(feature.contribution * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </>
          )}

          {/* Recommendation */}
          {candidate.recommendation && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                {t('candidateComparison.recommendation')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {candidate.recommendation}
              </Typography>
            </>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CompareIcon sx={{ fontSize: 28, color: 'primary.main' }} />
              <Typography variant="h5" fontWeight={600}>
                {t('candidateComparison.title')}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {data.vacancy_title} • {t('candidateComparison.subtitle', { count: data.candidates.length })}
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            {t('candidateComparison.refresh')}
          </Button>
        </Box>

        {/* Summary Stats */}
        {data.summary && (
          <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={<TrophyIcon />}
              label={`${t('candidateComparison.best')}: ${Math.round(data.summary.best_score * 100)}%`}
              color="success"
              variant="outlined"
            />
            <Chip
              label={`${t('candidateComparison.average')}: ${Math.round(data.summary.average_score * 100)}%`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${t('candidateComparison.passed')}: ${data.summary.passed_count}/${data.summary.total_candidates}`}
              color={data.summary.passed_count > 0 ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>
        )}
      </Paper>

      {/* Key Differences */}
      {showDetailedDifferences && data.differences && data.differences.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {t('candidateComparison.keyDifferences')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('candidateComparison.keyDifferencesDescription')}
          </Typography>
          <Grid container spacing={2}>
            {data.differences.slice(0, isMobile ? 2 : 4).map((diff, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    borderLeft: 4,
                    borderColor: 'primary.main',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <CompareIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                    <Typography variant="subtitle2" fontWeight={600}>
                      {diff.feature_name}
                    </Typography>
                    <Chip
                      label={`+${diff.difference_percentage.toFixed(1)}%`}
                      size="small"
                      color="primary"
                      sx={{ ml: 'auto', fontWeight: 700 }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {diff.explanation}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Candidate Comparison Cards */}
      <Grid container spacing={2}>
        {data.candidates.map((candidate, index) => {
          const isExpanded = expandedCandidates.has(candidate.resume_id);
          // Use top candidate as reference for comparison
          const referenceCandidate = index > 0 ? data.candidates[0] : undefined;

          return (
            <Grid item xs={12} md={data.candidates.length === 2 ? 6 : 4} key={candidate.resume_id}>
              <CandidateCard
                candidate={candidate}
                rank={index + 1}
                isExpanded={isExpanded}
                referenceCandidate={referenceCandidate}
              />
            </Grid>
          );
        })}
      </Grid>

      {/* Legend */}
      <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrophyIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {t('candidateComparison.legend.best')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <BetterIcon sx={{ fontSize: 18, color: 'success.main' }} />
            <Typography variant="caption" color="text.secondary">
              {t('candidateComparison.legend.better')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <WorseIcon sx={{ fontSize: 18, color: 'error.main' }} />
            <Typography variant="caption" color="text.secondary">
              {t('candidateComparison.legend.worse')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <EqualIcon sx={{ fontSize: 18, color: 'disabled.main' }} />
            <Typography variant="caption" color="text.secondary">
              {t('candidateComparison.legend.equal')}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Processing Time */}
      {data.processing_time_ms && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          {t('candidateComparison.processingTime', { seconds: (data.processing_time_ms / 1000).toFixed(2) })}
        </Typography>
      )}
    </Stack>
  );
};

export default CandidateComparisonView;

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Chip,
  Grid,
  Divider,
  Tooltip,
} from '@mui/material';
import { config } from '@/config';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';

/**
 * Ranking feature weights (13 fields)
 */
export interface RankingFeatureWeights {
  skill_match_weight: number;
  experience_weight: number;
  education_weight: number;
  location_weight: number;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  recency_weight: number;
  culture_fit_weight: number;
  salary_match_weight: number;
  availability_weight: number;
  certifications_weight: number;
  industry_experience_weight: number;
}

/**
 * Individual candidate ranking from backend
 */
interface CandidateRanking {
  candidate_id: string;
  candidate_name: string | null;
  match_score: number;
  rank: number;
}

/**
 * Preview rankings response from backend
 */
interface PreviewRankingsResponse {
  vacancy_id: string;
  weights_used: RankingFeatureWeights;
  rankings: CandidateRanking[];
  total_candidates: number;
}

/**
 * Candidate ranking with comparison data
 */
interface CandidateRankingComparison {
  candidate_id: string;
  candidate_name: string;
  before_rank: number;
  after_rank: number;
  before_score: number;
  after_score: number;
  rank_change: number;
  score_change: number;
}

/**
 * MatchingWeightsPreview Component Props
 */
interface MatchingWeightsPreviewProps {
  /** Vacancy ID for the preview */
  vacancyId: string;
  /** Current/baseline weights configuration */
  baselineWeights: RankingFeatureWeights;
  /** Modified/new weights configuration to preview */
  modifiedWeights: RankingFeatureWeights;
  /** Optional list of candidate IDs to limit preview to */
  candidateIds?: string[];
  /** API endpoint URL for fetching preview results */
  apiUrl?: string;
}

/**
 * Helper to get rank change color
 */
const getRankChangeColor = (change: number): 'success' | 'error' | 'default' => {
  if (change < 0) return 'success'; // Improved rank (lower number)
  if (change > 0) return 'error'; // Worse rank (higher number)
  return 'default';
};

/**
 * Helper to get rank change icon
 */
const getRankChangeIcon = (change: number) => {
  if (change < 0) return <TrendingUpIcon sx={{ fontSize: 16 }} />;
  if (change > 0) return <TrendingDownIcon sx={{ fontSize: 16 }} />;
  return <TrendingFlatIcon sx={{ fontSize: 16 }} />;
};

/**
 * Helper to format percentage
 */
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * MatchingWeightsPreview Component
 *
 * Displays before/after ranking comparison when matching algorithm weights are adjusted:
 * - Side-by-side comparison of candidate rankings
 * - Rank change indicators (up/down/same)
 * - Match score differences
 * - Highlighting of significant changes
 * - Responsive table layout
 *
 * @example
 * ```tsx
 * <MatchingWeightsPreview
 *   vacancyId="vacancy-123"
 *   baselineWeights={currentWeights}
 *   modifiedWeights={newWeights}
 * />
 * ```
 */
const MatchingWeightsPreview: React.FC<MatchingWeightsPreviewProps> = ({
  vacancyId,
  baselineWeights,
  modifiedWeights,
  candidateIds,
  apiUrl = `${config.api.url}/api/matching-weights`,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [beforeData, setBeforeData] = useState<PreviewRankingsResponse | null>(null);
  const [afterData, setAfterData] = useState<PreviewRankingsResponse | null>(null);
  const [comparison, setComparison] = useState<CandidateRankingComparison[]>([]);

  /**
   * Fetch preview rankings for a given set of weights
   */
  const fetchPreview = async (weights: RankingFeatureWeights): Promise<PreviewRankingsResponse> => {
    const response = await fetch(`${apiUrl}/preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        vacancy_id: vacancyId,
        ...weights,
        candidate_ids: candidateIds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch preview: ${response.statusText}`);
    }

    return await response.json();
  };

  /**
   * Fetch both before and after rankings
   */
  const fetchComparison = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch both baseline and modified rankings in parallel
      const [beforeResult, afterResult] = await Promise.all([
        fetchPreview(baselineWeights),
        fetchPreview(modifiedWeights),
      ]);

      setBeforeData(beforeResult);
      setAfterData(afterResult);

      // Create comparison data
      const comparisonData: CandidateRankingComparison[] = [];

      // Map candidate IDs to their before/after data
      const beforeMap = new Map(
        beforeResult.rankings.map((r) => [r.candidate_id, r])
      );
      const afterMap = new Map(
        afterResult.rankings.map((r) => [r.candidate_id, r])
      );

      // Get all unique candidate IDs
      const allCandidateIds = new Set([
        ...beforeResult.rankings.map((r) => r.candidate_id),
        ...afterResult.rankings.map((r) => r.candidate_id),
      ]);

      allCandidateIds.forEach((candidateId) => {
        const before = beforeMap.get(candidateId);
        const after = afterMap.get(candidateId);

        if (before && after) {
          comparisonData.push({
            candidate_id: candidateId,
            candidate_name: after.candidate_name || before.candidate_name || candidateId,
            before_rank: before.rank,
            after_rank: after.rank,
            before_score: before.match_score,
            after_score: after.match_score,
            rank_change: after.rank - before.rank,
            score_change: after.match_score - before.match_score,
          });
        }
      });

      // Sort by after_rank
      comparisonData.sort((a, b) => a.after_rank - b.after_rank);
      setComparison(comparisonData);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load preview data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [vacancyId, baselineWeights, modifiedWeights, candidateIds, apiUrl]);

  useEffect(() => {
    if (vacancyId) {
      fetchComparison();
    } else {
      setError('Vacancy ID is required for preview');
      setLoading(false);
    }
  }, [vacancyId, fetchComparison]);

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
          Calculating ranking changes...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Comparing baseline and modified weight configurations
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert severity="error">
        <Typography variant="subtitle1" fontWeight={600}>
          Preview Failed
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!beforeData || !afterData || comparison.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Preview Data
        </Typography>
        <Typography variant="body2">
          No candidates found for comparison. Check that the vacancy ID is valid and has candidates.
        </Typography>
      </Alert>
    );
  }

  // Calculate statistics
  const significantChanges = comparison.filter((c) => Math.abs(c.rank_change) >= 3);
  const avgScoreChange = comparison.reduce((sum, c) => sum + c.score_change, 0) / comparison.length;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Ranking Preview: Before vs After
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Compare how weight changes affect candidate rankings
        </Typography>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {comparison.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Candidates
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main" fontWeight={700}>
                {significantChanges.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Significant Changes (&ge;3 ranks)
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
              <Typography
                variant="h4"
                color={avgScoreChange >= 0 ? 'success.main' : 'error.main'}
                fontWeight={700}
              >
                {avgScoreChange >= 0 ? '+' : ''}
                {formatPercentage(avgScoreChange)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Score Change
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Paper>

      {/* Desktop Table View */}
      <Box sx={{ display: { xs: 'none', md: 'block' } }}>
        <TableContainer component={Paper} elevation={1}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 200 }}>
                  Candidate
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 100 }}>
                  Before Rank
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 100 }}>
                  After Rank
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  Change
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  Before Score
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  After Score
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  Score Change
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparison.map((candidate, index) => {
                const isSignificant = Math.abs(candidate.rank_change) >= 3;
                const isTopRank = candidate.after_rank <= 3;

                return (
                  <TableRow
                    key={candidate.candidate_id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      ...(isSignificant && {
                        bgcolor: 'warning.50',
                      }),
                    }}
                  >
                    {/* Candidate Name */}
                    <TableCell sx={{ fontWeight: 600 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {isTopRank && (
                          <TrophyIcon
                            sx={{
                              fontSize: 20,
                              color: candidate.after_rank === 1 ? 'warning.main' : 'text.secondary',
                            }}
                          />
                        )}
                        <Typography variant="body2" fontWeight={600}>
                          {candidate.candidate_name}
                        </Typography>
                      </Box>
                    </TableCell>

                    {/* Before Rank */}
                    <TableCell align="center">
                      <Chip label={`#${candidate.before_rank}`} size="small" variant="outlined" />
                    </TableCell>

                    {/* After Rank */}
                    <TableCell align="center">
                      <Chip
                        label={`#${candidate.after_rank}`}
                        size="small"
                        color={isTopRank ? 'primary' : 'default'}
                        sx={{ fontWeight: isTopRank ? 700 : 400 }}
                      />
                    </TableCell>

                    {/* Rank Change */}
                    <TableCell align="center">
                      {candidate.rank_change === 0 ? (
                        <Chip
                          icon={<TrendingFlatIcon />}
                          label="No change"
                          size="small"
                          color="default"
                        />
                      ) : (
                        <Tooltip
                          title={
                            candidate.rank_change < 0
                              ? `Improved by ${Math.abs(candidate.rank_change)} positions`
                              : `Dropped by ${candidate.rank_change} positions`
                          }
                        >
                          <Chip
                            icon={getRankChangeIcon(candidate.rank_change)}
                            label={`${candidate.rank_change > 0 ? '+' : ''}${candidate.rank_change}`}
                            size="small"
                            color={getRankChangeColor(candidate.rank_change)}
                            sx={{ fontWeight: 600 }}
                          />
                        </Tooltip>
                      )}
                    </TableCell>

                    {/* Before Score */}
                    <TableCell align="center">
                      <Typography variant="body2" color="text.secondary">
                        {formatPercentage(candidate.before_score)}
                      </Typography>
                    </TableCell>

                    {/* After Score */}
                    <TableCell align="center">
                      <Typography variant="body2" fontWeight={600}>
                        {formatPercentage(candidate.after_score)}
                      </Typography>
                    </TableCell>

                    {/* Score Change */}
                    <TableCell align="center">
                      <Typography
                        variant="body2"
                        color={
                          candidate.score_change > 0
                            ? 'success.main'
                            : candidate.score_change < 0
                            ? 'error.main'
                            : 'text.secondary'
                        }
                        fontWeight={600}
                      >
                        {candidate.score_change >= 0 ? '+' : ''}
                        {formatPercentage(candidate.score_change)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Mobile Card View */}
      <Box sx={{ display: { xs: 'block', md: 'none' } }}>
        <Stack spacing={2}>
          {comparison.map((candidate) => {
            const isSignificant = Math.abs(candidate.rank_change) >= 3;
            const isTopRank = candidate.after_rank <= 3;

            return (
              <Paper
                key={candidate.candidate_id}
                variant="outlined"
                sx={{
                  p: 2,
                  ...(isSignificant && {
                    border: 2,
                    borderColor: 'warning.main',
                  }),
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {isTopRank && (
                      <TrophyIcon
                        sx={{
                          fontSize: 20,
                          color: candidate.after_rank === 1 ? 'warning.main' : 'text.secondary',
                        }}
                      />
                    )}
                    <Typography variant="subtitle1" fontWeight={700}>
                      {candidate.candidate_name}
                    </Typography>
                  </Box>
                  {candidate.rank_change !== 0 && (
                    <Chip
                      icon={getRankChangeIcon(candidate.rank_change)}
                      label={`${candidate.rank_change > 0 ? '+' : ''}${candidate.rank_change}`}
                      size="small"
                      color={getRankChangeColor(candidate.rank_change)}
                      sx={{ fontWeight: 600 }}
                    />
                  )}
                </Box>

                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Before Rank
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      #{candidate.before_rank}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      After Rank
                    </Typography>
                    <Typography variant="body2" fontWeight={700} color="primary.main">
                      #{candidate.after_rank}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 1 }} />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Before Score
                    </Typography>
                    <Typography variant="body2">
                      {formatPercentage(candidate.before_score)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      After Score
                    </Typography>
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      color={
                        candidate.score_change > 0
                          ? 'success.main'
                          : candidate.score_change < 0
                          ? 'error.main'
                          : 'text.primary'
                      }
                    >
                      {formatPercentage(candidate.after_score)} (
                      {candidate.score_change >= 0 ? '+' : ''}
                      {formatPercentage(candidate.score_change)})
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            );
          })}
        </Stack>
      </Box>

      {/* Legend */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" gutterBottom>
          Legend
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
            <Typography variant="caption" color="text.secondary">
              Rank improved
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
            <Typography variant="caption" color="text.secondary">
              Rank dropped
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingFlatIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              No change
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: 'warning.50',
                border: '1px solid',
                borderColor: 'warning.main',
                borderRadius: 0.5,
              }}
            />
            <Typography variant="caption" color="text.secondary">
              Significant change (&ge;3 ranks)
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Stack>
  );
};

export default MatchingWeightsPreview;
